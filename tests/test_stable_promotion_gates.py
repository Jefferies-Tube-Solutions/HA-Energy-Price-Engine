"""Stable publication must reject missing native proof and incomplete CI/policy gates."""

import importlib
from pathlib import Path

import pytest


@pytest.fixture
def stable(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).parents[1] / "tools"))
    return importlib.import_module("promote_v11_stable")


def fixture_checks(stable):
    return [
        {"name": n, "status": "completed", "conclusion": "success", "html_url": "recorded"}
        for n in stable.REQUIRED
        for _ in range(2)
    ]


def fixture_runs(source):
    return [
        {"head_sha": source, "event": event, "path": path, "conclusion": "success"}
        for event in ("push", "pull_request")
        for path in (
            ".github/workflows/tests.yml",
            ".github/workflows/validate.yml",
            ".github/workflows/package.yml",
        )
    ]


def install_responses(monkeypatch, stable, checks, runs):
    def api(path):
        if "check-runs" in path:
            return {"check_runs": checks}
        if "actions/runs" in path:
            return {"workflow_runs": runs}
        return {"statuses": []}

    monkeypatch.setattr(stable, "api", api)

    def pending(_):
        raise RuntimeError("gate still pending")

    monkeypatch.setattr(stable.time, "sleep", pending)


def test_both_push_and_pr_workflows_required(monkeypatch, stable):
    source = "a" * 40
    checks = fixture_checks(stable)
    runs = fixture_runs(source)
    install_responses(monkeypatch, stable, checks, runs)
    assert len(stable.wait_checks(source, copies=2)) == 12
    # Duplicate push runs must never substitute for missing PR runs.
    runs[:] = [r for r in runs if r["event"] == "push"] * 2
    with pytest.raises(RuntimeError, match="pending"):
        stable.wait_checks(source, copies=2)


@pytest.mark.parametrize("result", ["failure", "cancelled", "skipped", "timed_out"])
def test_any_failed_security_check_blocks(monkeypatch, stable, result):
    source = "a" * 40
    checks = fixture_checks(stable)
    checks.append({"name": "security", "status": "completed", "conclusion": result})
    install_responses(monkeypatch, stable, checks, fixture_runs(source))
    with pytest.raises(RuntimeError, match="Failing source checks"):
        stable.wait_checks(source, copies=2)


def test_pending_external_review_blocks(monkeypatch, stable):
    source = "a" * 40
    checks = fixture_checks(stable)
    checks.append({"name": "review", "status": "in_progress", "conclusion": None})
    install_responses(monkeypatch, stable, checks, fixture_runs(source))
    with pytest.raises(RuntimeError, match="pending"):
        stable.wait_checks(source, copies=2)


def test_required_review_cannot_be_bypassed(monkeypatch, stable):
    monkeypatch.setattr(stable, "api", lambda path: {"protected": False})
    monkeypatch.setattr(
        stable,
        "command",
        lambda args: '{"reviewDecision":"REVIEW_REQUIRED","latestReviews":[],"reviewRequests":[]}',
    )
    with pytest.raises(AssertionError, match="actual GitHub review"):
        stable.repository_gates()
