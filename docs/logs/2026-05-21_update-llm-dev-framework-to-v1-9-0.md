---
id: log_20260521_update-llm-dev-framework-to-v1-9-0
type: log
status: active
event_type: chore
source: codex
branch: main
created: 2026-05-21
concepts: [devops, workflow, testing, docs]
---

# Update llm-dev framework to v1.9.0

## Summary

Updated the repo-local llm-dev-framework adoption from `v1.8.0` to the
new latest GitHub release tag, `v1.9.0`.

## Goal

Pull the newly published llm-dev-framework update from GitHub and keep the
Project-Ontos adopter wrapper aligned with the checked-out framework.

## Changes Made

- Synced the `.llm-dev/framework` submodule remote from `.gitmodules`.
- Ran `scripts/llm-dev update --to latest`, which resolved `v1.9.0`.
- Updated `.llm-dev/config.yaml` so `framework_ref` is `v1.9.0`.
- Refreshed `scripts/llm-dev` from the v1.9.0 framework copy via
  `install-adopter.sh --from .llm-dev/framework`.

## Key Decisions

- Used the repo-local wrapper to resolve the framework path and latest tag.
- Refreshed the copied wrapper after pulling so adopter commands stay in sync
  with framework changes.

## Alternatives Considered

- Updating only the submodule was rejected because the framework installer
  reported wrapper content drift, meaning the adopter wrapper would have lagged
  behind v1.9.0 behavior.

## Impacts

- The adopter now points at llm-dev-framework `v1.9.0`.
- The framework submodule now references commit `6e6c40878f0c44f41ff34d9ac8d818ac1cff69d5`.
- `Ontos_Context_Map.md` and `AGENTS.md` were regenerated through Ontos after
  adding this session log.

## Testing

- `ontos activate` completed with `usable_with_warnings`.
- `scripts/llm-dev doctor` passed with `framework_ref: v1.9.0`.
- `scripts/llm-dev verify manifests/project-ontos-v44-agentic-activation-resilience.yaml`
  passed all 4 manifest-conformance checks.
- `scripts/llm-dev verify-lifecycle manifests/project-ontos-v44-agentic-activation-resilience.yaml`
  still fails because the existing manifest is `review_pending` and has no
  lifecycle receipt inventory at:
  `manifests/review-board/project-ontos-v44-agentic-activation-resilience-lifecycle-receipts.yaml`.
