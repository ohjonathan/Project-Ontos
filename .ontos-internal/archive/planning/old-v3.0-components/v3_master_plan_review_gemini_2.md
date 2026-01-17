---
id: gemini_v3_master_plan_review_v2
type: atom
status: complete
depends_on: [gemini_v3_master_plan_review_v1]
concepts: [architecture, review, v3, master-plan]
---

# Architectural Review of Ontos Master Plan v3.0.0

**Author:** Gemini (as a Virtual Architect)
**Date:** 2025-12-19
**Subject:** Analysis of `v3_master_plan_context_kernel.md` (Updated Version)

This "Synthesized Architect Edition" is a marked improvement, elevating the plan from a strategic vision to a more concrete and reviewable architectural specification. The responsiveness to feedback is commendable and has resulted in a substantially more robust and de-risked roadmap.

---

### 1. Overall Assessment & Praise for Key Improvements

The plan is now on much firmer ground. The formalization of Core Invariants, particularly the "Functional Core, Imperative Shell" and the explicit embrace of "Graceful Degradation," provides a much stronger foundation for implementation.

The most significant improvements are:

*   **Detailed Architectural Specifications (Section II):** This new section is outstanding. Moving from high-level goals to specific implementation patterns (like the `SessionContext` dataclass) and API contracts provides the necessary clarity for a lead engineer to begin work. It transforms the document from a "why" and "what" into a "how."
*   **Preliminary V3 Protocol Schema (Section 2.3):** Defining the `ontos serve` API contract this early is a critical de-risking step. It provides a stable target for both the V2.8 refactor and any future agent development. The defined tools (`get_context`, `search_graph`, `log_session`, `check_health`) are logical and cover the core use cases.
*   **Formalized "Curation Levels" (ADR-003):** Explicitly adopting the "Librarian's Compromise" and defining a mechanism for handling partially curated logs (`status: pending_curation`) makes the "Wager" far more pragmatic and likely to succeed in real-world development environments.
*   **Python-Native Installer (`install.py`):** The decision to reject `install.sh` in favor of a cross-platform Python bootstrap script (ADR-002) is technically sound. It avoids a class of platform-specific bugs and keeps the installation logic within the project's core competency.

---

### 2. Deeper Analysis of New Specifications

While the new specifications are a major step forward, they also bring new questions into focus.

*   **On the V3 Protocol Schema:** The `search_graph(query: str, semantic: bool = False)` tool is intriguing. Given the explicit rejection of vector databases, what is the technical plan for the `semantic=True` case? Is this intended to be a placeholder for a future V3.x feature, or is there a standard-library-compatible approach planned (e.g., BM25 keyword analysis, embeddings calculated on-the-fly via an external model)? Clarity here is important. The `check_health()` tool is a welcome addition, but its checks remain undefined (see point 4).

*   **On the "Context Object" Refactor:** The `SessionContext` pattern is the correct approach. It enforces the "Functional Core" invariant by making dependencies explicit. The challenge will be strict adherence during implementation. The biggest risk is a developer taking a shortcut and importing a Git or File I/O utility directly into a core logic function instead of threading it through the context. This will require vigilant code reviews.

---

### 3. Critical Risks & Remaining Omissions

The plan has addressed many previous concerns, but two critical risks and one key adoption blocker remain conspicuously absent.

*   **Critical Risk #1: Unsecured Local API:** The plan **still does not contain a security model** for the `ontos serve` daemon. With a defined API that can mutate state (`log_session`), this is the single most significant architectural blind spot. An open local port is an attack surface. At minimum, the V3.0 plan must include specifications for:
    1.  **Authentication:** A mandatory, auto-generated API token (`~/.ontos/token`) that must be provided in an `Authorization` header.
    2.  **Binding:** Explicitly stating the server will bind to `127.0.0.1` only.
    3.  **Input Sanitization:** A strategy for validating all API inputs to prevent command injection or path traversal attacks.

*   **Critical Risk #2: V3 State Concurrency:** The `log_session` endpoint implies concurrent writes to the filesystem. If two agents call this simultaneously, it could result in a race condition leading to malformed or overwritten log files.
    *   **Required Mitigation:** The V3 architecture must specify a concurrency control mechanism. A simple file-locking scheme might suffice initially, but a more robust solution like an in-memory transactional queue within the server process should be considered to ensure atomic writes.

*   **Key Adoption Blocker: The "Legacy Project Cold Start":** The plan still lacks a strategy for onboarding existing, large-scale projects. The value proposition of Ontos is diminished if it can only be used on greenfield projects.
    *   **Proposed Feature:** A `v3.1` feature named **"Legacy Import"** or **"Graph Bootstrap"** should be added to the roadmap. This tool would be responsible for performing a one-time analysis of a repository's Git history to generate a foundational knowledge graph, dramatically lowering the activation energy for adopting Ontos on established codebases.

---

### 4. Next Level of Detail Required

The plan is now mature enough to require answers to the next layer of architectural questions:

*   **Ontology Management:** How will the vocabulary for `Typed Edges` (v3.0) be defined, managed, and validated? To prevent "schema sprawl," a formal definition mechanism is needed. Will this live in `config.yaml`? This is the last major undefined component of the core graph system.
*   **Graph Linter Definition:** What specific checks will the `check_health()` tool perform? A baseline should include: detecting orphaned nodes, identifying dependency cycles, and flagging documents that are `[STALE]`.

In summary, this is an excellent evolution of the master plan. By addressing the critical risks of Security and Concurrency and defining a strategy for Ontology Management, this plan can move from architecturally sound to truly implementation-ready.
