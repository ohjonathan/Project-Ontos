# 🧶 Project Ontos

**Context-Aware Documentation for the Agentic Era.**

Ontos is a lightweight protocol that turns your documentation folder into a structured **Knowledge Graph**. It allows AI Agents (Cursor, Claude, Antigravity) to navigate your project intelligently, understanding dependencies and architectural decisions without hallucinating.

## � Why Ontos?

*   **Stop Hallucinations**: Agents read a map, not just random files.
*   **Zero Overhead**: Just markdown files with simple YAML headers.
*   **Agent-Native**: Built specifically for the "Agentic Workflow" (CLI tools).

## � Documentation

*   **[Installation Guide](DEPLOYMENT.md)**: How to set up Ontos in your project.
*   **[The Manual](20251124_Project%20Ontos%20The%20Manual.md)**: The complete protocol reference and usage guide.
*   **[Agent Instructions](AGENT_INSTRUCTIONS.md)**: The system prompt for your AI agents.

## ⚡️ Quick Start

Once installed, simply tell your Agent:

> **"Ontos"** (or "Activate Ontos")

The Agent will:
1.  Read the Context Map.
2.  Load *only* the relevant files for your task.
3.  Confirm what context it has loaded.

## 📦 Archiving

When you are done with a session:

> **"Archive Ontos"** (or "Ontos archive")

The Agent will save a log of all decisions made, ensuring no context is lost for the next session.
