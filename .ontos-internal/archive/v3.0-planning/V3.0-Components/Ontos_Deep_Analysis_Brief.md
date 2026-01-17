---
id: ontos_deep_analysis_brief
type: atom
status: draft
depends_on: [philosophy, mission]
concepts: [analysis, summary, marketing, v3]
---

# Project Ontos: Deep Analysis Brief

**Purpose:** Comprehensive summary for external AI analysis (marketing fit, V3.0 strategy, collaboration, improvement opportunities)
**Generated:** 2026-01-08
**Current Version:** 2.9.5
**Codebase:** ~11,500 lines Python (25+ scripts), 132 tests, MIT licensed

---

## I. CORE IDENTITY

### The Problem: "Context Death"

Context dies in three ways in AI-assisted development:

1. **AI Amnesia** — Each tool (Claude, ChatGPT, Cursor, Gemini) starts from zero. You re-explain architecture endlessly.
2. **Prototype Graveyards** — Rewrite from Streamlit to Next.js; the code is new, but product decisions are lost in old chat logs.
3. **Tribal Knowledge** — Your project's "why" lives in Slack threads, abandoned docs, and your head.

**Root cause:** Context isn't portable between tools, sessions, or team members.

### The Solution: Portable Knowledge Graph

Ontos turns documentation into a **structured knowledge graph** stored as markdown files with YAML frontmatter:

```yaml
---
id: pricing_strategy
type: strategy
status: active
depends_on: [target_audience, mission]
concepts: [monetization, growth]
---
```

A script generates `Ontos_Context_Map.md` — a navigable index any AI can read. The map shows document hierarchy, dependencies, curation levels, token estimates, and recent changes.

### Mission Statement

> "Eliminate context death in AI-assisted development. Enable LLMs to recover project context with minimal token expense. Create shared memory that survives tool switches, session resets, and team changes."

### The Name

From Greek *ontos*, meaning "being" — the root of ontology. Your documentation gains existence as a persistent knowledge graph, not ephemeral chat history.

---

## II. CORE PHILOSOPHY

### 1. Curated, Not Automatic

The developer (or responsible agent) acts as "librarian," explicitly curating what enters the graph. We do NOT dump everything into a vector database hoping RAG figures it out.

**Why:** Curation creates signal. The act of deciding "this matters" forces clarity. You can't capture your way to understanding — you have to think.

### 2. Portable & Local-First

Context lives in the repo as markdown files. No database. No cloud service. No API keys. `git clone` = full knowledge transfer.

**Why:** No vendor lock-in. Switch AI tools freely. Your memory travels with your code.

### 3. Git-Native

Decisions are tracked in version control. The history of *why* you built it is as important as *what* you built.

**Why:** Explicit structure beats probabilistic search. For critical decisions, deterministic wins.

### 4. Functional Core, Imperative Shell (v2.8+)

Logic must be separated from I/O. The "Brain" (Logic) never calls print() directly. All file writes go through transactional buffers with atomic commit.

**Why:** Testability, API exposure, and v3.0 MCP Server preparation.

### 5. Graceful Curation (v2.9+)

Lower the adoption barrier with tiered validation: L0 (Scaffold) → L1 (Stub) → L2 (Full). Don't demand full metadata upfront — let teams grow into it.

**Why:** De-risks the "Librarian's Wager." Teams can start with minimal friction and add rigor as value proves itself.

### 6. Structure Over Search

The context map IS the query interface — human-readable, agent-navigable. No semantic search, no vector databases.

**Why:** AI agents improve faster at navigating structured knowledge than extracting signal from noise.

---

## III. THE DUAL ONTOLOGY MODEL (v2.0+)

### Core Insight: Knowledge Has Two Dimensions

| Dimension | Question | Changes How? | Examples |
|-----------|----------|--------------|----------|
| **Space (Truth)** | What IS? | Deliberate updates | Architecture, features, specs |
| **Time (History)** | What HAPPENED? | Accumulation | Decisions, fixes, explorations |

v1.x collapsed these. v2.0 separates them.

### Space Ontology (The Graph)

| Type | Rank | Purpose | Depends On |
|------|------|---------|------------|
| `kernel` | 0 | Mission, values, principles | Nothing |
| `strategy` | 1 | Goals, roadmap, audience | Kernel |
| `product` | 2 | Features, user flows, requirements | Kernel, Strategy |
| `atom` | 3 | Technical specs, implementation | Kernel, Strategy, Product, Atom |
| `log` | 4 | Session history (Time dimension) | Uses `impacts`, not `depends_on` |

**Rule:** Dependencies flow DOWN. Atoms depend on products, not vice versa.

### Time Ontology (The Timeline)

Logs are first-class citizens with extended frontmatter:

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

**Event types:** `feature`, `fix`, `refactor`, `exploration`, `chore`, `decision`

**Key innovation:** Logs connect to Space through `impacts` field — bridging "what we decided" and "what it affected."

### Status Semantics

| Status | Meaning | Survives in Graph? |
|--------|---------|-------------------|
| `scaffold` | L0 auto-generated | Yes |
| `pending_curation` | L1 stub | Yes |
| `draft` | Work in progress | Yes |
| `active` | Current truth | Yes |
| `deprecated` | Past truth (superseded) | Yes |
| `complete` | Finished work (reviews) | Yes |
| `archived` | Historical record | Excluded by default |
| `rejected` | Considered, not approved | Excluded by default |

---

## IV. ARCHITECTURE & TOOLING (v2.9.5)

### Package Structure (v2.8+)

```
ontos/
├── core/                    # Pure logic layer (no I/O)
│   ├── context.py           # SessionContext — transactional file ops
│   ├── schema.py            # Schema versioning (1.0 → 3.0)
│   ├── curation.py          # Curation levels (L0/L1/L2)
│   ├── staleness.py         # Describes field validation
│   ├── history.py           # Decision history generation
│   ├── paths.py             # Mode-aware path resolution
│   ├── frontmatter.py       # Pure YAML parsing
│   └── config.py            # Configuration resolution
└── ui/
    └── output.py            # OutputHandler for display
```

### Unified CLI (v2.8+)

Single entry point: `python3 ontos.py <command>`

| Command | Purpose |
|---------|---------|
| `log` | Create/enhance session logs |
| `map` | Generate context map |
| `verify` | Update describes_verified dates |
| `maintain` | Run maintenance tasks |
| `consolidate` | Archive old logs |
| `query` | Query the graph |
| `scaffold` | Generate L0 scaffolds |
| `stub` | Create L1 stubs |
| `promote` | Promote L0/L1 to L2 |
| `migrate` | Migrate schema versions |
| `update` | Update Ontos from GitHub |

### Script Inventory (~11,500 lines)

| Script | Lines | Purpose |
|--------|-------|---------|
| `ontos_end_session.py` | 1,625 | Create/enhance session logs |
| `ontos_generate_context_map.py` | 1,043 | Build graph, validate, generate map |
| `ontos_update.py` | 521 | Pull updates from GitHub |
| `ontos/core/curation.py` | 489 | Curation level detection/validation |
| `ontos/core/schema.py` | 421 | Schema versioning |
| `ontos_consolidate.py` | 396 | Archive old logs into history |
| `ontos_pre_push_check.py` | 385 | Pre-push hook logic |
| `ontos/core/staleness.py` | 353 | Describes validation |
| `ontos/core/paths.py` | 345 | Path helpers |
| `ontos_verify.py` | 316 | Staleness verification |
| ... | ... | 15+ more scripts |

### Dual-Mode Architecture

**Contributor Mode:** Developing Ontos itself (`.ontos-internal/`)
**User Mode:** Using Ontos in your project (`docs/`)

Detection: Presence of `.ontos-internal/` directory.

### Configuration Modes (v2.5+)

| Mode | Promise | Archiving | Consolidation |
|------|---------|-----------|---------------|
| **automated** | "Zero friction — just works" | Auto on push | Auto on commit |
| **prompted** | "Keep me in the loop" (DEFAULT) | Blocks push | Agent reminder |
| **advisory** | "Maximum flexibility" | Warning only | Manual only |

### Validation System (6 checks)

1. **[BROKEN LINK]** — Reference to nonexistent ID
2. **[CYCLE]** — Circular dependency (A → B → A)
3. **[ORPHAN]** — No dependents (floating doc)
4. **[DEPTH]** — Chain exceeds 5 levels
5. **[ARCHITECTURE]** — Lower rank depends on higher
6. **[STALE]** — describes_verified older than atom modification

### Testing Infrastructure

- 6 test files, 132 tests
- Dual-mode testing: `pytest --mode=contributor` and `pytest --mode=user`
- CI via GitHub Actions

---

## V. KEY FEATURES

### 1. Curation Levels (v2.9.1)

Lower adoption barrier with tiered validation:

| Level | Name | Required | Status |
|-------|------|----------|--------|
| 0 | Scaffold | `id`, `type` | `scaffold` |
| 1 | Stub | `id`, `type`, `status`, `goal` | `pending_curation` |
| 2 | Full | All + `depends_on`/`concepts` | `draft`, `active`... |

**Commands:**
```bash
python3 ontos.py scaffold --apply  # Add L0 frontmatter to untagged files
python3 ontos.py stub --goal "..." # Create L1 document
python3 ontos.py promote --check   # See what's ready for L2
```

### 2. Schema Versioning (v2.9.0)

Forward compatibility for v3.0 migration:

| Schema | Required Fields | Introduced |
|--------|-----------------|------------|
| 1.0 | `id` | Legacy |
| 2.0 | `id`, `type` | v2.0 |
| 2.1 | `id`, `type` | v2.7 (describes) |
| 2.2 | `id`, `type`, `status` | v2.9 (curation) |
| 3.0 | `id`, `type`, `status`, `ontos_schema` | v3.0 |

**Commands:**
```bash
python3 ontos.py migrate --check  # Check schema versions
python3 ontos.py migrate --apply  # Migrate to latest
```

### 3. Documentation Staleness (v2.7)

Track when docs become outdated after code changes:

```yaml
---
id: ontos_manual
type: atom
describes: [ontos_end_session, ontos_maintain]
describes_verified: 2025-12-20
---
```

When described atoms change, Ontos warns about potentially stale docs.

### 4. Transactional File Operations (v2.8)

All file writes go through `SessionContext`:
- Two-phase commit (temp-then-rename)
- Atomic operations
- Stale lock detection with PID liveness
- Rollback on failure

### 5. install.py Bootstrap (v2.9.3)

Curl-bootstrapped installation with security:
```bash
curl -sO https://raw.githubusercontent.com/ohjona/Project-Ontos/v2.9.5/install.py
python3 install.py
```

Features: SHA256 verification, path traversal protection, offline mode, upgrade with rollback.

### 6. Context Map Generation

```markdown
## 1. Hierarchy Tree
### KERNEL
- **mission** [L2] (mission.md) ~377 tokens
  - Status: active
  - Depends On: None

### STRATEGY
- **v2_strategy** [L2] (v2_strategy.md) ~2,600 tokens
  - Status: active
  - Depends On: mission
```

Token estimates enable context budgeting. Curation markers ([L0]/[L1]/[L2]) show completeness.

### 7. Immutable History (v2.7)

`decision_history.md` is regenerated deterministically from archived logs:
- Sorted by date (desc), event type, slug
- No merge conflicts
- Full traceability

### 8. Deprecation Warnings (v2.9.2)

Prepares users for v3.0:
- FutureWarning on `ontos_lib` import
- Direct script execution notices
- Points to unified CLI equivalents

---

## VI. VERSION HISTORY (KEY MILESTONES)

| Version | Theme | Key Changes |
|---------|-------|-------------|
| **2.9.5** | Quality & Testing | 20 SessionContext tests, pure/impure fix |
| **2.9.3** | install.py Bootstrap | Curl-bootstrapped with SHA256 |
| **2.9.1** | Curation Levels | L0 Scaffold → L1 Stub → L2 Full |
| **2.9.0** | Schema Versioning | Forward compat for v3.0 |
| **2.8.5** | Unified CLI | `python3 ontos.py <command>` |
| **2.8.0** | Clean Architecture | `ontos/` package, SessionContext |
| **2.7.0** | Documentation Staleness | `describes` field, immutable history |
| **2.6.0** | Proposals Workflow | Type-status matrix, rejection metadata |
| **2.5.0** | The Promises | Mode system (automated/prompted/advisory) |
| **2.0.0** | Dual Ontology | Space/Time separation, impacts field |

**Development cadence:** Rapid iteration since Nov 2025. ~25 releases in ~7 weeks.

---

## VII. CURRENT FOCUS: V3.0 PREPARATION

### The v3.0 Vision

Move from script-based tools to a **system-wide daemon** (MCP Server):
- `pip install ontos` — Logic moves to PyPI
- `ontos serve` — Local MCP Server
- Agents "pull" context dynamically

### Master Plan Core Invariants

1. **Zero-Dependency (V2.x):** Python Standard Library only
2. **System Package (V3.x):** PyPI distribution with boto3, mcp deps
3. **Local-First:** Data lives in user's git repo
4. **Functional Core, Imperative Shell:** Logic never calls print()
5. **The Librarian's Wager:** Higher friction → Higher signal
6. **Deterministic Purity:** No vector/semantic search

### v3.0 Feature Tracker

| Feature | Type | Status |
|---------|------|--------|
| pip install ontos | Distro | Planned |
| Local MCP Server | Protocol | Planned |
| Typed Edges | Ontology | Planned |
| Test Suite Overhaul | Arch | Planned |

### Security Requirements (v2.9.4)

- MCP Server binds to 127.0.0.1 only
- Auto-generated auth token required
- File locking for concurrent access
- No HTTP fallback

---

## VIII. TARGET AUDIENCE

### Primary: Small Teams Using AI Coding Agents

- 1-5 developers with Claude Code, Cursor, Windsurf, etc.
- Building products where decisions matter more than code volume
- Switching between AI tools depending on task
- **Onboarding new team members constantly** — contractors, new hires, fresh AI sessions

**Litmus test:** Can a new person become productive in under 10 minutes? If context is trapped in Slack/heads/expired chats — no. Ontos makes it yes.

### Secondary: Solo Developers with Multiple Projects

- Juggling 2-5 projects simultaneously
- Returning to projects after weeks of dormancy
- Frustrated by re-explaining context to every AI session

### Anti-Audience

NOT building for:
- **Large enterprises** — they have Confluence, Notion, dedicated doc teams
- **Real-time collaboration** — we're git-native, not Google Docs
- **Zero-maintenance users** — Ontos requires intent; that's the point

---

## IX. MARKET POSITIONING

### Competitive Landscape

| Approach | Tools | Ontos Differentiator |
|----------|-------|---------------------|
| Vector DB + RAG | LangChain, Pinecone | Structure over probabilistic search |
| IDE-integrated | Cursor, Windsurf | Tool-agnostic, portable |
| Knowledge bases | Notion, Confluence | Local-first, git-native, AI-optimized |
| Project memory | Mem.ai, Obsidian | Explicit curation, not capture-everything |

### Value Proposition

> "Clone the repo. Activate Ontos. Instant shared brain."

**The bet:** Curated knowledge beats captured data in AI-native workflows.

- Teams need **shared** context (individual memory doesn't transfer)
- Signal degrades over time (noise compounds; curation doesn't)
- AI agents improve faster at navigating structure than extracting signal from noise
- Intent forces clarity (documenting a decision makes you understand it better)

### Tagline

> **Project Ontos: The conscious memory system for AI-native teams.**
> *Truth + History. Portable. Version-controlled. Intent over automation.*

---

## X. TECHNICAL STRENGTHS

1. **Zero dependencies** — Pure Python 3.9+, standard library only
2. **Deterministic** — No ML, no probability, no surprises
3. **Testable** — Dual-mode testing, 132 tests, comprehensive CI
4. **Transactional** — Two-phase commit with atomic operations
5. **Extensible** — Clean package structure, path helpers
6. **Backward compatible** — Schema versioning, graceful migration
7. **Fast** — Context map generation in milliseconds
8. **Secure** — SHA256 verification, no network in core operations

---

## XI. KNOWN LIMITATIONS / RISKS

1. **Maintenance burden** — Requires discipline to keep `depends_on`, `impacts`, `concepts` accurate
2. **Manual curation** — No auto-detection of what matters (by design, but friction)
3. **Git-only** — No support for non-git workflows
4. **Single-repo** — No cross-repo knowledge graphs (yet)
5. **No GUI** — CLI and markdown only (by design)
6. **Adoption risk** — Requires team buy-in; one person can undermine shared memory
7. **Learning curve** — Curation levels help, but still requires understanding the model

---

## XII. FUTURE DIRECTIONS

### Confirmed (v3.0)

- **pip install ontos** — System-wide installation
- **Local MCP Server** — Agent pulls context dynamically
- **Typed Edges** — `implements`, `tests`, `deprecates` relationships

### Speculative / Under Consideration

- **Cross-repo federation** — Shared kernel across projects
- **AI-assisted tagging** — Suggest `concepts`, `depends_on` from content
- **S3 archive backend** — Offload old logs to cloud storage
- **VS Code extension** — Visual graph explorer (but not a dashboard)

### Philosophy Tensions to Watch

1. **Curation vs. friction** — How much manual work is acceptable?
2. **Structure vs. flexibility** — Strict validation vs. permissive defaults
3. **Completeness vs. simplicity** — Track everything vs. track what matters
4. **Tool-agnostic vs. optimized** — Generic protocol vs. Claude/Cursor-specific features

---

## XIII. DOCUMENT LIFECYCLE (v2.9.5)

| Status | Meaning |
|--------|---------|
| `draft` | Planning phase, open questions |
| `active` | Being implemented |
| `complete` | Implemented and released |

**Archival:** Once a major version is released and the next version stabilizes, move its `strategy/` and `proposals/` directories to `archive/`.

---

## XIV. SUCCESS METRICS

### For Users

1. **Onboarding time** — Clone to productive in <10 minutes
2. **Context re-establishment** — Return to dormant project without re-explaining
3. **Decision archaeology** — "Why is X like this?" returns real history, not guesses

### For the Project

1. **Adoption signal** — GitHub stars, forks, issues from real users
2. **Retention signal** — Users who adopt stay (vs. churn back to ad-hoc)
3. **Ecosystem signal** — Other tools support Ontos-style frontmatter (long-term)

---

## XV. ANALYSIS PROMPTS

Use this brief to explore:

### Marketing Fit
- What positioning resonates with "small teams using AI agents"?
- How does "intent over automation" play vs. "zero-friction" competitors?
- What's the wedge? First use case that proves value fastest?

### V3.0 Strategy
- Is the MCP Server the right v3.0 bet?
- Should cross-repo federation be a v3.0 feature?
- How does Ontos stay relevant as AI context windows grow (1M+ tokens)?

### Collaboration Opportunities
- Which AI coding tools (Cursor, Windsurf, etc.) would benefit from Ontos integration?
- Is there a partnership play with knowledge management tools (Obsidian, Notion)?
- What would an "Ontos-compatible" certification look like?

### Improvement Opportunities
- Where does the UX have the most friction?
- What's the 80/20 feature that would unlock adoption?
- Is the type hierarchy (kernel → strategy → product → atom) too rigid or too loose?
- Are curation levels (L0/L1/L2) the right abstraction?

---

*End of brief. Total: ~4,000 words, ~6,000 tokens.*
