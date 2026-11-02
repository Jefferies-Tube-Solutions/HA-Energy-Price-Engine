# Native device Diagnostics

Open **Settings → Devices & services → Energy Price Engine → your device →
Diagnostic**. No dashboard or extra YAML is needed to see how the price is calculated.
Version1.0.0 retains the complete calculation rows and saved VAT display preference. All are enabled by default.
The nine primary entities keep their IDs and behavior. The availability
row uses the compact caption **Status** so its full label fits beside longer
readiness guidance; user-assigned names are preserved.

| Visible diagnostic | Value |
|---|---|
|Including VAT|Yes / No (Danish Ja / Nej), saved in initial setup or normal Configure|
|Current quarter / Next verified quarter|Local clock range of the selected verified stored record|
|Nord Pool spot|That record's spot component in the selected VAT basis|
|Applied DSO tariff|That record's grid component|
|Radius 1–4 · actual clock range|Today's independently verified grid schedule|
|Energinet network / system|The two recorded national components|
|Supplier markup|The site's actual configured, recorded markup|
|Electricity tax|The recorded applicable tax|
|VAT amount|Sum of the recorded component VAT amounts|
|Verified final price|The recorded final marginal price including VAT|
|Status (existing price availability entity)|Current readiness and corrective guidance|

All numeric rows use **øre/kWh, two decimals by default**. Internal stored amounts
remain full-precision DKK/kWh. With **Including VAT = Yes** (default), six component amounts use each stored
`incl_vat` value and sum to the VAT-inclusive final. With **No**, they use stored
`ex_vat` and sum to the VAT-exclusive final. **VAT amount** always shows the actual
stored tax amount, unchanged; in No mode it is informational. Do not add VAT a second
time in Yes mode. Independently rounded rows can differ
slightly from the displayed final. Negative spot/VAT amounts remain signed.

When the current final price is unavailable but the next quarter is READY, the period
row explicitly says **Next verified quarter** and shows its local time range. Every
component, VAT and final comes from that same stored record and revision. The
ordinary **Current spot** and **Current DSO** sensors remain independently current;
they must not be mistaken for the selected next-quarter breakdown. At the boundary,
the diagnostic period and components switch automatically to the current quarter.
If neither quarter is verified, the numeric component rows are Unknown, with the
missing component/source reason in the period/availability rows. No prices become zero.

The Radius day rows use the already prepared verified grid cache, even when supplier
coverage is missing and the final-price ledger is empty. Their names contain actual
local clock ranges, ending with24:00 at day end. Distinct nonadjacent bands retain
separate rows even when their amounts match. Explicitly configured adjacent bands
also remain separate. PE never infers undocumented band boundaries from illustrative
hours. A flat or different source schedule is shown truthfully: unused first-four
rows are unavailable, and additional actual ranges gain enabled diagnostic rows.
Extra rows from an earlier day remain unavailable when no longer applicable. Each
row's attributes include its actual range count, source, effective dates and UTC/
local timestamps, including DST offsets. Repeated clocks are distinguished when needed.
Manual sites use DSO labels rather than incorrectly claiming a Radius source.

Diagnostics reads never fetch Nord Pool, Radius or Energinet, normalize provider
tariffs, recompose final prices or write SQLite. Grid cache verification metadata is
published once with its update-time snapshot; stale/failed grid verification is
unavailable. A Nord Pool failure does not itself erase a separately fresh grid cache.
Price component rows still fail closed under API2 readiness, including source errors.

The primary Sensors show live current/next/statistical values. Native Diagnostics
shows the calculation and grid bands. The optional bundled Lovelace card adds graphs
and today/tomorrow tables. All three views share the same stored/cached price data;
none replaces native Diagnostic visibility.

Beta.12 → v1.0.0 is an in-place update: back up, select v1.0.0 in HACS with beta
visibility off, restart and
reload the app/browser. Keep existing sites, histories, manual overrides and CM API2
mappings. Reset is only for deliberately recreating older incompatible beta1–9 sites.
Owner private contract values are never supplied as defaults. In particular, the
historical EWII household0.030DKK/kWh exVAT applies only June–September2026.

## VAT presentation and history safety

Set **Including VAT?** during the normal Site/source setup step; default Yes. For an
existing site, open **Configure → Including VAT — display preference** (not Advanced).
Submitting saves immediately; closing an unsubmitted form leaves the saved value.
The preference persists through restart and defaults Yes for beta.11 entries lacking
it. It is strictly boolean and separate from source-rate `vat_included`, the actual
VAT fraction, canonical ledger data and CM API2. Changing it does not reload sources,
request providers, write/reprice the ledger or change price revisions/readiness.

The new enabled **Including VAT** enum row displays Yes/No, localized Ja/Nej. A normal
four-band site has 15 Diagnostic rows / 23 total entities. All beta.11 identities are
preserved. The nine primary sensor values keep their fixed basis (spot/DSO ex VAT,
final/statistics incl VAT), with explicit names/metadata, preserving Recorder continuity.
The dashboard follows the preference except the explicitly raw ex-VAT spot graph.
Grid periods project verified cache components, respecting already-inclusive inputs
and different VAT rates rather than multiplying arbitrary source rates by 1.25.

## Native HA evidence

The validated flow is **Devices & services → Energy Price Engine → device →
Diagnostic**, inspecting current/next/missing states, opening supplier more-info,
and observing the automatic selected-period switch. Desktop1440×1100/mobile390×1000,
English and Danish, had no browser errors/warnings, source requests on reads or
framework overlays. Browser plugin was unavailable; locked Playwright/system
Chromium was used. This is disposable software QA, not owner Raspberry Pi acceptance.

[Next quarter, desktop](images/beta11/next-diagnostic-desktop.png) ·
[Next quarter, mobile](images/beta11/next-diagnostic-mobile.png) ·
[Current quarter](images/beta11/current-diagnostic-desktop.png) ·
[Missing supplier with verified bands](images/beta11/missing-supplier-diagnostic-mobile.png) ·
[Danish next quarter](images/beta11/next-diagnostic-da-mobile.png) ·
[Supplier more-info](images/beta11/supplier-more-info-mobile.png) ·
[Exact snapshots and image hashes](receipts/v0.1.0-beta.11-simulation.json).


Beta.12 native Yes/No evidence and restart/upgrade results are recorded in
[the beta.12 simulation receipt](receipts/v0.1.0-beta.12-simulation.json).
These use disposable HA with recorded public tariffs and fictional private values;
they are separate from the owner's PAHA02-DEV acceptance.


[Beta.12 including VAT, mobile](images/beta12/next-yes-en-mobile.png) ·
[Excluding VAT, mobile](images/beta12/next-no-en-mobile.png) ·
[Danish Ja](images/beta12/next-yes-da-mobile.png) ·
[Danish Nej](images/beta12/next-no-da-mobile.png) ·
[Initial native setup](images/beta12/initial-setup-en-desktop.png) ·
[Configure No](images/beta12/configure-en-no.png) ·
[Current quarter No](images/beta12/current-no-en-mobile.png) ·
[Missing final with verified grid ranges](images/beta12/missing-final-no-en-mobile.png) ·
[No after restart](images/beta12/restarted-no-da-mobile.png) ·
[Native card No](images/beta12/native-card-no-da-desktop.png).


## Stable v1.0.0 acceptance evidence

[Native stable receipt](receipts/v1.0.0-simulation.json) records 30 screenshot hashes
and real HA2026.10.4 fresh setup, actual public beta.12 package upgrade and restart.
All69 original entity IDs, three effective site configurations and mixed Yes/No VAT
choices survived; both price-ledger files remained byte-identical and SQLite integrity
checks passed. The clean manual ZIP setup also retained23 IDs, its No preference and
ledger after restart. A fictional3.75øre including-VAT supplier input correctly showed
3.00øre in excluding-VAT Diagnostics. No owner private contract is inferred.

[Version1.0.0](images/v1.0.0/stable-device-version-desktop.png) ·
[Next quarter No](images/v1.0.0/stable-next-no-en-mobile.png) ·
[Danish Ja](images/v1.0.0/stable-next-yes-da-mobile.png) ·
[Missing final, verified grid](images/v1.0.0/stable-missing-no-en-mobile.png) ·
[Automatic next→current](images/v1.0.0/stable-switched-current-no-da-mobile.png) ·
[Fresh setup](images/v1.0.0/stable-fresh-site-desktop.png) ·
[Fresh Diagnostics](images/v1.0.0/stable-fresh-diagnostic-mobile.png) ·
[Fresh restart](images/v1.0.0/stable-fresh-restarted-mobile.png) ·
[Upgrade restart](images/v1.0.0/stable-restarted-no-da-mobile.png).

These are isolated recorded/synthetic software checks, separate from owner hardware
acceptance. Public HACS stable channel verification follows publication; a local
manual/native install alone does not establish public HACS discovery.
