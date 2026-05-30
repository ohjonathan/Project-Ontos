---
id: log_20260525_update-llm-dev-framework-to-v1-10-1
type: log
status: active
event_type: chore
source: cli
branch: main
created: 2026-05-25
concepts: [devops, workflow, testing, docs]
---

# Update llm-dev framework to v1.10.1

## Summary

Updated the repo-local llm-dev-framework adoption from `v1.10.0` to the
new latest GitHub release tag, `v1.10.1`.

## Goal

Pull the newly published llm-dev-framework patch from GitHub and keep the
Project-Ontos adopter wrapper aligned with the checked-out framework.

## Changes Made

- Ran `scripts/llm-dev update --to latest`, which resolved `v1.10.1`.
- Updated `.llm-dev/config.yaml` so `framework_ref` is `v1.10.1`.
- Updated the `.llm-dev/framework` submodule pointer to framework commit
  `7112119f4d6be26f9ca3f8553f97ac63126dee3c`.
- Refreshed `scripts/llm-dev` from the v1.10.1 framework copy via
  `install-adopter.sh --from .llm-dev/framework` after detecting wrapper
  drift from the previous adopter wrapper.
- Refreshed the managed llm-dev-framework block in `AGENTS.md` through the
  adopter installer.

## Key Decisions

- Used the repo-local `scripts/llm-dev` wrapper so `.llm-dev/config.yaml`
  remained the source of truth for framework location and ref resolution.
- Used the checked-out v1.10.1 framework installer to refresh the copied
  wrapper because the v1.10.0 adopter wrapper did not yet contain the new
  self-refresh logic added in v1.10.1.

## Alternatives Considered

- Leaving the wrapper at the v1.10.0 surface was rejected because v1.10.1
  adds wrapper-drift detection, update-time wrapper refresh, and adopter
  operations helpers.
- Updating only `.llm-dev/config.yaml` and the submodule pointer was rejected
  because `scripts/llm-dev doctor` in v1.10.1 expects the adopter wrapper to
  match the framework copy.

## Impacts

- The adopter now points at llm-dev-framework `v1.10.1`.
- The local wrapper now exposes v1.10.1 commands including `rebind-artifact`,
  `post-merge`, `review-chain report`, and `verify-live-docs`.
- Future `scripts/llm-dev update --to latest` runs should refresh wrapper
  drift automatically.

## Testing

- `python3 -m ontos activate` completed with usable context after the direct
  `ontos activate` command reported `not_usable`.
- Confirmed the GitHub release page marks `v1.10.1` as the latest release.
- `scripts/llm-dev doctor` passed with `framework_ref: v1.10.1` and
  `scripts/llm-dev` matching the framework copy.
- `scripts/llm-dev verify manifests/project-ontos-issue-119-cli-activate-json-warning-metadata.yaml`
  passed all 4 manifest-conformance checks.
- `scripts/llm-dev verify manifests/project-ontos-github-issues-115-117.yaml`
  passed all 4 manifest-conformance checks.
- `scripts/llm-dev verify manifests/project-ontos-v44-agentic-activation-resilience.yaml`
  passed all 4 manifest-conformance checks.
- `cmp -s scripts/llm-dev .llm-dev/framework/scripts/llm-dev` passed after
  refreshing the wrapper.
- `git diff --check` passed.
