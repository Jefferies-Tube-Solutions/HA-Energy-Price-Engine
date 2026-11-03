# Install and update Energy Price Engine

## Opt-in v1.1.0-beta.1

The dedicated Issue20 prerelease adds automatic card resources and independent
øre/DKK card units. Keep v1.0.0 for stable use. To install the published prerelease,
HACS → Energy Price Engine → Show beta versions → explicitly select **v1.1.0-beta.1**
→ download → restart HA → reload the app/browser. Enabling visibility alone need not
change HACS's selected download version. No site reset, history migration or second
HACS dashboard repository is required. Main and latest stable stay v1.0.0.

Storage-mode Lovelace automatically receives exactly one installed-version module;
an existing single manual PE URL is updated in place. YAML resources stay user-managed.
[One-card quick start, two-card YAML and troubleshooting](PRICE_DASHBOARD.md) ·
[Prerelease notes and scope](RELEASE_V11_BETA1.md) · [Current publication status](DEVELOPMENT_STATUS.md).

## Fresh HACS installation

1. Install HACS using its supported instructions and back up Home Assistant.
2. HACS → **Custom repositories** → add
   `https://github.com/NicolaiTandrup/HA-Energy-Price-Engine`, category **Integration**.
3. Leave **Show beta versions off**. Download the stable **v1.0.0** release, then
   restart Home Assistant. Device info must show **1.0.0**.
4. Add the official Home Assistant **Nord Pool** integration for DK1 or DK2 and DKK.
   PE reads its supported `get_prices_for_date` service in DKK/MWh excluding VAT.
   A legacy custom Nordpool integration must not shadow the same `nordpool` domain.
   Simultaneous legacy/official operation is not required; recorded data can be
   compared offline with `tools/compare_recorded_prices.py`.
5. Add **Energy Price Engine** in Devices & services. In the normal Site/source
   form, choose **Including VAT?** (default Yes). Confirm Radius C only for a matching
   connection; otherwise supply a verified grid rate. Enter actual supplier markup
   in øre/kWh. The rate-input **includes VAT** checkbox describes that source amount;
   it is separate from the display preference. No private rate is assumed.
6. Submitted steps save immediately; unsubmitted fields remain unsaved. Configure
   resumes incomplete setup. **Done — close setup** finishes. Add independent entries
   for additional sites. **Check prices now** retries source verification.
7. Inspect the native device **Diagnostic** section. Add the optional
   [bundled dashboard](PRICE_DASHBOARD.md) for graphs and today/tomorrow tables.

Normal confirmed rates start at the next complete quarter. Confirm earlier-today
coverage only if it is true. Advanced dated rates use an inclusive start and exclusive
end date, with optional local hours. Remove overlapping manual rules before replacing
them. Expired public rates need verified replacements; do not extend dates just to
obtain READY. Missing input prices remain unavailable.

## Update from beta.12

1. Take a complete HA backup, including configuration, `.storage`, Recorder and PE
   SQLite files. Record source and private contract settings.
2. In HACS, open Energy Price Engine. Turn **Show beta versions off** to use the
   stable channel, refresh information, select **v1.0.0**, download and restart HA.
3. Reload the app/browser and cached card resources. The recommended resource is
   `/ha_energy_price_engine/energy-price-engine-card.js?v=1.0.0`.
4. **Keep existing sites, entity IDs, history, revisions, overrides and VAT display
   choice. No beta.12 reset or database migration is required.** Device info shows
   1.0.0; the stable price API remains v2. Beta.10/11 use the same schema4, while
   [older incompatible beta1–9](LEGACY_BETA_UPGRADE.md) have a separate procedure.
5. Verify current/next readiness, the native components and actual grid ranges, supplier
   terms and VAT Yes/No. See the [acceptance checklist](ACCEPTANCE.md).

A stable release fixes the historic HACS no-stable-release fallback to a short main
SHA. HACS should offer `v1.0.0`, not a commit hash, even after newer main commits. If
information is stale, refresh HACS and inspect the HACS-owned update entity. PE has
no duplicate release-update entity. Explicit beta opt-in can offer future prereleases;
leave it off for stable updates. Do not edit HACS storage or patch HACS globally.

## Manual installation

Download `ha_energy_price_engine-manual.zip`, `BUILD_MANIFEST.json` and `SHA256SUMS`
from [v1.0.0](https://github.com/NicolaiTandrup/HA-Energy-Price-Engine/releases/tag/v1.0.0).
Verify SHA-256 before extraction into the HA configuration directory. The result is
`custom_components/ha_energy_price_engine/manifest.json`, containing version `1.0.0`.
Restart HA. Do not overlay a manual copy onto a HACS-managed integration.

The separate `ha_energy_price_engine.zip` asset has integration files at its root for
HACS's installer; do not extract it directly into the HA configuration root. Both
layouts are independently tested outside the repository source tree.

## Data retention and rollback

Normal HA entry deletion and HACS uninstall retain PE history. Explicit PE **Reset
this site** permanently removes only that selected entry's PE files after exact-name
confirmation. It does not delete other sites, Recorder, Nord Pool or unrelated data.
Never bulk-delete PE files or edit `.storage` by hand. To return to an earlier version,
stop HA and restore a matching complete backup; avoid mixing older code with newer
configuration or edited ledger files.

## Catalog and artwork

A GitHub stable custom-repository release is independent of admission to the official
HACS default catalog. A separate owner submission/review is required for catalog
listing. Local HA branding is bundled and tested through the supported brands route;
some HACS artwork uses the external Home Assistant brands catalog and requires separate
brand acceptance. See [compatibility](COMPATIBILITY.md). No catalog admission is claimed.
