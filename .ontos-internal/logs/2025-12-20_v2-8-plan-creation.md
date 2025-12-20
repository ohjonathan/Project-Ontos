---
id: log_20251220_v2_8_plan_creation
type: log
status: active
event_type: decision
concepts: []
impacts: [v2_8_implementation_plan]
---

# Session Log: V2 8 Plan Creation
Date: 2025-12-20 01:23 KST
Source: Claude Opus 4.5
Event Type: decision

## 1. Goal
Create and refine v2.8 implementation plan through LLM Review Board process.

## 2. Key Decisions

### v1.0.0 (Initial)
- **Feature 1: Context Object Refactor** - Split ontos_lib.py into ontos/core/ (pure) and ontos/ui/ (I/O)
- **Feature 2: Unified CLI** - Create ontos.py dispatcher replacing direct script invocation
- **SessionContext dataclass** - Transaction pattern with commit/rollback for file writes
- **Backwards compatibility** - ontos_lib.py becomes a shim re-exporting from new locations

### v2.0.0 (After LLM Review Board Round 1)
- **Two-phase commit** - temp-then-rename for true atomicity (Claude, Codex feedback)
- **Stale lock detection** - PID liveness checking (Chief Architect addition)
- **Phased PR strategy** - 4 stable PRs instead of single atomic (Gemini "In-Between State Risk")
- **OutputHandler separation** - Output formatting NOT in SessionContext (Chief Architect)
- **All 10 questions resolved** with rationale

## 3. Alternatives Considered
- Single atomic PR vs. phased PRs → Chose phased (Gemini insight)
- Provider pattern for git vs. mark as impure → Chose mark as impure (pragmatic for 2 functions)
- flush_output() in SessionContext → Moved to OutputHandler (separation of concerns)

## 4. Changes Made
- Created v1.0.0: `.ontos-internal/strategy/proposals/v2.8/v2.8_implementation_plan.md` (784 lines)
- Updated to v2.0.0: Incorporated LLM Review Board feedback (1,090 lines)
- Critically reviewed Claude, Codex, Gemini reviews
- Resolved all 10 open questions

## 5. Next Steps
- Share v2.0.0 with LLM Review Board (Round 2)
- Obtain final approval
- Begin implementation with PR #1 (Library Structure)
