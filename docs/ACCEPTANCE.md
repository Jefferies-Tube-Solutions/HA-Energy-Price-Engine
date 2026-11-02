# v1.0.0 owner verification checklist

Software gates are recorded separately from the owner's actual installation acceptance.

Completed isolated software gates ([receipt](receipts/v1.0.0.json)):

- [x] PR19 ordinary review/merge and all12 source CI checks.
- [x] All seven CI checks on exact main19af5bf4412c5f3cc3b3e07c6d756da372f81ba6.
- [x] Native fresh setup, actual public beta.12 upgrade and restart persistence.
- [x] Stable Device info, all Diagnostics, mixed VAT and retained IDs/history.
- [x] Immutable tag, public non-prerelease/latest, both ZIPs, checksums and provenance.
- [x] Anonymous downloads and independent source/SHA256 verification.
- [x] Actual pinned HACS stable discovery/install/update with beta visibility off.
- [x] Newer-main SHA rejection, future-beta isolation and both native ZIP layouts.

Owner installation acceptance remains separate:

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
