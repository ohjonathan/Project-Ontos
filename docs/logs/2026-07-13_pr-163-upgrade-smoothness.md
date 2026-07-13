---
id: log_20260713_pr-163-upgrade-smoothness
type: log
status: active
event_type: fix
source: codex
branch: codex/ontos-v5.0.0
created: '2026-07-13'
concepts: [release, cli, hardening, testing]
depends_on: [project-ontos-v5-0-0-spec]
---

# PR 163 upgrade smoothness

## Goal

Keep the Ontos 4.7.1 to 5.0.0 upgrade operationally smooth by making the
session-start `activate` command and the diagnostic `doctor` command return
zero for warning-only outcomes, without hiding warnings or changing the
`link-check` warning contract.

## Key Decisions

- Normalized warning-only results to exit `0` only at the public `doctor`
  command boundaries. The private diagnostic runner keeps its internal warning
  classification so `ontos maintain health_check` does not silently change
  semantics.
- Kept `result.status: warnings` and detailed `result.diagnostics` in JSON,
  while deriving `result.exit_category: clean` from the public zero exit code.
- Left validation findings, usage failures, and internal failures at exits `1`,
  `2`, and `5`, respectively.
- Left `link-check` unchanged: orphan-only findings continue to exit `3`.
- Kept lifecycle evidence isolated on
  `lifecycle-evidence/project-ontos-v5-0-0`; this product-only fix does not
  re-adjudicate D.6 or alter release governance.

## Alternatives Considered

- Changing the shared exit-code taxonomy so all warnings map to zero: rejected
  because the maintainer decision is limited to `activate` and `doctor`, and
  `link-check` intentionally retains exit `3` for orphans.
- Changing the private doctor diagnostic runner to return zero: rejected
  because maintenance orchestration consumes that internal classification and
  would lose its warning-state signal.
- Adding new strict options: rejected because neither command currently exposes
  one, and the existing strict behavior on other commands is outside scope.

## Impacts

- Agents and CI may continue gating session startup on a zero `activate` exit
  when a project is usable with warnings.
- Automation that needs to detect `activate` or `doctor` warnings must inspect
  `result.status` or `result.diagnostics`, not the process exit code.
- Existing 4.x data and `.ontos.toml` configurations continue to load in place;
  no migration command is required.
- The v5 migration guide now records the command-specific warning behavior,
  JSON schema changes, MCP graph-stat shape, and unaffected Git-hook path.

## Root Cause

The initial v5 exit taxonomy applied exit `3` uniformly to warning-only
commands. That made routine `activate` and `doctor` invocations regress from
exit `0` to exit `3` on otherwise usable projects, even though warnings were
already available in both human output and structured diagnostics.

## Fix Applied

Updated the `activate` and public `doctor` command boundaries to return exit
`0` for warning-only states while retaining warning status, counts, records,
and human messages. Added command and envelope regressions for warning, clean,
usage-failure, and link-check-orphan behavior, and expanded the v5 migration
guide with an explicit 4.x upgrade section.

## Testing

- Focused command, contract, maintenance, and link-diagnostic suites:
  `202 passed`.
- Full supported Python 3.12 suite: `1,556 passed` with one pre-existing
  deprecation warning.
- `pre-commit run --all-files`: Ontos graph validation and auto-consolidation
  passed.
- `python -m ontos link-check --no-orphans --quiet`: passed.
- `git diff --check`: passed.
