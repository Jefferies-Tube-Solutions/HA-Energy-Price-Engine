# Energy Price Engine v1.1.0 — Stable

Promotes the owner-approved v1.1.0-beta.1 source
`d7cb97c3b1efbed49d7f68a023c52ed6ba5fe10f` through cumulative PR #23 / issue #22.
The only integration payload change is manifest version 1.1.0. All Python runtime
modules, dashboard JavaScript, canonical API v2, price calculations, provider adapters,
VAT, site/entity identities and SQLite data/schema/revisions remain byte-identical.

Storage-mode Lovelace registers one bundled module, adopts an existing exact local
resource in place and updates its dynamic version URL. YAML resources remain manual.
Each card independently selects `ore_kwh` (two decimals) or `dkk_kwh` (four decimals).
Raw spot prices exclude VAT; final display follows the site's saved VAT preference.
Unavailable prices remain gaps. No private rate or provider availability is promised.

Supported/tested cores: Home Assistant 2026.10.3 and 2026.10.4, Python 3.14.8.
Back up HA, select v1.1.0 in HACS's stable channel after publication, download,
restart HA and reload the browser. Keep existing sites and history. No beta.1 reset
or migration is required. For YAML resources use `?v=1.1.0` manually.

[Installation and rollback](HACS_DISTRIBUTION.md) ·
[Both card YAML examples](PRICE_DASHBOARD.md) · [Actual validation status](DEVELOPMENT_STATUS.md).

The guarded publisher must verify candidate and exact-main CI, native beta-to-stable
acceptance, reproducible packages, prior release integrity and normal repository
policies. These notes alone do not establish publication. No production HA, vehicle,
Node-RED, CM or charging changes; no JTS Tariff Engine rebrand.
