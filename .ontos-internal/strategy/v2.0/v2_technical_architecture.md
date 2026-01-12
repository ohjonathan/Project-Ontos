---
id: v2_technical_architecture
type: strategy
status: deprecated
depends_on: [mission, philosophy, constitution]
---

> **DEPRECATED:** This is the v2.x-era technical architecture. For current architecture, see [V3.0-Technical-Architecture.md](../v3.0/V3.0-Technical-Architecture.md).

# Project Ontos: Technical Architecture (v2.x)

*Document Type: Architectural Decision Record (ADR) & Implementation Guide*

*Version: 4.0.0*

*Date: 2025-12-19*

*Status: APPROVED FOR IMPLEMENTATION*

*Target Audience: Implementation Agents (Code Generators)*

---

> **Note:** For Core Invariants (the "Constitution"), see [constitution.md](../kernel/constitution.md).

## I. Architectural Specifications

### 1.1 The "Context Object" Pattern (V2.8)

*Resolves Claude's "Hidden State" Risk.*

We must implement a **Transactional Session** pattern. The Core Logic never touches disk directly; it buffers changes.

```python
@dataclass
class SessionContext:
    repo_root: Path
    config: Dict
    pending_writes: List[FileOperation]  # The Buffer

    def commit(self):
        # 1. Acquire Lock
        # 2. Atomic write of all pending_writes
        # 3. Release Lock

    def rollback(self):
        # Clear buffer
```

### 1.2 The Configuration Cascade (V3.0)

*Resolves Claude's "Logic/Data Separation" Risk.*

When ontos (System) runs, it must resolve config in this order (Precedence High -> Low):

1. **CLI Flag:** ontos --config=x
2. **Environment:** ONTOS_CONFIG=x
3. **Repo Root:** .ontos/config.yaml (Walks up directory tree from CWD)
4. **User Home:** ~/.config/ontos/config.yaml
5. **Package Defaults**

### 1.3 The MCP Protocol Schema & Security (V3.0)

*Resolves Gemini's Security Risk.*

**Security Invariants:**

* **Binding:** 127.0.0.1 ONLY.
* **Auth:** X-Ontos-Token required (generated at ~/.ontos/token).

**JSON-RPC Tools:**

1. **get_context(focus_ids, depth, max_tokens)**: Returns Markdown. Constraint: Must handle token limits gracefully (truncation).
2. **search_graph(query)**: Constraint: Keyword/Regex search only. **No Semantic/Vector search** (Adheres to ADR-004).
3. **log_session(event, changes, decisions)**: Constraint: Must use file locking (.ontos/write.lock) to prevent race conditions.

---

## II. Architectural Decision Records (ADR)

### ADR-001: Rejection of S3 in V2.x

* **Decision:** Deferred to V3.1.
* **Rationale:** Premature Optimization. Text logs are tiny. V2 must remain Zero-Dep. V3 Server handles S3 via boto3.

### ADR-002: Python Installer (install.py) over Shell (install.sh)

* **Decision:** Accepted for V2.9.
* **Rationale:** Shell scripts are fragile (Windows vs Linux). Python is our native runtime. install.py can be signed/checksummed more reliably.

### ADR-003: Graceful Curation (Levels 0-2)

* **Decision:** Accepted.
* **Rationale:** To de-risk the "Librarian's Wager."
  * **Level 0:** Scaffold (Heuristic).
  * **Level 1:** Stub Log (User only provides Goal).
  * **Level 2:** Full Ontos (Dependencies + Concepts).

### ADR-004: Rejection of Probabilistic Search

* **Decision:** ontos serve will NOT support semantic=True (Vector Search).
* **Rationale:** Philosophical alignment. Ontos provides deterministic structure. If the user wants fuzzy search, they use the Agent's native RAG. Ontos is the Index, not the Search Engine.

---

*End of Technical Architecture v4.0.0.*
