# Beta.11 owner acceptance checklist

Focused native Diagnostic restoration, issue16. Software evidence uses isolated HA,
recorded public tariffs and fictional private rates. Owner boxes remain unchecked.

- [ ] Back up development HA and update HACS to **v0.1.0-beta.11**, then restart/reload.
- [ ] Keep beta.10 sites, histories, overrides and original entity IDs; no reset is needed.
- [ ] Device info shows **0.1.0-beta.11**.
- [ ] Open the **native device → Diagnostic** section without installing a dashboard.
- [ ] All14 rows appear on a four-band site: period,8numeric price components,
      4actual day ranges,Status. New diagnostic entities are enabled by default.
- [ ] Numeric values default to **øre/kWh with two decimals**.
- [ ] All four real Radius clock ranges/rates are visible, including separated equal-price bands.
- [ ] Applied DSO and actual supplier markup are directly visible as separate diagnostic rows.
- [ ] Current READY shows one coherent current-quarter breakdown.
- [ ] Current Unknown with next READY explicitly says **Next verified quarter**, shows
      its exact time range and uses that same stored record/revision for every component.
- [ ] At the boundary the selected breakdown automatically changes to current.
- [ ] Ex-VAT components + stored VAT reconcile with final before independent display rounding.
- [ ] Missing supplier/input gives Unknown values with a reason; independently verified
      grid day ranges remain visible. No fabricated zero or substituted season/site.
- [ ] Different/missing/additional actual grid ranges are identified truthfully.
- [ ] The original nine live/statistical entities, daily statistics, card and CM API2 still work.
- [ ] Actual contracts, provider availability and physical Pi/mobile behavior are acceptable.

Automated evidence:123 tests/core on HA2026.10.3/current2026.10.4,90%coverage;
18 card browser regressions;native current/next/missing/EN/DA/desktop/mobile screenshots;
real downloaded-beta10 upgrade preserving27 original IDs,3 configs and2 ledgers;
actual HACS/native ZIP install/update tests;official hassfest/HACS and exact-source CI;
clean reproducible packages;guarded beta11-only publication;fresh independent public
verification on both cores. Exact results are recorded in the permanent handoff and
publication receipt, not inferred from this checklist.

[Native guide](DIAGNOSTICS.md) · [HACS procedure](HACS_DISTRIBUTION.md) ·
[Simulation proof](receipts/v0.1.0-beta.11-simulation.json) ·
[Permanent handoff](DEVELOPMENT_STATUS.md).

No production HA, Node-RED, Tesla/Easee or charging commands are part of this acceptance.
No stable release or main merge. Owner acceptance remains separate after publication.
