"""Guarded Issue20 prerelease promotion; never merge main, approve PRs or retag."""

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

from promote_stable import REPO, REQUIRED, api, prior_integrity
from verify_v11_source import BASELINE, VERSION, verify

TAG = "v" + VERSION
BRANCH = "feat/v1.1-beta1-dashboard"
STATE = Path(os.environ.get("RUNNER_TEMP", tempfile.gettempdir())) / "pe-v11-state.json"


def stable_integrity():
    previous = json.loads(Path("docs/receipts/v1.0.0.json").read_text())
    stable = api("releases/tags/v1.0.0")
    assert api("commits/main")["sha"] == BASELINE, "Main changed; do not merge or publish"
    assert (
        stable["id"] == previous["release_id"] and not stable["prerelease"] and not stable["draft"]
    )
    assert api("releases/latest")["id"] == stable["id"], "Latest stable must remain v1.0.0"
    assert api("git/ref/tags/v1.0.0")["object"]["sha"] == previous["tag_object"]
    current = {a["name"]: a for a in stable["assets"]}
    for asset in previous["assets"]:
        assert all(current[asset["name"]][k] == asset[k] for k in ("id", "size", "digest"))
    return stable


def wait_checks(source):
    for _ in range(90):
        checks = api(f"commits/{source}/check-runs?per_page=100&filter=all")["check_runs"]
        # The publishing workflow lives on a later automation-only commit. The
        # immutable source already has ordinary push + PR + tag validation.
        assert not any(
            c["status"] == "completed" and c["conclusion"] != "success" for c in checks
        ), "Exact-source CI/security gate failed"
        statuses = api(f"commits/{source}/status").get("statuses", [])
        assert not any(s["state"] in {"error", "failure"} for s in statuses)
        if (
            all(
                sum(c["name"] == n and c["conclusion"] == "success" for c in checks) >= 3
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
    raise RuntimeError("Exact-source push/PR/tag CI remains pending; no publication")


def review_pr():
    prs = api("pulls?state=open&base=main&head=NicolaiTandrup%3Afeat%2Fv1.1-beta1-dashboard")
    assert len(prs) == 1, "One ordinary reviewable beta PR is required"
    pr = prs[0]
    assert pr["head"]["ref"] == BRANCH and pr["base"]["ref"] == "main"
    result = subprocess.check_output(
        ["gh", "pr", "view", str(pr["number"]), "--json", "reviewDecision,latestReviews"], text=True
    )
    review = json.loads(result)
    assert review["reviewDecision"] not in {"REVIEW_REQUIRED", "CHANGES_REQUESTED"}, (
        "Required review remains outstanding"
    )
    assert not any(r.get("state") == "CHANGES_REQUESTED" for r in review["latestReviews"])
    return pr


def publish():
    assert os.environ["GITHUB_REPOSITORY"] == REPO
    source = os.environ["PE_SOURCE"]
    tag_object = os.environ["PE_TAG_OBJECT"]
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip() == source
    verify(native=True)
    assert subprocess.check_output(["git", "cat-file", "-t", TAG], text=True).strip() == "tag"
    assert subprocess.check_output(["git", "rev-parse", TAG], text=True).strip() == tag_object
    assert (
        subprocess.check_output(["git", "rev-parse", TAG + "^{commit}"], text=True).strip()
        == source
    )
    pr = review_pr()
    subprocess.run(["git", "fetch", "origin", BRANCH], check=True)
    changed = subprocess.check_output(
        ["git", "diff", "--name-only", source, pr["head"]["sha"]], text=True
    ).splitlines()
    assert set(changed) <= {".github/workflows/publish-v11.yml", "docs/DEVELOPMENT_STATUS.md"}, (
        "Reviewed beta payload changed after tagging"
    )
    checks = wait_checks(source)
    stable = stable_integrity()
    prior = prior_integrity()
    subprocess.run(["uv", "venv"], check=True)
    subprocess.run(
        ["uv", "pip", "sync", "--require-hashes", "requirements-ha-current.lock"], check=True
    )
    for directory in ("dist", str(Path(os.environ["RUNNER_TEMP"]) / "v11-repeat")):
        subprocess.run(
            [".venv/bin/python", "tools/build_beta.py", "--output", directory], check=True
        )
    build = json.loads(Path("dist/BUILD_MANIFEST.json").read_text())
    repeat = json.loads(
        (Path(os.environ["RUNNER_TEMP"]) / "v11-repeat/BUILD_MANIFEST.json").read_text()
    )
    proof = json.loads(Path("docs/receipts/v1.1.0-beta.1-simulation.json").read_text())
    assert build["commit"] == source and not build["dirty"] and build["version"] == VERSION
    assert build["archives"] == repeat["archives"] == proof["archive_hashes"]
    assert build["runtime_files"] == proof["runtime_files_sha256"]
    for name, digest in build["archives"].items():
        assert hashlib.sha256((Path("dist") / name).read_bytes()).hexdigest() == digest
        subprocess.run(
            [
                ".venv/bin/python",
                "tools/smoke_install_package.py",
                "dist/" + name,
                "--expected-version",
                VERSION,
            ],
            check=True,
        )
    ref = api("git/ref/tags/" + TAG)
    assert (
        ref["object"]["sha"] == tag_object
        and api("git/tags/" + tag_object)["object"]["sha"] == source
    )
    notes = Path("docs/RELEASE_V11_BETA1.md").read_text()
    base = f"https://github.com/{REPO}/blob/{TAG}/docs/"
    notes = re.sub(r"\]\((?!https?://)([^)]+)\)", lambda m: "](" + base + m[1] + ")", notes)
    notes += (
        f"\n\nExact source: `{source}`. Immutable annotated tag: `{tag_object}`. Reviewable PR: {pr['html_url']}. Main/latest stable remain v1.0.0.\n\n```text\n"
        + Path("dist/SHA256SUMS").read_text()
        + "```\n"
    )
    path = Path(os.environ["RUNNER_TEMP"]) / "v11-notes.md"
    path.write_text(notes)
    if api("releases/tags/" + TAG, optional=True) is None:
        subprocess.run(
            [
                "gh",
                "release",
                "create",
                TAG,
                "--target",
                source,
                "--verify-tag",
                "--prerelease",
                "--latest=false",
                "--title",
                "Energy Price Engine v1.1.0-beta.1 — automatic card setup and display units",
                "--notes-file",
                str(path),
                *["dist/" + n for n in (*build["archives"], "BUILD_MANIFEST.json", "SHA256SUMS")],
            ],
            check=True,
        )
    release = api("releases/tags/" + TAG)
    assert release["prerelease"] and not release["draft"]
    assets = {a["name"]: a for a in release["assets"]}
    assert set(assets) == {*build["archives"], "BUILD_MANIFEST.json", "SHA256SUMS"}
    for name, digest in build["archives"].items():
        assert assets[name]["digest"] == "sha256:" + digest
    stable_integrity()
    state = {
        "source_commit": source,
        "tag_object": tag_object,
        "release_id": release["id"],
        "release_url": release["html_url"],
        "pr": pr["number"],
        "pr_url": pr["html_url"],
        "archive_hashes": build["archives"],
        "checks": checks,
        "stable_release_id": stable["id"],
        "prior_releases": prior,
    }
    STATE.write_text(json.dumps(state, indent=2) + "\n")
    print("Published opt-in beta; stable/main unchanged: " + release["html_url"])


def audit():
    state = json.loads(STATE.read_text())
    receipts = {
        p.parent.name: json.loads(p.read_text())
        for p in Path("public-verification").rglob("PUBLIC_BETA_RECEIPT.json")
    }
    assert len(receipts) == 2
    for receipt in receipts.values():
        assert (
            receipt["source_commit"] == state["source_commit"]
            and receipt["archive_hashes"] == state["archive_hashes"]
        )
        assert receipt["isolated_hacs_and_native_install"] == "passed"
    stable_integrity()
    prior_integrity()
    release = api("releases/tags/" + TAG)
    assert release["id"] == state["release_id"] and release["prerelease"] and not release["draft"]
    assert api("git/ref/tags/" + TAG)["object"]["sha"] == state["tag_object"]
    pr = api(f"pulls/{state['pr']}")
    assert pr["state"] == "open" and not pr["merged"]
    jobs = api(f"actions/runs/{os.environ['GITHUB_RUN_ID']}/jobs?per_page=100")["jobs"]
    done = [
        j for j in jobs if j["name"].startswith(("publish beta v1.1", "Verify public v1.1 beta"))
    ]
    assert len(done) == 3 and all(j["conclusion"] == "success" for j in done)
    report = {
        **state,
        "version": VERSION,
        "tag": TAG,
        "verified_at": datetime.now(UTC).isoformat(),
        "draft": False,
        "prerelease": True,
        "main_commit": BASELINE,
        "main_unmerged": True,
        "latest_stable": "v1.0.0",
        "prior_releases_preserved": True,
        "public_verification_receipts": receipts,
        "publisher": {
            "id": int(os.environ["GITHUB_RUN_ID"]),
            "url": f"https://github.com/{REPO}/actions/runs/{os.environ['GITHUB_RUN_ID']}",
            "publication_and_public_jobs": "success",
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
    parser.add_argument("stage", choices=("publish", "audit"))
    try:
        {"publish": publish, "audit": audit}[parser.parse_args().stage]()
    except Exception as err:
        message = str(err).replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        print("::error title=Guarded v1.1 beta publication::" + message, flush=True)
        raise
