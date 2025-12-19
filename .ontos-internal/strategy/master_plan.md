---
id: master_plan_v4
type: strategy
status: active
depends_on: [mission, v2_strategy]
---

# ***Project Ontos: Strategic Master Plan & Context Kernel***

*Document Type: Architectural Decision Record (ADR) & Strategic Roadmap*

*Version: 4.0.0 (Final Consensus Edition)*

*Date: 2025-12-19*

*Status: APPROVED FOR IMPLEMENTATION*

*Target Audience: Implementation Agents (Code Generators)*

*Repo Identity: Project-Ontos*

---

## ***0\. Meta-Instructions for Implementation Agents***

*To the AI Model generating the implementation plan:*

*You are the Lead Engineer for Project Ontos. This document is your Constitution. You must respect the Constraints, Philosophy, and "Watch-outs" defined below.*

***Core Invariants (The Constitution):***

1. ***Zero-Dependency (V2.x):** V2 tools must run on **Python Standard Library (3.9+) ONLY**. No pip install.*
2. ***System Package (V3.x):** V3.0 moves logic to PyPI (pip install ontos). This is the only time we introduce dependencies (e.g., boto3, mcp).*
3. ***Local-First:** Data lives in the user's git repo. Logic lives in the System (V3).*
4. ***Functional Core, Imperative Shell:** Logic must be separated from I/O. The "Brain" (Logic) never calls print() or input().*
5. ***The Librarian's Wager:** We trade **Higher Friction** (manual curation) for **Higher Signal** (deterministic context).*
6. ***Deterministic Purity:** We reject probabilistic retrieval (Vector/Semantic Search) in favor of structural graph traversal.*

---

## ***I. Executive Strategy: The Pivot to Protocol***

### ***1.1 The Market Gap: Context Death in a Long-Context World***

*Critique addressed: "Why does Ontos matter if Gemini has a 1M token window?"*

*Even with infinite context windows, **Signal-to-Noise Ratio** degrades.*

* ***Raw Context (The Noise):** Dumping 50 files into an LLM forces it to probabilistically guess relationships. It includes deprecated code, abandoned features, and distracting implementation details.*
* ***Curated Context (The Signal):** Ontos provides the causal graph ("Atom A implements Strategy B"). It indexes the **Time Dimension** (Logs) to explain why code exists, which is often missing from the code itself.*
* ***The Thesis:** We are not an indexing tool; we are a **Reasoning Anchor**. We provide the structure that prevents hallucination during complex refactors.*

### ***1.2 The Solution: From Tool to Protocol***

* ***V2.x (Remediation):** A stable, script-based toolset to fix immediate friction (Git conflicts, Stale docs).*
* ***V3.x (Platform):** A system-wide daemon (MCP Server) that allows Agents to "pull" context dynamically.*

---

## ***II. Master Feature Tracker (The Roadmap)***

*This table aggregates the Logic, Rationale, and specific **Implementation Watch-outs** raised by the AI Review Board.*

### ***Phase 1: Remediation (V2.x Era)***

*Theme: Internal Integrity & Friction Reduction (Target: Humans)*

| *Version* | *Feature* | *Type* | *Context & Logic (The "What")* | *Strategic Rationale (The "Why")* | *⚠️ Implementation Watch-outs (LLM Consensus)* |
| :---- | :---- | :---- | :---- | :---- | :---- |
| ***v2.7*** | ***describes Field*** | *Feat* | ***Logic:** Add frontmatter describes: \[atom\_id\]. Logic: If atom.mtime \> doc.verified\_date, flag \[STALE\].* | ***Trust.** Closes loop between Code and Docs.* | ***Codex:** Needs strict schema validation rules. Define behavior if target ID is missing (Error vs Warn). Check cross-platform mtime reliability.* |
| ***v2.7*** | ***Immutable History*** | *Fix* | ***Logic:** Regenerate decision\_history.md from logs on-demand (Read-Only).* | ***Collaboration.** Solves Git Merge Conflicts.* | ***Claude:** Ensure deterministic sorting (Timestamp \+ Branch \+ Slug) to prevent history jitter on different machines.* |
| ***v2.8*** | ***Context Object Refactor*** | ***Arch*** | ***Logic:** SessionContext dataclass. Split ontos.lib.core (Pure) vs ontos.lib.ui.* | ***V3 Prep.** Decouples "Brain" from "Mouth" for API access.* | ***Claude/Gemini:** **CRITICAL.** Do not hide state. Use "Transaction Boundaries" (commit/rollback) for file writes. Logic layer must capture all env state (CWD, Env Vars) to be testable.* |
| ***v2.8*** | ***Unified CLI (ontos.py)*** | ***UX*** | ***Logic:** Dispatcher python3 ontos.py \[init|log\]. Deprecate direct script usage.* | ***Standardization.** Trains users on V3 syntax.* | ***Codex:** Ensure this wrapper handles sys.argv parsing robustly. Provide clear deprecation warnings for old scripts.* |
| ***v2.9*** | ***install.py Bootstrap*** | *Distro* | ***Logic:** Single-file Python installer (curl-bootstrapped).* | ***Bridge.** Simulates V3 ease without PyPI overhead.* | ***Gemini:** Security Risk. Must verify checksums (SHA256) of downloaded assets. Must be idempotent (safe to run twice).* |
| ***v2.9*** | ***Schema Versioning*** | *Arch* | ***Logic:** ontos\_schema: 3.0 in frontmatter. Migration tools.* | ***Forward Compat.** Prepares for V3 transition.* | ***Claude:** Define explicit migration path. What happens if V2 script reads V3 data? (Should fail gracefully).* |
| ***v2.9*** | ***Curation Levels*** | *Growth* | ***Logic:** Level 0 (Scaffold) → Level 1 (Stub) → Level 2 (Full).* | ***Adoption.** De-risks "Librarian's Wager."* | ***Gemini:** Define strict validation rules per level. Level 1 must allow status: pending\_curation.* |

### ***Phase 2: The Platform (V3.0 Era)***

*Theme: Connectivity & Protocols (Target: Agents)*

| *Version* | *Feature* | *Type* | *Context & Logic (The "What")* | *Strategic Rationale (The "Why")* | *⚠️ Implementation Watch-outs (LLM Consensus)* |
| :---- | :---- | :---- | :---- | :---- | :---- |
| ***v3.0*** | ***pip install ontos*** | *Distro* | ***Logic:** Logic to PyPI. Repo \= Data/Config only.* | ***Separation.** Enables system deps (boto3).* | ***Claude:** **Config Management.** How does System Binary find Repo Config? (See Sec 3.2).* |
| ***v3.0*** | ***Local MCP Server*** | ***Proto*** | ***Logic:** Anthropic MCP. ontos serve. get\_context, log\_session.* | ***Inversion of Control.** Agents "pull" context.* | ***Gemini:** **SECURITY RISK.** Must bind to 127.0.0.1 only. Require auto-generated Auth Token. **Concurrency:** File locking needed.* |
| ***v3.0*** | ***Typed Edges*** | *Ontology* | ***Logic:** implements, tests, deprecates.* | ***Reasoning.** Enables A2A logic chains.* | ***Codex:** Define validation matrix (e.g., Log cannot implement Atom). Prevent "Edge Sprawl."* |
| ***v3.0*** | ***Test Suite Overhaul*** | *Arch* | ***Logic:** Restructure tests/ into core/, features/, scripts/, hooks/, legacy/. Consolidate hook tests. Add CI exclusion for legacy/.* | ***Maintainability.** Reduces test debt, clarifies mental model.* | ***Chief Architect:** Keep total test count stable. Focus on organization, not deletion. Ensure pytest discovery still works after restructure.* |

---

## ***III. Detailed Architectural Specifications (The "How")***

### ***3.1 The "Context Object" Pattern (V2.8)***

*Resolves Claude's "Hidden State" Risk.*

*We must implement a **Transactional Session** pattern. The Core Logic never touches disk directly; it buffers changes.*

*Python*

*@dataclass*

*class SessionContext:*

    *repo\_root: Path*

    *config: Dict*

    *pending\_writes: List\[FileOperation\] \# The Buffer*

    *def commit(self):*

        *\# 1\. Acquire Lock*

        *\# 2\. Atomic write of all pending\_writes*

        *\# 3\. Release Lock*

    *def rollback(self):*

        *\# Clear buffer*

### ***3.2 The Configuration Cascade (V3.0)***

*Resolves Claude's "Logic/Data Separation" Risk.*

*When ontos (System) runs, it must resolve config in this order (Precedence High \-\> Low):*

1. ***CLI Flag:** ontos \--config=x*
2. ***Environment:** ONTOS\_CONFIG=x*
3. ***Repo Root:** .ontos/config.yaml (Walks up directory tree from CWD)*
4. ***User Home:** \~/.config/ontos/config.yaml*
5. ***Package Defaults***

### ***3.3 The MCP Protocol Schema & Security (V3.0)***

*Resolves Gemini's Security Risk.*

***Security Invariants:***

* ***Binding:** 127.0.0.1 ONLY.*
* ***Auth:** X-Ontos-Token required (generated at \~/.ontos/token).*

***JSON-RPC Tools:***

1. ***get\_context(focus\_ids, depth, max\_tokens)**: Returns Markdown. Constraint: Must handle token limits gracefully (truncation).*
2. ***search\_graph(query)**: Constraint: Keyword/Regex search only. **No Semantic/Vector search** (Adheres to ADR-006).*
3. ***log\_session(event, changes, decisions)**: Constraint: Must use file locking (.ontos/write.lock) to prevent race conditions.*

---

## ***IV. Architectural Decision Records (ADR) \- "The Anti-Roadmap"***

### ***ADR-001: Rejection of S3 in V2.x***

* ***Decision:** Deferred to V3.1.*
* ***Rationale:** Premature Optimization. Text logs are tiny. V2 must remain Zero-Dep. V3 Server handles S3 via boto3.*

### ***ADR-002: Python Installer (install.py) over Shell (install.sh)***

* ***Decision:** Accepted for V2.9.*
* ***Rationale:** Shell scripts are fragile (Windows vs Linux). Python is our native runtime. install.py can be signed/checksummed more reliably.*

### ***ADR-003: Graceful Curation (Levels 0-2)***

* ***Decision:** Accepted.*
* ***Rationale:** To de-risk the "Librarian's Wager."*
  * ***Level 0:** Scaffold (Heuristic).*
  * ***Level 1:** Stub Log (User only provides Goal).*
  * ***Level 2:** Full Ontos (Dependencies \+ Concepts).*

### ***ADR-004: Rejection of Probabilistic Search***

* ***Decision:** ontos serve will NOT support semantic=True (Vector Search).*
* ***Rationale:** Philosophical alignment. Ontos provides deterministic structure. If the user wants fuzzy search, they use the Agent's native RAG. Ontos is the Index, not the Search Engine.*

---

## ***V. Validation Metrics***

***Experiment:** SWE-bench Simulation.*

* ***Control:** Standard RAG (Retrieve top-k chunks).*
* ***Test:** Ontos MCP (Retrieve focus\_ids \+ 1-hop dependencies).*
* ***Metric:** **Repair Turns** (Count of user corrections needed).*
* ***Success Criteria:** 40% reduction in Repair Turns.*

---

*End of Strategic Master Plan v4.0.0.*
