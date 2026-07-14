---
id: project_ontos_audit_tail_config_provenance_tracker
type: tracker
status: active
depends_on:
  - project_ontos_audit_remediation_release_line_tracker
  - project_ontos_audit_tail_config_provenance_spec
---

# Audit-tail PR D — config and provenance tracker

Baseline: `origin/main@82078066aabe90d8b7b1e57696276833bfd67019`, the
independently approved merge of PR #169. This patch closes the v5.0.1 code
tail; release actions remain maintainer-owned.

| Phase | Owner | Status | Artifact | Evidence | Timestamp |
|---|---|---|---|---|---|
| 0 — setup | Codex | complete | isolated `codex/audit-tail-config-provenance` worktree | Ontos activation clean; `scripts/llm-dev doctor` passed; four findings and maintain exit 5 reproduced | 2026-07-14 |
| A — specification | Codex | complete | `docs/specs/project-ontos-audit-tail-config-provenance-spec.md` | Neutral configuration, retention, provenance, and self-heal contracts recorded | 2026-07-14 |
| B.1/B.2 — design review | external families | pending | `docs/reviews/project-ontos-audit-tail-config-provenance/` | Strict lifecycle evidence awaits draft review | — |
| C — implementation | Codex | complete | config, consolidation, release workflow, documentation, and regressions | 1,631 full-suite tests passed; activation/map 223 docs and 0/0 diagnostics; exact doctor tripwire, link-check, package build, manifest, twine, clean-install, and llm-dev gates passed | 2026-07-14 |
| D — verification | external families | pending | `docs/reviews/project-ontos-audit-tail-config-provenance/` | CI and independent verification pending | — |
| E — retrospective | Codex | pending | `docs/retros/project-ontos-audit-tail-config-provenance-retro.md` | Runs after final approval | — |

## Baseline reproductions

| Surface | `main@8207806` | Required result |
|---|---|---|
| First portfolio use | Writes `~/Dev` and `.dev-hub` paths; `verify --portfolio` silently supplies the same private registry fallback | Writes an inert config; writable discovery and verification refuse until explicitly configured |
| `consolidate` without `--count` | Hard-coded CLI retention 15 overrides configured/default retention 20 | User mode honors configured retention; contributor mode uses `WorkflowConfig()` default 20 |
| Bundle defaults | 8,000 / 20 / 30 repeated at four implementation sites apiece | Three named constants, with byte-identical generated TOML numerics |
| TestPyPI verification | Unpinned dual-index install; version only printed; no CI-wheel hash comparison | Exact tagged artifact names, metadata, sizes, and hashes verified before clean external smoke test |
| Maintain consolidation | Generated narrative lacks `## History Ledger`; eight selected logs fail with exit 5 and zero moves | Recognized history self-heals once; malformed arbitrary content still fails closed |

## Finding status

- [x] `D4a-config-1` — neutral portfolio defaults and explicit verification
  authority implemented; review/merge pending.
- [x] `D4a-config-3` — omitted consolidate count resolves from workflow
  retention (normally 20); review/merge pending.
- [x] `D4a-config-5` — the three bundle defaults have named, single sources;
  review/merge pending.
- [x] `R2-testpypi-provenance-1` — the TestPyPI gate binds to the exact release
  bundle; review/merge pending.
- [x] Inherited maintain exit-5 tail — canonical History Ledger self-heal;
  operational tail only, outside the 33-finding arithmetic.

## Gate

After these four findings merge, 32 of 33 audit-tail findings are landed and
the v5.0.1 code tail is complete. Do not tag, upload, merge, close #148/#149,
or begin the v6 branch here. `D5b-dead-code-3` remains deferred to v6.0.0.
