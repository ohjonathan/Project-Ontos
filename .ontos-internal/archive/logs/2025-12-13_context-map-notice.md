---
id: log_20251213_context_map_notice
type: log
status: active
event_type: feature
concepts: [context-map, documentation, contributor-mode]
impacts: [schema]
---

# Session Log: Context Map Notice
Date: 2025-12-13 22:56 KST
Source: Claude
Event Type: feature

## 1. Goal
Add a notice to the context map when generated in Project Ontos repo (Contributor mode) explaining that users' context maps will be overwritten when they initialize Ontos in their own projects.

## 2. Key Decisions
- **Notice placement:** Added as blockquote between HTML comment header and main content, only when `is_ontos_repo()` returns True.
- **Update safety verified:** Confirmed `Ontos_Context_Map.md` is NOT in any `UPDATABLE_*` lists in `ontos_update.py`, so users' maps won't be overwritten during updates.

## 3. Changes Made
- **[MODIFY]** `.ontos/scripts/ontos_generate_context_map.py`: Added conditional notice in `generate_provenance_header()` for Contributor mode.
- **[MODIFY]** `Ontos_Context_Map.md`: Regenerated with new notice.

## 4. Next Steps
- None immediate. Feature complete.

---
## Raw Session History
```text
[main 2048ac8] feat: add notice to context map for Project Ontos repo
```
