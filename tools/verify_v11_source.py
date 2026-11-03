"""Verify the Issue20 surface and preserve the published stable price engine."""

import argparse
import ast
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "19af5bf4412c5f3cc3b3e07c6d756da372f81ba6"
VERSION = "1.1.0-beta.1"
PREFIX = "custom_components/ha_energy_price_engine/"
ALLOWED = {
    "dashboard.py",
    "lovelace_resource.py",
    "manifest.json",
    "www/energy-price-engine-card.js",
}


def verify(*, native=False):
    manifest = json.loads((ROOT / PREFIX / "manifest.json").read_text())
    assert manifest["version"] == VERSION
    assert manifest["dependencies"] == ["http", "lovelace", "websocket_api"]
    baseline = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", BASELINE, "--", PREFIX], cwd=ROOT, text=True
    ).splitlines()
    expected = {path.removeprefix(PREFIX) for path in baseline} | {"lovelace_resource.py"}
    actual = {
        str(p.relative_to(ROOT / PREFIX))
        for p in (ROOT / PREFIX).rglob("*")
        if p.is_file()
        and p.suffix in {".py", ".js", ".json", ".png"}
        and "__pycache__" not in p.parts
    }
    assert actual == expected, "Unexpected runtime package files"
    frozen = {}
    for path in baseline:
        name = path.removeprefix(PREFIX)
        if name in ALLOWED:
            continue
        original = subprocess.check_output(["git", "show", BASELINE + ":" + path], cwd=ROOT)
        assert (ROOT / path).read_bytes() == original, "Stable runtime changed: " + path
        frozen[name] = hashlib.sha256(original).hexdigest()
    # The dashboard backend payload/calculations/permissions also remain identical.
    old = ast.parse(
        subprocess.check_output(["git", "show", BASELINE + ":" + PREFIX + "dashboard.py"], cwd=ROOT)
    )
    new = ast.parse((ROOT / PREFIX / "dashboard.py").read_text())

    def functions(tree):
        return {
            node.name: ast.dump(node)
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name != "async_setup_dashboard"
        }

    assert functions(old) == functions(new), "Dashboard data/permissions changed"
    if native:
        proof = json.loads((ROOT / "docs/receipts/v1.1.0-beta.1-simulation.json").read_text())
        assert proof["version"] == VERSION and proof["baseline_commit"] == BASELINE
        assert proof["fresh_cold_start"] and proof["upgrade_manual_resource"] and proof["restart"]
        assert proof["original_entity_ids_preserved"] == 69
        assert (
            proof["original_site_settings_preserved"] == 3 and proof["ledger_bytes_preserved"] == 2
        )
        assert proof["two_units_independent"] and proof["no_provider_requests_from_card_reads"]
        assert not proof["errors"] and not proof["warnings"] and not proof["owner_acceptance"]
        for name, digest in proof["runtime_files_sha256"].items():
            path = ROOT / "LICENSE" if name == "LICENSE" else ROOT / PREFIX / name
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
        for path, digest in proof["screenshots"].items():
            assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest
    return {
        "version": VERSION,
        "baseline": BASELINE,
        "frozen_runtime_files": frozen,
        "dashboard_data_functions_unchanged": True,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-native", action="store_true")
    args = parser.parse_args()
    print(json.dumps(verify(native=args.require_native)))
