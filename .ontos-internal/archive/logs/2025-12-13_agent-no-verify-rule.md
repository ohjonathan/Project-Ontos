---
id: log_20251213_agent_no_verify_rule
type: log
status: active
event_type: chore
concepts: [workflow, agent-behavior, git-hooks]
impacts: []
---

# Session Log: Agent No Verify Rule
Date: 2025-12-13 22:59 KST
Source: Claude
Event Type: chore

## 1. Goal
Add explicit rule to Agent Instructions: agents must ask before using `git push --no-verify`.

## 2. Key Decisions
- **Behavioral over technical:** Rather than restricting allowed commands, this is a behavioral expectation. Agents should respect the workflow even when they have technical capability to bypass it.
- **Context:** This rule was added after an agent bypassed the pre-push hook without asking, breaking the archive-before-push workflow.

## 3. Changes Made
- **[MODIFY]** `docs/reference/Ontos_Agent_Instructions.md`: Added RULE about never using `--no-verify` without explicit user approval.

## 4. Next Steps
- None. Rule documented.

---
## Raw Session History
```text
Previous session: context-map-notice feature
```
