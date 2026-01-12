This is the correct strategic pivot. I have reviewed the v2.9.5 codebase, the `install.py` bootstrap, and your strategic drafts (S3 archive, Installation UX).

As your technical co-founder, my verdict is: **Ontos v2 is a library users maintain; Ontos v3 must be a service users consume.**

Your current architecture (injecting 50+ scripts into `.ontos/`) was necessary for rapid prototyping, but it violates your "simplicity" philosophy at scale. It creates "folder pollution," update friction, and security risks.

Here is the architectural specification for **Ontos v3.0: The MCP Edition**.

---

### 1. The Core Critique: Why v2.9 Won't Scale

While v2.9 is robust, three specific architectural choices block the "plug and play" MCP experience:

1. **The "Injection" Anti-Pattern:**
* **Problem:** To use Ontos, users must commit the runtime (`.ontos/scripts`) to their repo. This means every bug fix requires every user to re-run an update script.
* **Fix:** **Invert the control.** Ontos becomes a global tool (`pip install ontos`). The user's repo contains *only* data (`docs/`, `ontos.toml`).


2. **The Interactivity Trap (Critical for MCP):**
* **Problem:** Your scripts rely on `input()` (e.g., `ontos_end_session` asking for impacts).
* **Why it breaks:** MCP is "headless." An Agent cannot pause to answer a terminal prompt. If Claude calls `ontos_log_session`, the process will hang.
* **Fix:** **Pure Logic Separation.** Core functions must accept arguments (e.g., `impacts=['auth']`) and never prompt.


3. **Configuration Security:**
* **Problem:** `ontos_config.py` is executable Python.
* **Why it breaks:** A global MCP server cannot safely execute a Python file from an untrusted user directory (Arbitrary Code Execution risk).
* **Fix:** Switch to **Declarative Configuration** (`ontos.toml` or `pyproject.toml`).



---

### 2. v3.0 Architecture: "Official MCP Style"

We will move to a **Global Logic, Local Data** model.

**The Stack:**

* **Distribution:** A standard Python package (`pip install ontos`).
* **Server:** A global binary that runs the MCP server.
* **Client:** Claude Desktop, Cursor, or any MCP-compliant IDE.

**The Experience:**

* **Old (v2):** `curl install.py`, `python3 ontos_init.py`, commit files.
* **New (v3):** `pip install ontos`. Open Claude.
* *Agent:* "I see an `ontos.toml` file. I have loaded the context map."



#### The MCP Primitives Mapping

| Ontos Concept | v2 Implementation | v3 MCP Implementation |
| --- | --- | --- |
| **Context Map** | Static File (`Ontos_Context_Map.md`) | **Resource (`ontos://map/topology`)**<br>

<br>Dynamic, read-only view of the graph hierarchy. |
| **Doc Content** | File Read | **Resource (`ontos://doc/{id}`)**<br>

<br>Returns content of a specific node + immediate neighbors. |
| **Log Session** | Script (`ontos_end_session.py`) | **Tool (`ontos_log_session`)**<br>

<br>Agent calls function with `summary`, `impacts`, `type`. |
| **Validation** | Script (`ontos_maintain.py`) | **Tool (`ontos_validate`)**<br>

<br>Runs integrity checks and returns a JSON report. |
| **Archive** | Local `archive/` folder | **Tool (`ontos_search_archive`)**<br>

<br>Connects to S3 (per your draft) or local archive. |

---

### 3. Critical Features for "Bigger Layers"

To support scaling without bloating the context window, v3.0 needs these specific features:

#### A. "Lazy Loading" (The Zoomable Interface)

* **The Problem:** As you add layers, `Ontos_Context_Map.md` will exceed token limits.
* **The Solution:**
1. **Resource `ontos://map/topology**`: Returns a lightweight tree (IDs and relationships only). Cost: Low.
2. **Tool `ontos_query(id)**`: The Agent sees the tree, spots "UserAuth", and requests details.
3. **Resource `ontos://doc/user_auth**`: Server returns the full content of that node.


* *Result:* You can have 10,000 docs, but the Agent only loads the 5 relevant ones.



#### B. The "Shim" Hook (Preserving the "Prompted" Workflow)

* **The Problem:** You promised a "Prompted" mode that blocks `git push` if not archived. If we delete `.ontos/scripts`, the hook breaks.
* **The Solution:** The `ontos init` command installs a "Shim" in `.git/hooks/pre-push`:
```bash
#!/bin/sh
# Checks if global ontos is installed and delegates
if command -v ontos >/dev/null; then
    ontos hook pre-push
fi

```


This keeps the repo clean but maintains the safety net.

#### C. S3 Archive Integration

* **Context:** I reviewed your `s3_archive_implementation_plan`.
* **Implementation:** This fits perfectly as an MCP Tool.
* `ontos_archive_search(query="v2 migration")`: The server searches your S3 bucket and returns relevant historical decisions.
* This solves the "Infinite Memory" problem without bloating the local git repo.



---

### 4. Implementation Roadmap

**Phase 1: The Purge (Refactor Core)**

* Extract logic from `.ontos/scripts/ontos/core` into a standalone library structure.
* **Critical:** Remove all `input()` calls. Replace with arguments.
* Create a `ConfigParser` for `ontos.toml`.

**Phase 2: The Server (Build MCP)**

* Implement the MCP Server using the Python SDK.
* Expose `ontos://map` and `ontos_log_session`.

**Phase 3: The Migration (Release)**

* Release `ontos migrate-v3`.
* It reads `ontos_config.py`, creates `ontos.toml`, and **deletes** `.ontos/scripts`.
* It installs the Shim Hook.

### Final Verdict

**Proceed immediately.** The "MCP Style" isn't just a feature; it's the only way to satisfy your constraints of "simplicity," "lightweight," and "scaling."

**First Step:** Create a `pyproject.toml` for Project Ontos itself and begin refactoring `ontos.core` to be importable and headless.