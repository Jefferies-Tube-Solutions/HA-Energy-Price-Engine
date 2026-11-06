# JTS Tariff Engine v1.2.0

Prepared for publication. See the [latest published release](https://github.com/Jefferies-Tube-Solutions/HA-Energy-Price-Engine/releases/latest)
for the version currently available to install.

- Energy Price Engine becomes JTS Tariff Engine in Home Assistant, HACS, the
  bundled dashboard and the documentation.
- The Home Assistant service shows JTS Tariff Engine as the model,
  Jefferies Tube Solutions as the manufacturer and the installed software version.
  The configured site name remains the service name.
- The packaged Home Assistant icon comes from the approved
  [JTS Brand System artwork](../assets/brand/README.md).

Update the existing integration and restart Home Assistant. The
`ha_energy_price_engine` domain, site and entity identifiers, price calculations,
ledger format, read-only API v2, ZIP names and Lovelace card type remain compatible
with v1.1.0. Existing storage-mode dashboard resources update to the installed
version. For YAML resources, update the version query and reload the browser.
Follow the [installation and update guide](HACS_DISTRIBUTION.md).
