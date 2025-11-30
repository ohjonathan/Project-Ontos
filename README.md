# Project Ontos

[![CI](https://github.com/ohjona/Project-Ontos/actions/workflows/ci.yml/badge.svg)](https://github.com/ohjona/Project-Ontos/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

**Context-Aware Documentation for the Agentic Era.**

Ontos is a lightweight protocol that turns your documentation folder into a structured **Knowledge Graph**. It allows AI Agents (Cursor, Claude, Gemini) to navigate your project intelligently, understanding dependencies and architectural decisions without hallucinating.

## Why Ontos?

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
