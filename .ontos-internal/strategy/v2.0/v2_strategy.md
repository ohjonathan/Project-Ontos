---
id: v2_strategy
type: strategy
status: deprecated
depends_on: [philosophy]
---

> **DEPRECATED:** This is the v2.x strategy document. For current strategy, see [V3.0-Strategy-Decisions-Final.md](../v3.0/V3.0-Strategy-Decisions-Final.md).

# Project Ontos v2.0 Strategy

*V2 Implementation: From Knowledge Graph to Conscious Memory*

---

## Why v2.0?

Ontos v1.x solved the **AI Amnesia** problem: context dying every time you switch tools or start a new session. It did this by creating a knowledge graph of your documentation — tagged markdown files with explicit dependencies.

But v1.x had a blind spot: **it only captured what IS, not how you got there.**

Session logs existed, but they were second-class citizens. Typed as `atom`, dumped in `/logs/`, structurally identical to technical specs. The system couldn't distinguish between "this is our API design" and "this is why we chose REST over GraphQL last Tuesday."

That distinction matters. When a new team member (human or AI) asks "why is the auth system like this?", they need two things:

1. **The Truth** — what the auth system IS (architecture docs)
2. **The History** — what decisions SHAPED it (session logs)

v1.x gave them the first. v2.0 gives them both.

---

## What v2.0 Delivers

### Phase 1: Structure (v2.0.x)

**Unified Initialization**

v1.x had two separate steps: "install" (copy files) and "initiate" (create structure). v2.0 combines them into one:

```bash
# v1.x (two steps)
cp -r /path/to/ontos/.ontos .
python3 .ontos/scripts/ontos_initiate.py

# v2.0 (one step)
python3 ontos_init.py
```

One command. Project ready. Like `git init` for your documentation.

**The Schema**

New `type: log` with extended frontmatter:

```yaml
---
id: log_20251210_auth_refactor
type: log
status: active
event_type: refactor
concepts: [auth, oauth]
impacts: [auth_flow, api_spec]
---
```

Event types: `feature`, `fix`, `refactor`, `exploration`, `chore`

**Auto-Suggested Impacts**

When archiving a session, the script parses git diff and suggests which doc IDs were likely impacted. Human confirms or edits. Friction down, accuracy up.

### Phase 2: Visibility (v2.1.x)

**Token Estimates**

Every entry in the context map shows approximate token count:

```markdown
- **api_spec** (api_spec.md) ~2,100 tokens
```

Agents can budget context intelligently.

**Timeline Section**

The context map gains a fourth section — recent session history:

```markdown
## 4. Recent Timeline
- **2025-12-10** [refactor] Auth Refactor → `auth_flow`, `api_spec`
- **2025-12-09** [exploration] Database Options → `data_model`
```

### Phase 3: Intelligence (v2.2.x)

**Summary Generation**

New script `ontos_summarize.py` generates 50-word summaries for documents, stored in frontmatter. Agents read summaries first, expand full docs only when needed.

**Auto-Activation**

Agents silently check for `Ontos_Context_Map.md` at session start. No more requiring "Activate Ontos" — it's default behavior.

**Archival Enforcement**

Pre-commit hook that checks for session log before allowing commit. Human stays in loop, but with a nudge.

---

## Success Criteria

### For Users

1. **Onboarding time drops** — new team member goes from "clone" to "productive" in under 10 minutes
2. **Context re-establishment drops** — returning to a dormant project requires reading the context map, not re-explaining to Claude
3. **Decision archaeology works** — asking "why is X like this?" returns actual historical context, not guesses

### For the Project

1. **Adoption signal** — GitHub stars, forks, issues from real users (not just curiosity clicks)
2. **Retention signal** — users who adopt v2.0 stay on it (vs churning back to ad-hoc methods)
3. **Ecosystem signal** — other tools start supporting Ontos-style frontmatter (long-term)
