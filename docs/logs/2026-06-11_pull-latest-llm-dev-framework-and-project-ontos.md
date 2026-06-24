---
id: log_20260611_pull-latest-llm-dev-framework-and-project-ontos
type: log
status: active
event_type: chore
source: codex
branch: main
created: 2026-06-11
concepts: [devops, workflow, docs]
---

# pull latest llm-dev framework and Project-Ontos

## Summary

Pulled Project Ontos and refreshed its repo-local llm-dev framework adoption.
`origin/main` was already up to date; the llm-dev framework moved from
`v1.10.1` to `v1.10.2`, including the refreshed adopter wrapper.

## Goal

- Pull the latest Project Ontos state and llm-dev framework release from
  GitHub.

## Changes Made

- Activated Project Ontos with `python3 -m ontos activate` after the installed
  `ontos` entrypoint reported `not_usable`.
- Fetched and pulled `origin/main`; the repo was already up to date.
- Ran `scripts/llm-dev update --to latest`, moving `.llm-dev/framework` and
  `.llm-dev/config.yaml` from `v1.10.1` to `v1.10.2`.
- Refreshed `scripts/llm-dev` from the framework copy, adding the
  `repair-redispatch` command surface.
- Regenerated Ontos context and AGENTS files.

## Key Decisions

- Used the local module invocation for Ontos operations in this repo because it
  provided usable v4.7.0 activation.
- Re-ran the llm-dev update after the wrapper refreshed itself; the second run
  completed cleanly from the updated script.

## Alternatives Considered

- No manual wrapper edits were made; the wrapper was accepted only after
  `bash -n` and `scripts/llm-dev doctor` passed.

## Impacts

- Project Ontos now pins llm-dev framework `v1.10.2` at commit `3d6357c`.
- Generated Ontos files now include the post-merge archive log in the context
  map.

## Testing

- `git pull --ff-only origin main`
- `scripts/llm-dev update --to latest`
- `bash -n scripts/llm-dev`
- `scripts/llm-dev doctor`
- `python3 -m ontos doctor`
