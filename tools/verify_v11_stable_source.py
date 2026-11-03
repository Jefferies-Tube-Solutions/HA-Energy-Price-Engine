"""Fail closed unless v1.1 stable is the exact approved beta payload plus version."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "d7cb97c3b1efbed49d7f68a023c52ed6ba5fe10f"
PREFIX = "custom_components/ha_energy_price_engine/"


def verify(expected_source=None):
    source = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if expected_source:
        assert source == expected_source, "Wrong stable checkout"
    paths = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", BASELINE, "--", PREFIX], cwd=ROOT, text=True
    ).splitlines()
    actual = subprocess.check_output(
        ["git", "ls-files", "--", PREFIX], cwd=ROOT, text=True
    ).splitlines()
    assert set(paths) == set(actual), "Stable package membership changed"
    frozen = {}
    for path in paths:
        original = subprocess.check_output(["git", "show", BASELINE + ":" + path], cwd=ROOT)
        current = (ROOT / path).read_bytes()
        if path == PREFIX + "manifest.json":
            old, new = json.loads(original), json.loads(current)
            assert old.pop("version") == "1.1.0-beta.1"
            assert new.pop("version") == "1.1.0" and old == new
        else:
            assert original == current, "Approved beta runtime changed: " + path
        frozen[path.removeprefix(PREFIX)] = hashlib.sha256(current).hexdigest()
    frozen["LICENSE"] = hashlib.sha256((ROOT / "LICENSE").read_bytes()).hexdigest()
    candidate = json.loads((ROOT / "docs/receipts/v1.1.0-candidate.json").read_text())
    assert candidate["runtime_files"] == frozen
    proof = json.loads((ROOT / "docs/receipts/v1.1.0-simulation.json").read_text())
    assert proof["baseline_commit"] == BASELINE and proof["version"] == "1.1.0"
    assert proof["runtime_files_sha256"] == frozen
    assert proof["archive_hashes"] == candidate["archives"]
    assert proof["native_beta_upgrade_restart"] and proof["native_fresh_restart"]
    assert proof["original_entity_ids_preserved"] == 69
    assert proof["original_site_settings_preserved"] == 3
    assert proof["ledger_bytes_preserved"] >= 2
    assert proof["resource_id_and_order_preserved"] and proof["resource_version"] == "1.1.0"
    assert proof["reload_preserved"] and proof["sqlite_integrity"] == "ok"
    assert not proof["production_controls_touched"]
    for name, digest in proof["evidence_files"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
    return {"source": source, "baseline": BASELINE, "native_evidence": "passed"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-source")
    print(json.dumps(verify(parser.parse_args().expected_source)))
