---
id: project_ontos_audit_tail_config_provenance_spec
type: spec
status: active
depends_on:
  - project_ontos_audit_remediation_release_line_tracker
  - project-ontos-fable-repo-audit-2026-07
---

# Audit-tail PR D — config hygiene, provenance, and maintain self-heal

## Goal

Close the v5.0.1 code tail from fresh
`origin/main@82078066aabe90d8b7b1e57696276833bfd67019`. Resolve
`D4a-config-1`, `D4a-config-3`, `D4a-config-5`, and
`R2-testpypi-provenance-1` without changing a public import or command
contract. Retire the inherited maintain exit-5 operational tail. Tags,
publication, merge, and release timing remain maintainer-owned.

## Configuration contracts

- First-run portfolio configuration is neutral: no scan roots, exclusions, or
  registry are inferred from the developer's machine, the current directory,
  or an XDG directory.
- `ensure_portfolio_config()` remains create-if-absent and never clobbers an
  existing file. Writable portfolio mode refuses before creating its database
  until a scan root or registry is configured. Read-only mode may open an
  existing database without creating configuration or SQLite sidecars.
- `verify --portfolio` requires an explicit registry because verification is
  a comparison against that external authority.
- Omitted `consolidate --count` resolves from
  `workflow.log_retention_count`; an explicit count wins and zero remains a
  usage error. Contributor mode uses the schema default rather than loading
  the repository's `.ontos.toml`; age selection is independent.
- The bundle defaults 8,000 tokens, 20 logs, and 30 days have one named source
  each. Unrelated result caps, map budgets, and workflow retention values are
  not combined with them.

## Release provenance contract

- One immutable release bundle contains the wheel, sdist, and a manifest
  binding the tag, exact tag-derived version, source commit, artifact kind, filename,
  size, embedded package metadata, and SHA-256 digest.
- TestPyPI publication refuses an occupied version. Verification compares the
  exact remote wheel and sdist hashes with the CI bundle and installs only
  `ontos==<tag-version>` from TestPyPI with the CI wheel hash required. PyPI is
  not a fallback.
- The installed wheel is smoke-tested outside the checkout and both
  `ontos.__version__` and installed distribution metadata must equal the tag.
  Production publication depends on this verification and revalidates the
  same release bundle.

## Consolidation self-heal contract

- A missing decision history is initialized with one canonical six-column
  `## History Ledger` table.
- A recognized generated/narrative decision history preserves all existing
  bytes as a prefix and receives that section once. Recognition requires the
  Decision History heading plus the generated marker or `id: decision_history`.
- An arbitrary document or malformed/ambiguous existing ledger fails closed,
  leaving logs and history unchanged. An existing archive-path row is
  idempotent.
- The tracked scaffold template uses the same canonical table. The dead
  narrative generator and broader two-writer architecture remain a v5.x
  follow-up. Promote-scan noise is deliberately excluded because it changes
  the PR C document-count surface.

## Acceptance

- Focused configuration, consolidation, portfolio, release-script, and doctor
  regressions pass; the doctor clean-path tripwire remains exactly 12 checks.
- The full test suite, `git diff --check`, Ontos activation/doctor/map/link
  validation, llm-dev manifest verification, wheel/sdist inspection, and a
  non-editable clean-install smoke test pass before publication of the draft.
- The release-line ledger records four implemented findings and the separate
  maintain tail without claiming merge or release. The sole remaining audit
  finding is the v6 removal `D5b-dead-code-3`.
