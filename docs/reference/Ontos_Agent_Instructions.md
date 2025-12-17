---
id: ontos_agent_instructions
type: kernel
status: active
depends_on: [ontos_manual]
---

# Ontos Agent Instructions

## Commands

### "Ontos" (Activate)
1. Check for `Ontos_Context_Map.md`
2. If missing: `python3 .ontos/scripts/ontos_generate_context_map.py`
3. Read map, identify relevant IDs for user's request
4. **Check consolidation status (prompted/advisory modes only):**
   - Context map generation now shows consolidation warning when needed
   - In automated mode, consolidation happens automatically on commit
5. Read ONLY those files
6. print("Loaded: [id1, id2]")

### "Query Ontos"
1. `python3 .ontos/scripts/ontos_query.py --depends-on [id]` (Check dependencies)
2. `python3 .ontos/scripts/ontos_query.py --concept [tag]` (Find by concept)
3. `python3 .ontos/scripts/ontos_query.py --stale 30` (Find stale docs)

### "Archive Ontos" (End Session)

**Step 1: Check for auto-generated log first (v2.4)**
```bash
python3 .ontos/scripts/ontos_end_session.py --enhance
```

Exit codes:
- `0` — Auto-generated log found, displayed for enrichment
- `1` — No auto-generated log found, proceed to Step 2
- `2` — Log already enriched (status: active), nothing to do

**Step 2a: If --enhance found a log (exit 0)**
1. Read the displayed log content
2. Fill in Goal, Key Decisions, Alternatives Considered
3. Add relevant concepts (check `Common_Concepts.md`)
4. Verify impacts are correct
5. Change `status: auto-generated` to `status: active`
6. Commit the enriched log

**Step 2b: If no auto-generated log (exit 1)**
1. Run: `python3 .ontos/scripts/ontos_end_session.py -e <type> -s "Agent Name"`
2. Read generated log and fill in sections
3. Commit

Event types: `feature`, `fix`, `refactor`, `exploration`, `chore`, `decision`

**Pre-push blocking:** In `prompted` mode, push fails without archived session. In `automated` mode, logs are created automatically.

**RULE:** Never use `git push --no-verify` without explicit user approval.

### "Maintain Ontos" (Weekly)
1. `python3 .ontos/scripts/ontos_maintain.py`
2. This runs four steps:
   - Migrate untagged files
   - Regenerate context map
   - Consolidate old logs (if `AUTO_CONSOLIDATE=True`)
   - **Review proposals (v2.6.1)** — prompts to graduate implemented proposals
3. Fix any errors reported
4. Commit context map if changed

### "Update Ontos"
1. `python3 .ontos/scripts/ontos_update.py`

## Type Hierarchy

| Type | Rank | Depends On |
|------|------|-----------|
| kernel | 0 | nothing |
| strategy | 1 | kernel |
| product | 2 | kernel, strategy |
| atom | 3 | kernel, strategy, product, atom |
| log | 4 | uses `impacts`, not `depends_on` |

Rule: Dependencies flow DOWN (atom → product → strategy → kernel).

## Validation Errors

| Error | Fix |
|-------|-----|
| `[BROKEN LINK]` | Create referenced doc or remove from depends_on |
| `[CYCLE]` | Remove one dependency in the loop |
| `[ORPHAN]` | Add to another doc's depends_on |
| `[ARCHITECTURE]` | Lower-rank can't depend on higher-rank |


## Historical Recall

The `archive/` directory is excluded from the Context Map to save tokens.

To understand rationale behind past decisions:

1. **Read** `docs/strategy/decision_history.md`
2. **Locate** the relevant entry by date, slug, or impacted document
3. **Retrieve** — You are authorized to read the file at the Archive Path, even though it's not in the Context Map


## Proposal Awareness (v2.6+)

### Finding Proposals
Proposals live in `strategy/proposals/`. Check for:
- **Draft proposals** — In progress, may be discussed in context
- **Active proposals** — Approved, should be in `strategy/` (not `proposals/`)

### Reviewing a Proposal
When user asks to review a proposal:
1. Read the proposal document
2. Identify the problems it solves
3. Evaluate against existing architecture
4. Suggest improvements or identify risks

### Recalling Rejected Ideas
Rejected proposals are **excluded by default** to save tokens. To recall:
```bash
python3 .ontos/scripts/ontos_generate_context_map.py --include-rejected
```

**Why rejected proposals matter:**
- Avoid re-analyzing the same ideas
- Understand why something wasn't done
- Revisit if circumstances change

### Creating New Proposals
When user wants to propose something:
1. Create in `strategy/proposals/` with `status: draft`
2. Link to relevant strategy docs via `depends_on`
3. Include clear problem statement and proposed solution

### Graduating Proposals (v2.6.1)
When a proposal is implemented:

**Automatic detection:** Archive Ontos detects implementation based on:
- Branch name matches proposal version (e.g., `feat/v2.6-*`)
- Session impacts a proposal document

**Graduation prompt:**
```
💡 Detected: This session may implement proposal 'v2_6_proposals'
   (Branch matches version 2.6)
   Graduate to strategy/? [y/N]: y

   ✅ Graduated: v2_6_proposals_and_tooling.md
      proposals/v2.6/ → strategy/v2.6/
      Status: draft → active
```

**Maintain Ontos fallback:** If graduation was missed, Maintain Ontos prompts for any draft proposals where ONTOS_VERSION matches.

**Example:**
```
User: "Why did we choose OAuth2?"

Agent:
1. Reads decision_history.md
2. Finds: "2025-12-10 | auth-migration | Chose OAuth2..."
3. Reads .ontos-internal/archive/logs/2025-12-10_auth-migration.md
4. Responds with sourced explanation
```

**Rule:** Only read archived files explicitly listed in `decision_history.md` or requested by the user.

---

## Auto-Generated Logs (v2.4)

In `automated` mode, logs are created automatically on push with `status: auto-generated`.

**Identifying auto-generated logs:**
```yaml
---
status: auto-generated  # ← Needs enrichment
branch: feat/my-feature
---
```

**Session Appending:** Multiple pushes on the same branch in one day append to the same log file. This prevents "ghost log" pollution.

**Enrichment workflow:**
1. Run `--enhance` to find the log
2. Fill in the human context (Goal, Decisions, Alternatives)
3. Change status to `active`
4. Commit

**Lint warnings:** The context map generator flags auto-generated logs:
```
[LINT] log_20251215_feature: Auto-generated log needs enrichment
```

---

## Tagging Discipline (v3.0 Readiness)

Quality tagging now enables intelligent querying later.

### Concepts

1. **Check first:** Read `docs/reference/Common_Concepts.md`
2. **Prefer existing:** Use standard vocabulary over synonyms
3. **Be specific:** 2-4 concepts per log, not 10 vague ones
4. **Be consistent:** If you used `auth` before, don't switch to `authentication`

**Example:**
```yaml
# Good
concepts: [auth, api]

# Bad - too many, inconsistent vocabulary
concepts: [authentication, login, oauth, jwt, security, backend, api-design]
```

### Impacts

1. **Never empty:** Every session impacts *something* — find it
2. **Use suggestions:** Run `ontos_end_session.py --suggest-impacts`
3. **Include indirect:** If you modified code that `api_spec.md` documents, include `api_spec`
4. **Think broadly:** Design discussions impact strategy docs, not just atoms

**Example:**
```yaml
# Good - specific and complete
impacts: [auth_flow, api_spec, user_model]

# Bad - lazy or incomplete
impacts: []
```

### Alternatives Considered

1. **Always fill:** Document what you *didn't* do
2. **Include rationale:** "Rejected X because Y"
3. **Name names:** "Considered Firebase, PostgreSQL, SQLite" not "considered options"
4. **Be honest:** If you didn't consider alternatives, say "No alternatives evaluated"

**Example:**
```markdown
## 3. Alternatives Considered
- Considered Firebase Auth — rejected due to vendor lock-in concerns
- Considered session-based auth — rejected, need stateless for horizontal scaling
- Evaluated Auth0 — too expensive for current stage
```

## Changelogs

- `Ontos_CHANGELOG.md` — Only for Ontos tooling changes
- `CHANGELOG.md` — For project using Ontos (use `--changelog` flag)

## Context Selection

1. Start with IDs matching user's request
2. Follow `depends_on` chains upward
3. Stop at kernel or sufficient context
4. Prefer fewer, more relevant docs
