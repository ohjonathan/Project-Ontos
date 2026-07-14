---
id: project_ontos_audit_tail_consistency_tracker
type: tracker
status: active
depends_on:
  - project_ontos_audit_remediation_release_line_tracker
  - project_ontos_audit_tail_consistency_spec
---

# Audit-tail PR C — consistency tracker

Baseline: `origin/main@f2ed48d8b935a486a1d09778efa345910400257b`, the
independently approved merge of PR #168. This is a v5.0.1 bug-fix slice;
release actions remain maintainer-owned.

| Phase | Owner | Status | Artifact | Evidence | Timestamp |
|---|---|---|---|---|---|
| 0 — setup | Codex | complete | isolated `codex/audit-tail-consistency` worktree | Ontos activation clean; `scripts/llm-dev doctor` passed | 2026-07-13 |
| A — specification | Codex | complete | `docs/specs/project-ontos-audit-tail-consistency-spec.md` | Four count contracts, clean-path direction, and deterministic WAL contract recorded | 2026-07-13 |
| B.1/B.2 — design review | external families | pending | `docs/reviews/project-ontos-audit-tail-consistency/` | Strict lifecycle evidence awaits draft review | — |
| C — implementation | Codex | complete | shared validation, scan scope, link diagnostics, SQLite lifecycle, and tests | 229 focused and 1,600 full-suite tests passed; forward/reverse/isolated WAL orders repeatably green | 2026-07-13 |
| D — verification | external families | pending | `docs/reviews/project-ontos-audit-tail-consistency/` | CI and independent verification pending | — |
| E — retrospective | Codex | pending | `docs/retros/project-ontos-audit-tail-consistency-retro.md` | Runs after final approval | — |

## Reproduced before/after counts

Controlled fixtures isolate one counted concept at a time. `N/A` means the
surface intentionally does not expose that diagnostic class.

| Finding / fixture | `map` | `activate` | `doctor` | `link-check` | `maintain` | MCP snapshot / map |
|---|---:|---:|---:|---:|---:|---:|
| `D1b-counts-1`, one unknown concept | 1 → 1 curation warning | 0 → 1 | 0 → 1 | N/A | N/A | 0 → 1 |
| `D1b-counts-2`, depth-8 chain with configured max 10 | 0 → 0 depth warnings | 0 → 0 | 0 → 0 | N/A | N/A | 3 → 0 |
| `D1b-counts-3`, two real docs plus configured map under `docs/` | 2 docs / 0 map-orphans → same | 2 / 0 → same | docs check 3 → 2; activation 2 / 0 → same | 3 docs / 1 map-orphan → 2 / 0 | 2 / 0 → same | 3 docs / 1 map-orphan → 2 / 0 |
| `D1b-counts-4`, one broken body wikilink | N/A | N/A | N/A | 1 → 1 broken ref, exit 1 | 0 / success → 1 / failure | N/A |

Query health, an additional consumer of the shared scanner, also changes from
3 documents / 1 generated-map orphan to 2 / 0 in the D1b-3 fixture.

## Finding status

- [x] `D1b-counts-1` — shared authoritative vocabulary across full validators.
- [x] `D1b-counts-2` — configured dependency depth reaches snapshot and MCP map.
- [x] `D1b-counts-3` — configured generated map centrally excluded.
- [x] `D1b-counts-4` — maintain and link-check both count body references.
- [x] Accepted PR B WAL/SHM flake — deterministic connection closure and
  sidecar-free teardown; operational tail only, outside 33-finding arithmetic.
- [x] Inherited activation no-op map-write tail — semantic writer prevents
  timestamp-only map churn; outside 33-finding arithmetic.

## Gate

Do not start PR D until this branch is merged and independently verified. Do
not change version metadata, tag, publish, close #148, or claim the v6 path
removal from this branch.
