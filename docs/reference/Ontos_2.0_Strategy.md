---
id: ontos_2_0_strategy
type: strategy
status: active
depends_on: []
---

# Project Ontos: 2.0 Strategy Document

*Documented: December 2025*

---

## 1. Mission

Build the simplest possible context management system for developers who waste hours re-explaining their projects to AI tools.

**The one-sentence pitch:** Your documentation becomes a knowledge graph that any AI can read, so you never explain twice.

---

## 2. The Problem

Context dies in three ways:

### 2.1 AI Amnesia

You explain your architecture to Claude. Then again to ChatGPT. Then again to Cursor. Each starts from zero. Each gives conflicting advice because none has the full picture.

The cost: 10+ hours per week re-establishing context across tools.

### 2.2 Prototype Graveyards

You build fast in Streamlit. You make dozens of product decisions—pricing model, user flows, edge case handling. Then you rewrite in Next.js.

The code is new. The decisions? Buried in old chat logs. Three weeks of thinking, gone.

### 2.3 Tribal Knowledge

Your project's "why" lives in Slack threads, abandoned Google Docs, and your head. When you switch tools, onboard a collaborator, or return after a break, the rediscovery begins.

**The common thread:** Context isn't portable. It's trapped in tool-specific sessions that don't talk to each other.

---

## 3. The Solution

Ontos turns documentation into a **portable knowledge graph** through three mechanisms:

1. **Structured Metadata**: YAML frontmatter tags each document with `id`, `type`, `status`, and `depends_on`. This transforms flat files into graph nodes.

2. **Deterministic Validation**: Python scripts enforce graph integrity—catching broken links, cycles, orphans, depth violations, and architectural inversions. No AI hallucination in the validation layer.

3. **Universal Activation**: Any AI tool reads the same `Ontos_Context_Map.md`, loads relevant context, and confirms what it knows. The protocol is tool-agnostic.

**What survives migration:**

| Layer | What It Captures | Survives Tech Migration? |
|-------|------------------|--------------------------|
| `kernel` | Why you exist, core values | ✅ Always |
| `strategy` | Goals, audience, approach | ✅ Always |
| `product` | Features, user flows, requirements | ✅ Always |
| `atom` | Technical implementation | ❌ Rewritten |

Your Streamlit atoms die. Your product decisions don't.

---

## 4. Core Philosophy

### 4.1 LLM-Powered Generation, Deterministic Validation

AI agents handle creative work:
- Tagging documents with appropriate types
- Inferring dependency relationships
- Generating session summaries
- Loading relevant context for tasks

Python scripts handle validation:
- Cycle detection via DFS
- Broken link identification
- Architectural violation checks
- Dependency depth enforcement

**Why this split?** LLMs are good at understanding intent and generating structured output. They're bad at guaranteeing correctness. The validation layer provides the guarantees.

### 4.2 Lightweight Over Complex

Ontos resists automation complexity. No orchestrator agents. No automatic context injection. No magic.

The user says "Ontos." The agent reads the map. The agent loads files. The agent confirms.

This simplicity is intentional. LLMs will continue to evolve—what's "necessary automation" today becomes unnecessary overhead tomorrow. The minimal protocol survives capability improvements.

### 4.3 The Library Metaphor

Ontos is a library with disciplined librarians, not an omniscient assistant.

The librarians (AI agents) must "do their homework"—read the catalog, locate relevant materials, load them explicitly. They don't guess. They don't assume they already know.

This constraint improves reliability. An agent that declares "Loaded: [mission, pricing_strategy, user_flows]" is accountable for what it knows.

---

## 5. Target Audience

### 5.1 Primary: Agentic CLI Users

Developers who work with:
- Claude Code
- Cursor
- ChatGPT Codex / Canvas
- Google Gemini in Antigravity
- Any future AI-assisted development environment

**Defining characteristic:** They treat AI as a collaborator, not a search engine. They have ongoing projects where context accumulation matters.

### 5.2 Use Cases

**Multi-AI Workflows**: Switch between Claude, ChatGPT, and Gemini without re-explaining. Each reads from the same map.

**Prototype → Production**: Build a demo in one framework, rewrite in another. Atoms are disposable; strategy survives.

**Project Handoffs**: Pass a project to another developer. Session logs + context map = instant knowledge transfer.

**Documentation Audits**: CI/CD validation catches architectural drift before it becomes tribal knowledge.

### 5.3 Anti-Audience

We are NOT building for:
- Teams needing real-time collaboration features
- Enterprises requiring access control and audit logs
- Developers who prefer GUI-based project management
- Users who want "set and forget" automation

---

## 6. Value Proposition

### What You Get

1. **Portable Context**: One documentation system works across all AI tools
2. **Decision Persistence**: Product decisions survive code rewrites
3. **Explicit Loading**: Know exactly what context your AI has
4. **Graph Integrity**: Catch broken links and circular dependencies automatically
5. **Session History**: Decision logs that persist across tool switches

### What You Don't Get

- Cloud sync (local-first by design)
- Automatic context injection (explicit is better)
- Multi-user collaboration features
- Proprietary lock-in

---

## 7. Competitive Positioning

### 7.1 What Ontos Is

- A documentation protocol with validation tooling
- A way to structure knowledge for AI consumption
- A lightweight, local-first system
- Tool-agnostic and vendor-neutral

### 7.2 What Ontos Isn't

- A RAG system or vector database
- A project management tool
- A cloud service
- An AI agent framework

### 7.3 Alternatives Considered

| Approach | Why Not |
|----------|---------|
| **Custom GPTs / Claude Projects** | Vendor-locked. Can't take context to another tool. |
| **RAG with vector DB** | Over-engineered for small-to-medium projects. Requires infrastructure. |
| **Obsidian / Notion** | Great for humans, no protocol for AI consumption. Links aren't typed. |
| **No system (just re-explain)** | The problem we're solving. |

Ontos occupies a specific niche: structured context for developers who use multiple AI tools and want their documentation to be machine-readable without cloud dependencies.

---

## 8. Design Decisions (v1.0)

### 8.1 Included

| Feature | Rationale |
|---------|-----------|
| YAML frontmatter schema | Simple, human-readable, widely supported |
| Four-type hierarchy (kernel/strategy/product/atom) | Minimal but sufficient for dependency direction |
| Python validation scripts | No build step, runs anywhere Python exists |
| `--strict` mode for CI/CD | Enables automated enforcement |
| Session logging with git integration | Decision history tied to commits |
| Update script pulling from GitHub | Keeps tooling current without package managers |
| Pre-push hook for session reminders | Gentle nudge toward good hygiene |

### 8.2 Explicitly Excluded

| Feature | Rationale |
|---------|-----------|
| pip packaging | Target audience can paste install instructions into AI tools |
| Web UI / dashboard | Adds complexity, reduces portability |
| Automatic context injection | Explicit loading is more reliable |
| Multi-directory support by default | Simplicity; can be configured in ontos_config.py |
| Custom type definitions | Four types cover 95% of use cases; complexity not worth it |
| Real-time file watching in production | `--watch` exists for development; not default behavior |

### 8.3 Configuration Philosophy

Two-file config system:
- `ontos_config_defaults.py`: Shipped defaults, updated by `ontos_update.py`
- `ontos_config.py`: User overrides, never touched by updates

Users customize by overriding defaults, not by forking. This enables updates without losing customizations.

---

## 9. Success Criteria

### 9.1 Individual Success

A developer using Ontos should be able to:

1. Switch from Claude Code to Cursor mid-project without re-explaining architecture
2. Rewrite a prototype in a new framework while preserving product decisions
3. Return to a project after 2 weeks and regain full context in under 5 minutes
4. Hand off a project to another developer with documentation alone

### 9.2 Project Health Indicators

| Indicator | Healthy | Unhealthy |
|-----------|---------|-----------|
| Context map generation | `0 issues found` | Persistent broken links or cycles |
| Session logs | Created at natural breakpoints | Weeks without archival |
| Type distribution | Mix of all four types | All atoms, no strategy |
| Dependency depth | Under 5 levels | Deep chains indicating poor factoring |

### 9.3 Adoption Signals

- Users report reduced "re-explaining time"
- Users maintain session logs voluntarily
- Users run validation in CI/CD
- Users contribute feedback on friction points

---

## 10. Roadmap Direction (Post-v1.0)

### 10.1 Near-Term Possibilities

These are directions being considered, not commitments:

- **JSON output mode**: Machine-readable context maps for tooling integration
- **Improved orphan detection**: Smarter heuristics for intentionally standalone docs
- **Tag/label support**: Optional taxonomy beyond the four core types
- **Template expansion**: More starter templates for common project types

### 10.2 Explicitly Not Planned

- Cloud sync or hosted service
- Team collaboration features
- Proprietary AI integrations
- Mobile applications

### 10.3 Guiding Principle

Any new feature must pass the "lightweight test": Does this make Ontos simpler to use, or does it add complexity that will become obsolete as LLMs improve?

---

## 11. Open Questions

These are unresolved tensions in the current design:

1. **Type naming**: "Atom" linguistically suggests fundamental/indivisible, but in Ontos it's the most disposable layer. Is this confusing?

2. **Orphan strictness**: Should atoms always require dependents, or are standalone implementation docs legitimate?

3. **Cross-project context**: How should Ontos handle developers working on multiple projects that share concepts?

4. **Version compatibility**: As the schema evolves, how do we handle migrations from older Ontos installations?

---

## 12. The Name

From Greek ὄντος (ontos), meaning "being"—the root of ontology.

Your documentation gains existence as a persistent knowledge graph, not ephemeral chat history.

Or simpler: **your project's memory that works everywhere.**

---

*This document captures the strategic intent of Project Ontos at v1.0. It should be updated when significant directional decisions are made, not for tactical changes.*
