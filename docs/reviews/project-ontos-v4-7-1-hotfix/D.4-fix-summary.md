---
id: project-ontos-v4-7-1-hotfix-D.4-fix-summary
deliverable_id: project-ontos-v4-7-1-hotfix
role: fix-author
family: codex
phase: D.4
canonical_verdict_consumed: docs/reviews/project-ontos-v4-7-1-hotfix/D.3-verdict.md
template_version: 1.1.0
status: completed
---

# Fix Summary — Project Ontos v4.7.1 Hotfix / D.4

## Per-blocker fix table

| Blocker ID | Fix | Regression test | File:line | Evidence |
|---|---|---|---|---|
| D1-FM-QUOTED-KEY-BOUNDARY | Index plain and quoted scalar keys by semantic value; reject quoted/plain duplicates; compare the complete output mapping with `parsed + updates` so unsupported key syntax fails closed instead of losing fields. | `tests/core/test_frontmatter_edit_pipeline.py::test_patch_recognizes_quoted_target_key_without_adding_a_duplicate`; `::test_patch_preserves_quoted_non_target_key_as_a_field_boundary`; `::test_patch_rejects_duplicate_target_across_plain_and_quoted_keys`; `::test_patch_fails_closed_if_an_unindexed_yaml_key_would_be_removed`; `tests/commands/test_promote_parity.py::test_promote_updates_quoted_curation_key_without_duplicate` | `ontos/core/frontmatter_edit.py:25`, `ontos/core/frontmatter_edit.py:91`, `ontos/core/frontmatter_edit.py:139`, `ontos/core/frontmatter_edit.py:301` | direct-run |
| D1-PORTFOLIO-WAL-SNAPSHOT | Route full and per-workspace rebuilds through one truncating checkpoint helper and fail if SQLite reports a busy/incomplete checkpoint. | `tests/mcp/test_portfolio.py::test_rebuild_workspace_publishes_snapshot_after_concurrent_reader` | `ontos/mcp/portfolio.py:125`, `ontos/mcp/portfolio.py:463`, `ontos/mcp/portfolio.py:465` | direct-run |

## Test-anchor additions

| Test file:line | Test name | Closes blocker | Satisfies spec anchor | Evidence |
|---|---|---|---|---|
| `tests/core/test_frontmatter_edit_pipeline.py:110` | `test_patch_recognizes_quoted_target_key_without_adding_a_duplicate` | D1-FM-QUOTED-KEY-BOUNDARY | §6 duplicate fields and serializer consumers | direct-run |
| `tests/core/test_frontmatter_edit_pipeline.py:124` | `test_patch_preserves_quoted_non_target_key_as_a_field_boundary` | D1-FM-QUOTED-KEY-BOUNDARY | §6 untouched-frontmatter preservation | direct-run |
| `tests/core/test_frontmatter_edit_pipeline.py:151` | `test_patch_rejects_duplicate_target_across_plain_and_quoted_keys` | D1-FM-QUOTED-KEY-BOUNDARY | §6 duplicate fields | direct-run |
| `tests/core/test_frontmatter_edit_pipeline.py:160` | `test_patch_fails_closed_if_an_unindexed_yaml_key_would_be_removed` | D1-FM-QUOTED-KEY-BOUNDARY | §6 format-preserving failure safety | direct-run |
| `tests/commands/test_promote_parity.py:101` | `test_promote_updates_quoted_curation_key_without_duplicate` | D1-FM-QUOTED-KEY-BOUNDARY | §6 mutation consumers | direct-run |
| `tests/mcp/test_portfolio.py:78` | `test_rebuild_workspace_publishes_snapshot_after_concurrent_reader` | D1-PORTFOLIO-WAL-SNAPSHOT | §6 read-only MCP SQLite behavior | direct-run |

## Regression Coverage (EH-15-A)

| Finding ID | Change class | Regression |
|---|---|---|
| D1-FM-QUOTED-KEY-BOUNDARY | code | tests/core/test_frontmatter_edit_pipeline.py, tests/commands/test_promote_parity.py |
| D1-PORTFOLIO-WAL-SNAPSHOT | code | tests/mcp/test_portfolio.py |

The fixtures exist and pass under the adopter's full pytest suite. The pinned
v2.0.1 `verify-fix-summary-regressions.sh` nevertheless cannot admit them:
Project Ontos has no adopter `scripts/verify-all.sh`, while the verifier roots
fixture registration at the framework checkout and its own registry. No
framework file or receipt was edited to conceal that EH-15-A defect.

## Should-fix disposition

| Finding ID | Disposition | Rationale |
|---|---|---|
| D1-YAML-ANCHOR-OVERREFUSAL | deferred | Fail-closed false refusal; no corruption. Parser-aware narrowing is separate work. |
| D1-IMMUTABLE-CONCURRENT-DB | deferred | Versioned immutable snapshots or a different locking/journal design are broader than the demonstrated WAL publication fix. |
| D2-LOG-DIR-RUNTIME-WARNING | deferred | Would change observable warning-envelope output in a patch release. |
| D2-UTF8-COPY-COMMAND | deferred | Existing path-specific recovery copy is sufficient for the hotfix. |
| D2-LOG-HELP-COLLISION | deferred | Would change observable help output; collision runtime copy is complete. |

## Spec deviations declared

None. The quoted-key fix enforces the existing format-preservation and
duplicate-rejection clauses. The portfolio fix enforces the existing
self-contained read-only snapshot clause. Adding the portfolio regression file
to manifest scope is a test-scope refinement required by D.3, not a product
contract change.

## Scope-lock proof

- Forbidden product paths remain byte-identical to `bf91b42`, including
  `ontos/ui/json_output.py`; tracked golden paths are unchanged.
- Package version assertion prints `4.7.1`.
- Command envelope assertion prints `3.4`, with the baseline eight-key set and
  no `result` member.
- `ontos/command_registry.py` remains absent.
- The D.4 implementation commit touches only manifest-allowed product and test
  paths after adding `tests/mcp/test_portfolio.py` to the declared test scope.

## Regression count

| Counter | Value |
|---|---|
| Preserved blockers CLOSED this round | 2 |
| Preserved blockers REMAINING | 0 |
| New test functions added | 6 |
| Lines changed | +207 / -16 |
| Commits in this D.4 round | 1 |
| New blockers INTRODUCED by this D.4 round | 0 observed before D.5 |

## Smoke checks after fix

| Check | Result | Evidence |
|---|---|---|
| Quoted-key, portfolio, read-only MCP, and promotion focused set | PASS | `82 passed in 1.01s` |
| Complete pytest suite | PASS | `1572 passed, 2 skipped, 2 warnings in 60.24s`; exact pre/post porcelain snapshots matched |
| Whitespace | PASS | `git diff --check` exit 0 |

## Smoke-check re-baseline

- [x] No fix in this summary changes the shape of an artifact that a
  manifest smoke-check regex consumes. The Phase C/D.5 commands remain valid.
- [ ] At least one fix changes an artifact shape consumed by a smoke-check regex.

## Commits

| SHA | Blocker addressed | Message |
|---|---|---|
| `a0062ae8b6e8413f15e64259ec16d1c927d55328` | D1-FM-QUOTED-KEY-BOUNDARY; D1-PORTFOLIO-WAL-SNAPSHOT | `fix: close final hotfix review gaps` |
