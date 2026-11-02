# v1.0.0 focused release-readiness review

Baseline: published beta.12 `e506ccfc40b61413bd83e3ce60081a60d517348f`, accepted by the
owner on PAHA02-DEV in issue18. PR19 is merged; final stable main/tag source is
19af5bf4412c5f3cc3b3e07c6d756da372f81ba6. Cumulative PR14 and all history are retained.
The current mission explicitly authorizes stable publication and ordinary reviewed PR
merge after all gates; it does not authorize bypassing repository rules or production.

## Risk review

| Area | Finding and evidence | Release disposition |
|---|---|---|
|Pricing/VAT/units|Canonical DKK/kWh, component ex/vat/incl snapshots, mixed source VAT, negative values and display projection retain beta.12 code; contract/VAT tests|No confirmed blocker; preserve arithmetic|
|Source/readiness|Official supported HA Nord Pool read service, source verification, per-interval masks, missing/stale/error fail-closed; partial tomorrow not full READY|Preserve bounded verification; no provider uptime claim|
|Public validity|National rates have explicit expiry; manual overrides require real evidence; no private EWII/future assumptions|Document known operational limitation|
|Persistence/revisions|SQLite checksums, atomic changed-row writes, historical freeze, retained revisions, rollback/corruption/concurrent-writer/backup tests|No schema change; native update/restart retained both ledger byte hashes|
|API/security|Immutable API2 memory reads; future whole-range readiness; WebSocket entity-read permission checks; no price-write/control service|Freeze stable API2; unchanged code|
|Lifecycle/resources|Idempotent stop, source registry listeners/unsubscribe, scheduled/pending cancellation, executor-based disk I/O; repeated reload/unload tests|Keep existing proven lifecycle; ResourceWarning is an error in CI|
|HACS/version|Prior no-stable fallback yields SHA; real stable metadata selects1.0.0; actual HACS tests cover opt-in/out, cache, newer main and future beta|Passed public stable discovery/install/update on both cores|
|Branding|HA local icon/logo/dark supported route passes; HACS2.0.5 uses external brands catalog|Document external submission; do not claim catalog admission|
|Onboarding/docs|Accepted saved-step configuration and Diagnostics retained; stable user-neutral install/API/limits docs; no forced beta.12 reset|Passed native fresh/upgrade/restart, 30 images, 69 IDs/three sites|
|Production|No owner HA, Node-RED, vehicle/charger or CM repository modifications|Out of scope; publication is not charging cutover|

No pricing/persistence/lifecycle defect requiring a runtime code fix was confirmed by
this focused review. All22 runtime Python modules and bundled JS are byte-identical
to beta.12. Manifest version and reset translations are the only runtime differences.

## Completed release evidence

Supported/current cores:142passed each,90%coverage,zero skips,two unchanged HACS deprecations.
Four actual-HACS cases cover two pins × beta visibility on/off, including fresh stable
and real beta.12 filesystem update. Native local-brand HTTP tests verify fallback
responses. All12 exact-source CI checks passed on766ecfc and e27dac9;22 browser
cases and official hassfest succeeded. [Native stable proof](receipts/v1.0.0-simulation.json)
records30 images,69 preserved IDs/three sites/two byte-identical ledgers, fresh setup
and both restarts. All12 final-source checks, seven exact-main checks and all four
publisher/public-verification/audit jobs passed. [Public stable receipt](receipts/v1.0.0.json)
and [anonymous downloads](receipts/v1.0.0-local-public.json) confirm publication, HACS
stable selection/install/update, both ZIP layouts and exact source/SHA256 equivalence.

No actual public provider queries or owner hardware are used by software fixtures.
Native simulation uses a controlled PE source/presentation clock with unchanged HA
auth/wall time; any timer mapping remains confined to QA, outside the shipped package.

## Issue disposition for owner review

|Issue|Disposition|Evidence / remaining scope|
|---|---|---|
|8|Done for accepted MVP|Saved source/grid/supplier steps, explicit Done, actual activation guidance, decimal rates and normal Configure; broader superseded product/subscription proposals are not stable scope|
|10|Done for accepted MVP|Owner accepted native component visibility in beta.11; stable retains all rows and beta.12 VAT preference|
|12|Partly done|Public stable semantic-version/install/update passed; local branding verified; external HACS artwork/catalog admission remains separate|
|15|Done for accepted MVP|Nine primary entities, daily/remaining statistics, today/tomorrow card and direct native components retained|
|16|Done|Owner real-HA beta.11 acceptance, coherent period/components and four real day bands preserved|
|17|Done|Owner accepted beta.12 VAT Yes/No; stored/API/Recorder invariance retained|
|5|Pending consumer work|Unreleased CM v1 adapter needs separate API2 migration and coupled tests; PE stable is independent|

No issue is closed automatically. Stable1.0.x maintenance should preserve this accepted
MVP and API2, fixing confirmed defects rather than introducing breaking features.
