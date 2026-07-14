---
id: project_ontos_audit_tail_consistency_spec
type: spec
status: active
depends_on:
  - project_ontos_audit_remediation_release_line_tracker
  - project-ontos-fable-repo-audit-2026-07
---

# Audit-tail PR C — count consistency and WAL isolation

## Goal

Resolve `D1b-counts-1/2/3/4` from fresh
`origin/main@f2ed48d8b935a486a1d09778efa345910400257b` without adding warnings to
the default clean repository path. Retire the portfolio SQLite WAL/SHM flake by
fixing deterministic connection ownership rather than accepting reruns. This
v5.0.1-track PR does not change package metadata or perform release actions.

## Count contracts

- Full-validation surfaces (`map`, CLI activation/doctor, snapshot-backed MCP
  activation, and MCP `context_map`) load one authoritative concept vocabulary.
  Reference-only surfaces (`link-check` and maintain `check_links`) do not add a
  new curation-warning contract.
- Every full graph validator receives configured `max_dependency_depth`
  verbatim, including zero.
- `collect_scoped_documents` excludes the configured generated context map by
  resolved path for every caller. Map retains an additional custom-output
  exclusion.
- `link-check` and maintain `check_links` both scan frontmatter and body links
  through `run_link_diagnostics`; the same broken body reference produces the
  same count and failing result.

The validation-on choice preserves default docs-scope activation at zero
warnings. It intentionally changes non-default library scope to match map:
the baseline reproduction loaded 792 documents and rose from 576 to 1,450
warnings because map already reported 874 vocabulary findings. This is an
explicit reconciliation, not a silent golden rebaseline.

## Cache and generated-artifact contracts

- MCP snapshot cache freshness includes both vocabulary candidate paths,
  including absent-to-present and precedence changes, so snapshot activation
  cannot disagree with a freshly generated MCP context map.
- Activation uses the existing semantic map writer. A timestamp-only second
  activation leaves the map bytes unchanged and reports `refreshed=false`.
- Invalid or unreadable vocabulary input disables membership validation while
  structural validation continues.

## Portfolio isolation contract

SQLite connection context managers commit or roll back but do not close.
`PortfolioIndex` therefore owns a managed connection context that closes on
normal, exception, and setup-failure paths. Portfolio tests create databases
under their own `tmp_path`, close tracked indexes in teardown, and fail if WAL
or SHM sidecars remain. Forward, reverse, and isolated orders run with
`ResourceWarning` promoted to failure.

## Acceptance

- The before/after matrix in the branch tracker is reproduced by focused tests.
- The doctor 12-check exit-code tripwire and clean activation health remain
  green with no default baseline reconfiguration.
- The original portfolio/read-only order, its reverse, and isolated target pass
  repeatedly with no resource warning or sidecar leak.
- Focused regressions, the complete test suite, `git diff --check`, Ontos
  activation/doctor/map/link validation, llm-dev manifest verification, and
  clean worktree checks pass before publication.
- `D1b-counts-1/2/3/4` may be checked as implemented in #148, while merge,
  release, tags, package publication, and closure remain maintainer-owned.
