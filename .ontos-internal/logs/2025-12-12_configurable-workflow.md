---
id: log_20251212_configurable_workflow
type: log
status: active
event_type: feature
concepts: [configuration, workflow-enforcement, opt-out, relaxed-mode]
impacts: [v2_architecture, self_dev_protocol]
---

# Session Log: Configurable Workflow
Date: 2025-12-12 21:16 KST
Source: Claude Code
Event Type: feature

## 1. Goal
Add configuration options to allow users to opt-out of strict workflow enforcement (blocking pre-push hook, required --source flag).

## 2. Key Decisions
- **Two config options added**: `ENFORCE_ARCHIVE_BEFORE_PUSH` and `REQUIRE_SOURCE_IN_LOGS` in ontos_config_defaults.py
- **Defaults to strict**: Both options default to `True` (recommended for teams)
- **Relaxed mode available**: Set to `False` for solo devs or rapid prototyping
- **Hook reads config via Python**: Pre-push hook calls Python inline to check config, keeping logic centralized
- **Documentation first**: Added Configuration section to Manual with examples

## 3. Changes Made
- `ontos_config_defaults.py`: Added WORKFLOW ENFORCEMENT section with two new settings
- `ontos_config.py`: Imported and re-exported new settings, added example customizations
- `.ontos/hooks/pre-push`: Updated to check `ENFORCE_ARCHIVE_BEFORE_PUSH` config; shows advisory vs blocking
- `ontos_end_session.py`: `--source` requirement now respects `REQUIRE_SOURCE_IN_LOGS`
- `docs/reference/Ontos_Manual.md`: Added Configuration section with settings table and examples
- `Ontos_CHANGELOG.md`: Documented new features in [Unreleased]

## 4. Next Steps
- Test relaxed mode end-to-end (set both to False and verify behavior)
- Consider adding more configuration options as needed
- Merge PR #11 to main

---
## Raw Session History
```text
No commits found since last session (2025-12-12).
```
