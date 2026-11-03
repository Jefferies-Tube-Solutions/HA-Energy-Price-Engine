# Development instructions

Read this file and `docs/DEVELOPMENT_STATUS.md` first in every session. Inspect
Git status, history and the active PR before editing. Resume existing work from
evidence; preserve user changes. Use this isolated checkout; do not create a Git
worktree unless the owner explicitly requests one.

## Ownership and safety

`ha_energy_price_engine` alone owns retrieval, verification, calculation, tariff
sources, price history and publishing. Consumers only read versioned final prices.
Reuse the tested EV Charge Manager PR #11/#12 implementation and retain attribution.
Do not duplicate tariff arithmetic in consumers. Unknown prices are never zero.
Never modify live Home Assistant, Node-RED, vehicle or charging controls. Tests use
mocked read services. No stable release, merge or production cutover without owner
approval. Do not infer future contracts, rates or authorization from test success.
EWII household markup is documented as 0.030 DKK/kWh excluding VAT only for June
through September 2026; it is not a default for another site or later period.

## Checkpoints

Work in small cohesive, tested incremental commits. After each meaningful milestone,
update the same `docs/DEVELOPMENT_STATUS.md` with branch, known commit, completed
and pending issue work, exact local tests and actual remote CI, decisions, blockers
and precise next steps. A document cannot include its own final commit hash; use
the checkpoint subject for that commit. Commit and push throughout development;
post meaningful progress updates to the active draft PR/issue when access permits.
Before stopping, leave a coherent committed checkpoint and an accurate handoff.
Never claim pending/unrun checks passed. Do not add competing handoff documents.

## v1.1 dashboard scope

Issue20 permits only optional native Lovelace resource registration and frontend
ore_kwh/dkk_kwh projection over the accepted stable engine. Load the collection before
listing; adopt only the exact local card path; preserve unrelated resources and YAML.
Registration failures must leave pricing operational. Do not change canonical API v2,
ledger schema/data, identities, site configuration or tariff calculations. The owner
authorizes a reviewable v1.1 beta PR and guarded prerelease after all checks, never
a main merge or stable/latest replacement. PAHA02-DEV visual acceptance remains owner
work. If ordinary GitHub PR creation is rejected, record its exact gate and comparison
URL without bypassing it; complete and preserve all independent validation first.
