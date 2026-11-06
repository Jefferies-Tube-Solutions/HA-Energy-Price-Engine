<p align="right">
  <a href="https://github.com/Jefferies-Tube-Solutions/jts-tariff-engine/releases/latest">
    <img alt="Latest stable JTS Tariff Engine release" src="https://img.shields.io/github/v/release/Jefferies-Tube-Solutions/jts-tariff-engine?label=stable&amp;color=2ea44f">
  </a>
</p>
<p align="center">
  <img src="assets/brand/jts/v4/jts-white-transparent.png#gh-dark-mode-only" alt="Jefferies Tube Solutions — white text for dark theme" width="760">
  <img src="assets/brand/jts/v4/jts-deep-space-transparent.png#gh-light-mode-only" alt="Jefferies Tube Solutions — Deep Space text for light theme" width="760">
</p>
<p align="center">
  <img src="assets/brand/tariff-engine/v1/JTS_Tariff_Engine_Icon.png" alt="Approved Tariff Engine euro and lightning product symbol" width="128">
</p>

# JTS Tariff Engine

## Mission Directive

JTS Tariff Engine, formerly Energy Price Engine, is a native Home Assistant integration that calculates and
stores verified 15-minute electricity prices for **DK1 and DK2**. It combines
Nord Pool spot prices, grid tariffs, Energinet charges, your supplier markup,
electricity tax and VAT into a transparent marginal price per kWh.

The integration provides persistent price history and a stable read-only **API v2**.
It works independently of EV Charge Manager and sends no vehicle or charging commands.

## System Registry

| Component | Contract |
| --- | --- |
| Home Assistant | HACS custom integration with domain `ha_energy_price_engine` |
| Price sources | Official Nord Pool for DK1 and DK2, grid tariffs, supplier markup, national charges and VAT |
| Storage and consumers | SQLite price history and [read-only Python API v2](docs/API.md) |
| Dashboard | Bundled Lovelace card with per-card øre/kWh or DKK/kWh display |
| Version | The badge shows the published stable release. This branch prepares v1.2.0. |

## Commissioning

Requires Home Assistant 2026.10 or later and the official **Nord Pool** integration,
configured for DK1/DK2 and DKK. Tested Home Assistant versions are 2026.10.3 and
2026.10.4. A legacy Nordpool integration is not required; it must not shadow the
official `nordpool` integration.

1. In HACS, open **Custom repositories**, add
   `https://github.com/Jefferies-Tube-Solutions/jts-tariff-engine` as an **Integration**.
2. Keep **Show beta versions off** for the stable channel. Download the latest stable release and
   restart Home Assistant. A custom repository does not require Marketplace admission.
3. In **Settings → Devices & services → Add integration**, select **JTS Tariff Engine** (**Energy Price Engine** on v1.1.0 and earlier).
4. Name the site, select the official Nord Pool source and choose whether to display
   prices including VAT. Confirm **Radius C** only if your connection uses that product;
   otherwise enter your verified grid rate. Enter your actual supplier markup in
   **øre/kWh**, specifying whether the entered rate already includes VAT.
5. Each submitted step saves immediately. **Configure** resumes setup or changes
   settings later. Create a separate entry for every independently configured site.

[Complete installation and update guide](docs/HACS_DISTRIBUTION.md) ·
[Manual installation](docs/HACS_DISTRIBUTION.md#manual-installation).

## Operational Protocol

### Prices and Diagnostics

Nine primary entities show current/next spot and final prices, today's
average/minimum/maximum, current grid tariff and availability. Values default to
**øre/kWh with two decimals**; calculations and API values retain full precision.
Negative prices and 92/96/100-quarter daylight saving days are supported.

Open the native **device → Diagnostic** section to see the selected current or next
verified quarter, every price component, four actual Radius day ranges and rates,
VAT amount, verified final price, availability and **Including VAT — Yes/No**.
A four-band site has 15 Diagnostic rows. No dashboard is needed to inspect the price.

The saved VAT preference controls Diagnostics and the bundled card. Each component
uses its stored VAT-inclusive or VAT-exclusive value. Actual VAT amount remains visible
and unchanged in both modes. The nine primary sensors retain their explicitly labeled
VAT basis to preserve Recorder history; API v2 always returns canonical final prices
including VAT. See [Diagnostics](docs/DIAGNOSTICS.md).

### Today and tomorrow dashboard

Storage-mode dashboards automatically register the card. Each card can use
`unit: ore_kwh` or `unit: dkk_kwh` independently. YAML resources are managed by the user.

The bundled read-only card shows separate raw spot and final-price graphs, every
quarter, verified grid periods and a component/source inspector. It follows the VAT
preference; the clearly labeled raw Nord Pool graph remains excluding VAT.

[Add the bundled dashboard](docs/PRICE_DASHBOARD.md). After an update, reload the
browser/app and card resource. Daily statistics use complete verified schedule data,
including future quarters. When earlier rates are unverified, statistics explicitly
cover the remaining day. Unknown history is never invented.

## Verification

The integration owns retrieval, verification, calculation, persistence and price publishing.
Missing or stale inputs produce **Unavailable**, never an invented zero. Availability
reports the affected period and corrective action. Tomorrow may be unpublished while
today is ready; each requested API window must be fully verified to be READY.

Source refresh checks occur at **13:05, 13:20, 13:40, 23:59 and 00:01** Copenhagen
time, with conditional retries and restart recovery. The SQLite ledger retains
historical prices and revisions; back up Home Assistant and monitor storage capacity.
[Persistence and recovery](docs/PERFORMANCE.md).

Supplier terms are private site settings and are never guessed. Bundled national
charges have verified effective dates: Energinet network/system defaults expire on
1 January 2027; electricity tax defaults expire on 1 January 2028. New rates require
verified documentation. The historical EWII household markup of 0.030 DKK/kWh ex VAT
applies only June–September 2026; it is not a current or future default.

## Fault Isolation and Recovery

The [stable read-only Python API v2](docs/API.md) exposes immutable full-precision
DKK/kWh prices and readiness.
The unreleased EV Charge Manager consumer still needs its own
[API v1→v2 migration](docs/INTEROPERABILITY.md).

JTS Tariff Engine models variable electricity cost. It does not reconstruct invoices, allocate
subscriptions, infer heating eligibility or control vehicles. Hardware performance
and private contract/source acceptance depend on the installation; cloud benchmarks
are not Raspberry Pi guarantees.

[Backup and rollback](docs/HACS_DISTRIBUTION.md#data-retention-and-rollback) ·
[Troubleshooting and limitations](docs/COMPATIBILITY.md) ·
[Implementation provenance](docs/PROVENANCE.md) ·
[Report a problem](https://github.com/Jefferies-Tube-Solutions/jts-tariff-engine/issues).

## Manuals

- [Human Operations Manual](docs/guides/tariff-engine.md)
- [AI Systems Reference](docs/ai/tariff-engine.md)

## Operations Log

- [v1.2.0 rebrand and upgrade notes](docs/RELEASE_V12.md) · prepared for publication.
- [Published releases](https://github.com/Jefferies-Tube-Solutions/jts-tariff-engine/releases).
- [Development and verification history](docs/DEVELOPMENT_STATUS.md).

## Approved artwork

[Logo variants and previews](assets/brand/README.md) · [Human asset guide](docs/guides/brand-assets.md) · [AI asset contract](docs/ai/brand-assets.md). The central brand system owns the editable sources; this project keeps pinned PNG copies.
