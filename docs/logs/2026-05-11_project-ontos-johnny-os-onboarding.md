---
id: log_20260511_project-ontos-johnny-os-onboarding
type: log
status: active
event_type: chore
source: codex
branch: codex/project-ontos-johnny-os-onboarding
created: 2026-05-11
---

# project-ontos-johnny-os-onboarding

## Goal

Bring `https://github.com/ohjonathan/Project-Ontos` into the Johnny-OS
ecosystem as a separately managed workspace under `/Users/jonathanoh/workspaces`,
matching the Folio onboarding pattern without nesting the repository inside
`/Users/jonathanoh/johnny-os`.

## Summary

Project-Ontos was cloned to `/Users/jonathanoh/workspaces/Project-Ontos`,
activated with Ontos, synced with current generated agent/context files, and
given a `.johnny-os.yaml` manifest for Johnny-OS runtime registration.

The onboarding branch is `codex/project-ontos-johnny-os-onboarding`.

## Changes Made

- Added `.johnny-os.yaml` with workspace `project-ontos` and repo entity
  `project-ontos-repo`.
- Regenerated `Ontos_Context_Map.md` and synced `AGENTS.md` via
  `ontos map --sync-agents`.
- Bootstrapped a local editable Python environment at `.venv/` with
  `.[dev,mcp]` extras for Project-Ontos development and MCP smoke testing.
- Installed local pre-commit/pre-push hooks via the Project-Ontos venv.

## Testing

- `ontos map`: generated context map with 79 documents.
- `ontos map --sync-agents`: synced generated agent instructions.
- `ontos doctor`: 10 passed, 0 failed, 1 warning (`Non-Ontos hooks:
  pre-push, pre-commit` after installing pre-commit-managed hooks).
- Johnny-OS manifest loader against `.johnny-os.yaml`: 0 errors, 0 warnings.
- Johnny-OS reference adapter smoke via the Project-Ontos venv: returned
  `source=ontos`, `ontos_version=4.3.0`, 6 included documents.
- `.venv/bin/python -m pytest`: 1287 passed, 2 skipped, 2 warnings.

## Key Decisions

- Keep Project-Ontos outside the Johnny-OS repo at
  `/Users/jonathanoh/workspaces/Project-Ontos` to avoid nested-repo coupling.
- Classify the workspace as `kind: infra`, with the repo entity in
  `domain: infra`, because Ontos is part of the Johnny-OS knowledge/runtime
  substrate rather than a user-facing product.
- Use `maturity: usable` and `risk_tier: sandbox`: the package is usable and
  versioned, but this checkout is a local development workspace.

## Alternatives Considered

- Did not clone Project-Ontos under `/Users/jonathanoh/johnny-os`; the Folio
  pattern favors separate active workspaces.
- Did not treat the existing installed `ontos` CLI as sufficient; Johnny-OS
  can consume it, but that is not the same as having the upstream source repo
  available as a managed workspace.
- Did not register runtime assets or scheduled jobs yet; this onboarding only
  registers the source repo entity.

## Impacts

Project-Ontos is now ready for Johnny-OS-managed development from
`/Users/jonathanoh/workspaces/Project-Ontos`. Johnny-OS runtime state can point
to the repo path and retrieve Ontos context from it through the reference
adapter once the workspace registration is applied in Johnny-OS.
