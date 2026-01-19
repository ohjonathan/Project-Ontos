---
id: ontos_philosophy_and_ontology
type: kernel
status: active
depends_on: [mission, philosophy, constitution]
concepts: [ontology, philosophy, architecture, curation, documentation]
---

# Research Briefing: Project Ontos Conceptuality & Philosophy

**Version:** 2.0
**Date:** 2026-01-17
**Ontos Version:** 3.0.2
**Subject:** Comprehensive Analysis of Ontos's Design Philosophy and Ontology Architecture

---

## 1. The Core Problem: Context Death

Project Ontos addresses three critical failures in modern AI-assisted development:

| Problem | Description |
|---------|-------------|
| **AI Amnesia** | You explain your architecture to Claude, then again to ChatGPT, then again to Cursor. Each tool starts from zero. |
| **Prototype Graveyards** | You build fast in Streamlit, make dozens of product decisions, then rewrite in Next.js. The code is new; the decisions are lost in old chat logs. |
| **Tribal Knowledge** | Your project's "why" lives in Slack threads, abandoned docs, and people's heads. New collaborators (human or AI) have to rediscover everything. |

**The Common Thread:** Context isn't portable.

---

## 2. The Four Philosophical Pillars

### 2.1 Intent Over Automation

> "Ontos requires you to structure knowledge explicitly. Tag sessions with intent. Connect decisions to documents. This friction is the feature."

Rather than automatically capturing everything and hoping search finds it later, Ontos demands **deliberate curation**. The act of deciding "this session matters" and "it impacted these documents" forces clarity.

**Important distinction:** "Friction" here means **cognitive work** (deciding what matters), NOT **mechanical busywork** (typing YAML). Ontos automates the ceremony while requiring the curation. See Section 3 for details.

### 2.2 Portability Over Platform

Ontos is markdown files in your repo. No database. No cloud service. No account.
- Switch AI tools freely (Claude today, Cursor tomorrow)
- Your knowledge travels with `git clone`
- Zero vendor lock-in, forever

### 2.3 Shared Memory Over Personal Memory

Individual memory doesn't transfer. What you remember is useless to your teammate, contractor, or the AI agent that just opened a fresh session. Ontos encodes knowledge at the **repo level**. Everyone who clones the repo gets the same brain.

**Zero-ceremony handoffs:** Ontos travels with git. When you share a repo, you share the brain:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PROJECT HANDOFF: ZERO CEREMONY                            │
│                                                                              │
│    DEVELOPER A                              DEVELOPER B (or AI Agent)        │
│    ───────────                              ─────────────────────────        │
│                                                                              │
│    git push origin main ───────────────────► git clone repo                  │
│                                              │                               │
│                                              ▼                               │
│    That's it.                               Instant access to:               │
│    No export.                               • Context map                    │
│    No sync.                                 • All documentation              │
│    No invite.                               • Decision history               │
│    No account.                              • Session logs                   │
│                                             • Dependency graph               │
│                                                                              │
│    ════════════════════════════════════════════════════════════════════════  │
│    The knowledge transfer IS the git workflow developers already use.        │
│    No new tools. No new habits. No ceremony.                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.4 Structure Over Search

Ontos doesn't rely on semantic search or vector databases. The context map IS the query interface - a human-readable, agent-navigable index.

> "Structure is explicit; search is probabilistic. For critical decisions, explicit wins."

---

## 3. Curation vs Ceremony: The Critical Distinction

Ontos demands **curation** but eliminates **ceremony**. This distinction is fundamental to the design philosophy.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CURATION vs CEREMONY                                   │
├─────────────────────────────────┬───────────────────────────────────────────┤
│           CURATION (We Want)    │         CEREMONY (We Eliminate)           │
│         Human judgment required │         Mechanical busywork               │
├─────────────────────────────────┼───────────────────────────────────────────┤
│                                 │                                           │
│  "This session was about auth"  │  Typing `type: log` in YAML               │
│  "This doc impacts the API spec"│  Running `ontos map` manually             │
│  "We chose OAuth over SAML because"│  Formatting frontmatter correctly     │
│  "This design is ready for review"│  Creating scaffold files                │
│  "Consolidate logs older than 30d"│  Generating the context map             │
│                                 │                                           │
│  ──────────────────────────────  │  ──────────────────────────────          │
│  HUMAN DECIDES:                 │  MACHINE EXECUTES:                        │
│  • What matters                 │  • The mechanics of recording it          │
│  • What it relates to           │  • Validation and formatting              │
│  • Why a decision was made      │  • Graph updates and maintenance          │
│  • When something is complete   │  • Routine checks and fixes               │
│                                 │                                           │
└─────────────────────────────────┴───────────────────────────────────────────┘
```

### Examples: What Gets Curated vs Automated

| Action | Curation (Human) | Ceremony (Automated) |
|--------|------------------|----------------------|
| **End a session** | "This was a feature session about auth that impacted 3 docs" | Generate log filename, scaffold frontmatter, validate impacts exist |
| **Create a document** | "This is a product spec for user onboarding" | Auto-assign L0 scaffold, infer id from filename, set default status |
| **Promote to L2** | "This doc is now production-ready" | Validate all L2 requirements met, update curation_level field |
| **Weekly maintenance** | "Set rule: consolidate logs > 30 days" | Run validation, archive old logs, report issues, regenerate map |
| **Project handoff** | "Share the repo with new team member" | Nothing - it's just `git clone` (zero ceremony) |

### The Librarian's Wager, Clarified

The "Librarian's Wager" trades **intentional friction** (curation) for **higher signal**. But it does NOT mean manual busywork:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     THE LIBRARIAN'S WAGER (Clarified)                        │
│                                                                              │
│    We trade:  CURATION EFFORT    ──►   DETERMINISTIC CONTEXT                 │
│                                                                              │
│    NOT:       CEREMONY / BUSYWORK                                            │
│                                                                              │
│    ────────────────────────────────────────────────────────────────────────  │
│                                                                              │
│    GOOD FRICTION (Curation):         BAD FRICTION (Ceremony):                │
│    ✓ Deciding "this matters"         ✗ Typing YAML by hand                   │
│    ✓ Choosing relationships          ✗ Running scripts manually              │
│    ✓ Writing decision rationale      ✗ Remembering command flags             │
│    ✓ Reviewing before promotion      ✗ Formatting files correctly            │
│                                                                              │
│    The friction we want is COGNITIVE (thinking about what matters).          │
│    The friction we eliminate is MECHANICAL (repetitive actions).             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### How Ontos Automates Ceremony

| Ceremony | How Ontos Automates It |
|----------|------------------------|
| YAML frontmatter | L0 scaffolds auto-generated; fields inferred from context |
| Context map generation | `ontos map` runs automatically (hooks, maintain) |
| Log creation | Filename, date, and scaffold auto-generated from session |
| Validation | Rules are set once; `ontos doctor` runs them automatically |
| Consolidation | Configure once (`--days 30`); runs via `ontos maintain` |
| Graph maintenance | Dependency validation automatic; broken links detected |

**The user's job:** Decide what matters and why.
**The tool's job:** Handle the mechanics of recording and maintaining it.

---

## 4. The Dual Ontology: Space & Time (The Two Dimensions)

Project knowledge exists in two orthogonal dimensions that interact through a bridge mechanism:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              THE DUAL ONTOLOGY                               │
├─────────────────────────────────┬───────────────────────────────────────────┤
│     SPACE (Truth Graph)         │          TIME (History Timeline)          │
│     "What IS the system?"       │          "What HAPPENED?"                 │
├─────────────────────────────────┼───────────────────────────────────────────┤
│                                 │                                           │
│  ┌─────────┐                    │         ┌─────────┐                       │
│  │ kernel  │ ◄── Foundation     │    t1   │  log    │ "Added auth"          │
│  └────┬────┘                    │         └────┬────┘                       │
│       │ depends_on              │              │                            │
│       ▼                         │              │ impacts                    │
│  ┌─────────┐                    │              │                            │
│  │strategy │ ◄── Direction      │              ▼                            │
│  └────┬────┘                    │    ┌─────────────────────┐                │
│       │ depends_on              │    │ auth_architecture   │◄───────────────┤
│       ▼                         │    └─────────────────────┘                │
│  ┌─────────┐                    │                                           │
│  │ product │ ◄── User-facing    │         ┌─────────┐                       │
│  └────┬────┘                    │    t2   │  log    │ "Fixed OAuth bug"     │
│       │ depends_on              │         └────┬────┘                       │
│       ▼                         │              │ impacts                    │
│  ┌─────────┐                    │              ▼                            │
│  │  atom   │ ◄── Technical      │    ┌─────────────────────┐                │
│  └─────────┘                    │    │ oauth_integration   │◄───────────────┤
│                                 │    └─────────────────────┘                │
│  Changes: Deliberate updates    │    Changes: Accumulation over time        │
│  Structure: Acyclic DAG         │    Structure: Linear timeline             │
│  Field: depends_on              │    Field: impacts                         │
│                                 │                                           │
└─────────────────────────────────┴───────────────────────────────────────────┘
```

### How Space and Time Interact: The Bridge

```
                    ┌─────────────────────────────────────────┐
                    │           SPACE (Truth)                  │
                    │                                          │
                    │   mission ◄── philosophy                 │
                    │      │                                   │
                    │      ▼                                   │
                    │   v3_roadmap ◄── api_spec                │
                    │      │              │                    │
                    │      ▼              ▼                    │
                    │   auth_flow ◄── oauth_impl               │
                    │                                          │
                    └──────────▲──────────▲────────────────────┘
                               │          │
                               │ impacts  │ impacts
                               │          │
┌──────────────────────────────┼──────────┼────────────────────────────────────┐
│                    TIME (History)                                             │
│                                                                               │
│  ═══════════════════════════════════════════════════════════════════════►    │
│  │         │           │           │           │           │                 │
│  t1        t2          t3          t4          t5          t6                │
│  │         │           │           │           │           │                 │
│ ┌┴───────┐┌┴─────────┐┌┴─────────┐┌┴─────────┐┌┴─────────┐┌┴───────────┐    │
│ │session │││session  │││session  │││session  │││session  │││session    │    │
│ │"init"  │││"auth"   │││"oauth"  │││"bug fix"│││"refactor││"v3 plan"  │    │
│ └────────┘│└─────────┘│└─────────┘│└─────────┘│└─────────┘│└───────────┘    │
│           │           │           │           │           │                  │
│           └───────────┴───────────┴───────────┴───────────┘                  │
│                    All these sessions IMPACTED                               │
│                    documents in the Space graph                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Concrete Example: A Day's Work

```
SESSION: "Implement OAuth2 login"
──────────────────────────────────────────────────────────────────────────────

BEFORE SESSION:                          AFTER SESSION:

Space Graph (unchanged structure):       Log Created (Time):

┌──────────────┐                         ---
│   mission    │                         id: 2026-01-14_oauth_impl
│   (kernel)   │                         type: log
└──────┬───────┘                         event_type: feature
       │                                 concepts: [auth, api, security]
       ▼                                 impacts:
┌──────────────┐                           - auth_architecture    ◄─── UPDATED
│ v3_roadmap   │                           - oauth_integration    ◄─── CREATED
│  (strategy)  │                           - api_spec             ◄─── UPDATED
└──────┬───────┘                         ---
       │
       ▼                                 ## Summary
┌──────────────┐                         Implemented OAuth2 flow with
│  auth_flow   │  ◄─── impacted          Google and GitHub providers.
│  (product)   │
└──────┬───────┘                         ## Changes
       │                                 - Added OAuth provider abstraction
       ▼                                 - Implemented token refresh logic
┌──────────────┐                         - Updated API authentication middleware
│ oauth_impl   │  ◄─── impacted/created
│   (atom)     │                         ## Decisions
└──────────────┘                         - Chose OAuth2 over SAML (simpler)
                                         - Storing tokens in HTTP-only cookies

The log records WHAT HAPPENED            The Space docs record WHAT IS TRUE
(temporal, immutable)                    (current state, updatable)
```

### Why Two Dimensions?

| Aspect | Space (depends_on) | Time (impacts) |
|--------|-------------------|----------------|
| **Direction** | Downward (atom → product → strategy → kernel) | Outward (log → any document) |
| **Cardinality** | Many-to-many within hierarchy | One-to-many (log impacts docs) |
| **Mutability** | Documents updated over time | Logs are immutable records |
| **Purpose** | "What should I read to understand X?" | "Why did X change?" |
| **Query** | `ontos query --deps auth_flow` | `ontos query --history auth_flow` |

---

## 5. The Ontology Architecture

### 5.1 Document Type Hierarchy (Ranked)

Dependencies flow **DOWN** the hierarchy. Higher-rank documents depend on lower-rank documents, ensuring an **acyclic graph by construction**.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SPACE ONTOLOGY: THE TRUTH GRAPH                      │
│                                                                              │
│    RANK 0                         ┌─────────────────────┐                    │
│    KERNEL                         │      mission        │                    │
│    (Foundational)                 │    philosophy       │                    │
│                                   │    constitution     │                    │
│                                   └─────────┬───────────┘                    │
│                                             │                                │
│                        ┌────────────────────┼────────────────────┐           │
│                        │                    │                    │           │
│                        ▼                    ▼                    ▼           │
│    RANK 1        ┌───────────┐        ┌───────────┐        ┌───────────┐    │
│    STRATEGY      │ v3_roadmap│        │ market_fit│        │ team_goals│    │
│    (Direction)   └─────┬─────┘        └─────┬─────┘        └─────┬─────┘    │
│                        │                    │                    │           │
│                        ▼                    ▼                    ▼           │
│    RANK 2        ┌───────────┐        ┌───────────┐        ┌───────────┐    │
│    PRODUCT       │ auth_flow │        │ dashboard │        │onboarding │    │
│    (User-facing) └─────┬─────┘        └─────┬─────┘        └─────┬─────┘    │
│                        │                    │                    │           │
│              ┌─────────┼─────────┐          │          ┌─────────┼─────────┐ │
│              ▼         ▼         ▼          ▼          ▼         ▼         ▼ │
│    RANK 3  ┌────┐   ┌────┐   ┌────┐     ┌────┐     ┌────┐   ┌────┐   ┌────┐│
│    ATOM    │oauth│   │jwt │   │rbac│     │charts│   │wizard│  │forms│  │api ││
│    (Tech)  └────┘   └────┘   └────┘     └────┘     └────┘   └────┘   └────┘│
│                                                                              │
│    ════════════════════════════════════════════════════════════════════════  │
│    ARROWS (▼) = depends_on relationship                                      │
│    Reading: "oauth depends on auth_flow depends on v3_roadmap depends on..." │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         TIME ONTOLOGY: THE HISTORY TIMELINE                  │
│                                                                              │
│    RANK 4        ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐      │
│    LOG           │ t1  │  │ t2  │  │ t3  │  │ t4  │  │ t5  │  │ t6  │      │
│    (Temporal)    │     │  │     │  │     │  │     │  │     │  │     │      │
│                  │init │  │auth │  │oauth│  │ fix │  │test │  │docs │      │
│                  └──┬──┘  └──┬──┘  └──┬──┘  └──┬──┘  └──┬──┘  └──┬──┘      │
│                     │       │        │        │        │        │          │
│                     │       │        │        │        │        │          │
│    ─────────────────┴───────┴────────┴────────┴────────┴────────┴────────► │
│                              impacts (connects to Space)          time      │
│                                                                              │
│    NO depends_on between logs - they are independent temporal snapshots     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 The Complete Picture: Space + Time + Concepts

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    THE THREE AXES OF ONTOS KNOWLEDGE                         │
│                                                                              │
│                                   CONCEPTS                                   │
│                                   (semantic)                                 │
│                                      │                                       │
│                                      │ concepts: [auth, api, security]       │
│                                      │                                       │
│                                      ▼                                       │
│                              ┌───────────────┐                               │
│                              │               │                               │
│                              │   DOCUMENT    │                               │
│                              │               │                               │
│                              └───────────────┘                               │
│                             ╱                 ╲                              │
│                            ╱                   ╲                             │
│                           ╱                     ╲                            │
│              depends_on  ╱                       ╲  impacts                  │
│              (structural)                         (temporal)                 │
│                         ╱                           ╲                        │
│                        ▼                             ▼                       │
│                                                                              │
│                    SPACE                          TIME                       │
│                 (Truth Graph)                  (History)                     │
│                                                                              │
│  ═══════════════════════════════════════════════════════════════════════════ │
│                                                                              │
│  THREE WAYS TO NAVIGATE THE KNOWLEDGE GRAPH:                                 │
│                                                                              │
│  1. SPACE: "What does this depend on?"                                       │
│     ontos query --deps oauth_impl                                            │
│     → oauth_impl → auth_flow → v3_roadmap → mission                          │
│                                                                              │
│  2. TIME: "What sessions touched this?"                                      │
│     ontos query --history auth_flow                                          │
│     → 2026-01-14_oauth_impl, 2026-01-10_auth_design, ...                     │
│                                                                              │
│  3. CONCEPTS: "What else discusses auth?"                                    │
│     ontos query --concept auth --hops 2                                      │
│     → auth_flow, oauth_impl, jwt_strategy, rbac_spec, ...                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Why This Design:**
- Strict rank ordering **prevents cycles** by construction
- Higher-level documents are more stable (kernel changes rarely)
- Technical details (atoms) can reference any conceptual level
- Logs bridge Time to Space without polluting the dependency graph
- Concepts enable cross-cutting queries without structural coupling

### 5.3 Frontmatter Schema Fields

**Required Fields (All Documents):**
- `id` - Unique identifier in snake_case (immutable)
- `type` - Document type from the 5-tier hierarchy
- `status` - Lifecycle state

**Optional Fields:**

| Field | Type | Applies To | Purpose |
|-------|------|------------|---------|
| `depends_on` | list | strategy, product, atom | IDs this document depends on |
| `impacts` | list | log | Document IDs modified in the session |
| `event_type` | enum | log | Session classification (feature, fix, refactor, etc.) |
| `concepts` | list | all | Abstract concepts for cross-cutting discovery |
| `describes` | list | atom | Source files this doc describes |
| `curation_level` | enum | all | L0 (scaffold), L1 (stub), L2 (full) |

---

## 6. The Three-Tier Curation Model

Ontos uses **progressive formalization** - documents can start minimal and be promoted:

| Level | Name | Status | Validation | Use Case |
|-------|------|--------|------------|----------|
| **L0** | Scaffold | `scaffold` | Minimal (id + type only) | Auto-generated placeholders |
| **L1** | Stub | `pending_curation` | Relaxed (type + goal, no deps required) | User provides objective |
| **L2** | Full | `draft`/`active`/etc | Strict (complete deps + concepts) | Production-ready |

**Promotion Rules:**
- L0 → L1: User specifies goal/purpose
- L1 → L2: User adds dependencies + concepts
- L2 requires `depends_on` for non-kernel/non-log types

**Why This Design:**
- **Gradual completeness:** Documents can start incomplete and improve
- **Quality assurance:** L2 enforces architectural constraints
- **Flexibility:** L0/L1 for exploration, L2 for production

---

## 7. Status Workflow

| Status | Applies To | Meaning |
|--------|------------|---------|
| **draft** | strategy, product, atom | Work in progress |
| **active** | All types | Current truth (authoritative) |
| **deprecated** | kernel, strategy, product, atom | Past truth (superseded) |
| **rejected** | strategy | Considered but NOT approved |
| **complete** | strategy, atom | Finished work |
| **scaffold** | All | L0 placeholder |
| **pending_curation** | All | L1 stub |
| **archived** | log | Historical record |

---

## 8. Concept Vocabulary

The `concepts` field enables semantic tagging for cross-document discovery:

**Core Technical Domains:**
- `auth`, `api`, `db`, `ui`, `schema`

**Process Domains:**
- `devops`, `testing`, `perf`, `security`, `docs`

**Workflow Concepts:**
- `cleanup`, `config`, `workflow`

**Convention:** Use existing terms over synonyms to ensure graph connectivity.

---

## 9. Constitutional Invariants

The Constitution establishes rules Ontos will **never compromise** on:

1. **Minimal Dependencies** - Core logic stdlib-only; 2 runtime deps (`pyyaml`, `tomli` for Python <3.11)
2. **System Package** - Distribution via PyPI (`pip install ontos`)
3. **Local-First** - Data in repos, logic in the system
4. **Functional Core** - Logic separated from I/O
5. **The Librarian's Wager** - Trade higher friction (manual curation) for higher signal
6. **Deterministic Purity** - Reject probabilistic retrieval (vector/semantic search)

---

## 10. The Single Source of Truth

**File:** `ontos/core/ontology.py`

As of v3.0.2, this module is the **canonical definition** for:
- `TYPE_DEFINITIONS` - All 5 document types with ranks and allowed dependencies
- `FIELD_DEFINITIONS` - All frontmatter fields with types and validation rules

All other modules import from this single source.

---

## 11. The Bet

Ontos is betting that **curated knowledge beats captured data** in AI-native workflows:

1. Teams need shared context - individual memory doesn't transfer
2. Signal degrades over time - noise compounds; curation doesn't
3. AI agents improve - they'll navigate structured knowledge faster than extracting signal from noise
4. Intent forces clarity - documenting a decision makes you understand it better

---

## 12. Key Reference Files

| Document | Path |
|----------|------|
| Philosophy | `.ontos-internal/kernel/philosophy.md` |
| Mission | `.ontos-internal/kernel/mission.md` |
| Constitution | `.ontos-internal/kernel/constitution.md` |
| Ontology (Single Source of Truth) | `ontos/core/ontology.py` |
| Type Definitions | `ontos/core/types.py` |
| Curation Logic | `ontos/core/curation.py` |
| Schema Versioning | `ontos/core/schema.py` |
| Graph Operations | `ontos/core/graph.py` |
| Concept Vocabulary | `.ontos-internal/reference/Common_Concepts.md` |

---

## 13. Related Analysis Documents

For additional context and complementary perspectives, see:

| Document | Focus Area |
|----------|------------|
| [`Ontos-Strategic-Analysis-Codex.md`](./../analysis/Ontos-Strategic-Analysis-Codex.md) | Market fit, value propositions, strategic roadmap |
| [`Ontos-Technical-Architecture-Map-Codex.md`](./../analysis/Ontos-Technical-Architecture-Map-Codex.md) | Technical implementation details, module structure |

---

## 14. The Tagline

> **Project Ontos: The conscious memory system for AI-native teams.**
>
> *Clone the repo. Activate Ontos. Instant shared brain.*
>
> **Truth + History. Portable. Version-controlled. Intent over automation.**

---

*End of Research Briefing*
