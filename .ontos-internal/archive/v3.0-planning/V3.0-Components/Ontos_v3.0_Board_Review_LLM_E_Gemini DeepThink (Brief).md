# Ontos v3.0 Board Review: LLM [E] Response

## A. Analysis Verification

### Accurately Captured

* **"Tool to Protocol" Pivot:** The synthesis correctly identifies my central thesis: Ontos must transition from a manually invoked tool to a system-invoked protocol.
* **"Interactivity Trap":** My warning that `input()` calls in the "God Script" are fatal for headless/agentic integration was correctly noted.
* **Shim Hooks:** My recommendation for `.git/hooks/pre-push` delegating to a global command was correctly attributed.
* **Legacy `install.py` as Anti-Pattern:** The synthesis correctly captured my stance that script injection is obsolete in a `pip` distribution model.

### Corrections Needed

* **Hybrid Persistence Attribution:** The synthesis attributes the "Hybrid Persistence" rule (generating Markdown for humans while serving Agents) to LLM [D]. While I support this, I explicitly argued for it as the *architectural mechanism* to ensure "Glass Box" compliance in a protocol architecture.
* **Daemon Necessity:** The synthesis implies I viewed the daemon as "essential" for the v3.0 launch. To clarify: I view the *Protocol* as essential. A daemon is one implementation, but a CLI returning structured data (JSON) can also serve as a primitive protocol. I accept the decision to defer the daemon if the CLI becomes sufficiently machine-readable.

### Omitted Points

* **The "Library vs. App" Architecture:** In my analysis of the pivot to `pip install`, I emphasized that the internal architecture must strictly separate the *library* (pure logic) from the *app* (CLI/Server). The synthesis mentions "Script Reorganization" generally, but misses that this is the specific architectural enabler for the "Layer Strategy" (Core vs. MCP) to work without refactoring twice.

## B. Decision Review

### Distribution Model

* **pip install ontos (ADOPTED):** [Agree] — Essential for the "Protocol" vision; the code must exist independently of the user's repo.
* **MCP as optional (ADOPTED):** [Agree] — A pragmatic compromise. It avoids over-engineering v3.0 while preparing the architecture.
* **MCP as primary (DECLINED):** [Agree] — Agents aren't mature enough to be the *only* interface yet; humans still need a CLI.
* **Legacy install.py (DECLINED):** [Agree] — Good riddance. It is technical debt.

### Architecture

* **Global CLI + local data (ADOPTED):** [Agree] — The Git pattern is the gold standard for this problem domain.
* **Daemon as default (DECLINED):** [Agree] — Reducing operational complexity aligns with "Simplicity." As long as the *code* is refactored to be importable (headless), the daemon can come later.
* **Functional Core/Imperative Shell (ADOPTED):** [Agree] — Critical for testing and the eventual MCP layer.

### Core Features

* **Magic defaults (ADOPTED):** [Agree] — Friction is the enemy of adoption.
* **Doctor command (ADOPTED):** [Agree] — Essential for diagnosing environment issues in a `pip` installed world where we don't control the Python path.
* **Declarative config (ADOPTED):** [Agree] — Executable config is a security risk and harder for agents to parse/modify safely.

### Scalability

* **S3 archive (DEFERRED):** [Agree] — Solves a problem 99% of users don't have yet. Local-first is the correct v3.0 focus.
* **Cross-repo federation (DEFERRED):** [Agree] — Complexity trap.

### Risks

* **MCP security model (ADOPTED):** [Agree] — Agents are remote code execution engines; caution is warranted.
* **Clean script architecture (ADOPTED):** [Agree] — This is the most critical technical debt item.

## C. Open Questions

### Q1: JSON Output Mode

**Recommendation:** Option A

**Confidence:** High

**Philosophy Alignment:** Aligns
"Glass box" means data is accessible. Agents read JSON better than Markdown tables.

**Reasoning:**

* **The "Protocol" Requirement:** If we are pivoting to a "Protocol" mindset, we must speak the language of agents (JSON). Even without an MCP server, an agent can run `ontos map --json` to get a structured understanding of the graph.
* **Programmatic Composition:** This enables users to write their own scripts (e.g., CI checks) that consume Ontos data without parsing Markdown regex.
* **Bridge to MCP:** The JSON output logic built now becomes the MCP resource payload later.

**Implementation Complexity:** Low

* ~1-2 days. If the internal data structures are clean dicts/dataclasses, just expose `json.dump`.

### Q2: Export to CLAUDE.md / AGENTS.md

**Recommendation:** Option B

**Confidence:** High

**Philosophy Alignment:** Aligns
"Simplicity" and "Zero-dep". Ontos is the source of truth, not a converter factory.

**Reasoning:**

* **Avoid Vendor Lock-in:** Ontos should be the universal standard. Generating `CLAUDE.md` implies Claude can't read `Ontos_Context_Map.md`. We should train agents to read Ontos, not degrade Ontos to fit agents.
* **Maintenance Burden:** Every time Anthropic or OpenAI changes their preferred context format, we have to update Ontos.
* **Redundancy:** The Context Map *is* the `AGENTS.md`.

**Implementation Complexity:** Low

* Easy to do, but creates ongoing maintenance debt.

### Q3: Lazy Loading / Context Slicing

**Recommendation:** Option A

**Confidence:** Medium

**Philosophy Alignment:** Tension
Adds complexity, but necessary for "Lightweight" usage in large repos.

**Reasoning:**

* **Token Budgeting:** "Readable, not retrievable" breaks when the map exceeds the context window.
* **The "Protocol" View:** We need a way to say "Give me the high-level map" vs "Give me the details of this module."
* **Implementation:** This doesn't need to be over-engineered. `ontos map --depth 1` or `ontos map --slice strategy` is sufficient for the CLI version.

**Implementation Complexity:** Medium

* Requires graph traversal logic to filter nodes before rendering.

### Q4: Passive Observation (Watchdog)

**Recommendation:** Option C

**Confidence:** High

**Philosophy Alignment:** Aligns
"Curation over ceremony." Automation should assist, not replace, judgment.

**Reasoning:**

* **The "Glass Box" Rule:** Background processes doing "magic" updates violate the glass box principle. Users should know exactly when the graph changes.
* **Reliability:** Watchdog on different OSs (Windows/Mac/Linux) is finicky and adds dependencies.
* **Workflow:** Detect changes at `ontos log` time by checking git status/diffs (which we do anyway) is safer than running a daemon.

**Implementation Complexity:** Low

* I recommend achieving Option C using **stateless** checks (Git diffs) rather than a stateful `watchdog` dependency.

**Dissent Note:**
I strongly advise **against** using the `watchdog` library (Option A technology). It is heavy and unnecessary for "detect-and-flag." Use `git diff --name-only` at runtime.

### Q5: Version Pinning in .ontos.toml

**Recommendation:** Option A

**Confidence:** High

**Philosophy Alignment:** Aligns
"Simplicity" includes "predictability." Version mismatch chaos is not simple.

**Reasoning:**

* **Protocol Stability:** If v3.1 introduces a new schema that v3.0 doesn't understand, a team member on the old version could corrupt the graph.
* **Low Friction:** It's a one-time config. The error message "Please run `pip install --upgrade ontos`" is helpful, not annoying.

**Implementation Complexity:** Low

* Simple semver check at startup.

### Q6: Shim Hooks for Git

**Recommendation:** Option A

**Confidence:** High

**Philosophy Alignment:** Aligns
"Local-first" data, "Global" tooling.

**Reasoning:**

* **The "Injection" Antidote:** We decided to kill `install.py` to stop injecting scripts. We must not replace it with injecting 500 lines of hook logic.
* **Mechanism:** The hook file in the repo should be a 3-line shell script: `ontos hook pre-push "$@"`.
* **Updates:** When we update Ontos logic, the hook logic updates automatically without the user needing to re-copy files into `.git/hooks`.

**Implementation Complexity:** Low

* The `ontos hook` subcommand needs to be written, but it just calls the existing validation logic.

### Q7: Auto-Configure MCP Clients

**Recommendation:** Option B

**Confidence:** Medium

**Philosophy Alignment:** Aligns
"Simplicity" vs "Glass box." Touching external config files is "Black box" behavior.

**Reasoning:**

* **Consent:** Modifying a user's `claude_desktop_config.json` is aggressive. If we break it, we break their entire IDE setup.
* **Transparency:** Print the JSON snippet they need to add. Let them paste it. It teaches them how the connection works.

**Implementation Complexity:** Low

* Documentation only.

### Q8: Context Slicing Without Sacrificing Lightweight

**Recommendation:** Option A (Progressive/Directories)

**Confidence:** Medium

**Philosophy Alignment:** Aligns
Uses existing structure (folders) rather than new metadata.

**Reasoning:**

* **Natural Slicing:** Users already organize code into directories. `ontos map --path core/` should generate a map of just that subgraph.
* **Simplicity:** No new DB or index needed. Just filter the file list before building the graph.
* **Scalability:** Large projects naturally split into folders. Slicing by folder scales perfectly with project organization.

**Implementation Complexity:** Medium

* Requires ensuring that dependencies *outside* the slice are handled gracefully (e.g., shown as "External References").

### Q9: MCP Security Model

**Recommendation:** Option B (Minimal/Localhost)

**Confidence:** Medium

**Philosophy Alignment:** Aligns
"Simplicity."

**Reasoning:**

* **Threat Model:** The MCP server is running locally, started by the user. It has the same permissions as the user. Sandboxing it protects against... the user?
* **Overhead:** Auth tokens and audit logs for a localhost CLI tool are overkill and add friction.
* **Constraint:** Bind to `127.0.0.1` explicitly. Do not allow network access.

**Implementation Complexity:** Low

* Standard socket binding.

### Q10: Pydantic Requirement

**Recommendation:** Option B

**Confidence:** High

**Philosophy Alignment:** Aligns
"Zero-dep core" is preserved.

**Reasoning:**

* **Core Purity:** The core logic (reading markdown, validating schema) does not strictly need Pydantic. `dict.get()` works fine.
* **Protocol Rigor:** The MCP layer *does* need Pydantic to ensure the JSON-RPC messages are perfect.
* **Separation:** `pip install ontos` (Core) = No Pydantic. `pip install ontos[mcp]` = Installs Pydantic.

**Implementation Complexity:** Medium

* Requires strict discipline to not import Pydantic in `ontos.core`.

### Q11: Script Reorganization Approach

**Recommendation:** Option A

**Confidence:** High

**Philosophy Alignment:** Aligns
"Glass box." The code structure should explain itself.

**Reasoning:**

* **The "God Script" Problem:** You cannot distribute `ontos_end_session.py` (1600 lines) as a library module. It must be broken down.
* **Module Structure:**
* `ontos.core.graph` (The logic)
* `ontos.core.io` (The markdown handling)
* `ontos.cli.commands` (The imperative shell)
* `ontos.server` (The future MCP layer)


* **Payoff:** This makes adding JSON output (Q1) or Shim Hooks (Q6) trivial because they just call `ontos.core.*`.

**Implementation Complexity:** High

* This is the biggest task in v3.0. It requires a rewrite of the entry points.

### Q12: Python vs Node/TS for MCP

**Recommendation:** Option A

**Confidence:** High

**Philosophy Alignment:** Aligns
"Lightweight" and "Simplicity." Splitting the stack violates both.

**Reasoning:**

* **Single Source of Truth:** If the Core is Python, the Server MUST be Python. Otherwise, you have to rewrite the graph parsing logic in TS. That leads to two implementations of the "Truth" and inevitable drift.
* **Ecosystem:** The Python MCP SDK is official and maintained. We don't need the mature Node ecosystem features; we just need basic stdio transport.

**Implementation Complexity:** Low

* Stick to what we have.

### Q13: JSON vs Markdown as Primary Output

**Recommendation:** Option B

**Confidence:** High

**Philosophy Alignment:** Aligns
"Readable, not retrievable."

**Reasoning:**

* **Human First:** Ontos is for the Human-AI team. Humans lose if the primary artifact becomes machine-code.
* **Git Friendly:** Markdown diffs are readable in PRs. JSON diffs are noise.
* **Protocol:** Use `ontos map --json` for the machine (Q1). Keep `Ontos_Context_Map.md` for the repo (Q13).

**Implementation Complexity:** Low

* Status quo.

## D. Cross-Cutting Concerns

### Interdependencies

* **Q6 (Shim Hooks) & Q11 (Script Reorg):** Shim hooks rely on the `ontos` CLI being fast and modular. If we don't fix the "God Script" (Q11), the hooks will be slow and clumsy.
* **Q1 (JSON) & Q13 (MD Primary):** My answers balance each other. MD stays primary on disk (Q13), but JSON is added as a CLI output (Q1) to satisfy the "Protocol" need without breaking "Readability."
* **Q4 (Watchdog) & "Zero-Dep":** My recommendation to use `git diff` instead of `watchdog` library is critical to maintaining the "Zero Dependency" core.

### Priority Recommendation

1. **Q11 Script Reorganization:** You cannot distribute a "God Script" via pip effectively. This is the foundation for everything else.
2. **Q6 Shim Hooks:** This is the bridge that allows you to delete `install.py` without losing the safety net.
3. **Q1 JSON Output:** This is the low-cost bridge to the future MCP world. It allows agents to "use" Ontos structurally before the server exists.

### Risk Flag

**The "Hidden" State Risk:** By moving to `pip install`, we hide the logic. In v2, users could fix a broken script in their repo. In v3, they assume it works. If `ontos` crashes, they are stuck. **Mitigation:** The `ontos doctor` command is not optional; it is critical for a "hidden" tool.

### Philosophy Check

The decision to defer **S3** and **Daemon** heavily reinforces "Local-first" and "Simplicity." The shift to **pip** reinforces "Lightweight" (user repo is cleaner). However, the **Script Reorganization** (Q11) runs a risk of over-engineering. We must ensure the new module structure remains "Simpler than a framework" — it should still look like a collection of utilities, not an enterprise Java app.