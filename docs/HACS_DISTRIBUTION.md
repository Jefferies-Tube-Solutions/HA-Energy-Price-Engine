# Install beta.12 on PAHA02-DEV

This procedure is for the owner's development HA. No owner HA was accessed by this
mission. Beta.12 preserves beta.10/11 configuration, entities, SQLite history and API2.
Back up first. An unreleased CM built for API1 remains incompatible with API2.

## Update beta.10 or beta.11 in place

Enable HACS **Show beta versions**, refresh information, select **v0.1.0-beta.12**,
download and restart HA, then reload the app/browser and any cached card resources. **Keep existing sites; no reset
is needed.** Device info must show 0.1.0-beta.12. Under **Diagnostic**, verify the price
period, eight component amounts, four real Radius time ranges, availability and Including VAT. All monetary Diagnostic
rows follow that preference; VAT amount always shows the actual stored tax amount.
The Including VAT row shows Yes/No. Change it through normal Configure; the source-rate
VAT checkbox remains separate. The original nine entities and source/contract mappings remain. See
[Native Diagnostics](DIAGNOSTICS.md) for the complete acceptance list.

The remaining reset procedure applies only to older incompatible beta1–9 sites.

## Older incompatible beta1–9 installations

1. Take a complete development HA backup (code, config, `.storage` and Recorder).
   Record supplier/grid values, effective periods, the official Nord Pool entry and
   any manual overrides. Keep the beta.9 backup if you need its history or a downgrade.
2. In HACS, open **Energy Price Engine**, use its three-dot menu and enable **Show
   beta versions**. Keep this setting enabled: without it HACS may offer main's short
   SHA because there is no stable PE release. Refresh information, select
   **v0.1.0-beta.12**, download, then restart HA and reload the app/browser and any cached card resources.
3. Old PE entries intentionally fail migration with a breaking-beta message. Nothing
   is deleted. Open the old entry's **Configure**: it opens **Reset this development
   site**. After confirming your backup, type that site's exact name and tick the
   permanent deletion confirmation. Only that entry and its PE files are removed.
   Repeat only for sites you intentionally want to recreate. Other sites, Recorder,
   automations, Nord Pool and unrelated files remain untouched.
4. Add **Energy Price Engine** again for each site. New IDs/entities/history are
   intentional. Update any development dashboards/automations and future CM site
   mappings. Do not edit `.storage` by hand or bulk-delete PE-prefixed files.
5. Check **Device info → 0.1.0-beta.12**, nine original entities plus native diagnostics, and the availability
   sensor. Validate with the [acceptance checklist](BETA_ACCEPTANCE.md).

Normal HA **Delete** retains the selected site's PE history files. Explicit PE reset
is the destructive operation above. HACS uninstall removes integration code and
retains HA data. Old files do not auto-attach to a newly generated site ID. A
stopped-HA full backup restore is the supported way to return to a prior beta.

## Clean installation

1. HACS → three-dot menu → **Custom repositories**: add
   `https://github.com/NicolaiTandrup/HA-Energy-Price-Engine`, category **Integration**.
   The existing approved main bootstrap contains HACS-compatible integration files.
   Beta.12 does not require another main merge or a stable release.
2. Enable **Show beta versions**, select **v0.1.0-beta.12**, download, restart HA.
   Do not select main or an older beta when following this guide.
3. Add official **Nord Pool** in Devices & services for DK1/DK2 (DKK). PE reads its
   supported `get_prices_for_date` service in DKK/MWh ex VAT. Disable/remove any legacy
   custom integration that shadows domain `nordpool` using your normal development
   procedure; simultaneous legacy/official operation is not required. Recorded legacy
   data can be compared offline with `tools/compare_recorded_prices.py`.
4. Add PE: **Site/source → Grid → Supplier → Saved**. Radius C fetches verified
   Datahub time bands after you confirm that product. Other grids need a confirmed
   marginal rate. Enter supplier markup in øre/kWh and specify whether it includes VAT.
   There is no assumed EWII or summer-house contract.
5. A confirmed ordinary rate applies from the next complete quarter until you edit
   it. Tick the separate earlier-today confirmation only when that is true. Use
   **Advanced dated rates** for actual start/end dates or local hours. Manual rules
   override public defaults; overlapping manual rules must be removed before adding
   replacements. End dates are exclusive. Check expired public rates with verified
   documentation; do not extend dates merely to obtain READY.
6. Accepted steps are durable. Closing keeps them; fields not submitted are unsaved.
   **Configure → Check prices now** retries. **Done — close setup** exits without a
   second Save. Add independent PE entries for additional sites.
7. Register and paste the [bundled dashboard](PRICE_DASHBOARD.md).

## Manual ZIP fallback

Download `ha_energy_price_engine-manual.zip` and `SHA256SUMS` from the exact beta.12
prerelease, verify SHA256, and extract into the development HA configuration folder.
The result must be `custom_components/ha_energy_price_engine/manifest.json` (one
level). Restart HA. The HACS ZIP instead contains files at its root for HACS's
installer; do not extract that ZIP directly into the HA config root. Do not overlay
a manual package on a HACS-managed copy. Both layouts are tested outside this repo.

HACS workflow tests run actual pinned HACS 2.0.5 and upstream registration, supported
admin beta-visibility command, beta.11→.12 file update, reinstall and uninstall with
mocked GitHub I/O. Post-publication verification uses independently downloaded public
source/assets. These software tests do not claim owner acceptance on PAHA02-DEV.
