---
id: log_20251214_v2_4_config_design
type: log
status: active
event_type: decision
concepts: [ux, config, tooling]
impacts: [v2_strategy]
---

# Session Log: V2 4 Config Design
Date: 2025-12-14 23:26 KST
Source: Claude Code
Event Type: decision

## 1. Goal
Design a two-tier configuration system for Ontos v2.4 that reduces friction for new users while preserving power-user flexibility.

## 2. Key Decisions
- **Three workflow modes:** automated, prompted, advisory (spectrum from zero-friction to full control)
- **Two-tier config:** High-level mode selection + low-level individual overrides
- **Session Appending:** One log per branch per day (from Gemini review) - prevents ghost log pollution
- **Auto-archive on push:** New feature for "automated" mode - creates session log automatically
- **`status: auto-generated`:** Quality signal for lint warnings (from Claude review)
- **Default mode = prompted:** Users should learn curation before automating (from Gemini review)
- **`ONTOS_SOURCE` env var:** CI and shared machine support (from Codex review)

## 3. Alternatives Considered
- Single-tier config only — rejected, too technical for new users
- Removing config options entirely — rejected, power users need flexibility
- Mode renaming (autopilot/guided/relaxed) — rejected, original names are clear
- Personas (solo/team/compliance) — rejected, over-engineering
- Telemetry — rejected, contradicts local-first philosophy
- "Minimal log is worse than no log" — rejected, breadcrumb is useful if marked auto-generated

## 4. Changes Made
- Created v2.4 design document (v1.0)
- Received architectural review from Claude, Codex, Gemini
- Critically analyzed feedback (adopted 11 ideas, rejected 8)
- Revised proposal to v1.1 with Session Appending model
- Rolled back prototype implementation pending final approval

## 5. Next Steps
- Final review of v1.1 proposal
- Implement v2.4.0 with revised design
- Key implementation: session appending in `ontos_end_session.py`

---
## Raw Session History
```text
- PR #14 review (v2.3)
- Root directory cleanup, migrate script fix
- Designed consolidation automation (v2.3.2 prototype)
- Expanded to full config automation proposal
- Wrote v2.4 design document (v1.0)
- Rolled back implementation pending review
- Received Claude/Codex/Gemini feedback
- Critical analysis: adopted session appending, status:auto-generated, env var support
- Rejected: mode renaming, personas, telemetry, checksum drift detection
- Revised proposal to v1.1
```
