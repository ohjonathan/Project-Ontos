---
id: log_20251217_v2_5_promises_implementation
type: log
status: active
event_type: feature
concepts: [config, ux, tooling, hooks]
impacts: [v2_5_promises_implementation_plan, ontos_manual, ontos_agent_instructions]
---

# Session Log: V2.5 "The Promises" Implementation

Date: 2025-12-17 10:39 KST
Source: Gemini
Event Type: feature

## 1. Goal

Implement the v2.5 "The Promises" feature as specified in the approved implementation plan. This delivers clear, honest communication about what each workflow mode provides through promise messaging and mode-based consolidation behavior.

## 2. Key Decisions

- Used ASCII-only characters for promise messaging UI to ensure compatibility across terminals (Windows CMD, SSH, CI logs)
- Pre-commit hook chosen over pre-push for consolidation to avoid "dirty working tree" paradox
- Implemented dual condition for consolidation trigger (count > threshold AND old logs exist) to prevent false alarms
- Added explicit file staging (specific paths only, never `git add -u`) to avoid staging user files

## 3. Alternatives Considered

- **Pre-push consolidation** — Rejected because it leaves dirty working tree after push
- **Context map warning only** — Rejected for automated mode; users want zero friction
- **Scriptable `ontos_check.py`** — Deferred to v2.6; context map warning covers 80% case

## 4. Changes Made

### New Files
- `.ontos/hooks/pre-commit` — Bash wrapper delegating to Python
- `.ontos/scripts/ontos_pre_commit_check.py` — Main consolidation hook with safety features

### Modified Files
- `ontos_init.py` — Promise messaging UI, hook installation with conflict detection
- `ontos_config_defaults.py` — Version 2.5.0, AUTO_CONSOLIDATE_ON_COMMIT, updated MODE_PRESETS
- `ontos_generate_context_map.py` — Added check_consolidation_status() function
- `docs/reference/Ontos_Agent_Instructions.md` — Updated activation flow
- `docs/reference/Ontos_Manual.md` — Updated to v2.5, new mode table
- `Ontos_CHANGELOG.md` — Added v2.5.0 release notes

## 5. Next Steps

- Create PR for review
- Merge after approval
- Consider v2.6 deferred items (ontos_check.py, ontos_unarchive.py)

---
## Verification

- 129 tests passed
- Context map generation works
- Hooks are executable
