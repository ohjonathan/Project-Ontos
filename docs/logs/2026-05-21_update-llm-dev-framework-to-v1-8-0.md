---
id: log_20260521_update-llm-dev-framework-to-v1-8-0
type: log
status: active
event_type: chore
source: codex
branch: main
created: 2026-05-21
---

# Update llm-dev framework to v1.8.0

## Summary

Updated the repo-local llm-dev-framework adoption from the prior detached
commit `9213fa4` to the latest GitHub release tag, `v1.8.0`.

## Goal

Pull the latest llm-dev-framework from GitHub and leave the Project-Ontos
adopter wiring usable through the repo-local `scripts/llm-dev` wrapper.

## Changes Made

- Synced the `.llm-dev/framework` submodule remote from `.gitmodules` so it
  points at `https://github.com/ohjonathan/llm-dev-framework.git`.
- Ran `scripts/llm-dev update --to latest`, which resolved and checked out
  `v1.8.0`.
- Updated `.llm-dev/config.yaml` so `framework_ref` is `v1.8.0`.
- Refreshed `scripts/llm-dev` from the v1.8.0 framework copy, adding
  wrapper support for `verify-lifecycle`, `verify-staging`, and
  `re-adjudication`.

## Key Decisions

- Used the repo-local wrapper and config-defined framework path instead of
  hard-coded paths.
- Refreshed the copied wrapper after updating the submodule so adopter-side
  commands match the v1.8.0 framework.

## Alternatives Considered

- Leaving `scripts/llm-dev` unchanged was rejected because v1.8.0 verifier
  output references wrapper commands that the old copied wrapper did not
  expose.
- Pulling the submodule via its existing remote was rejected after discovery
  that the checkout's `origin` was a stale local file URL; syncing from
  `.gitmodules` aligned it with the GitHub source requested by the user.

## Impacts

- The adopter now points at llm-dev-framework `v1.8.0`.
- The repo-local wrapper exposes newer framework checks, including lifecycle
  receipt verification and staging validation.
- `Ontos_Context_Map.md` was regenerated during mandatory Ontos activation.

## Testing

- `ontos activate` completed with `usable_with_warnings`.
- `scripts/llm-dev doctor` passed after the update.
- `scripts/llm-dev verify manifests/project-ontos-v44-agentic-activation-resilience.yaml`
  passed all 4 manifest-conformance checks.
- `scripts/llm-dev verify-lifecycle manifests/project-ontos-v44-agentic-activation-resilience.yaml`
  failed because the existing manifest is `review_pending` and has no lifecycle
  receipt inventory at the expected path:
  `manifests/review-board/project-ontos-v44-agentic-activation-resilience-lifecycle-receipts.yaml`.
