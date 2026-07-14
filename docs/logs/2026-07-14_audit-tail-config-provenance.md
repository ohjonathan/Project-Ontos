---
id: log_20260714_audit-tail-config-provenance
type: log
status: active
event_type: fix
source: codex
branch: codex/audit-tail-config-provenance
created: '2026-07-14'
depends_on:
  - project_ontos_audit_tail_config_provenance_spec
  - project_ontos_audit_remediation_release_line_tracker
concepts: [config, workflow, devops]
impacts:
  - project_ontos_audit_tail_config_provenance_tracker
  - ontos_manual
---

# Audit tail config provenance

## Goal

Close the v5.0.1 patch-safe code tail from `main@8207806`: resolve the three
configuration findings and the TestPyPI provenance finding, then retire the
separate maintain decision-history exit-5 tail without starting the breaking
v6 path removal or performing release actions.

## Root Cause

- Portfolio defaults repeated a developer-specific directory/registry layout,
  and verification supplied the same hidden fallback.
- Direct consolidation fixed retention at 15 while configuration and maintain
  used 20.
- Context-bundle defaults were duplicated at four implementation sites each.
- The tag workflow did not prove that TestPyPI served the CI-built wheel.
- The generated narrative history and consolidation's required ledger table
  were incompatible, causing maintain to select logs and then move none.

## Key Decisions

- Generate an inert portfolio config and refuse writable database creation
  until discovery is configured; retain read-only access to an existing DB.
- Resolve omitted consolidate count from user workflow config, but use the
  schema default in contributor mode. Explicit count and age semantics remain.
- Bind one wheel and one sdist to an immutable manifest and require exact
  TestPyPI filenames, metadata, sizes, and hashes before production publish.
- Give OIDC only to publisher jobs and hash-lock the smoke dependencies.
- Self-heal only missing or positively recognized decision histories. Preserve
  existing bytes, including CRLF, and fail closed on malformed identities or
  ledgers.

## Alternatives Considered

- A cwd, home, or XDG portfolio default was rejected because it can silently
  index unrelated repositories.
- Keeping the CLI's hard-coded 15 or forcing contributor `.ontos.toml` was
  rejected because each would preserve sibling disagreement.
- `skip-existing`, a dual-index pip install, and version-only output checks
  were rejected because each permits stale or wrong artifact verification.
- Rewriting the narrative generator was deferred; it is a broader two-writer
  architecture change than the patch-safe self-heal.
- Promote-check scan-noise changes were excluded because they affect the PR C
  counted-document contract and require a separate reconciliation.

## Impacts

- Implements `D4a-config-1`, `D4a-config-3`, `D4a-config-5`, and
  `R2-testpypi-provenance-1` for review, advancing the program from 28/33 landed
  to 32/33 after verified merge.
- Retires the decision-history maintain tail outside the 33-finding arithmetic.
- Leaves all 11 deprecated path aliases importable in 5.0.1; their removal is
  still the sole original finding assigned to v6.0.0.
- Sets source/package metadata to 5.0.1 without tagging or publishing it.

## Testing

- Baseline reproductions pinned personal defaults, 15-versus-20 retention,
  maintain exit 5, and the unbound publication gate.
- 135 focused regressions passed before adversarial review; follow-up CRLF and
  blank-root regressions passed with the exact doctor 12-check tripwire.
- Complete suite: 1,631 passed.
- Ontos activation: 222 documents, zero load issues, zero errors, and zero
  warnings after vocabulary correction.
- Wheel/sdist build, immutable manifest create/verify, `twine check`, Linux
  dependency-hash download, and a non-editable outside-checkout wheel smoke
  test passed at version 5.0.1.
- All workflow shell blocks passed `bash -n`; llm-dev manifest conformance,
  `compileall`, and `git diff --check` passed.
