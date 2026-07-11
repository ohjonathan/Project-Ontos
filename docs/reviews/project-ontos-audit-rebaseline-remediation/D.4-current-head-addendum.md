---
id: project-ontos-audit-rebaseline-remediation-D.4-current-head-addendum
deliverable_id: project-ontos-audit-rebaseline-remediation
role: fix-author
family: codex
phase: D.4
status: completed
depends_on:
  - project-ontos-audit-rebaseline-remediation-D.4-fix-summary
  - project-ontos-audit-rebaseline-remediation-pr-161-fable-feedback-disposition
---

# D.4 current-head addendum — PR #161

This append-only addendum advances the D.5 verification target from I3
`859ecf7` to PR head `388845c`. It does not rewrite the historical D.4 summary,
the I2/I3 verifier attempts, or any receipt. The target contains the PR-feedback
fix series `cdf904f..388845c`; GitHub Actions run `29155957357` is green in all
seven jobs at that exact head.

## Current-head fix table

| ID | Current-head behavior | Focused evidence to re-run at D.5 |
|---|---|---|
| PR161-IDLESS | Frontmatter patches preserve filename-derived IDs and validate only explicit or newly added IDs. | `tests/core/test_frontmatter_edit_pipeline.py` |
| PR161-UMASK | New staged files use `0o666 & ~umask`; existing destination modes remain preserved. | `tests/test_session_context.py` |
| PR161-FENCE | The canonical splitter accepts only unindented `---` fences with optional trailing spaces or tabs. | `tests/core/test_frontmatter_edit_pipeline.py` |
| PR161-COVERAGE | Local coverage artifacts are ignored, CI coverage floors block, registry validation runs in CI, and Codecov downloads stay outside the checkout. | `tests/test_ci_release_workflows.py`, `tests/test_test_isolation.py` |
| PR161-UTF8 | Direct decoding remains strict while batch loading reports invalid UTF-8 as `parse_error`; the comments describe detection versus decoding accurately. | `tests/test_document_loading_contract_a1.py` |
| PR161-PARITY | CLI help parity normalizes only interpreter-controlled rendering and context-map alias parity ignores only declared volatile timestamps. | `tests/commands/test_query_parity.py`, `tests/commands/test_verify_parity.py`, `tests/commands/test_scaffold_parity.py`, `tests/mcp/test_context_map.py` |

## Verification boundary

The current head is functionally green, but this addendum does not resolve
`D4-INFRA-1` or `D5-INFRA-2`. Fresh D.5 family artifacts and receipts must bind
their own work to `388845c`. Strict certification remains forbidden if the
pinned framework's own schema and lifecycle verifier disagree.
