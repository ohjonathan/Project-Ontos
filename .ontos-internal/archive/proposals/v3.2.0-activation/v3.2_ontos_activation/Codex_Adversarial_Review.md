# v3.2 Ontos Activation — Spec Review (Adversarial)

**Review signed by:**
- **Role:** Adversarial Reviewer
- **Model:** Codex (OpenAI)
- **Date:** 2026-01-29
- **Review Type:** Spec Review (Proposal)

---

## Part 1: Assumption Attack

| Assumption | Why It Might Be Wrong | Impact If Wrong |
|------------|----------------------|-----------------|
| Tools re-read AGENTS.md after compaction | Many tools load instruction files only at session start; compaction can drop them without re-fetch. | Core mechanism fails; users continue with stale/missing context; proposal becomes cosmetic. |
| 2k tokens is enough for Tier 1 | Large repos and “critical paths” summaries can exceed 2k; content may be too dense or too thin. | Tier 1 overflows or loses key info; re-activation still needs deep reads. |
| Users will notice context loss | Most users don’t detect subtle loss and keep working. | Re-activation trigger never fires; context loss persists. |
| `ontos map` is cheap to re-run | Large graphs and validation can be slow/noisy; errors/warnings reduce trust. | Users avoid re-running; auto-sync adds friction. |
| Recent logs indicate "active work" | Logs may be stale, missing, or unused; active work may be in git/tasks. | Tier 1 misleads; wrong priorities and confusion. |
| Auto-sync won't overwrite important user edits | Users do edit AGENTS.md; backups may be ignored or not obvious. | Loss of custom onboarding/compliance notes. |
| Tiered structure survives partial reads | LLMs can truncate mid-section or mid-table. | Partial reads still fail to orient; false confidence. |

---

## Part 2: Edge Case Analysis

| Scenario | Handled? | If Not, What Happens? |
|----------|----------|----------------------|
| AGENTS.md doesn't exist when `map` runs | ✅ | No auto-creation; still need `ontos agents`; re-activation gap remains. |
| User has customized AGENTS.md with project-specific notes | ❌ | Auto-sync overwrites custom content; backup may be ignored. |
| Context map is huge (100k+ tokens) — Tier 1 still 2k? | ❌ | 2k becomes too small or too compressed; insufficient orientation. |
| No recent logs exist (fresh project) | ✅ | “Active work” empty; may imply inactivity. |
| Multiple compactions in rapid succession | ❌ | Re-activation prompts repeated; warning fatigue; ignored guidance. |
| User runs `ontos map` but doesn't read output | ❌ | Tiered map unused; no benefit. |
| Tool compacts mid-command execution | ❌ | Partial map/AGENTS sync; inconsistent state; noisy staleness. |
| AGENTS.md and context map get out of sync | ✅ | Doctor warning exists, but may be ignored. |
| User on older Ontos version with new AGENTS.md format | ❌ | Older tools ignore/parse incorrectly; confusion. |
| Repo has no `.ontos-internal/logs/` directory | ✅ | Active work detection blank. |

---

## Part 3: Failure Mode Analysis

| Failure | How It Happens | Detection | Recovery |
|---------|----------------|-----------|----------|
| Auto-sync corrupts AGENTS.md | Concurrent write or crash mid-write | Only visible on next read | Backup exists but manual restore required. |
| Tier 1 exceeds token budget | Growth in docs/logs; verbose summaries | Tests fail or content truncated | Hard-fail or loss of key info. |
| "Active work" detection returns stale data | Logs unused/lagging; no git context | User notices mismatch | No clear correction path. |
| Staleness check false positives | Clock skew; timestamp order issues | Repeated warnings | Warning fatigue; ignored warnings. |
| Cross-tool files (.cursorrules) diverge | AGENTS auto-sync but .cursorrules not updated | Conflicting instructions | Manual reconciliation required. |

---

## Part 4: Race Conditions & Timing

| Race Condition | Scenario | Impact |
|----------------|----------|--------|
| Map runs while files changing | Docs edited during map | Inconsistent summary/table; Tier 1 inaccurate. |
| Two terminals run `ontos map` simultaneously | Competing writes | Corrupted/partial map or AGENTS.md. |
| Compaction happens during `ontos map` execution | Tool loses context mid-run | Output not read; activation steps missed. |
| User edits AGENTS.md while map auto-syncs | Overwrite race | Data loss; trust erosion. |

---

## Part 5: The "It Won't Actually Help" Attack

### Scenario A: Tool doesn't re-read AGENTS.md
- After compaction, tool keeps working without project context; nothing triggers reload.
- Proposal adds no automatic recovery; benefit near-zero unless user re-runs `ontos map`.
- Improvement over status quo is mainly cosmetic (tiered formatting).

### Scenario B: User doesn't notice context loss
- Common case: user continues unaware.
- Proposal relies on user noticing and acting; no proactive signal.
- Solves the wrong problem (silent failure remains).

### Scenario C: Re-activation still requires user action
- User must re-run `ontos map` and read Tier 1; same friction.
- Tier 1 helps only when user already does the right thing.

---

## Part 6: Security & Safety Review

| Attack Vector | Applicable? | Mitigation in Spec? |
|---------------|-------------|---------------------|
| Malicious AGENTS.md injection | Yes | ❌ |
| Path traversal in auto-sync | Yes | ❌ |
| Information leakage in Tier 1 | Yes | ❌ |
| Denial of service via huge context | Yes | ❌ |

---

## Part 7: Regression Risk

| Existing Behavior | Risk of Breaking | How |
|-------------------|------------------|-----|
| `ontos map` output format | High | Tiered structure breaks parsers/tests. |
| `ontos agents` standalone use | Medium | Auto-sync introduces duplicate source of truth. |
| User workflows depending on current format | High | Scripts/processes parse map tables. |
| CI/CD pipelines using Ontos | Medium | New warnings/staleness checks can fail strict pipelines. |

---

## Part 8: Blind Spot Identification

1. **Where is this proposal overconfident?**
   Assumes tool behavior (re-reading instruction files) that is usually false.

2. **What seems too simple?**
   A universal 2k Tier 1 target across all repo sizes.

3. **What problem is this actually solving vs. what it claims to solve?**
   It optimizes manual re-activation, not automatic recovery after compaction.

4. **What user behavior is assumed that won't happen?**
   Users noticing context loss and re-running `ontos map` promptly.

5. **What's the failure mode when the "happy path" doesn't happen?**
   Silent drift: tool works with wrong assumptions and produces incorrect edits.

---

## Part 9: The Killer Question

If tools don’t automatically re-read AGENTS.md after compaction, this proposal reduces to: “make `ontos map` output tiered.” Is that worth the complexity?

**Assessment:** Likely no. It adds format churn and maintenance risk without fixing the primary failure mode.

---

## Part 10: Issues Found

**Critical (Adversarial):**

| # | Issue | Attack Vector | Impact |
|---|-------|---------------|--------|
| X-C1 | No automatic recovery if tools don’t re-read instructions | Tool compaction behavior | Proposal fails main goal; context loss persists. |

**High (Adversarial):**

| # | Issue | Attack Vector | Impact |
|---|-------|---------------|--------|
| X-H1 | Auto-sync overwrites user customizations | User edits + auto-write | Loss of critical onboarding/compliance notes. |
| X-H2 | Tiered map breaks consumers/parsers | Format change | CI/scripts and downstream tools fail. |

**Medium (Adversarial):**

| # | Issue | Attack Vector | Impact |
|---|-------|---------------|--------|
| X-M1 | “Active work” misleads when logs are stale/missing | Heuristic reliance | Incorrect priorities and wasted effort. |

---

## Part 11: Verdict

**Proposal Robustness:** Fragile

**Recommendation:** Request changes

**Top 3 Concerns:**
1. No real recovery if tools don’t re-read AGENTS.md.
2. Format changes risk breaking existing workflows.
3. Auto-sync can overwrite user customizations.

**The one thing most likely to make this proposal fail:**
Tool behavior doesn’t re-load instruction files after compaction, so re-activation never happens.
