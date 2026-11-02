"""Fail closed unless stable source matches the accepted runtime and native evidence."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "e506ccfc40b61413bd83e3ce60081a60d517348f"
PREFIX = "custom_components/ha_energy_price_engine/"
ALLOWED = {"manifest.json", "strings.json", "translations/en.json", "translations/da.json"}


def verify(expected_source=None):
    source = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if expected_source:
        assert source == expected_source, "Wrong stable source checkout"
    manifest = json.loads((ROOT / PREFIX / "manifest.json").read_text())
    assert manifest["version"] == "1.0.0"
    changed = subprocess.check_output(
        ["git", "diff", "--name-only", BASELINE, source, "--", PREFIX], cwd=ROOT, text=True
    ).splitlines()
    assert {p.removeprefix(PREFIX) for p in changed} <= ALLOWED
    runtime = ROOT / PREFIX
    modules = sorted(runtime.glob("*.py"))
    assert len(modules) == 22
    for path in [*modules, runtime / "www/energy-price-engine-card.js"]:
        original = subprocess.check_output(
            ["git", "show", BASELINE + ":" + str(path.relative_to(ROOT))], cwd=ROOT
        )
        assert path.read_bytes() == original, f"Accepted runtime changed: {path.name}"
    proof = json.loads((ROOT / "docs/receipts/v1.0.0-simulation.json").read_text())
    assert proof["baseline_commit"] == BASELINE and proof["version"] == "1.0.0"
    assert proof["baseline_hacs_sha256"] == (
        "211384a19c513009414acbde19f4eed55656ea957611b3211c2b5cfd62d0a5c8"
    )
    upgrade = proof["upgrade"]
    assert upgrade["original_entity_ids_preserved"] == 69
    assert upgrade["original_site_settings_preserved"] == 3
    assert upgrade["price_ledgers_byte_identical"] == 2
    assert upgrade["saved_vat_choices_preserved"]
    assert upgrade["canonical_prices_and_primary_recorder_basis_unchanged"]
    assert upgrade["no_provider_requests_from_reads_or_preference_saves"]
    assert upgrade["diagnostic_rows_per_four_band_site"] == 15
    assert upgrade["automatic_next_to_current_selection"]
    assert proof["restart"]["upgraded_sites_and_ids_preserved"]
    assert proof["restart"]["vat_choices_preserved"]
    assert proof["restart"]["ledger_bytes_preserved"]
    assert proof["fresh"]["native_setup_complete"] and proof["fresh"]["no_beta_visibility_required"]
    assert proof["fresh"]["version"] == "1.0.0" and proof["fresh"]["entities"] == 23
    assert proof["fresh"]["including_vat"] is False
    assert proof["fresh"]["supplier_input_vat_included"] is True
    assert proof["fresh"]["restart_persisted"]
    assert proof["served_card_matches_package"]
    assert not proof["errors"] and not proof["warnings"] and not proof["owner_acceptance"]
    assert len(proof["screenshots"]) >= 18
    for path, digest in proof["screenshots"].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest
    for name, digest in proof["runtime_files_sha256"].items():
        path = ROOT / "LICENSE" if name == "LICENSE" else runtime / name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    return {"source": source, "baseline": BASELINE, "native_evidence": "passed"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-source")
    print(json.dumps(verify(parser.parse_args().expected_source)))
