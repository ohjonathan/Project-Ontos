# project-ontos-github-issues-115-117 — Tracker

| Phase | Owner | Status | Artifact | Evidence | Timestamp |
|-------|-------|--------|----------|----------|-----------|
| 0     | orchestrator | scope-locked | manifests/project-ontos-github-issues-115-117.yaml | gh issue list (#115/#116/#117) + scripts/llm-dev verify PASS + verify-schema/verify-tokens green + scripts/llm-dev doctor PASS (codex/claude/gemini present) | 2026-05-22 |
| -A.triage | codex (orchestrator-authored) | completed | docs/reviews/.../pre-a-triage-report.md + pre-a-triage-verdict.md | All three issues classified In-Scope; verify-pre-a.sh PASS | 2026-05-22 |
| A     | codex (orchestrator-authored) | completed | docs/specs/project-ontos-github-issues-115-117-spec.md | G-cardinality-2 grep gate passes with 9 #11[567] mentions | 2026-05-22 |
| B.1   | claude-opus / claude-sonnet / gemini | **pending-dispatch (strict-P3 receipts required)** | docs/reviews/.../B.1-<family>-<role>.md | Awaiting user authorization for 3 real CLI dispatches | — |
| B.3   | claude-opus | pending-dispatch | docs/reviews/.../B.3-verdict.md | Depends on B.1 receipts | — |
| C     | codex (orchestrator-authored) | completed | 7 commits: #115 schema fix + 6 #117 sub-tracks + #116 docs | 1320/1320 tests pass; targeted MCP + core + commands suites green | 2026-05-22 |
| D.1   | claude-sonnet | pending-dispatch |          | Post-B.3 implementation review |  |
| D.2   | claude-opus / claude-sonnet / gemini | **pending-dispatch (strict-P3 receipts required)** | docs/reviews/.../D.2-<family>-<role>.md | Awaiting user authorization for 3 real CLI dispatches | — |
| D.3   | claude-opus | pending-dispatch | docs/reviews/.../D.3-verdict.md | Depends on D.2 receipts | — |
| D.4   | codex | pending-dispatch | docs/reviews/.../D.4-fix-summary.md | Conditional on D.3 blockers | — |
| D.5   | claude-opus / claude-sonnet / gemini | **pending-dispatch (strict-P3 receipts required)** | docs/reviews/.../D.5-<family>-verifier.md | Awaiting user authorization for 3 real CLI dispatches | — |
| D.6   | claude-sonnet | pending-dispatch | docs/reviews/.../final-approval.md | strict-P3 verify-lifecycle + verify-d6-gate + full pytest | — |
| E     | gemini | pending-dispatch | docs/retros/project-ontos-github-issues-115-117-retro.md | Post-D.6 retrospective | — |

## Phase C summary (committed)

| Issue | Track | Commit | Tests |
|-------|-------|--------|-------|
| #115 | MCP schema-safe pre-activate warning routing | `fix(mcp): route pre-activate warning into get_context_bundle.warnings list (#115)` | 248/248 MCP suite |
| #117 | depends_on path resolution fallback | `fix(graph): add depends_on path-resolution fallback for workspace files (#117)` | 6 new + 473/473 |
| #117 | Warning enrichment (rule_id/document_id/file_path) | `feat(mcp): enrich validation warnings with rule_id/document_id/file_path (#117)` | 4 new + 461/461 |
| #117 | Type/status widening for lifecycle artifacts | `feat(types): widen DocumentType/Status for lifecycle artifacts (#117)` | 4 new + 1313/1313 |
| #117 | bare_id_token requires explicit wikilink sigil | `fix(link-check): tighten body.bare_id_token to require explicit wikilink sigil (#117)` | 4 new + 1317/1317 |
| #117 | README/template skip + doctor severity alignment | `feat(loader,doctor): README/template skip + activation severity alignment (#117)` | 3 new + 1320/1320 |
| #116 | MCP host reload documentation | `docs(mcp): document MCP host reload requirement after pipx upgrade (#116)` | docs-only |

## Halt point

Phase C lands all substantive code + docs work for #115/#116/#117. Strict-P3 verify-lifecycle requires receipts from B.1 ×3, D.2 ×3, and D.5 ×3 — 9 real subprocess CLI dispatches (claude-opus, claude-sonnet, gemini) totaling hours of wall-clock and a few tens of dollars in real LLM API billing across three providers. The orchestrator halts here for the operator to authorize the dispatches before continuing.
