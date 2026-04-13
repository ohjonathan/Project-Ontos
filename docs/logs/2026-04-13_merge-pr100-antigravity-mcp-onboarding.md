---
id: log_20260413_merge-pr100-antigravity-mcp-onboarding
type: log
status: active
event_type: fix
source: codex
branch: codex/issue-99-antigravity-mcp
created: 2026-04-13
---

# merge-pr100-antigravity-mcp-onboarding

## Goal

Archive the Antigravity native MCP onboarding work for issue #99, including
the D.4 PR #100 review fixes, and record the branch as merge-ready after the
requested doctor detection, install error handling, and `--write-enabled`
coverage updates landed.

## Root Cause

Ontos had fixed the stdio transport and `tools/list` schema issues in `v4.1.1`
and `v4.1.2`, but still had no native Antigravity onboarding path. Users could
run a healthy `ontos serve` while Antigravity remained tool-less because
`~/.gemini/antigravity/mcp_config.json` was never installed, validated, or
diagnosed from the CLI.

## Summary

Added Antigravity-native MCP client installation via `ontos mcp install
--client antigravity`, shared config validation and initialize probing, doctor
coverage for native config health, and docs for the native config path and
support model. After review, tightened Antigravity detection to the user-scoped
config directory, converted install write failures into exit-2 environment
errors, and added a CLI integration test for `--write-enabled`.

## Key Decisions

- Kept Antigravity as the only supported native installer target in this patch
  line rather than broadening the PR to Cursor, Claude Code, Codex, or other
  clients.
- Defaulted generated client config to read-only and kept `--write-enabled`
  explicit so MCP write tools remain opt-in.
- Tightened doctor detection to `~/.gemini/antigravity/` existence so users who
  only have the app installed are not forced through the probe path.
- Caught `OSError` only around config writes in `ontos mcp install`; existing
  read/load error handling remains owned by `load_antigravity_config`.
- Left the Antigravity initialize probe timeout behavior unchanged in this PR
  and treated probe configurability as a follow-up item.

## Alternatives Considered

- Expanding the same installer methodology to other MCP clients in PR #100:
  rejected for this pass to keep the issue #99 fix narrowly scoped and
  reviewable.
- Using app-bundle detection as the doctor trigger:
  rejected because it nudged users who never opted into Ontos integration and
  combined badly with the probe subprocess.
- Relying on chmod-based filesystem tests for install permission failures:
  rejected in favor of a deterministic monkeypatched `PermissionError`.

## Impacts

- PR #100 closes issue #99 with an explicit, diagnosable Antigravity-native MCP
  onboarding path.
- `ontos doctor` now only checks Antigravity native config after a user-scoped
  opt-in signal exists.
- `ontos mcp install` reports write-path environment failures clearly instead of
  surfacing them as internal CLI errors.
- A follow-up remains for probe timeout/configurability after opt-in.

## Testing

- `pytest tests/commands/test_doctor_phase4.py -v`
- `pytest tests/commands/test_mcp_command.py -v`
- `pytest tests/commands/test_mcp_command.py tests/commands/test_doctor_phase4.py -v`
- Temp-`HOME` smoke check for doctor skip/install/write-enabled behavior
- Full `pytest` collection remains blocked in this environment because the
  external `mcp` package is unavailable to `tests/mcp/*`
