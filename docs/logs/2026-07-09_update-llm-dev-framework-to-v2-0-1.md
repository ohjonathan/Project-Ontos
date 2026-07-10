---
id: log_20260709_update-llm-dev-framework-to-v2-0-1
type: log
status: active
event_type: chore
source: cli
branch: codex/update-llm-dev-framework-v2
created: 2026-07-09
concepts: [devops, workflow, testing, docs]
---

# Update llm-dev-framework to v2.0.1

## Goal

Pull the latest `llm-dev-framework` release after v2.0.1 was published and
update the existing framework-upgrade PR branch.

## Key Decisions

- Used `scripts/llm-dev update --to latest`, which resolved the remote latest
  tag to `v2.0.1`.
- Kept the existing branch `codex/update-llm-dev-framework-v2` and pushed a
  follow-up commit (`a423c34`) to draft PR #159 instead of opening another PR.
- Updated PR #159's title and body from v2.0.0 to v2.0.1.
- Staged only `.llm-dev/config.yaml`, `.llm-dev/framework`, and
  `scripts/llm-dev`; unrelated Ontos/audit worktree files were left out.

## Alternatives Considered

- Creating a fresh PR was unnecessary because the current checkout was already
  the active framework-upgrade PR branch.
- Amending the prior v2.0.0 commit would have hidden the already-pushed
  history; a follow-up v2.0.1 commit keeps the update explicit.

## Impacts

- Project-Ontos now points at `llm-dev-framework` `v2.0.1` locally and in PR
  #159.
- The refreshed wrapper exposes the new `record-fallback-receipt` command in
  addition to the v2.0.0 command surface.
- Existing manifest compatibility and strict-P3 evidence semantics are
  unchanged by this patch release.

## Testing

- `python3 -m ontos activate` returned `usable_with_warnings`.
- `scripts/llm-dev doctor` passed on `v2.0.1`.
- `bash .llm-dev/framework/scripts/verify-route-profile.sh .llm-dev/routes.yaml`
  passed.
- `scripts/llm-dev update --to latest` was rerun after the wrapper refresh and
  completed cleanly.
