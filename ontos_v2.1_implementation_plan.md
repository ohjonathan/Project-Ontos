# Ontos v2.1 Implementation Plan: Smart Memory

*Token management through structured archival without losing institutional knowledge.*

---

## 1. Overview

### Problem

Logs only grow. A project with 50+ sessions burns thousands of tokens in the Context Map, overwhelming agent context windows.

### Solution

Working Memory (hot, scanned) + Long-Term Memory (cold, indexed). The History Index bridges them.

### Philosophy

Time doesn't disappear — it gets consolidated into Space, then archived with a pointer.

### Key Concepts

| Term | Definition |
|:-----|:-----------|
| **Working Memory** | Last ~15 logs, actively scanned, appear in Context Map |
| **Long-Term Memory** | Archived logs, not scanned, accessible on demand |
| **History Index** | `decision_history.md` — permanent ledger bridging hot and cold storage |
| **Consolidation** | Ritual of absorbing decisions into Space docs before archiving |
| **Absorption** | Capturing outcome + constraints + rejected alternatives in Space docs |

---

## 2. Deliverables

### 2.1 Decision History Index

**File:** `docs/strategy/decision_history.md`

**Purpose:** Permanent, always-scanned ledger of all significant decisions. The bridge between active context and archived history.

**Type:** `strategy` (how the project evolves is a strategic concern)

**Content:**

```markdown
---
id: decision_history
type: strategy
status: active
depends_on: [mission]
---

# Decision History

Permanent ledger of project decisions and their archival locations.

## For Agents

1. **Search** this file to understand *why* a decision was made
2. **Retrieve** full context by reading the Archive Path if necessary (see Historical Recall in Agent Instructions)

## For Humans

Before archiving a log, record its key decision here. This ensures institutional knowledge survives consolidation.

---

## History Ledger

| Date | Slug | Event | Decision / Outcome | Impacted | Archive Path |
|:-----|:-----|:------|:-------------------|:---------|:-------------|
| YYYY-MM-DD | example-slug | feature | Brief decision summary. What was decided, what was rejected. | doc_id1, doc_id2 | `.ontos-internal/archive/logs/YYYY-MM-DD_example-slug.md` |

---

## Consolidation Log

Track when consolidation rituals were performed.

| Date | Sessions Reviewed | Sessions Archived | Performed By |
|:-----|:------------------|:------------------|:-------------|
| YYYY-MM-DD | N | N | Name |
```

---

### 2.2 Consolidation Ritual Documentation

**File:** `docs/reference/Ontos_Manual.md`

**Action:** Add new section after "Daily Workflow", before "Installation"

**Content to Add:**

```markdown
---

## 3. Monthly Consolidation

When `logs/` exceeds ~15 files, perform consolidation to keep context lean.

### The Ritual

1. **Review** — Scan the oldest 5-10 logs in `logs/`

2. **Verify Absorption** — For each log, check: have the key decisions been captured in Space documents?
   - If NO: Update the relevant `strategy` or `atom` doc first
   - If YES: Proceed to record

3. **Record** — Add an entry to `docs/strategy/decision_history.md`:
   - Date, slug, event type
   - One-line decision summary (what was decided, what was rejected)
   - Impacted documents
   - Archive path

4. **Cite** — Update impacted Space documents with a breadcrumb:
   ```markdown
   **Decision (2025-12-10):** Chose OAuth2 over session-based auth. See `decision_history.md`.
   ```

5. **Archive** — Move the log file:
   ```bash
   mv .ontos-internal/logs/2025-12-10_auth.md .ontos-internal/archive/logs/
   ```

6. **Commit** — Single commit: "chore: consolidate sessions from [date range]"

### Absorption Pattern

Good absorption captures outcome + constraints + citation.

**Before (Space doc says):**
```markdown
## Authentication
Uses OAuth2 with JWT tokens.
```

**After (Space doc says):**
```markdown
## Authentication
Uses OAuth2 with JWT tokens.

**Constraints:**
- Session-based auth rejected (statelessness requirement)
- Firebase Auth rejected (vendor lock-in)

**Decision (2025-12-10):** See `decision_history.md`.
```

### When to Consolidate

| Trigger | Action |
|---------|--------|
| `logs/` has >15 files | Consolidate oldest 5-10 |
| Quarterly review | Consolidate all logs >30 days old |
| Before major release | Consolidate all active logs |

### Why Consolidation Matters

1. **Token efficiency** — Keeps Context Map lean for agents
2. **Knowledge preservation** — Decisions survive in Space docs + History Index
3. **Discoverability** — History Index is always scanned; agents find decisions without loading all logs
4. **v3.0 readiness** — Clean, structured history enables future graph queries
```

---

### 2.3 Historical Recall (Agent Instructions Update)

**File:** `docs/reference/Ontos_Agent_Instructions.md`

**Action:** Add new section after "Validation Errors"

**Content to Add:**

```markdown
---

## Historical Recall

The `archive/` directory is excluded from the Context Map to save tokens.

To understand rationale behind past decisions:

1. **Read** `docs/strategy/decision_history.md`
2. **Locate** the relevant entry by date, slug, or impacted document
3. **Retrieve** — You are authorized to read the file at the Archive Path, even though it's not in the Context Map

**Example:**
```
User: "Why did we choose OAuth2?"

Agent:
1. Reads decision_history.md
2. Finds: "2025-12-10 | auth-migration | Chose OAuth2 over session-based..."
3. Reads .ontos-internal/archive/logs/2025-12-10_auth-migration.md for full context
4. Responds with sourced explanation
```

**Rule:** Only read archived files that are explicitly listed in `decision_history.md` or requested by the user.
```

---

### 2.4 Configuration: Log Retention Threshold

**File:** `.ontos/scripts/ontos_config_defaults.py`

**Action:** Add to WORKFLOW ENFORCEMENT section

**Content to Add:**

```python
# =============================================================================
# MEMORY MANAGEMENT (v2.1+)
# =============================================================================
# Controls the "Working Memory" size - how many logs stay in active scanning.
# Logs beyond this threshold should be consolidated and archived.

# Recommended threshold for active logs before consolidation
# - Lower = smaller context maps, more frequent consolidation
# - Higher = more history in context, less consolidation overhead
LOG_RETENTION_COUNT = 15
```

**File:** `.ontos/scripts/ontos_config.py`

**Action:** Add to example customizations section

**Content to Add:**

```python
# Memory management (set lower for token-constrained workflows):
# LOG_RETENTION_COUNT = 10
```

---

### 2.5 Changelog Entry

**File:** `Ontos_CHANGELOG.md`

**Action:** Add to [Unreleased] section

**Content to Add:**

```markdown
### Added (v2.1 - Smart Memory)
- **Decision History Index** (`docs/strategy/decision_history.md`) — Permanent ledger for archived session decisions
- **Consolidation Ritual** — Monthly maintenance process documented in Manual (section 3)
- **Absorption Pattern** — Documented pattern for capturing decisions in Space documents with constraints and citations
- **Historical Recall** — Agents can read archived logs referenced in decision_history.md (Agent Instructions update)
- **LOG_RETENTION_COUNT** — Configurable threshold for active logs before consolidation (default: 15)
```

---

## 3. File Changes Summary

| File | Action | Estimated Lines |
|:-----|:-------|:----------------|
| `docs/strategy/decision_history.md` | Create | ~50 |
| `docs/reference/Ontos_Manual.md` | Add section 3 | ~80 |
| `docs/reference/Ontos_Agent_Instructions.md` | Add section | ~25 |
| `.ontos/scripts/ontos_config_defaults.py` | Add config | ~10 |
| `.ontos/scripts/ontos_config.py` | Add example | ~2 |
| `Ontos_CHANGELOG.md` | Update | ~8 |

**Total:** ~175 lines added

---

## 4. Implementation Steps

### Step 1: Create Decision History Index

```bash
# Create the file
touch docs/strategy/decision_history.md

# Add content (use template from section 2.1)
```

### Step 2: Update Ontos Manual

```bash
# Open docs/reference/Ontos_Manual.md
# Add section 3 "Monthly Consolidation" after section 2 "Daily Workflow"
# Use content from section 2.2
```

### Step 3: Update Agent Instructions

```bash
# Open docs/reference/Ontos_Agent_Instructions.md
# Add "Historical Recall" section after "Validation Errors"
# Use content from section 2.3
```

### Step 4: Update Configuration

```bash
# Open .ontos/scripts/ontos_config_defaults.py
# Add LOG_RETENTION_COUNT to WORKFLOW ENFORCEMENT section

# Open .ontos/scripts/ontos_config.py
# Add example customization comment
```

### Step 5: Update Changelog

```bash
# Open Ontos_CHANGELOG.md
# Add v2.1 entries to [Unreleased] section
```

### Step 6: Validate and Commit

```bash
# Regenerate context map
python3 .ontos/scripts/ontos_generate_context_map.py --strict

# Verify decision_history.md appears in Context Map under STRATEGY
# Verify no validation errors

# Commit
git add -A
git commit -m "feat(v2.1): implement Smart Memory system

- Add decision_history.md as permanent ledger for archived decisions
- Document Consolidation Ritual in Manual (section 3)
- Document Absorption Pattern for capturing decisions in Space docs
- Add Historical Recall section to Agent Instructions
- Add LOG_RETENTION_COUNT config (default: 15)"
```

---

## 5. Validation Criteria

After implementation, verify:

- [ ] `decision_history.md` appears in Context Map under STRATEGY section
- [ ] `decision_history.md` has `depends_on: [mission]` and validates without errors
- [ ] `--strict` mode passes with no new errors
- [ ] Manual section 3 is clear and includes absorption pattern example
- [ ] Agent Instructions include Historical Recall with example workflow
- [ ] `LOG_RETENTION_COUNT` is defined in `ontos_config_defaults.py`
- [ ] `LOG_RETENTION_COUNT` example appears in `ontos_config.py`

---

## 6. Migration Notes

### For Existing Projects

1. **Create** `decision_history.md` with empty ledger tables
2. **Backfill** existing archived logs into the History Ledger:
   - Review each file in `.ontos-internal/archive/`
   - Add one-line entry per significant session
3. **No schema changes** — existing logs remain valid
4. **No script changes** — this is documentation + configuration only

### For New Projects

1. `decision_history.md` is created as part of initial setup
2. Consolidation ritual becomes part of monthly maintenance
3. Start with ~15 log threshold, adjust based on context window constraints

---

## 7. Future Considerations (v3.0)

This implementation sets up v3.0 graph queries:

| v2.1 Component | v3.0 Enablement |
|:---------------|:----------------|
| History Index with Impacted column | Reverse lookup: "What decisions shaped doc X?" |
| Bidirectional citations | Graph traversal: Space → Time, not just Time → Space |
| Absorption pattern | Semantic richness survives consolidation |
| Structured Archive Paths | Programmatic access to cold storage |

The History Index becomes queryable metadata. The archive becomes retrievable on-demand storage.

---

## 8. Example: Full Consolidation Workflow

### Starting State

```
.ontos-internal/logs/
├── 2025-12-01_api-design.md
├── 2025-12-03_db-selection.md
├── 2025-12-05_auth-research.md
├── 2025-12-08_auth-implementation.md
├── 2025-12-10_ui-framework.md
├── ... (18 files total)
```

### Consolidation Process

**1. Review oldest 5 logs** (Dec 1-8)

**2. Verify absorption for each:**

- `api-design`: Check `api_spec.md` — does it mention REST decision? ✓
- `db-selection`: Check `data_model.md` — does it mention PostgreSQL choice? ✗ Update it.
- `auth-research`: Check `auth_flow.md` — does it mention Firebase rejection? ✗ Update it.
- `auth-implementation`: Check `auth_flow.md` — does it mention OAuth2 details? ✓
- `ui-framework`: Check `ui_architecture.md` — does it mention React choice? ✓

**3. Update Space docs** (for db-selection and auth-research):

```markdown
<!-- In data_model.md -->
## Database
PostgreSQL for primary storage.

**Constraints:**
- SQLite rejected (concurrency limits)
- MongoDB rejected (relational requirements)

**Decision (2025-12-03):** See `decision_history.md`.
```

**4. Record in History Index:**

| Date | Slug | Event | Decision / Outcome | Impacted | Archive Path |
|:-----|:-----|:------|:-------------------|:---------|:-------------|
| 2025-12-01 | api-design | feature | REST over GraphQL (client compatibility) | api_spec | `.ontos-internal/archive/logs/2025-12-01_api-design.md` |
| 2025-12-03 | db-selection | feature | PostgreSQL over SQLite/MongoDB | data_model | `.ontos-internal/archive/logs/2025-12-03_db-selection.md` |
| 2025-12-05 | auth-research | exploration | Rejected Firebase (lock-in), session-auth (stateless req) | auth_flow | `.ontos-internal/archive/logs/2025-12-05_auth-research.md` |
| 2025-12-08 | auth-implementation | feature | OAuth2 + JWT implementation | auth_flow | `.ontos-internal/archive/logs/2025-12-08_auth-implementation.md` |
| 2025-12-10 | ui-framework | feature | React over Vue/Svelte (ecosystem) | ui_architecture | `.ontos-internal/archive/logs/2025-12-10_ui-framework.md` |

**5. Archive logs:**

```bash
mkdir -p .ontos-internal/archive/logs
mv .ontos-internal/logs/2025-12-01_api-design.md .ontos-internal/archive/logs/
mv .ontos-internal/logs/2025-12-03_db-selection.md .ontos-internal/archive/logs/
mv .ontos-internal/logs/2025-12-05_auth-research.md .ontos-internal/archive/logs/
mv .ontos-internal/logs/2025-12-08_auth-implementation.md .ontos-internal/archive/logs/
mv .ontos-internal/logs/2025-12-10_ui-framework.md .ontos-internal/archive/logs/
```

**6. Commit:**

```bash
git add -A
git commit -m "chore: consolidate sessions from 2025-12-01 to 2025-12-10

- Archived 5 session logs
- Updated data_model.md with database decision
- Updated auth_flow.md with auth research findings
- Added entries to decision_history.md"
```

### Ending State

```
.ontos-internal/logs/
├── 2025-12-11_testing-strategy.md
├── 2025-12-12_ci-setup.md
├── ... (13 files total — under threshold)

.ontos-internal/archive/logs/
├── 2025-12-01_api-design.md
├── 2025-12-03_db-selection.md
├── 2025-12-05_auth-research.md
├── 2025-12-08_auth-implementation.md
├── 2025-12-10_ui-framework.md
```

Context Map now shows 13 logs instead of 18. History Index provides discovery for archived sessions.

---

*End of v2.1 Implementation Plan*
