---
id: log_20251216_v2_5_promises_implementation_plan
type: log
status: active
event_type: decision
concepts: [ux, config, consolidation, workflow]
impacts: [v2_strategy]
---

# Session Log: V2 5 Promises Implementation Plan
Date: 2025-12-16 01:07 KST
Source: Claude Opus
Event Type: decision

## 1. Goal
Design v2.5 "The Promises" feature: mode-based consolidation behavior with clear user promises shown during installation.

## 2. Key Decisions
- **Pre-commit over pre-push:** Auto-consolidation uses pre-commit hook so changes are included in the commit (avoids "left behind" paradox)
- **Mode-specific behavior:** Automated=auto-consolidate, Prompted=agent reminder, Advisory=warning only
- **Promise messaging:** Show clear promises during `ontos_init.py` mode selection to set user expectations
- **Never block commits:** Pre-commit hook returns 0 always; consolidation failure shouldn't stop work

## 3. Alternatives Considered
- **Pre-push consolidation** — Rejected because consolidated files would be "left behind" (not in the push)
- **Always block on consolidation needed** — Rejected; too aggressive, violates "zero friction" promise
- **Consolidation reminder only** — Rejected for automated mode; users still forget

## 4. Changes Made
- [NEW] `.ontos-internal/strategy/v2.5_promises_implementation_plan.md` — Full implementation plan

## 5. Next Steps
- Review plan with other LLMs (Gemini, etc.)
- Implement v2.5 features per plan
- Add tests for pre-commit hook 

---
## Raw Session History
```text
be52684 - docs: add v2.5 "The Promises" implementation plan
d4154ee - chore: remove testing file
472ae15 - Merge pull request #16 from ohjona/TEST-GEMINI
8a1fc34 - test: add testing file for Gemini PR review
a9a0ede - feat: add Gemini CLI workflows for automated PR review
72caecb - chore: archive v2.4 planning docs after merge
739dfa3 - Merge pull request #15 from ohjona/v2.4-config-automation
0e9bce4 - docs: update documentation for v2.4 features
af13def - fix: final PR #15 fixes from Codex review
8d2bd50 - fix: address remaining PR #15 feedback
c9cbb15 - fix: address PR #15 reviewer feedback
cdc9b09 - feat: implement v2.4 config automation and UX overhaul
97e7a79 - fix(v2.4): add context map auto-regeneration to prevent stale maps
2b9ba37 - chore: regenerate context map (fix stale broken link)
967b10b - docs(v2.4): finalize proposal v1.4 after fourth architectural review
5cabf84 - docs(v2.4): finalize proposal v1.3 after third architectural review
```
