"""Actual pinned HACS: opt-in beta from stable, with main/stable left unchanged."""

import base64
import importlib
import io
import json
import os
import sqlite3
import subprocess
import zipfile
from contextlib import closing
from importlib.metadata import version
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from aiogithubapi.models.release import GitHubReleaseModel
from awesomeversion import AwesomeVersion

from tools.prepare_hacs_reference import PINS

from .test_hacs_workflow import candidate_tree, upstream

ROOT = Path(__file__).parents[1]
DOMAIN = "ha_energy_price_engine"
TAG = "v1.1.0-beta.1"
STABLE = "v1.0.0"


def inputs():
    stable = json.loads((ROOT / "docs/receipts/v1.0.0.json").read_text())
    reference = next(iter(stable["public_verification_receipts"].values()))
    if path := os.environ.get("PE_PUBLIC_BETA_RECEIPT"):
        receipt = json.loads(Path(path).read_text())
        beta = Path(receipt["source_archive"]).read_bytes()
        main = Path(receipt["main_archive"]).read_bytes()
        old = Path(receipt["previous_stable_asset"]).read_bytes()
        old_prefix = ""
        feed = receipt["releases"]
    else:
        receipt = {"repository": reference["repository"], "source_commit": "candidate-beta-source"}
        main = subprocess.check_output(
            ["git", "archive", "--format=zip", STABLE, f"custom_components/{DOMAIN}", "hacs.json"],
            cwd=ROOT,
        )
        old = main
        old_prefix = f"custom_components/{DOMAIN}/"
        content = io.BytesIO()
        with zipfile.ZipFile(content, "w") as z:
            for name, data in candidate_tree().items():
                z.writestr("beta-source/" + name, data)
        beta = content.getvalue()
        feed = [
            {"tag_name": TAG, "prerelease": True, "draft": False, "assets": []},
            reference["release"],
        ]

    def unpack(payload):
        with zipfile.ZipFile(io.BytesIO(payload)) as z:
            files = {n: z.read(n) for n in z.namelist() if not n.endswith("/")}
        if "hacs.json" not in files:
            files = {"/".join(n.split("/")[1:]): d for n, d in files.items()}
        return files

    return receipt, unpack(beta), unpack(main), beta, main, old, old_prefix, feed


@pytest.mark.parametrize("line", list(PINS))
async def test_beta_opt_in_native_update_install_and_stable_isolation(hass, tmp_path, line):
    (
        receipt,
        files,
        main_files,
        beta,
        main,
        old,
        old_prefix,
        feed,
    ) = await hass.async_add_executor_job(inputs)
    alias = upstream(line)
    base = importlib.import_module(alias + ".base")
    repo_base = importlib.import_module(alias + ".repositories.base")
    enums = importlib.import_module(alias + ".enums")
    hacs = base.HacsBase()
    hacs.hass = hass
    hacs.core.config_path = tmp_path
    hacs.core.ha_version = AwesomeVersion(version("homeassistant"))
    hacs.version = AwesomeVersion("2.0.5")
    hacs.queue = SimpleNamespace(has_pending_tasks=False)
    hacs.async_dispatch = Mock()
    hacs.githubapi = SimpleNamespace(
        repos=SimpleNamespace(
            contents=SimpleNamespace(get=Mock()), releases=SimpleNamespace(list=Mock())
        )
    )
    repository = receipt["repository"]["full_name"]
    obj = SimpleNamespace(
        full_name=repository,
        attributes=receipt["repository"],
        last_commit="stable-main",
        set_last_commit=AsyncMock(),
    )

    def tree(payload):
        directories = {str(p) for n in payload for p in Path(n).parents if str(p) != "."}
        return [
            SimpleNamespace(
                path=n,
                full_path=n,
                filename=Path(n).name,
                is_directory=n in directories,
                type="tree" if n in directories else "blob",
                url="https://api.github.com/recorded",
            )
            for n in sorted(set(payload) | directories)
        ]

    async def get_tree(repo, ref=None):
        return tree(files if ref == TAG else main_files)

    async def github(*, method=None, path=None, **kwargs):
        if method is hacs.githubapi.repos.releases.list:
            return SimpleNamespace(data=[GitHubReleaseModel(r) for r in feed])
        payload = files if kwargs.get("params", {}).get("ref") == TAG else main_files
        return SimpleNamespace(
            data=SimpleNamespace(content=base64.b64encode(payload[path]).decode())
        )

    calls = []

    async def download(url, **kwargs):
        calls.append(url)
        if url.endswith(f"/archive/refs/tags/{TAG}.zip"):
            return beta
        if url.endswith(f"/archive/refs/tags/{STABLE}.zip"):
            return main
        if "raw.githubusercontent.com" in url:
            for ref, payload in ((TAG, files), (STABLE, main_files)):
                if f"/{ref}/" in url:
                    return payload.get(url.split(f"/{ref}/", 1)[1], b"Read-only PE")
            raise AssertionError(url)
        raise AssertionError(url)

    async def commits(repo):
        repo.data.last_commit = "newer-main-sha"

    hacs.async_github_api_method = AsyncMock(side_effect=github)
    hacs.async_download_file = AsyncMock(side_effect=download)
    backup = repo_base.Backup

    def isolated_backup(**kwargs):
        kwargs.setdefault("backup_path", str(tmp_path / "backups") + "/")
        return backup(**kwargs)

    hass.data["custom_components"] = {}
    with (
        patch.object(
            repo_base.HacsRepository,
            "async_get_legacy_repository_object",
            AsyncMock(return_value=(obj, "public-metadata")),
        ),
        patch.object(repo_base.HacsRepository, "get_tree", get_tree),
        patch.object(repo_base.HacsRepository, "async_set_last_commits", commits, create=True),
        patch.object(repo_base, "Backup", side_effect=isolated_backup),
    ):
        await hacs.async_register_repository(repository, enums.HacsCategory.INTEGRATION)
        repo = hacs.repositories.get_by_full_name(repository)
        assert repo and repo.data.config_flow and not repo.data.show_beta
        hacs.coordinators[enums.HacsCategory.INTEGRATION] = Mock()
        update = importlib.import_module(alias + ".update").HacsRepositoryUpdateEntity(
            hacs=hacs, repository=repo
        )
        assert update.latest_version == STABLE and TAG not in repo.data.published_tags
        assert repo.version_to_download() == STABLE
        installed = tmp_path / "custom_components" / DOMAIN
        installed.mkdir(parents=True)
        with zipfile.ZipFile(io.BytesIO(old)) as z:
            for name in z.namelist():
                if name.startswith(old_prefix) and not name.endswith("/"):
                    target = installed / name.removeprefix(old_prefix)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(z.read(name))
        assert json.loads((installed / "manifest.json").read_text())["version"] == "1.0.0"
        history = tmp_path / ".storage" / "pe-preserved.ledger.sqlite3"
        history.parent.mkdir()
        with closing(sqlite3.connect(history)) as db:
            db.execute("CREATE TABLE historical_revisions(revision INTEGER)")
            db.execute("INSERT INTO historical_revisions VALUES (7)")
            db.commit()
        original = history.read_bytes()
        repo.data.installed = True
        repo.data.installed_version = STABLE
        repo.data.show_beta = True
        await repo.common_update_data(force=True)
        assert (
            update.latest_version == TAG
            and TAG in repo.data.published_tags
            and update.state == "on"
        )
        # HACS retains stable as its default download until the user selects a beta.
        repo.data.selected_tag = TAG
        assert repo.version_to_download() == TAG
        for _ in range(2):
            await repo.async_download_repository(ref=TAG)
            assert repo.data.installed_version == TAG and update.state == "off"
            assert (
                json.loads((installed / "manifest.json").read_text())["version"] == "1.1.0-beta.1"
            )
            assert (installed / "lovelace_resource.py").is_file()
            actual = {
                str(p.relative_to(installed)): p.read_bytes()
                for p in installed.rglob("*")
                if p.is_file()
            }
            expected = {
                str(Path(n).relative_to(f"custom_components/{DOMAIN}")): v
                for n, v in files.items()
                if n.startswith(f"custom_components/{DOMAIN}/")
            }
            assert actual == expected and history.read_bytes() == original
        repo.data.show_beta = False
        await repo.common_update_data(force=True)
        assert update.latest_version == STABLE and TAG not in repo.data.published_tags
        repo.data.show_beta = True
        await repo.common_update_data(force=True)
        assert update.latest_version == TAG
        await repo.uninstall()
        assert history.read_bytes() == original and not installed.exists()
        await repo.async_download_repository(ref=TAG)
        assert (
            history.read_bytes() == original
            and calls.count(f"https://github.com/{repository}/archive/refs/tags/{TAG}.zip") == 3
        )
