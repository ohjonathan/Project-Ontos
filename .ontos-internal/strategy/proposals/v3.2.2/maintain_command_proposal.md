---
id: v3_2_2_maintain_command_proposal
type: strategy
status: draft
depends_on: [ontos_agent_instructions, v3_2_2_interop_discussion]
concepts: [cli, maintenance, documentation-parity]
---

# v3.2.2: `ontos maintain` Command Implementation

**Author:** Antigravity  
**Date:** 2026-01-31  
**Status:** Draft

---

## 1. Problem Statement

The **Ontos Agent Instructions** document a `maintain` command that **does not exist** in the CLI:

```markdown
### "Maintain Ontos" (Weekly)
1. `ontos maintain`
2. This runs five steps:
   - Migrate untagged files
   - Regenerate context map
   - Report curation stats (L0/L1/L2)
   - Consolidate old logs (if AUTO_CONSOLIDATE=True)
   - Review proposals (v2.6.1) — prompts to graduate implemented proposals
```

**Actual behavior:**
```
$ ontos maintain
ontos: error: invalid choice: 'maintain' (choose from 'init', 'map', 'log', ...)
```

This is a **documentation-implementation gap** that causes agent confusion.

---

## 2. Proposed Solutions

### Option A: Implement `ontos maintain` (Recommended)

Create the command as documented, orchestrating existing commands:

```python
def run_maintain(options):
    """Weekly maintenance workflow."""
    # 1. ontos map
    # 2. ontos doctor
    # 3. ontos agents --force (if stale)
    # 4. ontos consolidate (if enabled)
    # 5. Report curation stats
```

**Pros:** Matches documentation, single command for agents
**Cons:** Additional code to maintain

### Option B: Update Documentation

Remove `ontos maintain` from Agent Instructions and replace with manual steps:
```markdown
### "Maintain Ontos" (Weekly)
1. `ontos map` — Regenerate context map
2. `ontos doctor` — Run health checks
3. `ontos agents --force` — Sync instruction files if stale
```

**Pros:** No new code
**Cons:** More steps for agents, documentation downgrade

---

## 3. Implementation Spec (Option A)

### Files to Create/Modify

| File | Change |
|------|--------|
| `ontos/commands/maintain.py` | **[NEW]** Orchestration command |
| `ontos/cli.py` | Register `maintain` subparser |
| `tests/commands/test_maintain.py` | **[NEW]** Tests |

### Command Behavior

```
$ ontos maintain [--verbose] [--dry-run]

Steps:
  ✓ Regenerating context map...
  ✓ Running health checks...
  ✓ Syncing AGENTS.md...
  ✓ Checking for stale proposals...

Maintenance complete: 542 docs, 8/9 health checks passed
```

---

## 4. Relationship to v3.2.2 Scope

This is a **small, focused fix** that can be bundled with the larger `ontos retrofit` work in v3.2.2, or shipped independently as a quick patch.

---

## 5. Decision Requested

1. **Option A or B?** — Implement the command or update documentation?
2. **Scope:** Bundle with v3.2.2 or ship separately?
