# Compatibility, troubleshooting and operational limits

## Supported installation

PE1.0.0 requires HA2026.10 or later, DK1/DK2, Europe/Copenhagen and the official
Nord Pool integration configured for DKK. The locked regression matrix uses
HA2026.10.3 and2026.10.4/Python3.14.8. Later HA versions still need normal compatibility
validation; a minimum version is not a promise about untested future releases.

HACS custom-repository installation uses the normal stable v1.0.0 release with beta
visibility off. Actual pinned HACS2.0.5 and upstream handling are tested with supported
HA update-entity and WebSocket behavior; GitHub transport is recorded/mocked in software
QA. Post-publication checks independently download actual public metadata and assets.

## Price availability

- Official source unavailable/stale: inspect Nord Pool entry, selected area/currency,
  affected period and retry time. Retained values never become fake READY prices.
- Missing supplier/grid: Configure the actual marginal rate and its VAT convention.
  Newly confirmed rates start next quarter unless earlier coverage is explicitly true.
- Current missing, next READY: first activation can start at the next complete quarter.
  Native Diagnostics explicitly selects that next record; numeric current stays Unknown.
- Tomorrow incomplete: publication or source coverage may be pending. It does not
  invalidate a separately verified today range, and partial tomorrow is never a full day.
- Public rates expire: Energinet network/system defaults end on1January2027; tax defaults
  end on1January2028. Add a verified replacement with real effective dates; no future
  rates, EWII terms, heating eligibility or private products are guessed.
- Storage error/corruption: preserve a backup, stop the affected workflow and use
  [explicit recovery](PERFORMANCE.md). PE refuses to overwrite corrupt authoritative
  history. Normal entry deletion/HACS removal retain history; explicit site reset does not.

## VAT and history

Including VAT is a display preference for native Diagnostics and the card. Source-rate
VAT inclusion and actual tax fractions are separate. Stored full-precision prices,
revisions and API2 remain canonical including VAT. Primary sensor values/state classes
keep their labeled fixed basis for Recorder continuity. Diagnostic numeric rows have
no long-term statistics state class; past Recorder samples retain the basis displayed
at that time. No historical samples are rewritten by the preference.

Price history is retained and indexed in memory by default. Monitor storage/RAM and
back up HA. Existing cloud scale/recovery measurements are software evidence, not
Raspberry Pi performance guarantees. Actual contracts, provider availability and
installation hardware still require owner acceptance.

## HACS version and branding

The historic short-SHA update (#12) was HACS's default-branch fallback while the
repository had no stable release and beta visibility was off. A real stable v1.0.0
supplies HACS's stable version. Tests exercise later main SHAs, cache restoration,
normal stable visibility and filtering of future prereleases. PE does not patch HACS,
spoof release versions or create a second release-update entity. Refresh stale HACS
information and leave Show beta versions off for the stable channel. Explicit opt-in
may intentionally offer future betas.

Current HA's supported authenticated `/api/brands/integration/<domain>/<image>`
route serves PE's bundled `brand/icon.png`; HA supplies logo/dark/high-resolution
fallbacks. This path is tested with the actual loader and HTTP route. HACS2.0.5's
update artwork uses `https://brands.home-assistant.io/_/<domain>/icon.png` instead.
Bundling a local icon does not register that external catalog. A generic HACS icon
can therefore remain until a separate Home Assistant brands submission is accepted.
No HACS/global frontend patches or unverified manifest icon fields are used.

Publishing a GitHub stable custom repository does **not** automatically list PE in
the official HACS default catalog/Marketplace. The owner can separately follow
[HACS integration publishing](https://www.hacs.xyz/docs/publish/integration/) and
[Home Assistant brands submission](https://github.com/home-assistant/brands).
Listing/artwork acceptance is not claimed by this release.

## Consumer compatibility

The stable producer contract is read-only Python API v2. The unreleased CM consumer
still requires a separate v1→v2 migration and validation; this does not block PE's
independent release. PE does not control vehicles, change Node-RED or authorize a
charging-controller cutover. See [API](API.md) and [CM handoff](INTEROPERABILITY.md).
