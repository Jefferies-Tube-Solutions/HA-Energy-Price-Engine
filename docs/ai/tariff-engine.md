# JTS Tariff Engine — AI Systems Reference

Based on v1.2.0 stable. Service info and Configure enhancements are in review. [Human Operations Manual](../guides/tariff-engine.md).

## System Registry

| Surface | Contract |
| --- | --- |
| Integration | `ha_energy_price_engine`, a Home Assistant service integration distributed as a HACS custom integration |
| Host | Home Assistant 2026.10.0 or later. CI targets 2026.10.3 and 2026.10.4. |
| Source | Official `nordpool.get_prices_for_date` for DK1/DK2 in DKK |
| Storage | Per-site SQLite history and revisions. [Storage contract](../ADR-002-ledger-storage.md). |
| Consumers | Synchronous read-only Python API v2. [Fields, types and revision event](../API.md). |
| Dashboard | `custom:energy-price-engine-card`. Optional `site_id` selects a site. Optional `unit` accepts `ore_kwh` (default) or `dkk_kwh`. [Example](../dashboard.yaml). |
| Packaging | Root `hacs.json` and `custom_components/ha_energy_price_engine/manifest.json`. [Installation and rollback](../HACS_DISTRIBUTION.md). |

The service name is the configured site name. The model is JTS Tariff Engine,
the manufacturer is Jefferies Tube Solutions and the software version comes
from the installed manifest. The service's `configuration_url` targets the README
Commissioning section. The Configure site and review steps display an English
product overview. The rebrand preserves the v1.1.0 domain, site
and entity identifiers, ledger format and API v2.

## Read and validate

Call `get_api(hass, version=2)` and use an actual loaded site ID from
`api.sites()`. Request an aware, UTC-quarter-aligned half-open interval.
For example, 12:00Z to 12:15Z covers one quarter. An end of 12:10Z raises
`ValueError`. An unknown or unloaded site raises `EngineNotReady`.

Consume quotes only when the whole window is `READY`. Quotes are in
full-precision DKK/kWh including VAT and may be negative. The dashboard VAT
preference leaves API values unchanged. Treat revision events as hints to
re-read the affected interval. Reads neither fetch sources nor write history.

## Verification

CI exercises metadata, installation layouts, both supported test environments
and dashboard scenarios. Installation-specific rates and physical hardware
are verified separately. [Development status](../DEVELOPMENT_STATUS.md) ·
[v1.2.0 release notes](../RELEASE_V12.md).
