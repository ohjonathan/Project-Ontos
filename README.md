# Project Ontos

[![CI](https://github.com/ohjona/Project-Ontos/actions/workflows/ci.yml/badge.svg)](https://github.com/ohjona/Project-Ontos/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/ontos.svg)](https://pypi.org/project/ontos/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-Source-black?logo=github)](https://github.com/ohjona/Project-Ontos)

**Portable context for the agentic era.**

*Never explain twice. Own your context.*

*Source available at [github.com/ohjona/Project-Ontos](https://github.com/ohjona/Project-Ontos).*

---

## Contents

- [The Problem](#the-problem)
- [The Solution](#the-solution)
- [Philosophy](#philosophy)
- [The Premise](#the-premise)
- [Who Ontos Is For](#who-ontos-is-for)
- [Use Cases](#use-cases)
- [Quick Start](#quick-start)
- [Workflow](#workflow)
- [Best Practices](#best-practices)
- [What Ontos Is NOT](#what-ontos-is-not)
- [FAQ](#faq)
- [Roadmap](#roadmap)
- [Documentation](#documentation)
- [Feedback](#feedback)
- [License](#license)

---

## The Problem

Context dies in three ways:

1. **AI Amnesia.** You explain your architecture to Claude. Then again to ChatGPT. Then again to Cursor. Each starts from zero.

2. **Prototype Graveyards.** You build fast in Streamlit, make dozens of product decisions, then rewrite in Next.js. The code is new. The decisions? Lost in old chat logs.

3. **Tribal Knowledge.** Your project's "why" lives in Slack threads, abandoned docs, and your head. New collaborators (human or AI) rediscover everything from scratch.

The common thread: **context isn't portable.** And even when it exists, you don't own it—it's locked in proprietary platforms, unexportable, unversioned, gone when you switch providers.

---

## The Solution

Ontos creates a **portable knowledge graph** that lives in your repo as markdown files with YAML frontmatter. No cloud service, no vendor lock-in.

**Readable, not retrievable.** Your context is a glass box—inspectable by humans, followable by AIs. Explicit structure instead of semantic search. You know exactly what the AI sees.

**How it works:**

1. Run `ontos scaffold` to auto-tag your docs with YAML headers (or add them manually if you prefer)
2. Run `ontos map` to generate your project's context map
3. Any AI agent reads the map, loads what's relevant, sees the full decision history

```yaml
---
id: pricing_strategy
type: strategy
depends_on: [target_audience, mission]
---
```

**The hierarchy** (rule of thumb: "If this doc changes, what else breaks?"):

| Layer | What It Captures | Survives Migration? |
|-------|------------------|---------------------|
| `kernel` | Why you exist, core values | ✅ Always |
| `strategy` | Goals, audience, approach | ✅ Always |
| `product` | Features, user flows, requirements | ✅ Always |
| `atom` | Implementation details | ⚠️ Often rewritten |

Your prototype atoms get rewritten. Your product decisions don't. Interface specs and data models often survive—implementation code rarely does.

---

## Philosophy

**Intent over automation.** You decide what matters. Tagging a session, connecting decisions to documents—this friction is the feature. Curation beats capture.

**You own your context.** Markdown in your repo, not locked in someone else's platform. No database, no account, no API key. It travels with `git clone`.

**Shared memory over personal memory.** What you remember is useless to your teammate or the AI that just opened a fresh session. Ontos encodes knowledge at the repo level. Everyone who clones gets the same brain.

**Decisions outlive code.** Ontos separates Space (what IS true) from Time (what HAPPENED). Your implementation atoms get rewritten on migration. Your strategy, your product decisions, your session logs—those survive.

---

## The Premise

- **LLMs get better; your tooling should too.** Ontos doesn't fight the model—it gives the model better input. As agents improve, structured context becomes more valuable, not less.
- **Platforms won't solve portability for you.** Vendor lock-in is a feature, not a bug, for model providers. If you want context that moves freely, you have to own it yourself.
- **"Vibe coding" becomes "context engineering."** The bottleneck isn't generating code anymore. It's giving the AI enough context to generate the *right* code.

---

## Who Ontos Is For

- **Small teams (1-5 devs) switching between AI tools** who are tired of re-explaining their project to Claude, then Cursor, then ChatGPT
- **Projects that outlive their prototypes**—when you rewrite from Streamlit to Next.js, your decisions should survive the migration
- **Developers who want context to transfer** across session resets, tool switches, and team changes
- **Anyone betting on AI-assisted development** who needs reliable, portable project memory

The litmus test: *Can a new person (or AI) become productive in under 10 minutes?*

---

## Use Cases

### Multi-AI Workflows
Switch between Claude Code, Cursor, ChatGPT, and Gemini without re-explaining your project. Ontos can generate `AGENTS.md` and `.cursorrules` so your context activates automatically when supported.

### Prototype → Production
Built a demo in Streamlit? When you rewrite in FastAPI or Next.js, your atoms are disposable but your strategy survives. Three weeks of product decisions don't vanish with the old code.

### Project Handoffs
Pass a project to another developer or agency. Because you own your context, everything travels with `git clone`—session logs, context map, decision history. No export wizard, no platform migration, no 2-hour call.

### Documentation Health
CI validation catches broken links, circular dependencies, and architectural violations before they become tribal knowledge buried in someone's head.

---

## Quick Start

**Requirements:** Python 3.9+, inside a git repository

**Install (recommended):**

```bash
# pipx installs in an isolated environment and adds to PATH automatically
pipx install ontos
```

> [!TIP]
> Don't have pipx? Install it with `brew install pipx` (macOS) or `pip install pipx`. See [pipx docs](https://pipx.pypa.io/).

**Alternative install:**

```bash
pip install ontos
```

> [!NOTE]
> **"command not found: ontos"?** Your Python scripts directory may not be on PATH.
> - **Quick fix:** Use `python -m ontos` instead (e.g., `python -m ontos map`)
> - **Permanent fix:** Add Python's bin directory to your PATH (the `pip install` output shows the location)

Source available at [github.com/ohjona/Project-Ontos](https://github.com/ohjona/Project-Ontos).

**Initialize:**

```bash
cd your-project
ontos init
```

This creates:
- `.ontos.toml` configuration file
- `docs/` directory with full type hierarchy (`kernel/`, `strategy/`, `product/`, `atom/`, `logs/`, `reference/`, `archive/`)
- `Ontos_Context_Map.md` document graph
- Git hooks (optional)
- `AGENTS.md` for AI agent activation (optional)

**Scaffold existing docs:** If you have existing markdown files, init will prompt to add Ontos metadata:
```bash
ontos init --scaffold    # Auto-scaffold docs/ without prompting
ontos init --no-scaffold # Skip scaffold prompt entirely
```

**Activate:** Tell any AI agent that supports Ontos activation:

> **"Ontos"** (or "Activate Ontos")

If configured, the agent reads `AGENTS.md`, regenerates the context map, loads relevant files, and confirms what context it has.

---

## Workflow

### Agent Prompts

Use these phrases with an AI agent that supports Ontos activation. They are not shell commands.

| Command | What It Does |
|---------|--------------|
| **"Ontos"** | Activate context—agent reads the map, loads relevant files |
| **"Archive Ontos"** | End session—save decisions as a log for next time |
| **"Maintain Ontos"** | Health check—scan for new files, fix broken links, regenerate map |

```bash
# CLI equivalents
ontos scaffold     # Auto-tag docs with YAML frontmatter
ontos map          # Generate/update context map
ontos log          # Create a session log
ontos doctor       # Check graph health
ontos agents       # Regenerate AGENTS.md and .cursorrules
```

**Update:** `pipx upgrade ontos` or `pip install --upgrade ontos`

---

## Best Practices

- **Start from the top.** Define kernel and strategy before creating atoms. The hierarchy exists for a reason.
- **Curate, don't hoard.** Not every session needs a log. Archive the ones with decisions that matter.
- **Review scaffold output.** Auto-tagging proposes; you decide. The human judgment is the point.
- **Run `ontos doctor` periodically.** Catch broken links and dependency issues before they compound.
- **Scan for secrets before release.** Use `gitleaks detect` and `trufflehog git file://. --no-update` (see `.trufflehog-exclude-paths.txt`).

---

## What Ontos Is NOT

- **Not a RAG system.** We use structural graph traversal, not semantic search. Concepts are curated tags, not vector embeddings. Deterministic beats probabilistic for critical decisions.
- **Not zero-effort.** You decide what matters (curation). The tooling handles the paperwork (tagging, validation, map generation).
- **Not a cloud service.** Markdown files in your repo. No API keys, no accounts.
- **Not magic.** The graph and map are deterministic—same input, same output. What the AI *does* with that context is still AI.

If you want automatic context capture, use a vector database. If you want reliable, portable, inspectable context, use Ontos.

---

## FAQ

### Why does Ontos start at version 3?

Versions 1 and 2 were internal. I built Ontos as a personal tool to manage context across AI sessions and tech stack migrations. After using it for months and seeing others struggle with the same problems—re-explaining projects to each new AI, losing decisions when prototypes get rewritten—I packaged the workflow as a Python library.

Version 3 is when Ontos became public. The earlier versions live on in the design decisions and battle-tested workflows, just not in a public release.

---

## Roadmap

| Version | Status | Highlights |
|---------|--------|------------|
| **v3.2.0** | ✅ Current | Re-architecture support, environment detection, activation resilience |
| **v3.3** | Next | Decision capture, typed dependencies, import capability |
| **v4.0** | Vision | MCP as primary interface, full template system, daemon mode |

v3.0 transformed Ontos from repo-injected scripts into a pip-installable package. v3.1 made all CLI commands native Python. v3.2 adds re-architecture support for stack migrations, environment detection for faster onboarding, and activation resilience for cheaper context recovery.

---

## Documentation

> *Note: Documentation links below point to the latest source on GitHub and may reflect features not yet released.*

- **[Ontos Manual](https://github.com/ohjona/Project-Ontos/blob/main/docs/reference/Ontos_Manual.md)**: Complete reference—installation, workflow, configuration, errors
- **[Agent Instructions](https://github.com/ohjona/Project-Ontos/blob/main/docs/reference/Ontos_Agent_Instructions.md)**: Commands for AI agents
- **[Migration Guide v2→v3](https://github.com/ohjona/Project-Ontos/blob/main/docs/reference/Migration_v2_to_v3.md)**: Upgrading from v2.x
- **[Minimal Example](https://github.com/ohjona/Project-Ontos/blob/main/examples/minimal/README.md)**: 3-file quick start
- **[Changelog](https://github.com/ohjona/Project-Ontos/blob/main/Ontos_CHANGELOG.md)**: Version history

---

## Feedback

Issues and feature requests welcome via [GitHub Issues](https://github.com/ohjona/Project-Ontos/issues).

---

## License

Apache-2.0. See [LICENSE](LICENSE).

### Why Apache-2.0?

Ontos exists because context should be portable and owned by you. A restrictive license would contradict that philosophy.

You can use, modify, distribute, and build commercial products on Ontos. The requirements: include the license text, keep copyright notices, and note significant changes if you redistribute. Apache-2.0 also includes a patent grant from contributors (though not from unrelated third parties).

### Contributing

Issues and PRs welcome. If you're planning something substantial, open an issue first so we can align on direction.
