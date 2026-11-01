# v0.1.0-beta.11 — restore native Device Diagnostics

Beta.11 corrects the beta.10 regression reported in #16: price components were
available in attributes/card data but missing from the native device Diagnostic
section. Every essential calculation value is visible again as an enabled entity.
A dashboard is not required.

Open **Settings → Devices & services → Energy Price Engine → device → Diagnostic**:

- **Current quarter** or **Next verified quarter**, with its local clock range.
- **Nord Pool spot, applied DSO, Energinet network/system, supplier markup and
  electricity tax**, excluding VAT.
- **VAT amount** and **verified final price**, including VAT once in the total.
- **Four actual Radius day ranges and rates**, independent of final-price history.
- **Status**, reusing the existing availability entity with readiness/corrective guidance.

All numeric amounts default to **øre/kWh, two decimals**. The eight component rows
come from one verified stored record/revision. When current final is Unknown but
next is READY, every diagnostic amount belongs to the explicitly labeled next
quarter; independently current spot/DSO sensors keep their current values. At the
boundary the breakdown switches automatically. Missing values stay Unknown, never
zero. Equal-price separate grid bands remain separate. Different/fewer/more ranges
are shown truthfully; additional actual bands receive enabled rows.

## HACS update from beta.10

1. Back up development HA. In HACS, keep **Show beta versions** enabled, refresh,
   select **v0.1.0-beta.11**, download and restart HA. Reload the app/browser.
2. **Keep existing sites. No beta.10 reset or reconfiguration is required.** Verify
   **Device info → 0.1.0-beta.11** and the 14 Diagnostic rows on a four-band site.
   The nine original entities remain, with their existing IDs and user settings;
   13 purposeful additional diagnostic entities bring the normal total to22.
3. Confirm the selected current/next period, actual supplier markup, applied DSO,
   all four day ranges, VAT and final. Old beta1–9 installations still need the
   explicit older-schema procedure in the setup guide; do not reset a beta.10 site.

[Native Diagnostic guide/screenshots](DIAGNOSTICS.md) ·
[Complete HACS installation procedure](HACS_DISTRIBUTION.md) ·
[Owner acceptance checklist](BETA_ACCEPTANCE.md) · [API2 contract](API.md).

## Verification

**123 tests per core**, HA2026.10.3 and current2026.10.4, **90% coverage**, zero skips;
18 existing card browser regressions; official hassfest/HACS/Ruff/package CI.
Cases cover coherent current/next values, the owner-shaped287.42 example with
explicitly fictional private rates, automatic switching, mixed VAT/negative prices,
missing/stale sources, midnight next-day DSO, seasonal/DST ranges and live extra-band
creation/removal from the applicable schedule.

A disposable native HA.4 installation was loaded from the downloaded, SHA-verified
published beta.10 package, then upgraded to the candidate. All27 original entity IDs
across3 sites, all3 site configurations and both existing price-ledger files were
preserved byte-for-byte through upgrade, locale reloads and restart. Fifteen native
screenshots show actual EN/DA desktop/mobile Diagnostics, before/after/current/next/
missing states, four Radius bands and supplier details. No browser errors/warnings
or extra provider requests on reads. [Recorded/synthetic receipt](receipts/v0.1.0-beta.11-simulation.json).

Nineteen runtime files remain byte-identical to published beta.10, including pricing
math, source adapters, SQLite, scheduler, configuration/Options, API2 and card JS.
The updater only publishes verification metadata atomically with its prepared grid
cache. Reads do not fetch providers, normalize tariffs, recompose prices or write SQL.
No invoice, subscription, provisional, technical alias or charging feature was added.

The guarded publisher requires successful exact-source CI, the exact annotated tag,
reproducible archive hashes, unchanged main and all previous beta1–10 releases/assets.
Two fresh jobs independently download public metadata/source/assets and test actual
pinned HACS2.0.5/upstream beta10→11 installation plus both native ZIP layouts on both
cores. BUILD_MANIFEST.json and SHA256SUMS identify the exact source and archive bytes.

## Remaining owner acceptance

These are isolated software tests, **not acceptance on the owner's Raspberry Pi or
PAHA02-DEV**. Verify the real device page and actual contract/source values after
updating. The sample11.1øre supplier rate is fictional QA data, not an inferred EWII
rate. Historical EWII0.030DKK/kWh exVAT remains June–September2026 only. No future or
summer-house terms are assumed. Cloud benchmarks are not Pi performance evidence.

Config schema4, API2, persistent revisions, daily statistics, the optional price
card and required13:05/13:20/13:40/23:59/00:01 Copenhagen refreshes are retained.
No stable release, main merge, production HA, Node-RED or charging controls were changed.
Stop after verified beta.11 publication for owner real-HA acceptance testing.
