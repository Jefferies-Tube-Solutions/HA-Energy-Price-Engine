# Bundled electricity-price dashboard

## v1.1 beta: add the card once

Install PE once as a HACS **Integration**. In v1.1.0-beta.1, storage-mode Lovelace
automatically receives its bundled JavaScript module, even before the first dashboard
visit. Add a manual card with:

```yaml
type: custom:energy-price-engine-card
```

No second HACS repository or manual Resource UI step is needed. PE derives the cache
URL from its installed manifest: `/ha_energy_price_engine/energy-price-engine-card.js?v=1.1.0-beta.1`.
It loads the native resource collection before listing it, adopts one existing exact
local PE path (including old v1.0.0 URLs) in place, and preserves unrelated resources
and their order. Restarts, site reloads and additional sites do not create duplicates.
A registration failure logs a corrective action and leaves pricing operational.

For multiple sites, select one in each card, or set its stable `site_id` explicitly.
Renaming a site does not change its ID; an intentional reset creates a new identity.

## Two cards, two units

Each card independently accepts `unit: ore_kwh` (default, two decimals) or
`unit: dkk_kwh` (four decimals). Units affect only frontend formatting. All views,
axes, tooltips, statistics, tariff rows, selected components and quarter tables use
the chosen unit. No intermediate rounding is applied before dividing the original
øre value by100; unavailable values remain gaps. Canonical data, API v2, sensor units,
VAT preference and historical revisions remain unchanged.

Complete storage-dashboard YAML (use a manual card/vertical stack for just the cards):

```yaml
title: Electricity prices
views:
  - title: Prices
    path: prices
    cards:
      - type: custom:energy-price-engine-card
        unit: ore_kwh
      - type: custom:energy-price-engine-card
        unit: dkk_kwh
```

Both can select the same site; `site_id: YOUR_EXISTING_SITE_ID` is optional on each.
Concurrent requests on the same authenticated HA connection are shared. Each card's
site/quarter selection, expansion and unit remain independent. Switching units uses
the already loaded snapshot without another backend request. Responses are not kept
in a shared stale cache. [Complete example](dashboard.yaml).

## YAML-managed resources and troubleshooting

`lovelace.resource_mode: yaml` remains user-managed. PE serves the file and logs the
required module URL but never edits YAML or silently injects extra JavaScript. Add
the resource yourself, then reload Lovelace resources:

```yaml
lovelace:
  resource_mode: yaml
  resources:
    - url: /ha_energy_price_engine/energy-price-engine-card.js?v=1.1.0-beta.1
      type: module
```

For **Custom element not found**, check Devices & services for a loaded PE integration,
HA logs, and Settings → Dashboards → Resources (Advanced mode). There should be one
PE module at the installed version URL. If multiple exact PE paths exist, PE reports
the conflicting IDs and leaves them unchanged: keep one through HA's supported UI,
then restart HA. Reload the app/browser after an upgrade. Storage permission failures
need correction before retrying; pricing does not depend on registering the card.

PE leaves its resource registered when a site unloads, is removed, or HA transiently
reloads. After completely uninstalling PE and removing its cards, the owner may remove
only the orphan PE URL through Resources UI, or edit their own YAML. PE never deletes
other resources. Stable v1.0.0 still uses its documented manual Resource UI step;
these automation/unit features require the opt-in v1.1 beta.

The card shows separate raw/final graphs for today and tomorrow, today's verified
DSO time bands, every local quarter, and a selected-quarter component/VAT/source
inspector. Select a bar or table interval. DST repeated hours show UTC offsets;
missing prices leave gaps. The default displays øre/kWh with two decimals; DKK uses four. Totals
use unrounded stored values. Horizontal tables scroll within the card on mobile.

**Full-day statistics** include all 92/96/100 calculated quarters immediately.
**Remaining-day statistics** cover a complete available suffix of today when
unverified earlier private rates prevent full-day coverage. The three native
statistic sensors change their friendly names accordingly and expose `scope`,
`used_slots`, `day_slots` and range attributes. A middle gap makes statistics
unavailable; PE does not skip that gap or pretend partial data is a complete day.
These are schedule statistics, not Recorder sample statistics or settled accounting.

Availability explains current/next/tomorrow readiness, missing components, the
source/verification failure, affected period and corrective action. Unknown current
price after first setup can be correct: the rate starts next complete quarter.
Tomorrow can be unpublished while today's future range is READY. After public rate
expiry, confirm new documented rates under Advanced. Missing rates are never zero.

The card is read-only and uses authenticated HA WebSocket commands filtered by
entity read permissions. It reads precomputed prices/cached source snapshots,
without provider requests, tariff recomposition or SQLite writes. Its two-day
schema is internal v3; Python consumer API v2 is documented separately.

## Native software screenshots

[Desktop dashboard](images/beta10/dashboard-desktop.png) ·
[Mobile dashboard](images/beta10/dashboard-mobile.png) ·
[Remaining-day/multiple sites](images/beta10/dashboard-remaining-mobile.png) ·
[DSO intervals](images/beta10/dashboard-grid-mobile.png) ·
[Component inspector](images/beta10/dashboard-inspector-mobile.png) ·
[Quarter table](images/beta10/dashboard-quarters-desktop.png) ·
[Nine-entity device](images/beta10/device-desktop.png) ·
[Danish saved setup](images/beta10/setup-saved-da-mobile.png).

These are actual disposable Home Assistant screens using recorded public tariffs and
fictional private rates, not owner installation screenshots. The
[simulation receipt](receipts/v0.1.0-beta.10-simulation.json) records hashes and results.


## VAT display and Recorder history

Configure → **Including VAT** controls the card's stored components, final graph,
statistics and verified DSO day bands. Default Yes uses each component's `incl_vat`;
No uses `ex_vat`. Ex-VAT final sums unrounded stored components from the same quarter.
Actual VAT amount remains informational and unchanged in both modes. Labels state the
selected basis. The separate **Raw Nord Pool spot** graph is always ex VAT and is
clearly labeled; it can remain available without a complete final-price record.

The nine primary sensor values and their Recorder state classes retain stable fixed
semantics: spot and current DSO exclude VAT; final and statistical sensors include VAT.
Their names and metadata state that fixed basis. This avoids switching long-term
statistics under an existing identity. Diagnostic numeric entities have no statistics
state class. No reset, historical reprice, price revision or API2 value change occurs.
After upgrading, reload app/browser resources: internal dashboard schema3 requires the
matching installed-version JavaScript and rejects older schema2 clients instead of mislabeling data.
