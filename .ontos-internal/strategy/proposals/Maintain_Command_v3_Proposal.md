---
id: maintain_command_v3_proposal
type: strategy
status: draft
depends_on: [v3_0_implementation_roadmap, v3_0_technical_architecture]
concepts: [cli, maintain, curation, proposals, consolidation, v3-transition]
---

# Chief Architect Briefing: "Maintain Ontos" Command in v3.0

**To:** Chief Architect (Claude Opus 4.5)
**From:** Research Assistant
**Date:** 2026-01-14
**Subject:** The `maintain` command is missing from v3.0 CLI - Analysis and Recommendations

---

## 1. Executive Summary

**Situation:** The v2.x `ontos maintain` command runs 5 maintenance tasks in a single workflow. In v3.0, this command is **not present** in the CLI specification. Some functionality has been split into separate commands, but key features are missing or unclear.

**Current State:**
- v2.x: `python3 ontos.py maintain` runs 5 tasks as documented in Agent Instructions
- v3.0: No `maintain` command in CLI spec (Tech Arch §7.1, lines 1195-1209)
- Agent Instructions still reference "Maintain Ontos" as a weekly workflow

**Chief Architect Tasks:**
1. Decide if `maintain` should be added to v3.0 CLI
2. If not, update Agent Instructions to reference new command structure
3. Clarify where curation stats and proposal graduation live in v3.0

---

## 2. Current v2.x "Maintain Ontos" Workflow

From `docs/reference/Ontos_Agent_Instructions.md` lines 69-78:

```
### "Maintain Ontos" (Weekly)
1. `python3 ontos.py maintain`
2. This runs five steps:
   - Migrate untagged files
   - Regenerate context map
   - **Report curation stats (L0/L1/L2)**
   - Consolidate old logs (if `AUTO_CONSOLIDATE=True`)
   - **Review proposals (v2.6.1)** — prompts to graduate implemented proposals
3. Fix any errors reported
4. Commit context map if changed
```

**Implementation:** `.ontos/scripts/ontos_maintain.py` (~200 lines)

---

## 3. v3.0 CLI Command List (No `maintain`)

From `V3.0-Technical-Architecture.md` §7.1:

```
Commands:
  init              Initialize Ontos in current repo
  map               Generate context map
  log               Create/enhance session log
  doctor            Health check and diagnostics
  verify            Verify describes dates
  query             Search documents
  migrate           Migrate schema versions
  consolidate       Archive old logs
  promote           Promote L0/L1 to Level 2
  scaffold          Generate L0 scaffolds
  stub              Create L1 stub document
  export            Generate agent bootstrap files (CLAUDE.md)
  hook              Git hook dispatcher (internal)
```

**Note:** `maintain` is NOT listed.

---

## 4. Feature Mapping: v2.x → v3.0

| v2.x `maintain` Feature | v3.0 Equivalent | Status |
|-------------------------|-----------------|--------|
| Migrate untagged files | `ontos migrate` | ✅ Present |
| Regenerate context map | `ontos map` | ✅ Present |
| Report curation stats (L0/L1/L2) | **???** | ❌ **Missing** |
| Consolidate old logs | `ontos consolidate` | ✅ Present |
| Review/graduate proposals | **???** | ❌ **Missing** |

### 4.1 What's Missing

**Curation Stats Reporting:**
- v2.x: `ontos maintain` prints L0/L1/L2 document counts
- v3.0: No command appears to provide this
- Possible home: `ontos doctor`? `ontos map --stats`?

**Proposal Graduation:**
- v2.x: `ontos maintain` prompts to graduate implemented draft proposals
- v3.0: No equivalent documented
- Possible home: `ontos promote`? Separate `ontos propose` command?

### 4.2 Aggregated Workflow Missing

The key value of `ontos maintain` is running **all 5 tasks in sequence** with a single command. In v3.0, users would need to run:

```bash
ontos migrate && ontos map && ontos consolidate --days 30
```

Plus manually check curation stats and proposal status.

---

## 5. Documentation Inconsistencies

### 5.1 Agent Instructions Still Reference `maintain`

`docs/reference/Ontos_Agent_Instructions.md` line 69-70:
```
### "Maintain Ontos" (Weekly)
1. `python3 ontos.py maintain`
```

### 5.2 Manual Shows v3.0 Alternative

`docs/reference/Ontos_Manual.md` lines 122-126:
```
### Maintain Graph
Say **"Maintain Ontos"** weekly:
```bash
ontos map && ontos consolidate --days 30
```
```

**Note:** This is missing `migrate`, curation stats, and proposal review.

### 5.3 Migration Guide Shows `ontos maintain`

`docs/reference/Migration_v2_to_v3.md` line 53:
```
ontos maintain
```

**Issue:** This command doesn't exist in v3.0 CLI spec.

---

## 6. Open Questions for Chief Architect

### 6.1 Should v3.0 Have a `maintain` Command?

| Option | Pros | Cons |
|--------|------|------|
| **Add `ontos maintain`** | Preserves v2.x workflow, simpler for users/agents | Adds another command, may be redundant |
| **Keep separate commands** | Explicit, composable | Users must remember multiple commands |
| **Add `--all` flag to `doctor`** | `doctor` already does health checks | May overload `doctor` semantics |

### 6.2 Where Should Curation Stats Live?

| Option | Implementation |
|--------|----------------|
| `ontos doctor` | Add curation stats to health check output |
| `ontos map --stats` | Add flag to map command |
| `ontos status` | New command for project status |
| `ontos maintain` | Keep as part of maintain workflow |

### 6.3 Where Should Proposal Graduation Live?

| Option | Implementation |
|--------|----------------|
| `ontos promote` | Expand to include proposal graduation |
| `ontos maintain` | Keep as part of maintain workflow |
| `ontos propose --graduate` | New subcommand |
| Remove feature | Rely on manual graduation |

---

## 7. Recommendations

### Option A: Add `ontos maintain` to v3.0

**Implementation:**
```
ontos maintain [--skip-consolidate] [--skip-migrate] [--verbose]
```

**Runs:**
1. `migrate` - Tag untagged files
2. `map` - Regenerate context map
3. Print curation stats (L0/L1/L2)
4. `consolidate` - Archive old logs (unless `--skip-consolidate`)
5. Check for draft proposals ready to graduate

**Effort:** ~2-3 hours (wrapper command calling existing modules)

### Option B: Update Documentation Only

**Changes:**
1. Update Agent Instructions to show new workflow:
   ```bash
   ontos map && ontos consolidate --days 30 && ontos doctor
   ```
2. Remove `ontos maintain` from Migration Guide
3. Add curation stats to `ontos doctor` output
4. Add proposal graduation to `ontos promote`

**Effort:** ~1-2 hours (doc updates + minor code changes)

### Option C: Defer to v3.1

Track as enhancement for v3.1 "Bridge Features" release. Update docs with temporary workaround.

---

## 8. Impact Assessment

| Stakeholder | Impact if `maintain` Missing |
|-------------|------------------------------|
| AI Agents | Must learn new multi-command workflow |
| Developers | More commands to remember |
| Documentation | Multiple inconsistencies to fix |
| Migration | Users expecting `ontos maintain` get error |

---

## 9. Reference Files

| Document | Path | Relevant Lines |
|----------|------|----------------|
| v3.0 Tech Architecture | `.ontos-internal/strategy/v3.0/V3.0-Technical-Architecture.md` | §7.1 (1195-1209) |
| Agent Instructions | `docs/reference/Ontos_Agent_Instructions.md` | 69-78 |
| Manual | `docs/reference/Ontos_Manual.md` | 122-126, 467, 483, 532 |
| Migration Guide | `docs/reference/Migration_v2_to_v3.md` | 46, 53 |
| v2.x Implementation | `.ontos/scripts/ontos_maintain.py` | Full file |

---

*End of Briefing*
