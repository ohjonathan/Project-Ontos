# Project Ontos

[![CI](https://github.com/ohjona/Project-Ontos/actions/workflows/ci.yml/badge.svg)](https://github.com/ohjona/Project-Ontos/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/ontos.svg)](https://pypi.org/project/ontos/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

**Context-Aware Documentation for the Agentic Era.**

*Never explain twice. Own your context.*

---

## Contents

- [The Problem](#the-problem)
- [The Solution](#the-solution)
- [Who Ontos Is For](#who-ontos-is-for)
- [Why "Ontos"?](#why-ontos)
- [Quick Start](#quick-start)
- [Workflow](#workflow)
- [Use Cases](#use-cases)
- [What Ontos Is NOT](#what-ontos-is-not)
- [Roadmap](#roadmap)
- [Documentation](#documentation)

---

## The Problem

Context dies in three ways:

1. **AI Amnesia.** You explain your architecture to Claude. Then again to ChatGPT. Then again to Cursor. Each starts from zero and gives conflicting advice.

2. **Prototype Graveyards.** You build fast in Streamlit, make dozens of product decisions, then rewrite in Next.js. The code is new. The decisions? Lost in old chat logs.

3. **Tribal Knowledge.** Your project's "why" lives in Slack threads, abandoned docs, and your head. New collaborators (human or AI) have to rediscover everything.

The common thread: **context isn't portable.**

---

## The Solution

Ontos creates a **portable knowledge graph** that lives in your repo as markdown files with YAML frontmatter. No cloud service, no vendor lock-in, no semantic search lottery.

**Glass box, not black box.** Your context is readable, not just retrievable. Explicit structure instead of probabilistic search. Humans can inspect it. AIs follow it. Same input, same output, every time.

**How it works:**

1. Tag your docs with YAML headers (or run `ontos scaffold` to auto-generate them - you review, it tags)
2. Run `ontos map` to generate `Ontos_Context_Map.md` - your project's memory
3. Any AI agent reads the map, loads only what's relevant, sees the full decision history

```yaml
---
id: pricing_strategy
type: strategy
depends_on: [target_audience, mission]
---
```

**The hierarchy** (when uncertain: "If this doc changes, what else breaks?"):

| Layer | What It Captures | Survives Migration? |
|-------|------------------|---------------------|
| `kernel` | Why you exist, core values | ✅ Always |
| `strategy` | Goals, audience, approach | ✅ Always |
| `product` | Features, user flows, requirements | ✅ Always |
| `atom` | Technical implementation | ❌ Rewritten |

Your Streamlit atoms die. Your product decisions don't.

---

## Who Ontos Is For

- **Teams switching between AI tools** (Claude, ChatGPT, Gemini, Cursor) who are tired of re-explaining their project
- **Projects that outlive their prototypes** - when you rewrite from Streamlit to Next.js, your decisions should survive
- **Developers who want context to persist** across session resets, tool switches, and team changes
- **Anyone betting on AI-assisted development** who needs reliable, portable project memory

---

## Why "Ontos"?

From Greek ὄντος (ontos), meaning "being" - the root of ontology. Your documentation gains existence as a persistent knowledge graph, not ephemeral chat history.

Or simpler: **your project's memory that works everywhere.**

---

## Quick Start

**Install** via pip (recommended for v3.0+):

```bash
pip install ontos
ontos init
```

If pip install fails (PyPI not yet available), use git:

```bash
pip install git+https://github.com/ohjona/Project-Ontos.git
ontos init
```

Or for development/custom installations:

```bash
git clone https://github.com/ohjona/Project-Ontos.git
cd Project-Ontos
pip install -e .
ontos init
```

> **v3.0 Update:** Ontos is now a proper Python package. Use `ontos` CLI commands instead of direct script execution.

**Use it** - once installed, tell your Agent:

> **"Ontos"** (or "Activate Ontos")

The Agent will:
1. Follow [Agent Instructions](docs/reference/Ontos_Agent_Instructions.md).
2. Read the Context Map.
3. Load *only* the relevant files for your task.
4. Confirm what context it has loaded.

---

## Workflow

| Command | What It Does |
|---------|--------------|
| **"Ontos"** | Activate context - agent reads the map, loads relevant files |
| **"Archive Ontos"** | End session - save decisions as a log for next time |
| **"Maintain Ontos"** | Health check - scan for new files, fix broken links, regenerate map |

```bash
# CLI equivalents
ontos map          # Generate/update context map
ontos log -e feature   # Archive a feature session
ontos doctor       # Check graph health
```

**Update:** `pip install --upgrade ontos`

---

## Use Cases

### Multi-AI Workflows
Switch between Claude Code, Cursor, ChatGPT, and Gemini CLI without re-explaining your project. Say "Activate Ontos" and they all read from the same map.

### Prototype → Production
Built a demo in Streamlit? When you rewrite in FastAPI or Next.js, your atoms are disposable but your strategy survives. Three weeks of product decisions don't vanish with the old code.

### Project Handoffs
Pass a project to another developer or agency. Everything travels with `git clone` - session logs, context map, decision history. No export, no onboarding docs, no 2-hour call. They clone, they know.

### Documentation Audits
CI/CD validation catches broken links, circular dependencies, and architectural violations before they become tribal knowledge.

---

## What Ontos Is NOT

- **Not a RAG system.** We use structural graph traversal, not semantic search. Deterministic beats probabilistic for critical decisions.
- **Not zero-effort.** You decide what matters (curation). The tooling handles the paperwork (tagging, validation, maintenance).
- **Not a cloud service.** Markdown files in your repo. No API keys, no accounts, no vendor lock-in.
- **Not magic.** You still need to make decisions. But CI/CD handles validation, and scaffolding handles tagging.

If you want zero-effort context capture, use a vector database. If you want reliable, portable, deterministic context delivery, use Ontos.

---

## Roadmap

| Version | Status | Theme |
|---------|--------|-------|
| **v3.0.0** | ✅ Current | pip-installable package, 13 CLI commands, JSON output |
| **v3.1** | Planned | Obsidian compatibility, `ontos deinit`, export templates |
| **v4.0** | Vision | MCP as primary interface, daemon mode, lazy loading |

v3.0 transformed Ontos from repo-injected scripts (~8,600 LOC) into a proper Python package with modular architecture. The core is zero-dependency (stdlib only).

---

## Documentation

- **[Ontos Manual](docs/reference/Ontos_Manual.md)**: Complete reference — installation, workflow, configuration, errors
- **[Agent Instructions](docs/reference/Ontos_Agent_Instructions.md)**: Commands for AI agents
- **[Migration Guide v2→v3](docs/reference/Migration_v2_to_v3.md)**: Upgrading from v2.x to v3.0
- **[Minimal Example](examples/minimal/README.md)**: 3-file quick start
- **[Changelog](Ontos_CHANGELOG.md)**: Version history

---

## Contributing

Contributions welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

MIT - see [LICENSE](LICENSE).
