# v1.0.0 owner verification checklist

Software gates are recorded separately from the owner's actual installation acceptance.

- [ ] Back up Home Assistant, leave HACS beta visibility off, install/update v1.0.0.
- [ ] Device info and HACS show stable1.0.0; no short-SHA update after refresh/restart.
- [ ] Keep beta.12 sites/IDs, private rates, overrides, VAT choice and SQLite history.
- [ ] Fresh setup uses official Nord Pool, confirmed grid/supplier and saved VAT choice.
- [ ] All native Diagnostics remain visible, including actual grid ranges and supplier.
- [ ] Yes/No values reconcile; actual VAT amount stays unchanged; primary basis is labeled.
- [ ] Current/next readiness, today/tomorrow windows and negative prices are correct.
- [ ] Restart preserves settings and history. Missing/stale/expired rates remain unavailable.
- [ ] EN/DA desktop/mobile and the bundled card work after reloading cached resources.
- [ ] Actual private contract, public-source availability and hardware performance are acceptable.

No remote production changes or charging-controller cutover are part of verification.
[Installation](HACS_DISTRIBUTION.md) · [Limits](COMPATIBILITY.md) · [API2](API.md).
