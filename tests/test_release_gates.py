"""High-impact release gates reject failed/pending checks and stable mutations."""

import importlib
import json
from copy import deepcopy
from pathlib import Path

import pytest


@pytest.fixture
def publisher(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).parents[1] / "tools"))
    return importlib.import_module("publish_v11")


def checks_for(publisher):
    return [
        {"name": name, "status": "completed", "conclusion": "success", "html_url": "recorded-check"}
        for name in publisher.REQUIRED
        for _ in range(3)
    ]


def fake_checks(monkeypatch, publisher, checks):
    monkeypatch.setattr(
        publisher,
        "api",
        lambda path: {"check_runs": checks} if "check-runs" in path else {"statuses": []},
    )


def test_all_eighteen_exact_source_checks_required(monkeypatch, publisher):
    checks = checks_for(publisher)
    fake_checks(monkeypatch, publisher, checks)
    assert len(publisher.wait_checks("f" * 40)) == 18


@pytest.mark.parametrize("name", ["CodeQL security", "hacs"])
async def test_any_failed_quality_or_security_check_blocks(monkeypatch, publisher, name):
    checks = checks_for(publisher)
    checks.append({"name": name, "status": "completed", "conclusion": "failure"})
    fake_checks(monkeypatch, publisher, checks)
    with pytest.raises(AssertionError, match="CI/security gate failed"):
        publisher.wait_checks("f" * 40)


def test_pending_external_check_is_never_ignored(monkeypatch, publisher):
    checks = checks_for(publisher)
    checks.append({"name": "required external review", "status": "in_progress", "conclusion": None})
    fake_checks(monkeypatch, publisher, checks)

    def pending(_):
        raise RuntimeError("gate remains pending")

    monkeypatch.setattr(publisher.time, "sleep", pending)
    with pytest.raises(RuntimeError, match="remains pending"):
        publisher.wait_checks("f" * 40)


@pytest.mark.parametrize("mutation", ["main", "latest", "asset"])
def test_beta_may_never_mutate_stable_identity(monkeypatch, publisher, mutation):
    previous = json.loads(Path("docs/receipts/v1.0.0.json").read_text())
    stable = {
        "id": previous["release_id"],
        "prerelease": False,
        "draft": False,
        "assets": deepcopy(previous["assets"]),
    }
    data = {
        "releases/tags/v1.0.0": stable,
        "commits/main": {"sha": publisher.BASELINE},
        "releases/latest": {"id": stable["id"]},
        "git/ref/tags/v1.0.0": {"object": {"sha": previous["tag_object"]}},
    }
    if mutation == "main":
        data["commits/main"]["sha"] = "a" * 40
    elif mutation == "latest":
        data["releases/latest"]["id"] += 1
    else:
        stable["assets"][0]["digest"] = "sha256:" + "f" * 64
    monkeypatch.setattr(publisher, "api", lambda path: data[path])
    with pytest.raises(AssertionError):
        publisher.stable_integrity()
