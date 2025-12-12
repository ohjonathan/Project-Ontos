---
id: v2_strategy
type: strategy
status: active
depends_on: [mission]
---

# Project Ontos v2.0 Strategy

*The Conscious Memory System for AI-Native Teams*

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

## The Scenario

Picture this: A new developer joins your team on Monday.

**Without Ontos:**

They clone the repo. They open Claude Code. They ask "How does auth work here?"

Claude reads the code. It guesses. It gives a technically accurate but contextually blind answer. It doesn't know you chose OAuth over SAML because your target users hate creating passwords. It doesn't know you rejected a popular auth library because of a licensing issue discovered three weeks ago. It doesn't know the auth refactor is half-done and there's a known bug in the refresh token flow.

The new developer spends their first week re-discovering context that already existed — just trapped in Slack threads, old PRs, and their teammates' heads.

**With Ontos:**

They clone the repo. They type "Activate Ontos."

Boom. They instantly have the exact same brain as you.

The context map shows them the project structure. The session logs show them WHY things are the way they are. When they ask Claude about auth, Claude loads `auth_flow.md` AND the three session logs that shaped it — including the one where you rejected that library, including the one where you documented the refresh token bug.

They're productive on day one. Not because they're smarter, but because the context transferred.

**This is the core value proposition:**

> Your project's memory shouldn't live in your head. It should live in your repo — structured, searchable, and instantly transferable to any team member, human or AI.

---

## The Core Insight: Dual Ontology

Project knowledge has two dimensions:

| Dimension | Question | Changes How? | Examples |
|-----------|----------|--------------|----------|
| **Space (Truth)** | What IS? | Through deliberate updates | Architecture, features, specs |
| **Time (History)** | What HAPPENED? | Through accumulation | Decisions, fixes, explorations |

v1.x collapsed these into one hierarchy. v2.0 separates them:

**Space Ontology (The Graph)**
- `kernel` — foundational principles
- `strategy` — goals and direction
- `product` — user-facing specs
- `atom` — technical implementation

**Time Ontology (The Timeline)**
- `log` — temporal record of a working session

The `log` type is new. It doesn't participate in the dependency hierarchy. Instead, it connects to Space through an `impacts` field — creating a bridge between "what we decided" and "what it affected."

---

## Who This Is For

### Primary: Small Teams Using AI Coding Agents

- 1-5 developers working with Claude Code, Cursor, Windsurf, or similar
- Building products where decisions matter more than code volume
- Switching between AI tools depending on task (Claude for architecture, Cursor for implementation)
- **Onboarding new team members constantly** — contractors, new hires, or just an AI agent that's never seen your codebase before

The litmus test: Can a new person (or a fresh AI session) become productive in under 10 minutes? If your context is trapped in Slack, in someone's head, or in chat logs that expired — the answer is no. Ontos makes the answer yes.

### Secondary: Solo Developers with Multiple Projects

- Juggling 2-5 projects simultaneously
- Returning to projects after weeks of dormancy
- Frustrated by re-explaining context to every AI session

### Anti-Audience

We are NOT building for:

- **Large enterprises** — they have Confluence, Notion, internal wikis with dedicated doc teams
- **Real-time collaboration** — we're git-native, not Google Docs
- **People who want zero maintenance** — Ontos requires intent; that's the point

---

## Core Philosophy

### Intent Over Automation

Ontos requires you to structure knowledge explicitly. Tag sessions with intent. Connect decisions to documents. This friction is the feature.

Why? Because **curation creates signal**. The act of deciding "this session matters" and "it impacted these documents" forces clarity. You can't capture your way to understanding — you have to think.

### Portability Over Platform

Ontos is markdown files in your repo. No database. No cloud service. No account.

This means:
- Switch AI tools freely (Claude today, Cursor tomorrow, whatever next month)
- Your knowledge travels with `git clone`
- No vendor lock-in, ever

### Shared Memory Over Personal Memory

Individual memory doesn't transfer. What you remember about the project is useless to your teammate, your contractor, or the AI agent that just opened a fresh session.

Ontos encodes knowledge at the repo level. Everyone who clones the repo gets the same brain. That's the unlock.

### Structure Over Search

We don't rely on semantic search or vector databases to surface relevant context. The context map IS the query interface — a human-readable, agent-navigable index of your project's knowledge.

Structure is explicit. Search is probabilistic. For critical decisions, explicit wins.

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

## What's Explicitly Out of Scope

### No Cloud Service

Ontos is files in your repo. No accounts, no API keys, no vendor lock-in. This is a feature, not a limitation.

### No Real-Time Sync

We're git-native. If you want Google Docs-style collaboration, use Google Docs. Ontos is for async, version-controlled knowledge.

### No Automatic Capture

We will not silently record everything. Ontos requires intent because intent creates signal. The moment you remove human judgment from the capture process, you're building a haystack, not a library.

### No Complex Querying

v2.0 doesn't include semantic search, vector databases, or natural language queries over the knowledge graph. The context map is the query interface. If you need more, you're probably building something else.

### No GUI

Ontos is markdown files and Python scripts. The interface is your editor and your AI agent. If you need a dashboard, you're not the target user.

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

---

## The Bet

We're betting that **curated knowledge beats captured data** in the AI-native workflow.

The easy path is to record everything and let search sort it out later. We're taking the harder path: record what matters, make it findable by structure, require human judgment in the loop.

Why we think this wins:

1. **Teams need shared context** — individual memory doesn't transfer; repo-level memory does
2. **Signal degrades over time** — noise compounds; curation doesn't
3. **AI agents improve** — they'll get better at navigating structured knowledge faster than they'll get better at extracting signal from noise
4. **Intent forces clarity** — the act of documenting a decision makes you understand it better

If we're right, Ontos becomes the standard way teams encode knowledge for AI-native development.

If we're wrong, we've still built a solid documentation system that works without AI.

---

## The Tagline

> **Project Ontos: The conscious memory system for AI-native teams.**
>
> *Clone the repo. Activate Ontos. Instant shared brain.*
>
> Truth + History. Portable. Version-controlled. Intent over automation.
