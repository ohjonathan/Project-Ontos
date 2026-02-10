---
id: maintain_command_review
type: strategy
status: draft
depends_on: [maintain_command_proposal]
---

# Review Consolidation: v3.2.2 `ontos maintain` Command

**Date:** 2026-02-10
**Review Lead:** Claude Opus 4.6
**Reviewers:** Peer (R1), Alignment (R2), Adversarial (R3)

## Verdict Table

| Reviewer | Role | Verdict | Blocking Issues |
|----------|------|---------|-----------------|
| R1 | Peer Reviewer | approve-with-nits | 0 |
| R2 | Alignment Reviewer | request-changes | 2 |
| R3 | Adversarial Reviewer | request-changes | 4 |

**Consolidated Verdict: REQUEST CHANGES** (2 of 3 reviewers)

---

## Blocking Issues

### B1. `review_proposals` collects interactive input but never graduates proposals [CRITICAL]
**Flagged by:** R3 (Adversarial) | **Category:** Functional correctness

`_task_review_proposals` (maintain.py:521-533) prompts the user with `input("Graduate proposal 'X'? [y/N]:")`, increments a `marked` counter, then returns a success message saying "N marked for graduation review" -- but never writes any file. The user's answers are silently discarded. This is deceptive UX: a user-facing interactive prompt that collects input and does nothing with it.

R1 (Peer) flagged this differently as a testability/usability concern (N4) noting the `input()` call is untestable and surprising in a batch runner. R1 did not flag the no-op behavior as blocking. **Disagreement preserved:** R1 views this as a design concern; R3 views it as a functional correctness bug.

**Required action:** Either integrate actual graduation logic, or remove the interactive prompt and replace with an informational report ("Found N draft proposals. Use `ontos promote` to graduate them.").

---

### B2. Agent Instructions document not updated -- says "five steps", implementation has 8 tasks [BLOCKING]
**Flagged by:** R2 (Alignment) | **Category:** Alignment

`docs/reference/Ontos_Agent_Instructions.md` (lines 84-92) documents 5 steps. The implementation registers 8 tasks, adding `health_check` (order 30), `check_links` (order 70), and `sync_agents` (order 80). The Agent Instructions document is the authoritative behavioral spec for AI agents -- shipping without updating it perpetuates the exact documentation-implementation gap this PR was designed to fix.

**Not flagged by R1 or R3.** This is a single-reviewer finding from the Alignment specialist -- retained per review rules.

**Required action:** Update `docs/reference/Ontos_Agent_Instructions.md` to document all 8 tasks, or reduce tasks to match the documented 5.

---

### B3. Registry pattern is architecturally novel -- no precedent, not in Technical Architecture [BLOCKING]
**Flagged by:** R2 (Alignment) | **Category:** Architecture

No existing command uses a registry/decorator/singleton pattern. All other commands (`doctor`, `consolidate`, `map`, etc.) use straightforward `*_command(options) -> int` functions. The `MaintainTaskRegistry` with `DEFAULT_TASK_REGISTRY` module-level singleton and `@register_maintain_task` decorator is unique. This introduces:
- Import-time side effects (decorators fire when module is imported via `__init__.py`)
- A pattern not described in `V3.0-Technical-Architecture.md`

R1 (Peer) assessed the registry as "clean and intuitive" (positive). R3 (Adversarial) flagged the mutable global singleton (B5/medium) but not the architectural novelty per se. **Disagreement preserved:** R1 views the pattern positively; R2 views it as an unapproved architectural decision.

**Tier 2 escalation consideration:** If the registry is intended as a reusable pattern for future commands, this is a Tier 2 architectural decision. If it's purely local to `maintain.py`, it can be approved with a documenting comment. The key question: **is this a precedent or an exception?**

**Required action:** Either (a) document the registry pattern as an approved extension in the Technical Architecture, or (b) add a comment in `maintain.py` explicitly stating this is not intended as a precedent, or (c) rewrite to use procedural orchestration matching other commands.

---

### B4. `config: object` type annotation -- 6 unsafe attribute access sites [HIGH]
**Flagged by:** R3 (Adversarial), R1 (Peer) | **Category:** Type safety

`MaintainContext.config` (maintain.py:80) is typed as `object` instead of `OntosConfig`. Six call sites access `ctx.config.paths.docs_dir`, `ctx.config.scanning.scan_paths`, etc. With `object` typing:
- Static analysis tools flag every access as an error
- IDEs provide no autocomplete
- A non-`OntosConfig` value slips through without type-checker protection
- Error isolation catches the `AttributeError`, but the cascade across multiple tasks produces confusing output

**Both R1 (N1) and R3 (B2) independently flagged this.** R1 as non-blocking, R3 as blocking. Consensus: this should be fixed.

**Required action:** Change `config: object` to `config: OntosConfig` and add the import.

---

### B5. `curation_stats` task performs full disk I/O scan in `--dry-run` mode [HIGH]
**Flagged by:** R3 (Adversarial) | **Category:** Dry-run contract violation

`_task_curation_stats` (maintain.py:351-389) has no `dry_run` guard. It scans all docs and parses all frontmatter even in `--dry-run` mode. Every other task with I/O has a dry-run early return. The inconsistency violates the dry-run contract.

Similarly, `_task_migrate_untagged` calls `find_untagged_files()` before checking `dry_run` (line 244 vs 259), performing the scan unconditionally. This is arguable (it needs the count for the dry-run message) but worth noting.

**Not flagged by R1 or R2.** Single-reviewer finding from adversarial specialist -- retained.

**Required action:** Add `if ctx.options.dry_run: return _ok("Would report curation levels.")` at the top of `_task_curation_stats`.

---

### B6. `_condition_agents_stale` ignores `ctx.repo_root`, resolves its own root independently [MEDIUM]
**Flagged by:** R3 (Adversarial) | **Category:** Correctness

`_condition_agents_stale` (maintain.py:194-203) calls `check_agents_staleness()` which internally calls `find_repo_root()` from `ontos.commands.agents` -- a different resolution chain than `find_project_root()` used by `maintain_command`. The condition function accepts `_ctx` but ignores it entirely. In monorepo or unusual CWD setups, the staleness check could evaluate a different project than the one being maintained.

R1 (Peer) flagged the fragile string matching in this same function (N8: checking `"stale" in message.lower()`) but not the root resolution mismatch.

**Required action:** Refactor `_condition_agents_stale` to use `ctx.repo_root` instead of relying on `check_agents_staleness()`'s independent resolution. Or pass `ctx` through to the check function.

---

## Agreement Analysis

| Finding | R1 (Peer) | R2 (Alignment) | R3 (Adversarial) |
|---------|-----------|-----------------|-------------------|
| `config: object` typing | N1 (non-blocking) | -- | B2 (blocking) |
| Agent Instructions gap | -- | B1 (blocking) | -- |
| Registry pattern novelty | Positive assessment | B2 (blocking) | Medium concern (B5) |
| `review_proposals` no-op | N4 (usability) | -- | B1 (critical) |
| `curation_stats` dry-run | -- | -- | B3 (high) |
| Condition ignores ctx | -- | -- | B4 (medium) |
| Fragile string matching in condition | N8 (non-blocking) | -- | -- |
| JSON missing `details` | N6 (non-blocking) | -- | -- |
| No exception-path test | N2 (non-blocking) | -- | -- |
| `--skip` discoverability | N3 (non-blocking) | N7 (non-blocking) | -- |
| Unknown `--skip` silent success | -- | -- | B6/medium (non-blocking) |
| v3.2.2 proposal still draft | -- | N3 (non-blocking) | -- |
| Command-to-command imports | -- | N1 (non-blocking) | -- |
| `input()` blocking in semi-TTY | N4 (non-blocking) | N5 (non-blocking) | N4 (non-blocking) |
| No `review_proposals` tests | -- | -- | N5 (non-blocking) |
| `_parse_bool` empty string | -- | -- | N6 (non-blocking) |
| `TaskResult.status` unconstrained | -- | -- | N7 (non-blocking) |

**Key disagreement:** R1 approves with nits while R2 and R3 request changes. R1 assessed the registry pattern positively ("clean and intuitive, a new developer can add a task by writing a decorated function"); R2 sees it as an unapproved architectural novelty. This disagreement is substantive and should be resolved by the project owner.

**Key agreement:** All three reviewers note `input()` in `review_proposals` is problematic, though for different reasons. All see `config: object` as an issue.

---

## Required Actions (prioritized)

### Priority 1: Fix functional bugs
1. **Fix `review_proposals`** -- either add graduation logic or remove the deceptive interactive prompt (B1)
2. **Fix `config: object`** -- change to `config: OntosConfig` (B4)
3. **Add dry-run guard to `curation_stats`** (B5)

### Priority 2: Documentation alignment
4. **Update Agent Instructions** to document all 8 tasks (B2)
5. **Graduate v3.2.2 proposal** from draft to active/complete (R2-N3)

### Priority 3: Architectural decision
6. **Resolve registry pattern status** -- document intent: precedent or exception? (B3)
   - If exception: add comment to maintain.py
   - If precedent: document in Technical Architecture (Tier 2)

### Priority 4: Correctness improvement
7. **Fix `_condition_agents_stale`** to use `ctx.repo_root` (B6)

### Priority 5: Non-blocking improvements (post-merge OK)
8. Add exception-path isolation test (R1-N2)
9. Add `details` to JSON output (R1-N6)
10. Add `--skip` task name discoverability to help text (R1-N3)
11. Add comma-separated `--skip` test (R1-N9)
12. Simplify `_condition_agents_stale` string matching (R1-N8)
13. Add `review_proposals` test coverage (R3-N5)

---

## Tier 2 Escalation Flag

**R2 (Alignment) recommends Tier 2 escalation** if the registry pattern is intended as a reusable architectural pattern. The pattern introduces a module-level singleton, import-time side effects via decorators, and a design not present in the Technical Architecture. If it is intended only as a local implementation detail of `maintain.py`, Tier 2 is not required -- but this intent must be documented explicitly.
