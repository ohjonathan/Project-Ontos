---
id: log_20260525_update-llm-dev-framework-to-v1-10-0
type: log
status: active
event_type: chore
source: cli
branch: main
created: 2026-05-25
concepts: [devops, workflow, testing, docs]
---

# Update llm-dev framework to v1.10.0

## Summary

Updated the repo-local llm-dev-framework adoption from `v1.9.0` to the
new latest GitHub release tag, `v1.10.0`.

## Goal

Pull the newly published llm-dev-framework update from GitHub and keep the
Project-Ontos adopter wrapper aligned with the checked-out framework.

## Changes Made

- Ran `scripts/llm-dev update --to latest`, which resolved `v1.10.0`.
- Updated `.llm-dev/config.yaml` so `framework_ref` is `v1.10.0`.
- Updated the `.llm-dev/framework` submodule pointer to framework commit
  `f0a725a552d50d36ab5e50c84d0bfeccf35628d0`.
- Refreshed `scripts/llm-dev` from the v1.10.0 framework copy via
  `install-adopter.sh --from .llm-dev/framework`; this added the
  `generate-overlays` command surface.

## Key Decisions

- Used the repo-local `scripts/llm-dev` wrapper so `.llm-dev/config.yaml`
  remained the source of truth for framework location and ref resolution.
- Refreshed the copied wrapper after detecting drift from the v1.10.0
  framework copy.

## Alternatives Considered

- Updating only the submodule and config was rejected because `scripts/llm-dev`
  differed from the v1.10.0 framework wrapper.

## Impacts

- The adopter now points at llm-dev-framework `v1.10.0`.
- The local wrapper now exposes the new v1.10.0 `generate-overlays` command.
- Existing Project-Ontos manifests continue to pass manifest-conformance under
  the v1.10.0 schema and checks.

## Testing

- `python3 -m ontos activate` completed with usable context after the direct
  `ontos activate` command reported `not_usable`.
- `scripts/llm-dev doctor` passed with `framework_ref: v1.10.0`.
- `scripts/llm-dev verify manifests/project-ontos-issue-119-cli-activate-json-warning-metadata.yaml`
  passed all 4 manifest-conformance checks.
- `scripts/llm-dev verify manifests/project-ontos-github-issues-115-117.yaml`
  passed all 4 manifest-conformance checks.
- `scripts/llm-dev verify manifests/project-ontos-v44-agentic-activation-resilience.yaml`
  passed all 4 manifest-conformance checks.
- `cmp -s scripts/llm-dev .llm-dev/framework/scripts/llm-dev` passed after
  refreshing the wrapper.
