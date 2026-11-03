# Energy Price Engine v1.1.0-beta.1 — Issue20

PE remains a single HACS integration. The bundled Lovelace card now registers its
versioned module automatically through HA's native storage-resource collection,
including cold startup before any dashboard visit. A single old manual PE URL is
adopted in place; unrelated resources and their order remain. Repeated startup/site
reload does not duplicate it. Ambiguous duplicate paths are reported without edits.
YAML resources stay user-managed, with precise instructions. Registration errors log
an action and leave the pricing engine operational.

Each card accepts optional `unit: ore_kwh` (default, two decimals) or `unit: dkk_kwh`
(four decimals). Full-precision frontend values are converted only at presentation.
Graphs, axes, tooltips, statistics, tariffs, breakdowns and every quarter use that
unit. Cards preserve independent selection and share concurrent authenticated reads.
Changing units does not request backend data. The saved VAT preference is retained.

```yaml
type: vertical-stack
cards:
  - type: custom:energy-price-engine-card
    unit: ore_kwh
  - type: custom:energy-price-engine-card
    unit: dkk_kwh
```

Optional `site_id` selects an existing site. [Full example](dashboard.yaml) ·
[Resource registration, YAML fallback and troubleshooting](PRICE_DASHBOARD.md).

The actual v1.0.0 engine/API v2, SQLite schema/history/revisions, tariff/source code,
sensors, site IDs and configuration are preserved. Dashboard data-producing functions
are unchanged; only native setup registers the optional module. Today+tomorrow,
92/96/100-quarter DST days, negative prices, readiness gaps and VAT semantics remain.
No new price sensors, controls, provider or contract defaults are introduced.

## Validation and release scope

Automated tests cover native collections, cold loading, adoption/order, concurrency,
YAML, ambiguous duplicates, pricing startup on resource failure and multi-site reload.
Browser tests cover paired units in EN/DA, desktop/tablet/mobile, full source precision,
negative/near-zero values, missing windows, DST and VAT projection. Actual pinned HACS
checks stable default versus explicit beta visibility/selection, upgrade/install,
reinstall/uninstall and persistence. Both package layouts are tested outside source.
Native disposable HA checks fresh cold load, public v1.0.0 upgrade, retained sites and
IDs/SQLite bytes, native resource loading, paired cards and restart. Exact outcomes
and source hashes are recorded in the [handoff](DEVELOPMENT_STATUS.md) and
[native receipt](receipts/v1.1.0-beta.1-simulation.json).

For HACS testing, enable **Show beta versions**, explicitly select **v1.1.0-beta.1**,
download, restart HA and reload the browser/app. Keep existing sites and history.
Storage resources update automatically; YAML resources need the versioned URL shown
in the dashboard guide. Uninstalling one site does not remove a global resource;
after complete PE uninstall the owner can remove only the orphan PE module in HA UI.

This is an opt-in prerelease on a dedicated reviewable branch/PR. Main stays at
v1.0.0 and v1.0.0 remains latest stable. Publication requires normal review/security,
exact-source push/PR/tag CI, clean reproducibility, immutable annotation and all prior
release/tag/asset integrity checks. Fresh public jobs independently verify actual
metadata/downloads, stable and beta HACS channels and both native ZIP layouts.

Owner PAHA02-DEV visual acceptance remains separate and required before any future
stable promotion. These recorded/synthetic tests establish neither provider uptime
nor Raspberry Pi performance. No production HA, Node-RED, CM or charging control
was changed. No main merge or v1.1 stable publication is part of this mission.
