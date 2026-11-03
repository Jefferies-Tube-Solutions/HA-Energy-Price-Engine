"""Independently verify the public Issue20 prerelease and actual HACS channels."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from verify_public_release import DOMAIN, REPOSITORY, api, download
from verify_v11_source import BASELINE, VERSION

ROOT = Path(__file__).resolve().parents[1]
TAG = "v" + VERSION


def verify(output, expected_commit):
    output.mkdir(parents=True, exist_ok=True)
    release = api(f"repos/{REPOSITORY}/releases/tags/{TAG}")
    stable = api(f"repos/{REPOSITORY}/releases/latest")
    assert release["tag_name"] == TAG and release["prerelease"] and not release["draft"]
    previous = json.loads((ROOT / "docs/receipts/v1.0.0.json").read_text())
    assert stable["tag_name"] == "v1.0.0" and stable["id"] == previous["release_id"]
    assert not stable["prerelease"] and not stable["draft"]
    source = api(f"repos/{REPOSITORY}/commits/{TAG}")["sha"]
    main = api(f"repos/{REPOSITORY}/commits/main")["sha"]
    assert source == expected_commit and main == BASELINE
    ref = api(f"repos/{REPOSITORY}/git/ref/tags/{TAG}")
    assert ref["object"]["type"] == "tag"
    tag = api(f"repos/{REPOSITORY}/git/tags/{ref['object']['sha']}")
    assert tag["object"]["sha"] == source
    assets = {a["name"]: a for a in release["assets"]}
    names = {f"{DOMAIN}.zip", f"{DOMAIN}-manual.zip", "BUILD_MANIFEST.json", "SHA256SUMS"}
    assert set(assets) == names
    for name in names:
        asset = assets[name]
        download(asset["browser_download_url"], output / name, asset["id"])
        assert (
            asset["digest"] == "sha256:" + hashlib.sha256((output / name).read_bytes()).hexdigest()
        )
    build = json.loads((output / "BUILD_MANIFEST.json").read_text())
    assert build["commit"] == source and not build["dirty"] and build["version"] == VERSION
    sums = dict(line.split()[::-1] for line in (output / "SHA256SUMS").read_text().splitlines())
    assert sums == build["archives"]
    for name, digest in sums.items():
        assert hashlib.sha256((output / name).read_bytes()).hexdigest() == digest
        with zipfile.ZipFile(output / name) as archive:
            prefix = f"custom_components/{DOMAIN}/" if "-manual" in name else ""
            actual = {
                p.removeprefix(prefix): hashlib.sha256(archive.read(p)).hexdigest()
                for p in archive.namelist()
            }
            assert actual == build["runtime_files"]
    tag_source = output / "public-beta-source.zip"
    main_source = output / "public-main-source.zip"
    download(f"https://codeload.github.com/{REPOSITORY}/zip/refs/tags/{TAG}", tag_source)
    download(f"https://codeload.github.com/{REPOSITORY}/zip/{main}", main_source)
    with zipfile.ZipFile(tag_source) as archive:
        prefix = archive.namelist()[0].split("/")[0] + "/"
        for name, digest in build["runtime_files"].items():
            path = "LICENSE" if name == "LICENSE" else f"custom_components/{DOMAIN}/{name}"
            assert hashlib.sha256(archive.read(prefix + path)).hexdigest() == digest
    stable_asset = next(a for a in stable["assets"] if a["name"] == f"{DOMAIN}.zip")
    old = output / "previous-stable.zip"
    download(stable_asset["browser_download_url"], old, stable_asset["id"])
    assert (
        hashlib.sha256(old.read_bytes()).hexdigest() == previous["archive_hashes"][f"{DOMAIN}.zip"]
    )
    repository = api(f"repos/{REPOSITORY}")
    assert repository["default_branch"] == "main"
    feed = api(f"repos/{REPOSITORY}/releases?per_page=100")
    receipt = {
        "verified_at": datetime.now(UTC).isoformat(),
        "repository": repository,
        "release": release,
        "latest_stable": stable,
        "releases": feed,
        "source_commit": source,
        "main_commit": main,
        "tag_object": ref["object"]["sha"],
        "source_archive": str(tag_source.resolve()),
        "main_archive": str(main_source.resolve()),
        "previous_stable_asset": str(old.resolve()),
        "archive_hashes": sums,
    }
    path = output / "PUBLIC_BETA_RECEIPT.json"
    path.write_text(json.dumps(receipt, indent=2) + "\n")
    # The ordinary stable path is tested against the actual stable source/main,
    # while the separate opt-in test consumes actual beta bytes and metadata.
    stable_path = output / "PUBLIC_STABLE_CHANNEL.json"
    stable_path.write_text(
        json.dumps(
            {
                "repository": repository,
                "release": stable,
                "releases": feed,
                "source_commit": main,
                "source_archive": str(main_source.resolve()),
                "main_archive": str(main_source.resolve()),
            }
        )
    )
    environment = {
        **os.environ,
        "PE_PUBLIC_BETA_RECEIPT": str(path.resolve()),
        "PE_PUBLIC_RELEASE_RECEIPT": str(stable_path.resolve()),
    }
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_hacs_beta.py",
            "tests/test_hacs_release.py",
            "-q",
            "-W",
            "error::ResourceWarning",
        ],
        cwd=ROOT,
        env=environment,
        check=True,
    )
    for name in sums:
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools/smoke_install_package.py"),
                str(output / name),
                "--expected-version",
                VERSION,
            ],
            check=True,
        )
    receipt["isolated_hacs_and_native_install"] = "passed"
    path.write_text(json.dumps(receipt, indent=2) + "\n")
    print(
        json.dumps(
            {
                "release": release["html_url"],
                "source": source,
                "latest_stable": stable["tag_name"],
                "hacs_beta_and_stable": "passed",
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    verify(args.output, args.expected_commit)
