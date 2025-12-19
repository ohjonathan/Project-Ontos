---
id: gemini_v3_master_plan_review_v1
type: atom
status: complete
depends_on: [master_plan_v4]
concepts: [architecture, review, v3, master-plan]
---

# Architectural Review of Ontos v3 Master Plan

**Author:** Gemini (as a Virtual Architect)
**Date:** 2025-12-19
**Subject:** Analysis of `v3_master_plan_context_kernel.md`

This document presents a clear, ambitious, and disciplined vision. The pivot from a developer toolset to an agent-facing protocol is a forward-thinking strategic leap that correctly identifies a major gap in the current AI development landscape: the need for deterministic, version-controlled context.

---

### 1. Honest Feedback & General Assessment

#### Strengths:

*   **Philosophical Clarity:** The plan's foundation on the "Zero-Dependency Rule," "Local-First" data, and the "Librarian's Wager" is its greatest strength. It establishes a robust decision-making framework that prevents architectural drift. The ADRs rejecting premature optimization (S3) and dependency bloat (Neo4j) are evidence of this discipline.
*   **Pragmatic Phasing:** The evolution from V2 (Human-centric remediation) to V3 (Agent-centric protocol) is logical. It allows the project to deliver immediate value and refine its core logic with human users before tackling the more abstract and complex agent integration.
*   **Problem-Solution Fit:** The diagnosis of "Context Death" is astute. Vector search excels at semantic similarity but fails at capturing structural and causal relationships, which are critical for robust software engineering. Ontos aims to solve this by creating a queryable, curated graph, a far more suitable data structure for the problem.

#### Critiques & Weaknesses:

*   **The "Librarian's Wager" is a High-Stakes Bet:** The core hypothesis—that developers will perform manual curation—is the project's single biggest risk. Developer time is expensive, and any added friction, no matter how small, faces a high adoption barrier. While the v2.9 scaffolding feature mitigates this, the plan is optimistic about sustained human compliance.
*   **Architectural Leap to V3:** The transition from a collection of self-contained scripts (V2) to a distributable PyPI package with a background server (V3) is a massive jump in complexity. It introduces challenges in packaging, dependency management, process management, and security that are non-trivial.
*   **The "God Object" Refactor may be Insufficient:** (Addressing Review Prompt #1) Splitting `ontos_end_session.py` into `logic` and `ui` modules is the correct first step. However, it's unlikely to be sufficient. True "headless" operation requires a deep audit for any hidden state assumptions. For example, does the logic implicitly rely on the current working directory, environment variables set by a user session, or file handles that are not explicitly passed? The refactor must be more aggressive, aiming for a library of pure functions that accept all required state as explicit arguments.

---

### 2. Potential Improvements to the Plan

*   **De-Risk the "Librarian's Wager":** (Addressing Review Prompt #2) Instead of a binary "curated or not" state, the architecture should be designed for **graceful degradation.**
    *   **Suggestion:** Formalize a multi-level curation model.
        *   **Level 0 (Zero Effort):** The system works purely on file system heuristics (the v2.9 scaffold). It can answer basic questions about file locations and dependencies inferred from imports.
        *   **Level 1 (Low Friction):** Developers use `ontos log --quick` to create simple, untagged logs. The system gains a historical timeline of changes.
        *   **Level 2 (The Wager):** Developers fully tag logs and define relationships, unlocking the full power of causal reasoning for agents.
    *   This approach provides incremental value at each level of investment, making adoption more palatable. The friction of manual tagging is most painful when its benefit is zero. For example, in a high-pressure bugfix, a developer might only do a Level 1 log, which is better than nothing.

*   **Define the V3 Protocol Now:** The plan mentions "Anthropic MCP" but doesn't specify the API. This is a critical missing piece to de-risk the V3 transition.
    *   **Suggestion:** Begin drafting a preliminary OpenAPI or GraphQL schema for the `ontos serve` API immediately. What are the core resources? `Nodes`, `Edges`, `Logs`? What are the primary endpoints? A `query` endpoint is implied, but what would its DSL look like? Defining this contract early will clarify the V2.8 refactoring goals and provide a stable target for future agent development.

*   **Address the "install.sh" Maintenance Burden:** (Addressing Review Prompt #3) The `install.sh` bootstrap script is a clever bridge, but it is indeed a maintenance risk. It couples the installation process directly to the repository's file structure.
    *   **Suggestion:** The script should not clone the `main` branch directly. It should clone a specific Git tag corresponding to a stable release. This ensures that a user running the install script gets a version of the code and the install logic that are known to work together, decoupling installation from active development. This practice should be established immediately with v2.9.

---

### 3. Overlooked Possibilities & Missing Considerations

*   **The "Legacy Project Cold Start" Problem:** The v2.9 scaffolding is for new projects. How do you apply Ontos to a 10-year-old, million-line codebase? This is the primary enterprise adoption hurdle.
    *   **Missing Solution:** A strategy for **"bulk-import" or "assisted back-fill."** This could involve a tool that ingests the entire Git history, analyzes file co-modification patterns, and uses an LLM to generate a *draft* knowledge graph and a set of `DRAFT-` prefixed log files that a human can then review and approve. Without this, Ontos risks being confined to greenfield projects.

*   **Security Model for the V3 Local Server:** A locally running server is a new attack surface. The plan completely omits this.
    *   **Missing Consideration:** A security-in-depth approach is needed.
        1.  **Authentication:** Should the server require an API token for access, even on `localhost`? This would prevent malicious scripts running on the same machine from easily accessing the context graph. The token could be stored in a config file with restricted permissions.
        2.  **CORS/Host Filtering:** The server should, by default, only bind to `127.0.0.1` and not `0.0.0.0` to prevent network exposure.
        3.  **Input Sanitization:** Any query language or API input must be rigorously sanitized to prevent injection-style attacks that could compromise the host system.

*   **Concurrency and State Management in V3:** The V2 model relies on Git for state management. The V3 server introduces live state. What happens when two agents (or an agent and a human) attempt to modify the graph simultaneously via the API?
    *   **Missing Solution:** The V3 API needs a clearly defined concurrency control model. This could be ETag-based optimistic locking for node/edge updates or a transactional system for more complex mutations. Simply putting a mutex around file writes will not be sufficient for a robust API.

*   **Graph Integrity and Validation:** The plan focuses on generating the graph but not on maintaining its health.
    *   **Missing Feature:** A "graph linter" or "health check" command (`ontos graph lint`). This tool would be invaluable for detecting:
        *   Orphaned nodes (files that have been deleted but still exist in the graph).
        *   Circular dependencies.
        *   "Stale" nodes that haven't been referenced or updated in a long time.
        *   Violations of ontological rules (e.g., a `bugfix` node that `implements` a `feature` node).
