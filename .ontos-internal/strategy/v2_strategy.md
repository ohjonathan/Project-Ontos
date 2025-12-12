---
id: v2_strategy
type: strategy
status: active
depends_on: [mission]
---

# Project Ontos: v2 Strategy

*Documented: December 2025*

## 1. Mission Link
Directly supports [mission](mission.md) by providing the strategic roadmap for the next iteration of the protocol.

## 2. The Problem (Refined for v2)

Context dies in three ways:
1.  **AI Amnesia:** Switching sessions/tools kills context.
2.  **Prototype Graveyards:** Rewrites kill product decisions buried in code.
3.  **Tribal Knowledge:** Context trapped in human heads or chat logs acts as a bottleneck.

## 3. The Solution: Dual Ontology

For v2, we are explicitly recognizing two types of context that need different handling:

1.  **The Space (Current State):** The static graph of documents (Kernel, Strategy, Product, Atom) that describes the *current* state of the project.
2.  **The Time (History):** The linear log of sessions and decisions that explains *how* we got here.

v1 focused on Space. v2 adds Time (Timeline).

## 4. Target Audience
**Agentic CLI Users:** Developers using Cursor, Claude Code, Gemini in Antigravity. They need a "shared brain" that persists across these tools.

## 5. Value Proposition
1.  **Portable Context:** One documentation system for all AI tools.
2.  **Decision Persistence:** Product decisions survive code rewrites.
3.  **Explicit Loading:** Deterministic context loading, no guessing.

## 6. v2 Strategic Shifts
-   **From "Docs" to "Graph":** Emphasize the graph nature more heavily in tooling.
-   **Self-Hosting:** Ontos must use Ontos to build Ontos (the Self-Development Protocol).
-   **Timeline First:** The session log isn't an afterthought; it's the primary way context evolves.
