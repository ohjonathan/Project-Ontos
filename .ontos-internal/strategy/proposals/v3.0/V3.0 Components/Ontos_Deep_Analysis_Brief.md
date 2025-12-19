# Project Ontos: Deep Analysis Brief

**Purpose:** Comprehensive summary for external AI analysis (marketing fit, V3.0 strategy, collaboration, improvement opportunities)
**Generated:** 2025-12-18
**Current Version:** 2.6.2
**Codebase:** ~6,800 lines Python (16 scripts), 16 test files, MIT licensed

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
---
```

A script generates `Ontos_Context_Map.md` — a navigable index any AI can read. The map shows document hierarchy, dependencies, token estimates, and recent changes.

### Mission Statement

> "Eliminate context death in AI-assisted development. Enable LLMs to recover project context with minimal token expense. Create shared memory that survives tool switches, session resets, and team changes."

### The Name

From Greek ontos, meaning "being" — the root of ontology. Your documentation gains existence as a persistent knowledge graph, not ephemeral chat history.

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

### 4. Intent Over Automation

Ontos requires deliberate action: tagging documents, connecting decisions to docs, marking what matters. This friction is the feature.

**Why:** Signal degrades with automation. Noise compounds; curation doesn't.

### 5. Structure Over Search

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
| `draft` | Work in progress | Yes |
| `active` | Current truth | Yes |
| `deprecated` | Past truth (superseded) | Yes |
| `archived` | Historical record | Excluded by default |
| `rejected` | Considered, not approved | Excluded by default |
| `complete` | Finished work (reviews) | Yes |

---

## IV. ARCHITECTURE & TOOLING

### Script Inventory (16 scripts, 6,800 lines)

| Script | Lines | Purpose |
|--------|-------|---------|
| `ontos_generate_context_map.py` | 1,043 | Build graph, validate, generate map |
| `ontos_end_session.py` | 1,625 | Create/enhance session logs |
| `ontos_lib.py` | 679 | Shared utilities, path helpers |
| `ontos_update.py` | 508 | Pull updates from GitHub |
| `ontos_consolidate.py` | 396 | Archive old logs into history |
| `ontos_pre_push_check.py` | 385 | Pre-push hook logic |
| `ontos_query.py` | 308 | Query graph (deps, concepts, stale) |
| `ontos_maintain.py` | 298 | Migration + regeneration |
| `ontos_config_defaults.py` | 282 | Mode presets, defaults |
| `ontos_pre_commit_check.py` | 252 | Pre-commit consolidation |
| `ontos_install_hooks.py` | 182 | Git hook installation |
| `ontos_migrate_frontmatter.py` | 183 | Find untagged files |
| `ontos_summarize.py` | 175 | Generate doc summaries |
| `ontos_remove_frontmatter.py` | 167 | Strip YAML headers |
| `ontos_config.py` | 159 | User configuration |
| `ontos_migrate_v2.py` | 127 | v1 to v2 migration |

### Dual-Mode Architecture

**Contributor Mode:** Developing Ontos itself (`.ontos-internal/`)
**User Mode:** Using Ontos in your project (`docs/`)

Detection: Presence of `.ontos-internal/` directory.

```
User Mode Structure:
docs/
  strategy/
    proposals/       # Draft proposals (status: draft)
    decision_history.md
  archive/
    logs/            # Consolidated logs
    proposals/       # Rejected proposals
  reference/
    Common_Concepts.md
    Ontos_Agent_Instructions.md
  logs/              # Active session logs
```

### Configuration Modes (v2.5+)

| Mode | Promise | Archiving | Consolidation |
|------|---------|-----------|---------------|
| **automated** | "Zero friction — just works" | Auto on push | Auto on commit |
| **prompted** | "Keep me in the loop" (DEFAULT) | Blocks push | Agent reminder |
| **advisory** | "Maximum flexibility" | Warning only | Manual only |

### Validation System

5 integrity checks:
1. **[BROKEN LINK]** — Reference to nonexistent ID
2. **[CYCLE]** — Circular dependency (A to B to A)
3. **[ORPHAN]** — No dependents (floating doc)
4. **[DEPTH]** — Chain exceeds 5 levels
5. **[ARCHITECTURE]** — Lower rank depends on higher (atom to strategy)

**Type-Status Matrix (v2.6):** Only valid combinations allowed.

### Testing Infrastructure

- 16 test files, 150+ tests
- Dual-mode testing: `pytest --mode=contributor` and `pytest --mode=user`
- CI via GitHub Actions

---

## V. KEY FEATURES

### 1. Context Map Generation

```markdown
## 1. Hierarchy Tree
### KERNEL
- **mission** (mission.md) ~377 tokens
  - Status: active
  - Depends On: None

### STRATEGY
- **v2_strategy** (v2_strategy.md) ~2,600 tokens
  - Status: active
  - Depends On: mission
```

Token estimates enable context budgeting. Agents load only what's needed.

### 2. Session Archival

```bash
python3 .ontos/scripts/ontos_end_session.py -e feature -s "Claude"
```

Auto-suggests impacted docs from git diff. Creates structured log with:
- Goal, Key Decisions, Alternatives Considered
- Concepts (tags), Impacts (affected docs)
- Status: auto-generated to active (after enrichment)

### 3. Pre-Push/Pre-Commit Hooks

- **Pre-push:** Validates context map, optionally blocks until session archived
- **Pre-commit:** Auto-consolidates old logs (automated mode)
- Detects CI environments, rebases; graceful degradation

### 4. Log Consolidation

Keeps newest N logs (default: 10), archives old ones to `decision_history.md`:

```markdown
| Date | Slug | Event | Decision / Outcome | Impacted | Archive Path |
|:-----|:-----|:------|:-------------------|:---------|:-------------|
| 2025-12-17 | v2-6-proposals | feature | APPROVED: Proposals workflow | v2_strategy | archive/... |
```

### 5. Proposal Workflow (v2.6+)

Proposals live in `strategy/proposals/` with `status: draft`:
- **Create** — draft in proposals/
- **Approve** — move to strategy/, change to active, log in decision_history
- **Reject** — require `rejected_reason` (min 10 chars), move to archive/proposals/

**Automated graduation (v2.6.1):** Archive Ontos detects implementation by branch name or impacts, prompts for graduation.

### 6. Query Interface

```bash
python3 .ontos/scripts/ontos_query.py --depends-on auth_flow
python3 .ontos/scripts/ontos_query.py --concept auth
python3 .ontos/scripts/ontos_query.py --stale 30
python3 .ontos/scripts/ontos_query.py --health
```

### 7. Historical Recall

Agents can read archived logs referenced in `decision_history.md` even though they're excluded from the context map by default.

---

## VI. VERSION HISTORY (KEY MILESTONES)

| Version | Theme | Key Changes |
|---------|-------|-------------|
| **2.6.2** | Count-Based Consolidation | Retention count (10), warning threshold (20) |
| **2.6.1** | Automated Graduation | Branch-based proposal detection, graduation prompts |
| **2.6.0** | Proposals Workflow | Type-status matrix, rejection metadata, stale detection |
| **2.5.2** | Dual-Mode Remediation | Template loader, nested directories, path helpers |
| **2.5.0** | The Promises | Mode promises (automated/prompted/advisory), pre-commit hook |
| **2.4.0** | Configuration UX | Mode system, session appending, --auto/--enhance flags |
| **2.3.0** | Tooling & Maintenance | query.py, consolidate.py, maintain.py, adaptive templates |
| **2.2.0** | Data Quality | Common concepts, lint warnings, alternatives section |
| **2.1.0** | Smart Memory | Decision history ledger, consolidation ritual, historical recall |
| **2.0.0** | Dual Ontology | Space/Time separation, impacts field, token estimates |
| **1.5.0** | Self-Development | Dual-mode (contributor/user), log type, .ontos-internal/ |
| **1.0.0** | First Release | Update script, backup system, CI/CD |

**Development cadence:** Rapid iteration since Nov 2025. ~15 releases in ~5 weeks.

---

## VII. CURRENT WORK: v2.7 DOCUMENTATION ONTOLOGY

### The Problem

Ontos tracks dependencies downward (strategy to atom) but has no mechanism for detecting when user-facing documentation (README, Manual) becomes stale after implementation atoms change.

**Example:** `ontos_end_session.py` gets new flags. The Manual doesn't mention them. There's no warning.

### The Insight: Second-Order Atoms

User-facing docs are **second-order atoms**: they describe implementations rather than implementing strategy directly. Their truth derives from implementation truth.

```
First-order: strategy to atom (implements)
Second-order: atom from doc (describes)
```

This is a different relationship than `depends_on`.

### Proposed Solution: `describes` Field

```yaml
---
id: ontos_manual
type: atom
depends_on: [v2_strategy]  # WHY this doc exists
describes:                  # WHAT this doc describes
  - ontos_end_session
  - ontos_maintain
describes_verified: 2025-12-18  # Last verified date
---
```

When described atoms change, Archive Ontos warns about potentially stale docs.

### Design Decisions (from multi-model review)

| Decision | Resolution | Rationale |
|----------|------------|-----------|
| Field name | `describes` (not `documents`) | Avoids noun/verb ambiguity |
| Targets | Valid atom IDs only | Maintain ontological closure |
| Verification | Doc-level `describes_verified` date | Survives git operations (unlike mtime) |
| Transitive staleness | No — direct only | Docs describe interfaces, not internals |
| Section-level tracking | Deferred to v2.8 | Adds precision but also maintenance burden |
| Performance | < 1 second for check | Hooks must be fast or get bypassed |

**Status:** Philosophy approved by 3-model review (Claude, Codex, Gemini). Implementation proposal pending.

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
3. **Testable** — Dual-mode testing, comprehensive CI
4. **Extensible** — Clean separation of concerns, path helpers
5. **Backward compatible** — Path helpers with fallback logic
6. **Fast** — Context map generation in milliseconds

---

## XI. KNOWN LIMITATIONS / RISKS

1. **Maintenance burden** — Requires discipline to keep `depends_on`, `impacts`, `concepts` accurate
2. **Manual curation** — No auto-detection of what matters (by design, but friction)
3. **Git-only** — No support for non-git workflows
4. **Single-repo** — No cross-repo knowledge graphs (yet)
5. **No GUI** — CLI and markdown only (by design)
6. **Adoption risk** — Requires team buy-in; one person can undermine shared memory

---

## XII. FUTURE DIRECTIONS (v3.0 and beyond)

### Confirmed / In Progress

- **v2.7:** Documentation staleness detection (`describes` field)

### Speculative / Under Consideration

- **Semantic query layer** — Natural language queries over graph (opt-in, local)
- **Cross-repo federation** — Shared kernel across projects
- **AI-assisted tagging** — Suggest `concepts`, `depends_on` from content
- **S3 archive backend** — Offload old logs to cloud storage
- **VS Code extension** — Visual graph explorer (but not a dashboard)
- **Multi-language support** — i18n for frontmatter fields

### Philosophy Tensions to Watch

1. **Curation vs. friction** — How much manual work is acceptable?
2. **Structure vs. flexibility** — Strict validation vs. permissive defaults
3. **Completeness vs. simplicity** — Track everything vs. track what matters
4. **Tool-agnostic vs. optimized** — Generic protocol vs. Claude/Cursor-specific features

---

## XIII. SUCCESS METRICS

### For Users

1. **Onboarding time** — Clone to productive in <10 minutes
2. **Context re-establishment** — Return to dormant project without re-explaining
3. **Decision archaeology** — "Why is X like this?" returns real history, not guesses

### For the Project

1. **Adoption signal** — GitHub stars, forks, issues from real users
2. **Retention signal** — Users who adopt stay (vs. churn back to ad-hoc)
3. **Ecosystem signal** — Other tools support Ontos-style frontmatter (long-term)

---

## XIV. ANALYSIS PROMPTS

Use this brief to explore:

### Marketing Fit
- What positioning resonates with "small teams using AI agents"?
- How does "intent over automation" play vs. "zero-friction" competitors?
- What's the wedge? First use case that proves value fastest?

### V3.0 Strategy
- Is `describes` the right v2.7 bet, or should v3.0 jump to semantic queries?
- Should cross-repo federation be v3.0's headline feature?
- How does Ontos stay relevant as AI context windows grow (1M+ tokens)?

### Collaboration Opportunities
- Which AI coding tools (Cursor, Windsurf, etc.) would benefit from Ontos integration?
- Is there a partnership play with knowledge management tools (Obsidian, Notion)?
- What would an "Ontos-compatible" certification look like?

### Improvement Opportunities
- Where does the UX have the most friction?
- What's the 80/20 feature that would unlock adoption?
- Is the type hierarchy (kernel to strategy to product to atom) too rigid or too loose?

---

*End of brief. Total: ~3,000 words, ~4,500 tokens.*
