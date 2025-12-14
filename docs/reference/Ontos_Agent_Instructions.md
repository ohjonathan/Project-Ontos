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
4. Read ONLY those files
5.    print("Loaded: [id1, id2]")

### "Query Ontos"
1. `python3 .ontos/scripts/ontos_query.py --depends-on [id]` (Check dependencies)
2. `python3 .ontos/scripts/ontos_query.py --concept [tag]` (Find by concept)
3. `python3 .ontos/scripts/ontos_query.py --stale 30` (Find stale docs)

### "Archive Ontos" (End Session)
2. Run: `python3 .ontos/scripts/ontos_end_session.py -e <type> -s "Agent Name"`
3. Read generated log. If template is adaptive, fill only the sections present.
4. If prompted for missing impacts/concepts, provide them.
5. Commit.

Event types: `feature`, `fix`, `refactor`, `exploration`, `chore`, `decision`

**Pre-push blocking:** Push fails without archived session. Run Archive Ontos first.

**RULE:** Never use `git push --no-verify` without explicit user approval. If the hook blocks you, archive the session — don't bypass.

### "Maintain Ontos" (Weekly)
1. `python3 .ontos/scripts/ontos_maintain.py`
2. Fix any errors reported by the script.
3. Commit context map if changed.

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
