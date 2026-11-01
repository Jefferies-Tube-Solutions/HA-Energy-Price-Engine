# Beta.12 owner acceptance checklist

Issue #17: saved VAT presentation; all approved beta.11 Diagnostics preserved.
Software evidence is disposable HA, not owner physical acceptance. Boxes stay unchecked.

- [ ] Back up development HA; install **v0.1.0-beta.12** through HACS beta versions.
- [ ] Restart HA and reload app/browser/card resources. Device info shows beta.12.
- [ ] Keep beta.10/11 site IDs, history, dated overrides and CM mappings; no reset.
- [ ] Initial setup shows **Including VAT?**, default Yes, in the normal Site step.
- [ ] Existing beta.11 sites default Yes; normal Configure offers the same saved choice.
- [ ] Native device Diagnostic shows **Including VAT — Yes/No** (Ja/Nej in Danish).
- [ ] All 15 Diagnostic rows are present on a four-band site, with enabled new row.
- [ ] Every monetary Diagnostic defaults to øre/kWh with two decimals.
- [ ] Yes uses actual VAT-inclusive spot, applied DSO, four grid rates, Energinet,
      supplier markup, tax and verified final from the selected verified record/cache.
- [ ] No uses actual ex-VAT amounts and the sum of unrounded ex-VAT components for final.
- [ ] VAT amount remains visible and unchanged; it is informational in No mode.
- [ ] Real grid periods/rates, current/next labels and automatic selection remain correct.
- [ ] Missing values stay Unknown, independently verified grid ranges remain visible.
- [ ] Toggle, close/reopen and restart preserve the saved choice without changing history.
- [ ] Nine primary sensor values retain their fixed labeled VAT basis and Recorder meaning.
- [ ] Card final/components/statistics/grid follow the choice; raw spot stays labeled ex VAT.
- [ ] Actual contracts, source availability, Pi performance and mobile behavior are acceptable.

[Setup](HACS_DISTRIBUTION.md) · [Native Diagnostics/screenshots](DIAGNOSTICS.md) ·
[Permanent handoff](DEVELOPMENT_STATUS.md). CM API2 remains canonical including VAT.
No production/Node-RED/charging commands or stable/main merge are part of acceptance.
