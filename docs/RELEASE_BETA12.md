# v0.1.0-beta.12 — choose VAT display without changing price history

Initial setup now includes **Including VAT?**, default Yes. Existing beta.11 sites
also default Yes without reset. Change it later in normal **Configure → Including VAT**.
The saved strictly boolean preference appears as an enabled native Diagnostic row,
**Including VAT — Yes/No**, localized **Inklusive moms — Ja/Nej**.

Every approved beta.11 Diagnostic remains: current/next verified quarter, eight price
components including VAT amount/final, four actual grid ranges and Status. A normal
four-band site has 15 Diagnostic rows / 23 entities. All monetary rows default to
øre/kWh, two decimals, in the selected basis. Six component values use the same stored
quarter's `incl_vat` or `ex_vat`. Ex-VAT final sums its unrounded stored components.
**VAT amount remains the actual stored tax amount in both modes**; it is informational
in No mode. No blind 1.25 conversion, double VAT, mixed quarters or invented zeroes.
Grid bands use verified cached components and retain real local ranges/DST.

The nine primary sensor values/state classes retain their previous fixed VAT basis
for Recorder safety, now explicitly labeled. The card follows the preference for
components, final graph, statistics and tariffs; its separate raw Nord Pool graph
stays clearly ex VAT. Internal dashboard schema3 requires reloading cached browser
resources. The Python CM API stays v2 with canonical VAT-inclusive final values.

Display-only saves notify entities without integration reload, acquisition, canonical
calculation, SQLite writes or price revisions. Price model, ledger schema, adapters,
scheduler, readiness and consumer API are preserved. All original IDs and dated rules
remain; contract rate-input `vat_included` remains a separate source convention.

## HACS update

1. Back up development HA. Enable **Show beta versions**, refresh information,
   select **v0.1.0-beta.12**, download and restart HA.
2. Reload the browser/app and cached card resource. Keep beta.10/11 sites and history;
   **no reset is needed**. Older incompatible beta1–9 sites have a separate reset guide.
3. Verify Device info 0.1.0-beta.12, then open the native device Diagnostic section.
   Toggle Yes/No through Configure and confirm all components/grid bands follow it,
   while VAT amount stays unchanged. Reopen Configure/restart to verify persistence.

[Setup guide](HACS_DISTRIBUTION.md) · [Diagnostics](DIAGNOSTICS.md) ·
[Owner checklist](BETA_ACCEPTANCE.md) · [Permanent handoff](DEVELOPMENT_STATUS.md).

## Validation and acceptance boundary

139 tests per core on HA2026.10.3/.4, 90% coverage; 22 desktop/mobile EN/DA card tests;
official hassfest 1 valid/0 invalid. Tests cover strict defaults/validation, saved No,
interruption/restart, unchanged API/ledger bytes/primary state classes, current/next,
mixed VAT rates/already-inclusive inputs, negative prices, missing inputs and DST.
Eighteen actual native screenshots cover EN/DA desktop/mobile Yes/No, initial setup,
normal Configure, current/next/missing, installed card and restart. Upgrade from the
hash-verified public beta.11 preserves66 original entity IDs, all3 original site data
and all other merged settings, and2 ledgers byte-for-byte through preference toggles,
locale reloads and restart. All3 No preferences persist. Reads/toggles add no provider
requests, browser errors or warnings. The actual served card JS matches the package.
[Native receipt/screenshots](receipts/v0.1.0-beta.12-simulation.json).

All13 first-source CI checks passed. Final exact-source/tag CI and two fresh public
HACS/native verification jobs are mandatory publication gates, recorded in the final
publication receipt after success. Both package layouts installed outside the source
on both cores, and two clean builds produced identical archive bytes.

Native QA is controlled recorded/synthetic software, not owner physical Pi acceptance.
No private rate is inferred. EWII 0.030 DKK/kWh ex VAT remains June–September2026 only.
No stable/main merge, production HA, Node-RED or charging actions. Stop after verified
publication for PAHA02-DEV acceptance. Cloud benchmarks do not establish Pi performance.
