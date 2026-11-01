# Native device Diagnostics

Open **Settings → Devices & services → Energy Price Engine → your device →
Diagnostic**. No dashboard or extra YAML is needed to see how the price is calculated.
Beta.11 restores the component rows missing in beta.10. All are enabled by default.
The existing nine beta.10 entities keep their IDs and behavior.

| Visible diagnostic | Value |
|---|---|
|Current quarter / Next verified quarter|Local clock range of the selected verified stored record|
|Nord Pool spot (ex VAT)|That record's raw spot component|
|Applied DSO tariff|That record's grid component|
|Radius 1–4 · actual clock range|Today's independently verified grid schedule|
|Energinet network / system|The two recorded national components|
|Supplier markup|The site's actual configured, recorded markup|
|Electricity tax|The recorded applicable tax|
|VAT amount|Sum of the recorded component VAT amounts|
|Verified final price|The recorded final marginal price including VAT|
|Price availability|Current readiness and corrective guidance|

All numeric rows use **øre/kWh, two decimals by default**. Internal stored amounts
remain full-precision DKK/kWh. The six ex-VAT components plus the applied VAT amount
reconcile to the final price before rounding. Independently rounded rows can differ
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

Beta.10 → beta.11 is an in-place update: back up, select beta.11 in HACS, restart and
reload the app/browser. Keep existing sites, histories, manual overrides and CM API2
mappings. Reset is only for deliberately recreating older incompatible beta1–9 sites.
Owner private contract values are never supplied as defaults. In particular, the
historical EWII household0.030DKK/kWh exVAT applies only June–September2026.
