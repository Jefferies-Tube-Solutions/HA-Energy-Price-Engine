# Energy Price Engine v1.0.0 — Stable

The first stable release promotes the owner-accepted published beta.12 MVP from
`e506ccfc40b61413bd83e3ce60081a60d517348f`. Product version is **1.0.0**; the documented
read-only producer contract remains **API v2**. PE works independently of CM.

This is a stabilization release. All22 runtime Python modules, the pricing model,
source adapters, SQLite schema/revisions, scheduler, entity identities, configuration
behavior and card JavaScript remain byte-identical beta.12. Runtime changes are
version metadata and neutral reset translations. No reset or repricing is introduced.

Official Nord Pool/DK1/DK2, verified Radius C, dated national charges, actual private
markup, VAT Yes/No, every native Diagnostic, 15-minute negative prices/DST, today and
tomorrow schedules, durable history and API2 readiness are retained. Primary sensor
Recorder basis stays fixed and labeled; Diagnostics/card follow the VAT preference,
while actual VAT amount stays unchanged. No invoice/subscription/control features.

## Install or update

Add the GitHub custom repository in HACS as an Integration, leave **Show beta versions
off**, download **v1.0.0** and restart HA. Existing beta.12 sites, entity IDs, rates,
VAT choices and SQLite history remain. Reload browser/app/card resources; use
`/ha_energy_price_engine/energy-price-engine-card.js?v=1.0.0`.

[Installation guide](HACS_DISTRIBUTION.md) · [Native Diagnostics](DIAGNOSTICS.md) ·
[Dashboard](PRICE_DASHBOARD.md) · [Stable API2](API.md) · [Acceptance](ACCEPTANCE.md).

## Release gates and provenance

The exact published beta.12 source is frozen as the baseline. Clean release branch
and review PR target main; normal repository approvals/protection are respected.
Pre-merge CI, recorded/native beta.12 upgrade and clean install evidence, actual-main
CI, immutable tag, reproducible packages and prior-release preservation are required.
Stable publication is non-prerelease/latest and is independently verified with public
source/assets, SHA256, actual HACS stable selection and both native package layouts.
Exact results/source/checksums are recorded by the permanent handoff and release receipt.

The supported/current matrix is HA2026.10.3/.4. Tests use recorded public and fictional
private inputs, real HA lifecycle/HTTP/flows, actual pinned HACS with GitHub transport
fixtures, and real SQLite disk recovery. Disposable native browser QA is separate from
owner live/Pi acceptance. No public-provider uptime or hardware performance is inferred.

Native HA2026.10.4 evidence includes30 hashed desktop/mobile EN/DA screenshots, fresh
manual setup and an upgrade from the hash-verified actual published beta.12 HACS ZIP.
All69 existing entity IDs, three effective site settings/mixed VAT preferences and
both SQLite ledger files survived update and restart. A fresh site also retained its
23 entities, No VAT display preference and inclusive-source supplier rate after restart.
[Native evidence](receipts/v1.0.0-simulation.json).

## Known limits

Private supplier terms must be configured and verified by the site owner. Bundled
national charges have actual expiry dates; no later rates are invented. Legacy custom
Nordpool must not shadow the official domain. History uses storage/RAM proportional to
retention; cloud benchmarks do not establish Pi performance. CM's unreleased API-v1
consumer needs its own migration. Separate HACS catalog and external brands submissions
remain owner actions; a custom-repository stable release is not catalog admission.
[Compatibility and troubleshooting](COMPATIBILITY.md).

Publication does not authorize production HA changes, Node-RED changes, EV commands
or a CM charging cutover. Stop after verified v1.0.0 publication for owner verification.
