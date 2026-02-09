---
id: log_20260131_v3_2_1_and_v3_2_2_proposals
type: log
status: active
event_type: feature
source: Antigravity
branch: main
created: 2026-01-31
concepts: [activation, agents, maintenance, proposals]
impacts: [ontos_agent_instructions, v3_2_re_architecture_support_proposal]
---

# v3.2.1 and v3.2.2 Proposal Planning

## 1. Goal

Document activation resilience gaps and missing CLI commands discovered during session.

## 2. Key Decisions

- Created **v3.2.1 proposal** for activation resilience after context compaction
- Created **v3.2.2 proposal** for missing `ontos maintain` command
- Identified root cause: AGENTS.md not re-read after `/compact` in Claude Code

## 3. Alternatives Considered

- Considered updating documentation only instead of implementing `maintain` — deferred decision to proposal review
- Considered adding activation to compaction summary — rejected (not controllable by Ontos)

## 4. Changes Made

| File | Change |
|------|--------|
| `.ontos-internal/strategy/proposals/v3.2.1c/activation_resilience_proposal.md` | **[NEW]** Trigger phrases, compaction survival |
| `.ontos-internal/strategy/proposals/v3.2.2/maintain_command_proposal.md` | **[NEW]** Missing `ontos maintain` command |
| `AGENTS.md` | Regenerated (was stale) |
| `Ontos_Context_Map.md` | Regenerated (542 docs) |

## 5. Testing

- Ran `ontos map` — 542 docs, 37 errors, 284 warnings
- Ran `ontos doctor` — 8/9 passed, AGENTS.md staleness fixed
