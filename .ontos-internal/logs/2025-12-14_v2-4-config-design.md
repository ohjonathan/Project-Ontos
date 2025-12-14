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
- **Auto-archive on push:** New feature for "automated" mode - creates session log automatically
- **Installation prompts:** Ask 3 questions during setup (workflow style, consolidation, attribution)
- **Architectural review required:** Changes are significant enough to warrant multi-agent review before implementation

## 3. Alternatives Considered
- Single-tier config only — rejected, too technical for new users
- Removing config options entirely — rejected, power users need flexibility
- Implementing immediately — rejected, design is significant and needs review
- Mode names (auto/standard/relaxed vs automated/prompted/advisory) — TBD pending review

## 4. Changes Made
- Created comprehensive design document: `.ontos-internal/strategy/v2.4_config_automation_proposal.md`
- Rolled back prototype implementation (was v2.3.2) to keep codebase clean pending review

## 5. Next Steps
- Review design document with Claude, Codex, and Gemini
- Address open questions (mode naming, default mode, auto-archive quality)
- Implement after architectural approval
- Target version: v2.4.0

---
## Raw Session History
```text
- PR #14 review (v2.3)
- Root directory cleanup
- Fixed migrate script to skip archive/
- Designed consolidation automation
- Expanded to full config automation proposal
- Wrote v2.4 design document
- Rolled back implementation pending review
```
