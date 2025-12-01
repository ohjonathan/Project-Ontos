# Project Ontos

[![CI](https://github.com/ohjona/Project-Ontos/actions/workflows/ci.yml/badge.svg)](https://github.com/ohjona/Project-Ontos/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

**Context-Aware Documentation for the Agentic Era.**

*Never explain twice. Own your context.*

## The Problem

I didn't want to be the orchestrator agent. Using multiple AI tools (Claude, ChatGPT, Gemini) means uploading the same documents repeatedly, each AI starting from zero and giving conflicting advice. Building several vibe coding projects, I was spending 10+ hours weekly re-establishing context across different LLMs. Each tool had its own interpretation of my intentions and owned fragments of the conversation. It felt like working with teammates who never talk to each other.

## The Solution

I built a library with disciplined librarians, and now I tell my LLMs to do their homework there. Ontos creates this shared context layer so all your agents can cooperate. Tag your docs with simple YAML headers, declare dependencies, and a generated CONTEXT_MAP.md becomes your project's memory. When you tell any AI "Activate Ontos," it reads the map, loads only relevant documents, and sees decisions from previous sessions—regardless of which AI made them. Your context becomes portable across platforms through a git-based protocol.

## Why "Ontos"?

From Greek ὄντος (ontos), meaning "being"—the root of ontology. Your documentation gains existence as a persistent knowledge graph that lives across all AI platforms, not trapped in separate chat histories.

## Key Benefits

- **Stop Hallucinations**: Agents read a map, not just random files.
- **Zero Overhead**: Just markdown files with simple YAML headers.
- **Agent-Native**: Built specifically for the "Agentic Workflow" (CLI tools).

## Documentation

### Guides
- **[Installation Guide](docs/guides/Ontos_Installation_Guide.md)**: How to set up Ontos in your project.
- **[Initiation Guide](docs/guides/Ontos_Initiation_Guide.md)**: How to tag your files and build your first graph.
- **[Migration Guide](docs/guides/MIGRATION_GUIDE.md)**: How to migrate existing documentation.

### Reference
- **[The Ontos Manual](docs/reference/Ontos_Manual.md)**: The complete protocol reference and usage guide.
- **[Agent Instructions](docs/reference/Ontos_Agent_Instructions.md)**: The system prompt for your AI agents.

### Meta
- **[Project Ontos Changelog](POCHANGELOG.md)**: Version history for Ontos tooling itself.

## Quick Start

Once installed and initiated, simply tell your Agent:

> **"Ontos"** (or "Activate Ontos")

The Agent will:
1. Follow [Agent Instructions](docs/reference/Ontos_Agent_Instructions.md).
2. Read the Context Map.
3. Load *only* the relevant files for your task.
4. Confirm what context it has loaded.

## Archiving

When you are done with a session:

> **"Archive Ontos"** (or "Ontos archive")

The Agent will save a log of all decisions made, ensuring no context is lost for the next session.

## Maintenance

To keep your graph healthy:

> **"Maintain Ontos"**

The Agent will scan for new files, rebuild the context map, and fix any integrity issues (broken links, circular dependencies).

## Development

### Running Tests

```bash
pip install pytest pytest-cov
pytest tests/ -v
```

### Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

### Script Usage

```bash
# Generate context map
python3 scripts/generate_context_map.py

# Watch for changes
python3 scripts/generate_context_map.py --watch

# Scan multiple directories
python3 scripts/generate_context_map.py --dir docs --dir specs

# Check for untagged files
python3 scripts/migrate_frontmatter.py

# Create session log
python3 scripts/end_session.py "session-name"

# Create session log with changelog entry
python3 scripts/end_session.py "session-name" --changelog
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.
