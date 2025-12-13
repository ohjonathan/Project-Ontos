# Project Ontos

[![CI](https://github.com/ohjona/Project-Ontos/actions/workflows/ci.yml/badge.svg)](https://github.com/ohjona/Project-Ontos/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

**Context-Aware Documentation for the Agentic Era.**

*Never explain twice. Own your context.*

---

## Contents

- [The Problem](#the-problem)
- [The Solution](#the-solution)
- [Why "Ontos"?](#why-ontos)
- [Quick Start](#quick-start)
- [Archiving](#archiving)
- [Maintenance](#maintenance)
- [Updating](#updating)
- [Use Cases](#use-cases)
- [What It Doesn't Do](#what-it-doesnt-do)
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

Ontos turns your documentation into a knowledge graph that survives everything - tool switches, tech migrations, team changes.

**How it works:**

1. Tag your docs with simple YAML headers (type, dependencies, status)
2. A script generates `Ontos_Context_Map.md` - your project's memory
3. Any AI tool reads the map, loads only what's relevant, and sees the full decision history

```yaml
---
id: pricing_strategy
type: strategy
depends_on: [target_audience, mission]
---
```

**The hierarchy:**

| Layer | What It Captures | Survives Migration? |
|-------|------------------|---------------------|
| `kernel` | Why you exist, core values | ✅ Always |
| `strategy` | Goals, audience, approach | ✅ Always |
| `product` | Features, user flows, requirements | ✅ Always |
| `atom` | Technical implementation | ❌ Rewritten |

Your Streamlit atoms die. Your product decisions don't.

---

## Why "Ontos"?

From Greek ὄντος (ontos), meaning "being" - the root of ontology. Your documentation gains existence as a persistent knowledge graph, not ephemeral chat history.

Or simpler: **your project's memory that works everywhere.**

---

## Quick Start

**Install** (paste into Claude Code, Cursor, or any agentic CLI):

```
Install Project Ontos in this repository.

1. Clone or download the Ontos scripts from: https://github.com/ohjona/Project-Ontos
2. Copy the `.ontos/` folder and `ontos_init.py` into my project root
3. Create `docs/reference` and copy `docs/reference/Ontos_Agent_Instructions.md` and `.ontos-internal/reference/Common_Concepts.md` into it
4. Run `python3 ontos_init.py` to initialize (installs hooks, generates context map)
5. If successful, show me the contents of Ontos_Context_Map.md
```

> See the [Ontos Manual](docs/reference/Ontos_Manual.md) for configuration options.

**Use it** - once installed, tell your Agent:

> **"Ontos"** (or "Activate Ontos")

The Agent will:
1. Follow [Agent Instructions](docs/reference/Ontos_Agent_Instructions.md).
2. Read the Context Map.
3. Load *only* the relevant files for your task.
4. Confirm what context it has loaded.

---

## Archiving

When you are done with a session:

> **"Archive Ontos"** (or "Ontos archive")

The Agent will save a log of all decisions made, ensuring no context is lost for the next session.

---

## Maintenance

To keep your graph healthy:

> **"Maintain Ontos"**

The Agent will scan for new files, rebuild the context map, and fix any integrity issues (broken links, circular dependencies).

---

## Updating

To update Ontos to the latest version:

> **"Update Ontos"**

Or manually:

```bash
python3 .ontos/scripts/ontos_update.py
```

Your `ontos_config.py` customizations are never overwritten.

---

## Use Cases

### Multi-AI Workflows
Switch between Claude Code, Cursor, ChatGPT, and Gemini without re-explaining your project. Say "Activate Ontos" and they all read from the same map.

### Prototype → Production
Built a demo in Streamlit? When you rewrite in FastAPI or Next.js, your atoms are disposable but your strategy survives. Three weeks of product decisions don't vanish with the old code.

### Project Handoffs
Pass a project to another developer or agency. Session logs + context map = instant knowledge transfer, not a 2-hour call.

### Documentation Audits
CI/CD validation catches broken links, circular dependencies, and architectural violations before they become tribal knowledge.

---

## What It Doesn't Do

- No cloud service
- No API keys
- No vendor lock-in
- Just Python scripts and markdown files in your repo

---

## Documentation

- **[Ontos Manual](docs/reference/Ontos_Manual.md)**: Complete reference — installation, workflow, configuration, errors
- **[Agent Instructions](docs/reference/Ontos_Agent_Instructions.md)**: Commands for AI agents
- **[Minimal Example](examples/minimal/README.md)**: 3-file quick start
- **[Changelog](Ontos_CHANGELOG.md)**: Version history

---

## Contributing

Contributions welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

MIT - see [LICENSE](LICENSE).
