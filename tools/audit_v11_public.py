"""Read-only recovery verification of the already published immutable beta.

The initial public check exposed a legacy test's wrong expectation for beta
visibility after restoring HACS state. No release source, tag or asset is changed.
"""

import argparse
import json
import os
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

from promote_stable import REQUIRED, api, prior_integrity
from publish_v11 import BASELINE, STATE, TAG, review_pr, stable_integrity, wait_checks
from verify_v11_source import verify

SOURCE = "d7cb97c3b1efbed49d7f68a023c52ed6ba5fe10f"
TAG_OBJECT = "d0b3a59e39691d83ed5a61bbc16434e042b62e2a"
ORIGINAL_RUN = 41594660100
METADATA = {
    "BUILD_MANIFEST.json": "0031cb74a8e61928243822c73b53c5f8fda0ec259bad80edf664b17e4eda94a8",
    "SHA256SUMS": "2b4799fc8f184651a7a7437c8eeb07e2e18fd1e40a61049ce4f4631653ab95fd",
}
ALLOWED = {
    ".github/workflows/publish-v11.yml",
    "docs/DEVELOPMENT_STATUS.md",
    "tests/test_hacs_release.py",
    "tools/audit_v11_public.py",
}
OWN_JOBS = (
    "Existing public beta integrity",
    "Verify public v1.1 beta",
    "Record verified v1.1 beta",
)


def check():
    state = json.loads(STATE.read_text())
    assert state["source_commit"] == SOURCE and state["tag_object"] == TAG_OBJECT
    verify(native=True)
    changed = subprocess.check_output(
        ["git", "diff", "--name-only", SOURCE, "HEAD"], text=True
    ).splitlines()
    assert set(changed) <= ALLOWED, "Only reviewed verification/test/handoff changes are allowed"
    assert subprocess.check_output(["git", "rev-parse", TAG], text=True).strip() == TAG_OBJECT
    assert (
        subprocess.check_output(["git", "rev-parse", TAG + "^{commit}"], text=True).strip()
        == SOURCE
    )
    assert api("git/ref/tags/" + TAG)["object"]["sha"] == TAG_OBJECT
    stable_integrity()
    prior_integrity()
    wait_checks(SOURCE)  # All18 original push/PR/tag checks, no exclusions.
    pr = review_pr()
    assert pr["number"] == 21 and pr["head"]["sha"] == os.environ["GITHUB_SHA"]
    old_jobs = api(f"actions/runs/{ORIGINAL_RUN}/jobs?per_page=100")["jobs"]
    publisher = [j for j in old_jobs if j["name"] == "publish beta v1.1"]
    assert len(publisher) == 1 and publisher[0]["conclusion"] == "success"
    release = api("releases/tags/" + TAG)
    assert release["id"] == state["release_id"] and release["prerelease"] and not release["draft"]
    assets = {a["name"]: a for a in release["assets"]}
    assert set(assets) == {*state["archive_hashes"], *METADATA}
    for name, digest in {**state["archive_hashes"], **METADATA}.items():
        assert assets[name]["digest"] == "sha256:" + digest
    return state, release, old_jobs


def verification_ci():
    source = os.environ["GITHUB_SHA"]
    for _ in range(90):
        all_checks = api(f"commits/{source}/check-runs?per_page=100&filter=all")["check_runs"]
        checks = [c for c in all_checks if not c["name"].startswith(OWN_JOBS)]
        assert not any(
            c["status"] == "completed" and c["conclusion"] != "success" for c in checks
        ), "A current quality/security gate failed"
        statuses = api(f"commits/{source}/status").get("statuses", [])
        assert not any(s["state"] in {"error", "failure"} for s in statuses)
        if (
            all(
                sum(c["name"] == n and c["conclusion"] == "success" for c in checks) >= 2
                for n in REQUIRED
            )
            and all(c["status"] == "completed" for c in checks)
            and not any(s["state"] == "pending" for s in statuses)
        ):
            return [
                {"name": c["name"], "conclusion": c["conclusion"], "url": c["html_url"]}
                for c in checks
            ]
        time.sleep(10)
    raise RuntimeError("Verification-source push/PR checks remain pending")


def audit():
    state, release, original_jobs = check()
    checks = verification_ci()
    receipts = {
        p.parent.name: json.loads(p.read_text())
        for p in Path("public-verification").rglob("PUBLIC_BETA_RECEIPT.json")
    }
    assert len(receipts) == 2
    for receipt in receipts.values():
        assert receipt["source_commit"] == SOURCE and receipt["tag_object"] == TAG_OBJECT
        assert (
            receipt["main_commit"] == BASELINE
            and receipt["archive_hashes"] == state["archive_hashes"]
        )
        assert receipt["isolated_hacs_and_native_install"] == "passed"
        assert {a["name"]: (a["id"], a["digest"]) for a in receipt["release"]["assets"]} == {
            a["name"]: (a["id"], a["digest"]) for a in release["assets"]
        }
    jobs = api(f"actions/runs/{os.environ['GITHUB_RUN_ID']}/jobs?per_page=100")["jobs"]
    done = [j for j in jobs if j["name"].startswith(OWN_JOBS[:2])]
    assert len(done) == 3 and all(j["conclusion"] == "success" for j in done)
    report = {
        **state,
        "version": "1.1.0-beta.1",
        "tag": TAG,
        "verified_at": datetime.now(UTC).isoformat(),
        "draft": False,
        "prerelease": True,
        "main_commit": BASELINE,
        "main_unmerged": True,
        "latest_stable": "v1.0.0",
        "prior_releases_preserved": True,
        "assets": [
            {k: a.get(k) for k in ("name", "id", "size", "digest", "browser_download_url")}
            for a in release["assets"]
        ],
        "public_verification_receipts": receipts,
        "public_verification_source": os.environ["GITHUB_SHA"],
        "public_verification_source_checks": checks,
        "verification_correction": {
            "original_run": ORIGINAL_RUN,
            "original_failed_jobs": [
                {"name": j["name"], "conclusion": j["conclusion"], "url": j["html_url"]}
                for j in original_jobs
                if j["name"].startswith("Verify public v1.1 beta")
            ],
            "cause": "Legacy stable-channel test expected v1.0.0 after restoring beta opt-in, although a real higher beta correctly becomes available.",
            "fix": "Assert the selected channel's actual newest release after cache restore, explicitly return to stable for stable filesystem checks, and include a higher beta in ordinary regression fixtures.",
            "released_runtime_tag_and_all_asset_digests_unchanged": True,
        },
        "publisher": {"id": ORIGINAL_RUN, "publication_job": "success"},
        "verification_workflow": {
            "id": int(os.environ["GITHUB_RUN_ID"]),
            "url": f"https://github.com/NicolaiTandrup/HA-Energy-Price-Engine/actions/runs/{os.environ['GITHUB_RUN_ID']}",
            "integrity_and_public_jobs": "success",
            "workflow_final_conclusion": "pending audit completion",
        },
        "owner_acceptance": False,
        "production_controls_touched": False,
    }
    Path("docs/receipts/v1.1.0-beta.1.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("check", "audit"))
    try:
        {"check": check, "audit": audit}[parser.parse_args().stage]()
    except Exception as err:
        print(
            "::error title=Immutable beta verification::"
            + str(err).replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A"),
            flush=True,
        )
        raise
