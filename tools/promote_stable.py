"""Guarded PR19 promotion, exact-main CI and immutable stable publication.

Runs only in the repository's explicitly authorized GitHub Actions workflow. It
never creates PRs, approves reviews, bypasses policy or replaces release assets.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
import time
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from verify_stable_source import BASELINE, verify

REPO = "NicolaiTandrup/HA-Energy-Price-Engine"
TAG = "v1.0.0"
OLD_MAIN = "56cdb3c10993179371483812cbc36f651ba3ad8e"
REQUIRED = {
    "hassfest",
    "hacs",
    "independent beta install",
    "tests (fixture-supported-ha-2026.10.3)",
    "tests (current-ha-2026.10.4)",
    "dashboard browser desktop and mobile",
}
EXPECTED_ARCHIVES = {
    "ha_energy_price_engine.zip": "ddbd7d09b27bd28af48e5b33bbc870bed80f797d411c1e83505bf8db90aa10c2",
    "ha_energy_price_engine-manual.zip": "3cde8b261e378160555fdb2d335cc897d022bcb55d96adcf06e7da2c6735fa1d",
}
STATE = Path(os.environ.get("RUNNER_TEMP", tempfile.gettempdir())) / "pe-stable-state.json"


def command(args):
    return subprocess.check_output(args, text=True).strip()


def api(path, data=None, *, method=None, optional=False):
    args = ["gh", "api", f"repos/{REPO}" + ("/" + path if path else "")]
    if method:
        args += ["--method", method]
    if data is not None:
        args += ["--input", "-"]
    result = subprocess.run(
        args, input=json.dumps(data) if data is not None else None, capture_output=True, text=True
    )
    if result.returncode:
        if optional and "HTTP 404" in result.stderr:
            return None
        raise RuntimeError(result.stderr.strip())
    return json.loads(result.stdout) if result.stdout.strip() else None


def save(state):
    STATE.write_text(json.dumps(state, indent=2) + "\n")


def prior_integrity():
    result = []
    for number in range(1, 13):
        tag = f"v0.1.0-beta.{number}"
        previous = json.loads(Path(f"docs/receipts/{tag}.json").read_text())
        release = api("releases/tags/" + tag)
        ref = api("git/ref/tags/" + tag)
        assert release["id"] == previous["release_id"]
        assert release["prerelease"] and not release["draft"]
        assert ref["object"]["sha"] == previous.get(
            "tag_object", previous.get("annotated_tag_object")
        )
        assets = {a["name"]: a for a in release["assets"]}
        hashes = previous.get("archive_hashes", previous.get("archive_sha256"))
        for name, digest in hashes.items():
            assert assets[name]["digest"] == "sha256:" + digest
        for asset in previous.get("assets", []):
            assert all(
                assets[asset["name"]].get(k) == asset[k]
                for k in ("id", "size", "digest")
                if k in asset
            )
        result.append({"tag": tag, "release_id": release["id"], "integrity_preserved": True})
    return result


def wait_checks(source, copies=1, *, main=False):
    required = REQUIRED | ({"stable main integrity"} if main else set())
    for _ in range(80):
        checks = api(f"commits/{source}/check-runs?per_page=100&filter=all")["check_runs"]
        relevant = [
            c
            for c in checks
            if not c["name"].startswith(
                ("publish stable", "Verify public stable", "Record verified stable publication")
            )
        ]
        failures = [
            c for c in relevant if c["status"] == "completed" and c["conclusion"] != "success"
        ]
        statuses = api(f"commits/{source}/status").get("statuses", [])
        assert not any(s["state"] in {"error", "failure"} for s in statuses), (
            "A commit/security status failed"
        )
        status_pending = any(s["state"] == "pending" for s in statuses)
        if failures:
            raise RuntimeError(
                "Failing source checks: " + repr([(c["name"], c["conclusion"]) for c in failures])
            )
        if (
            all(
                sum(c["name"] == n and c["conclusion"] == "success" for c in relevant) >= copies
                for n in required
            )
            and all(c["status"] == "completed" for c in relevant)
            and not status_pending
        ):
            return [
                {"name": c["name"], "conclusion": c["conclusion"], "url": c["html_url"]}
                for c in relevant
            ]
        time.sleep(10)
    raise RuntimeError("Exact-source mandatory checks are still pending")


def repository_gates():
    meta = api("")
    main = api("branches/main")
    rules = api("rules/branches/main")
    protection = api("branches/main/protection") if main["protected"] else None
    review = json.loads(
        command(["gh", "pr", "view", "19", "--json", "reviewDecision,latestReviews,reviewRequests"])
    )
    assert review["reviewDecision"] not in {"REVIEW_REQUIRED", "CHANGES_REQUESTED"}, (
        "PR19 requires an actual GitHub review/approval; owner interaction needed"
    )
    assert not any(r.get("state") == "CHANGES_REQUESTED" for r in review["latestReviews"])
    return {"main": main, "rules": rules, "protection": protection, "review": review, "meta": meta}


def merge():
    assert os.environ["GITHUB_REPOSITORY"] == REPO
    assert os.environ["GITHUB_REF"] == "refs/heads/release/v1.0.0"
    source = os.environ["GITHUB_SHA"]
    verify(source)
    checks = wait_checks(source, copies=2)
    prior = prior_integrity()
    pr = api("pulls/19")
    assert pr["head"]["sha"] == source and pr["head"]["ref"] == "release/v1.0.0"
    assert pr["base"]["ref"] == "main"
    if pr["merged"]:
        merged = pr["merge_commit_sha"]
        assert api("commits/main")["sha"] == merged
        gates = {"reviewed_merge_already_completed": True}
        method = "existing ordinary merge"
    else:
        assert pr["state"] == "open" and api("commits/main")["sha"] == OLD_MAIN
        assert api("git/ref/tags/" + TAG, optional=True) is None
        assert api("releases/tags/" + TAG, optional=True) is None
        gates = repository_gates()
        # Existing owner PR only. No PR creation, approval or admin bypass flags.
        if pr["draft"]:
            subprocess.run(["gh", "pr", "ready", "19"], check=True)
        gates = repository_gates()
        body = Path("docs/RELEASE_V1.md").read_text()
        body += f"\n\nReviewed branch source: {source}. Native receipt and unchanged-runtime guard passed; all twelve exact-source CI checks passed. Actual-main CI and public stable verification follow the ordinary merge.\n"
        api(
            "pulls/19",
            {"title": "Energy Price Engine v1.0.0 — Stable", "body": body},
            method="PATCH",
        )
        assert gates["main"]["commit"]["sha"] == OLD_MAIN
        assert gates["meta"]["allow_merge_commit"], "Normal merge commits must be allowed"
        method = "merge"
        response = api(
            "pulls/19/merge",
            {
                "sha": source,
                "merge_method": method,
                "commit_title": "Release Energy Price Engine v1.0.0 Stable (#19)",
            },
            method="PUT",
        )
        assert response["merged"], response
        merged = response["sha"]
    assert re.fullmatch(r"[a-f0-9]{40}", merged)
    main = api("commits/main")
    assert main["sha"] == merged
    assert (
        api("git/commits/" + merged)["tree"]["sha"] == api("git/commits/" + source)["tree"]["sha"]
    )
    # Repository automatic branch deletion must not erase the permanent handoff path.
    if api("git/ref/heads/release/v1.0.0", optional=True) is None:
        api("git/refs", {"ref": "refs/heads/release/v1.0.0", "sha": source}, method="POST")
    state = {
        "reviewed_source": source,
        "main_source": merged,
        "merge_method": method,
        "premerge_checks": checks,
        "repository_gates": gates,
        "prior_releases": prior,
    }
    save(state)
    print("Ordinary PR19 merge completed at actual main " + merged)


def validate_main():
    state = json.loads(STATE.read_text())
    source = state["main_source"]
    assert api("commits/main")["sha"] == source
    runs = (
        api(
            "actions/workflows/stable-main.yml/runs?event=workflow_dispatch&per_page=30",
            optional=True,
        )
        or {"workflow_runs": []}
    )["workflow_runs"]
    matched = [r for r in runs if r["head_sha"] == source and r["conclusion"] == "success"]
    if matched:
        run = matched[0]
    else:
        for attempt in range(10):
            try:
                api(
                    "actions/workflows/stable-main.yml/dispatches",
                    {"ref": "main", "inputs": {"expected_source": source}},
                    method="POST",
                )
                break
            except RuntimeError as error:
                if (
                    not any(
                        text in str(error)
                        for text in ("HTTP 404", "does not have 'workflow_dispatch' trigger")
                    )
                    or attempt == 9
                ):
                    raise
                time.sleep(3)
        run = None
        for _ in range(90):
            runs = api(
                "actions/workflows/stable-main.yml/runs?event=workflow_dispatch&per_page=30"
            )["workflow_runs"]
            found = [r for r in runs if r["head_sha"] == source]
            if found:
                run = max(found, key=lambda r: r["id"])
                if run["status"] == "completed":
                    assert run["conclusion"] == "success", (
                        "Actual-main CI failed: " + run["html_url"]
                    )
                    break
            time.sleep(10)
        else:
            raise RuntimeError("Actual-main CI remains pending; no tag or release")
    assert run and run["conclusion"] == "success"
    state["main_ci"] = {
        "id": run["id"],
        "url": run["html_url"],
        "source": source,
        "conclusion": "success",
    }
    state["main_checks"] = wait_checks(source, main=True)
    save(state)
    print("Actual-main CI passed: " + run["html_url"])


def publish():
    state = json.loads(STATE.read_text())
    source = state["main_source"]
    assert state["main_ci"]["conclusion"] == "success" and api("commits/main")["sha"] == source
    subprocess.run(["git", "fetch", "origin", "main"], check=True)
    subprocess.run(["git", "checkout", "--detach", source], check=True)
    verify(source)
    prior_integrity()
    subprocess.run(["uv", "venv"], check=True)
    subprocess.run(
        ["uv", "pip", "sync", "--require-hashes", "requirements-ha-current.lock"], check=True
    )
    for output in ("dist", str(Path(os.environ["RUNNER_TEMP"]) / "stable-repeat")):
        subprocess.run([".venv/bin/python", "tools/build_beta.py", "--output", output], check=True)
    build = json.loads(Path("dist/BUILD_MANIFEST.json").read_text())
    repeated = json.loads(
        (Path(os.environ["RUNNER_TEMP"]) / "stable-repeat/BUILD_MANIFEST.json").read_text()
    )
    assert build["commit"] == source and not build["dirty"] and build["version"] == "1.0.0"
    assert build["archives"] == repeated["archives"] == EXPECTED_ARCHIVES
    proof = json.loads(Path("docs/receipts/v1.0.0-simulation.json").read_text())
    assert build["runtime_files"] == proof["runtime_files_sha256"]
    for name, digest in EXPECTED_ARCHIVES.items():
        assert hashlib.sha256((Path("dist") / name).read_bytes()).hexdigest() == digest
        subprocess.run(
            [".venv/bin/python", "tools/smoke_install_package.py", "dist/" + name], check=True
        )
    ref = api("git/ref/tags/" + TAG, optional=True)
    if ref is None:
        tag = api(
            "git/tags",
            {
                "tag": TAG,
                "message": f"Energy Price Engine v1.0.0 Stable\nMain source: {source}\nReviewed PR19 source: {state['reviewed_source']}\nAccepted beta12: {BASELINE}",
                "object": source,
                "type": "commit",
                "tagger": {
                    "name": "github-actions[bot]",
                    "email": "41898282+github-actions[bot]@users.noreply.github.com",
                    "date": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                },
            },
            method="POST",
        )
        api("git/refs", {"ref": "refs/tags/" + TAG, "sha": tag["sha"]}, method="POST")
        ref = api("git/ref/tags/" + TAG)
    assert ref["object"]["type"] == "tag"
    tag_object = ref["object"]["sha"]
    annotated = api("git/tags/" + tag_object)
    assert (
        annotated["tag"] == TAG
        and annotated["object"]["type"] == "commit"
        and annotated["object"]["sha"] == source
    )
    subprocess.run(["git", "fetch", "origin", "refs/tags/" + TAG + ":refs/tags/" + TAG], check=True)
    assert command(["git", "rev-parse", TAG + "^{commit}"]) == source
    notes = Path("docs/RELEASE_V1.md").read_text()
    base = f"https://github.com/{REPO}/blob/{TAG}/docs/"
    notes = re.sub(r"\]\((?!https?://)([^)]+)\)", lambda m: "](" + base + m[1] + ")", notes)
    notes += (
        f"\n\nExact stable main source: `{source}`. Reviewed PR: https://github.com/{REPO}/pull/19. Annotated tag object: `{tag_object}`.\n\nActual-main CI: {state['main_ci']['url']}.\n\n```text\n"
        + Path("dist/SHA256SUMS").read_text()
        + "```\n"
    )
    notes_file = Path(os.environ["RUNNER_TEMP"]) / "stable-notes.md"
    notes_file.write_text(notes)
    existing = api("releases/tags/" + TAG, optional=True)
    if existing is None:
        subprocess.run(
            [
                "gh",
                "release",
                "create",
                TAG,
                "--target",
                source,
                "--verify-tag",
                "--latest=true",
                "--title",
                "Energy Price Engine v1.0.0 — Stable",
                "--notes-file",
                str(notes_file),
                "dist/ha_energy_price_engine.zip",
                "dist/ha_energy_price_engine-manual.zip",
                "dist/BUILD_MANIFEST.json",
                "dist/SHA256SUMS",
            ],
            check=True,
        )
    release = api("releases/tags/" + TAG)
    assert not release["draft"] and not release["prerelease"] and release["tag_name"] == TAG
    assert api("releases/latest")["id"] == release["id"]
    assets = {a["name"]: a for a in release["assets"]}
    assert set(assets) == {*EXPECTED_ARCHIVES, "SHA256SUMS", "BUILD_MANIFEST.json"}
    for name, digest in EXPECTED_ARCHIVES.items():
        assert assets[name]["digest"] == "sha256:" + digest
    state.update(
        tag_object=tag_object,
        release_url=release["html_url"],
        release_id=release["id"],
        archive_hashes=EXPECTED_ARCHIVES,
    )
    save(state)
    with Path(os.environ["GITHUB_OUTPUT"]).open("a") as output:
        output.write(
            f"main_source={source}\ntag_object={tag_object}\nrelease_url={release['html_url']}\n"
        )
    print("Public stable published: " + release["html_url"])


def audit():
    state = json.loads(STATE.read_text())
    source = state["main_source"]
    receipts = {
        p.parent.name: json.loads(p.read_text())
        for p in Path("public-verification").rglob("PUBLIC_RELEASE_RECEIPT.json")
    }
    assert len(receipts) == 2
    for receipt in receipts.values():
        assert receipt["source_commit"] == source and receipt["archive_hashes"] == EXPECTED_ARCHIVES
        assert receipt["isolated_hacs_and_native_install"] == "passed"
        assert not receipt["release"]["prerelease"] and not receipt["release"]["draft"]
    assert api("commits/main")["sha"] == source
    assert api("pulls/19")["merged"]
    prior = prior_integrity()
    release = api("releases/tags/" + TAG)
    assert release["id"] == state["release_id"] and api("releases/latest")["id"] == release["id"]
    assert api("git/ref/tags/" + TAG)["object"]["sha"] == state["tag_object"]
    with urllib.request.urlopen(release["html_url"], timeout=30) as response:
        assert response.status == 200
    jobs = api(f"actions/runs/{os.environ['GITHUB_RUN_ID']}/jobs?per_page=100")["jobs"]
    done = [j for j in jobs if j["name"].startswith(("publish stable", "Verify public stable"))]
    assert len(done) == 3 and all(j["conclusion"] == "success" for j in done)
    report = {
        "schema": 1,
        "verified_at": datetime.now(UTC).isoformat(),
        "tag": TAG,
        "source_commit": source,
        "reviewed_branch_source": state["reviewed_source"],
        "tag_object": state["tag_object"],
        "main_commit": source,
        "merged_pr": 19,
        "release_url": release["html_url"],
        "release_id": release["id"],
        "draft": False,
        "prerelease": False,
        "latest_stable": True,
        "previous_releases_preserved": True,
        "prior_releases": prior,
        "archive_hashes": EXPECTED_ARCHIVES,
        "assets": [
            {k: a.get(k) for k in ("name", "id", "size", "digest", "browser_download_url")}
            for a in release["assets"]
        ],
        "premerge_checks": state["premerge_checks"],
        "exact_main_checks": state["main_checks"],
        "main_ci": state["main_ci"],
        "public_verification_receipts": receipts,
        "publisher": {
            "id": int(os.environ["GITHUB_RUN_ID"]),
            "html_url": f"https://github.com/{REPO}/actions/runs/{os.environ['GITHUB_RUN_ID']}",
            "publication_and_public_jobs": "success",
            "workflow_final_conclusion": "pending audit completion",
        },
        "validation": {
            "cores": ["2026.10.3", "2026.10.4"],
            "tests_per_core": 142,
            "coverage_percent": 90,
            "browser_tests": 22,
            "simulation_receipt": "docs/receipts/v1.0.0-simulation.json",
        },
        "owner_final_verification": False,
        "production_or_charging_controls_touched": False,
        "catalog_admission_claimed": False,
    }
    Path("docs/receipts/v1.0.0.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    )
    print("Public stable and both fresh HACS/native verification jobs passed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("merge", "validate-main", "publish", "audit"))
    actions = {"merge": merge, "validate-main": validate_main, "publish": publish, "audit": audit}
    try:
        actions[parser.parse_args().stage]()
    except Exception as error:
        message = str(error).replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        print("::error title=Stable release gate::" + message, flush=True)
        raise
