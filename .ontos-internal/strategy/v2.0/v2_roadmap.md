---
id: v2_roadmap
type: strategy
status: deprecated
depends_on: [mission, philosophy]
---

> **DEPRECATED:** This is the v2.x-era roadmap. For current implementation plans, see [V3.0-Implementation-Roadmap.md](../v3.0/V3.0-Implementation-Roadmap.md).

# Project Ontos: Roadmap (v2.x)

*Document Type: Strategic Roadmap*

*Version: 4.0.0*

*Date: 2025-12-19*

*Status: APPROVED FOR IMPLEMENTATION*

---

## I. Executive Strategy: The Pivot to Protocol

### 1.1 The Market Gap: Context Death in a Long-Context World

*Critique addressed: "Why does Ontos matter if Gemini has a 1M token window?"*

*Even with infinite context windows, **Signal-to-Noise Ratio** degrades.*

* **Raw Context (The Noise):** Dumping 50 files into an LLM forces it to probabilistically guess relationships. It includes deprecated code, abandoned features, and distracting implementation details.
* **Curated Context (The Signal):** Ontos provides the causal graph ("Atom A implements Strategy B"). It indexes the **Time Dimension** (Logs) to explain why code exists, which is often missing from the code itself.
* **The Thesis:** We are not an indexing tool; we are a **Reasoning Anchor**. We provide the structure that prevents hallucination during complex refactors.

### 1.2 The Solution: From Tool to Protocol

* **V2.x (Remediation):** A stable, script-based toolset to fix immediate friction (Git conflicts, Stale docs).
* **V3.x (Platform):** A system-wide daemon (MCP Server) that allows Agents to "pull" context dynamically.

---

## II. Feature Tracker

### Phase 1: Remediation (V2.x Era)

*Theme: Internal Integrity & Friction Reduction (Target: Humans)*

| *Version* | *Feature* | *Type* | *Context & Logic (The "What")* | *Strategic Rationale (The "Why")* | *Implementation Watch-outs* |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **v2.7** | **describes Field** | *Feat* | **Logic:** Add frontmatter describes: \[atom\_id\]. Logic: If atom.mtime \> doc.verified\_date, flag \[STALE\]. | **Trust.** Closes loop between Code and Docs. | **Codex:** Needs strict schema validation rules. Define behavior if target ID is missing (Error vs Warn). Check cross-platform mtime reliability. |
| **v2.7** | **Immutable History** | *Fix* | **Logic:** Regenerate decision\_history.md from logs on-demand (Read-Only). | **Collaboration.** Solves Git Merge Conflicts. | **Claude:** Ensure deterministic sorting (Timestamp \+ Branch \+ Slug) to prevent history jitter on different machines. |
| **v2.8** | **Context Object Refactor** | **Arch** | **Logic:** SessionContext dataclass. Split ontos.lib.core (Pure) vs ontos.lib.ui. | **V3 Prep.** Decouples "Brain" from "Mouth" for API access. | **Claude/Gemini:** **CRITICAL.** Do not hide state. Use "Transaction Boundaries" (commit/rollback) for file writes. Logic layer must capture all env state (CWD, Env Vars) to be testable. |
| **v2.8** | **Unified CLI (ontos.py)** | **UX** | **Logic:** Dispatcher python3 ontos.py \[init\|log\]. Deprecate direct script usage. | **Standardization.** Trains users on V3 syntax. | **Codex:** Ensure this wrapper handles sys.argv parsing robustly. Provide clear deprecation warnings for old scripts. |
| **v2.9** | **install.py Bootstrap** | *Distro* | **Logic:** Single-file Python installer (curl-bootstrapped). | **Bridge.** Simulates V3 ease without PyPI overhead. | **Gemini:** Security Risk. Must verify checksums (SHA256) of downloaded assets. Must be idempotent (safe to run twice). |
| **v2.9** | **Schema Versioning** | *Arch* | **Logic:** ontos\_schema: 3.0 in frontmatter. Migration tools. | **Forward Compat.** Prepares for V3 transition. | **Claude:** Define explicit migration path. What happens if V2 script reads V3 data? (Should fail gracefully). |
| **v2.9** | **Curation Levels** | *Growth* | **Logic:** Level 0 (Scaffold) → Level 1 (Stub) → Level 2 (Full). | **Adoption.** De-risks "Librarian's Wager." | **Gemini:** Define strict validation rules per level. Level 1 must allow status: pending\_curation. |

### Phase 2: The Platform (V3.0 Era)

*Theme: Connectivity & Protocols (Target: Agents)*

| *Version* | *Feature* | *Type* | *Context & Logic (The "What")* | *Strategic Rationale (The "Why")* | *Implementation Watch-outs* |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **v3.0** | **pip install ontos** | *Distro* | **Logic:** Logic to PyPI. Repo \= Data/Config only. | **Separation.** Enables system deps (boto3). | **Claude:** **Config Management.** How does System Binary find Repo Config? (See Technical Architecture). |
| **v3.0** | **Local MCP Server** | **Proto** | **Logic:** Anthropic MCP. ontos serve. get\_context, log\_session. | **Inversion of Control.** Agents "pull" context. | **Gemini:** **SECURITY RISK.** Must bind to 127.0.0.1 only. Require auto-generated Auth Token. **Concurrency:** File locking needed. |
| **v3.0** | **Typed Edges** | *Ontology* | **Logic:** implements, tests, deprecates. | **Reasoning.** Enables A2A logic chains. | **Codex:** Define validation matrix (e.g., Log cannot implement Atom). Prevent "Edge Sprawl." |
| **v3.0** | **Test Suite Overhaul** | *Arch* | **Logic:** Restructure tests/ into core/, features/, scripts/, hooks/, legacy/. Consolidate hook tests. Add CI exclusion for legacy/. | **Maintainability.** Reduces test debt, clarifies mental model. | **Chief Architect:** Keep total test count stable. Focus on organization, not deletion. Ensure pytest discovery still works after restructure. |

---

## III. Validation Metrics

**Experiment:** SWE-bench Simulation.

* **Control:** Standard RAG (Retrieve top-k chunks).
* **Test:** Ontos MCP (Retrieve focus\_ids \+ 1-hop dependencies).
* **Metric:** **Repair Turns** (Count of user corrections needed).
* **Success Criteria:** 40% reduction in Repair Turns.

---

## IV. Document Lifecycle

| Status | Meaning |
|--------|---------|
| `draft` | Planning phase, open questions |
| `active` | Being implemented |
| `complete` | Implemented and released |

**Archival:** Once a major version is released and the next version stabilizes, move its `strategy/` and `proposals/` directories to `archive/`.

---

*End of Roadmap v4.0.0.*
