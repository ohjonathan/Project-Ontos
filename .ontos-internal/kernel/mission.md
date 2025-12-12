---
id: mission
type: kernel
status: active
depends_on: []
---

# Project Ontos: Mission

**The Goal:** Eliminate "context death" in AI-assisted development.

## The Problem
Every time you switch AI tools, start a new chat, or hand off a project, you lose the "why" behind your code. You spend hours re-explaining architecture, product decisions, and constraints to a new blank slate. This is **context death**.

## The Solution
Ontos turns your documentation into a **portable knowledge graph** that any AI agent can read. By structuring context with simple metadata and validating it with deterministic tools, we create a persistent memory for your project that survives tool migrations and chat resets.

## Core Principles

1.  **Curated, Not Automatic:** The developer (or a responsible agent) explicitly acts as the "librarian," curating what goes into the graph. We do not dump everything into a vector database and hope RAG figures it out.
2.  **Portable & Local-First:** Context lives in the repo, not in a proprietary cloud. It travels with the code.
3.  **Git-Native:** Decisions are tracked in version control. The history of *why* we built it is as important as *what* we built.
4.  **Tool-Agnostic:** Ontos works with Claude, ChatGPT, Gemini, and whatever comes next. The protocol is universal.

## What Ontos is NOT
-   **A Database:** It's just markdown files.
-   **A Cloud Service:** It runs locally on your machine.
-   **Magic:** It requires discipline to maintain, but the payoff is sanity.
