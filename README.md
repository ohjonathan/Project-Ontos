# 🧶 Project Ontos

**Context-Aware Documentation for the Agentic Era.**

Ontos is a lightweight protocol that turns your documentation folder into a structured **Knowledge Graph**. It allows AI Agents (Cursor, Claude, Antigravity) to navigate your project intelligently, understanding dependencies and architectural decisions without hallucinating.

## � Why Ontos?

*   **Stop Hallucinations**: Agents read a map, not just random files.
*   **Zero Overhead**: Just markdown files with simple YAML headers.
*   **Agent-Native**: Built specifically for the "Agentic Workflow" (CLI tools).

## � Documentation

*   **[Ontos Installation Guide](Ontos_Installation_Guide.md)**: How to set up Ontos in your project.
*   **[Ontos Initiation Guide](Ontos_Initiation_Guide.md)**: How to tag your files and build your first graph.
*   **[The Ontos Manual](Ontos_Manual.md)**: The complete protocol reference and usage guide.
*   **[Ontos Agent Instruction](Ontos_Agent_Instructions.md)**: The system prompt for your AI agents.

## ⚡️ Quick Start

Once installed and initiated, simply tell your Agent:

> **"Ontos"** (or "Activate Ontos")

The Agent will:
0.  Follow [Ontos_Agent_Instructions.md](Ontos_Agent_Instructions.md).
1.  Read the Context Map.
2.  Load *only* the relevant files for your task.
3.  Confirm what context it has loaded.

## 📦 Archiving

When you are done with a session:

> **"Archive Ontos"** (or "Ontos archive")

The Agent will save a log of all decisions made, ensuring no context is lost for the next session.

## 🛠️ Maintenance

To keep your graph healthy:

> **"Maintain Ontos"**

The Agent will scan for new files, rebuild the context map, and fix any integrity issues (broken links, circular dependencies).
