# Ontos v3.0 Board Review: LLM [A] Response

## A. Analysis Verification

### Accurately Captured

* My core stance that **pip distribution + global CLI with repo-local data** is the right v3 foundation is captured correctly. 
* My “MCP should be optional, not the primary interface” position is captured correctly. 
* My unique recommendations are captured correctly: `ontos doctor`, JSON output mode as an open question, and concurrency hardening via unique temp files and atomic replace. 

### Corrections Needed

* **MCP timing:** Synthesis says I was “middle ground - v3.1/v3.2”. 
  I did not recommend specific version numbers. My actual view was “design for MCP now, ship it only when the local CLI feels rock-solid” and I explicitly warned against making MCP the only front door.
* **S3 archive framing:** Synthesis says “LLM A, E recommend S3 as MCP Tool for ‘infinite memory’.” 
  My point was: keep local-first as the default, and if you ever add remote storage, it should be an optional backend. Whether it’s exposed via MCP tools or CLI is secondary.

### Omitted Points

* The “workspace safety model” I suggested for MCP-style execution: explicit repo root, path allowlisting, read-only default, and clear write gating. This is the core of making an MCP layer non-scary.
* Treating “prompts” as first-class distributables when MCP arrives, so users don’t have to copy magic incantations.
* “Git-based change detection” as a dependency-free alternative to watchdog for passive observation.

---

## B. Decision Review

### Distribution Model

* **pip install ontos (ADOPTED):** Agree — this is the cleanest “install once, use everywhere” path and matches your friction goals. 
* **MCP as optional (ADOPTED):** Agree — MCP should be an integration layer, not a requirement. 
* **MCP as primary (DECLINED):** Agree — making MCP primary would turn “just works” into “configure a server”. 
* **Legacy install.py (DECLINED):** Agree — given “founder-only user base”, cutting it reduces surface area and maintenance. 

### Architecture

* **Global CLI + local data (ADOPTED):** Agree — it’s the “git mental model” and preserves local-first. 
* **Functional Core / Imperative Shell (ADOPTED):** Agree — it’s the correct seam for future protocol layers. 
* **Daemon as default (DECLINED):** Agree — too much operational complexity for baseline value. 
* **MCP server timing (DEFERRED):** Agree — stabilize local UX first, then add MCP as a layer. 

### Core Features

* **Magic defaults / zero-config (ADOPTED):** Agree — this is how you actually win on friction. 
* **Doctor/health command (ADOPTED):** Agree — huge ROI and makes packaging migration survivable. 
* **Kill python3 ontos.py syntax (ADOPTED):** Agree — a real `ontos` entrypoint is table stakes for v3. 
* **Declarative config TOML (ADOPTED):** Agree — safer than executable config and easier to reason about. 
* **Progressive disclosure (ADOPTED):** Agree — keeps power without scaring new users. 

### Scalability

* **S3 archive backend (DEFERRED):** Agree — keep local-first; add optional storage only when you have a real pain. 
* **Cross-repo federation (DEFERRED):** Agree — this is a v4 problem unless enterprise use appears now. 

### Risks

* **Staged implementation (ADOPTED):** Agree — reduces “migration death spiral” even if you’re the only user. 
* **Clean script architecture (ADOPTED):** Agree — packaging is the moment to pay down the “25 scripts / god script” tax. 
* **Zero-dependency rule preserved (ADOPTED):** Agree — keep core tiny; push protocol extras behind optional installs. 

---

## C. Open Questions

### Q1: JSON Output Mode

**Recommendation:** Option A

**Confidence:** High

**Philosophy Alignment:** Aligns
Markdown stays human-first. JSON as an optional flag improves “glass box” automation without changing the core truth files.

**Reasoning:**

* JSON output becomes immediately useful for scripting, CI checks, and future MCP tooling without redesign.
* It’s easy to keep optional and stable, minimizing cognitive load.
* The trade-off is extra surface area, but it’s contained behind `--json`.

**Implementation Complexity:** Low

* Effort estimate: ~1–2 days
* Dependencies: none
* Risk: schema churn if you don’t version the JSON format up front

---

### Q2: Export to CLAUDE.md / AGENTS.md

**Recommendation:** Alternative: implement a generic `ontos export` with template presets, including `CLAUDE.md` and `AGENTS.md`, but frame them as “compat exports”

**Confidence:** Medium

**Philosophy Alignment:** Tension
Tool-specific artifacts can drift toward “optimize for one client.” Making it template-driven keeps Ontos universal and transparent.

**Reasoning:**

* The value is real: teams want one command to produce the file their agent expects.
* A template system avoids hardcoding “Claude-first” into Ontos.
* Trade-off: you’re still blessing specific integrations, but you can keep them optional and clearly labeled.

**Implementation Complexity:** Medium

* Effort estimate: ~3–5 days
* Dependencies: none if it’s just string templates + file rendering
* Risk: template creep and endless “support my tool” requests

**Dissent Note:** *(Only if disagreeing with Founder Lean)*

* Founder lean is skeptical. I think the middle-ground template approach avoids compromising universality while still capturing the adoption upside.
* I’d change my mind if you expect near-zero external users and want v3 strictly about packaging only.

---

### Q3: Lazy Loading / Context Slicing

**Recommendation:** Alternative: progressive map compaction + on-demand CLI expansion, not `ontos://` URIs yet

**Confidence:** Medium

**Philosophy Alignment:** Aligns
You keep readable Markdown as the interface, but avoid dumping an unbounded wall of text into contexts.

**Reasoning:**

* Token limits are real; you will hit them as projects grow.
* You can get 80 percent of the benefit with a compact map and explicit “expand this node” commands.
* Trade-off: adds “modes” to output, but it can be automatic based on size thresholds.

**Implementation Complexity:** Medium

* Effort estimate: ~4–5 days
* Dependencies: none
* Risk: users get confused if the compact view hides too much without obvious “how to expand” affordances

---

### Q4: Passive Observation (Watchdog)

**Recommendation:** Alternative: Option C behavior using git-based detection, no watchdog dependency

**Confidence:** High

**Philosophy Alignment:** Aligns
It preserves “curation over ceremony” by making detection assistive, not authoritative, and stays lightweight.

**Reasoning:**

* You can infer “touched files” via `git status` / `git diff --name-only` at log/archive time.
* No background daemon, no extra dependency, no platform edge cases.
* Trade-off: it’s less magical than real-time watching, but dramatically simpler.

**Implementation Complexity:** Low

* Effort estimate: ~1–2 days
* Dependencies: git available in repo
* Risk: non-git repos or large diffs could degrade UX unless you cap/summary output

---

### Q5: Version Pinning in .ontos.toml

**Recommendation:** Option A, but start as “warn-only” in v3.0

**Confidence:** High

**Philosophy Alignment:** Aligns
It prevents silent corruption and still keeps friction low if you don’t hard-fail by default.

**Reasoning:**

* Version drift becomes a real bug source the moment there are 2 machines.
* Warn-only keeps single-user flow clean.
* Trade-off: small ceremony in config, big payoff in safety later.

**Implementation Complexity:** Low

* Effort estimate: a few hours
* Dependencies: none
* Risk: false confidence if users ignore warnings and you never escalate later

---

### Q6: Shim Hooks for Git

**Recommendation:** Option A

**Confidence:** Medium

**Philosophy Alignment:** Aligns
It’s “glass box” enforcement without repo pollution, and keeps the global-tool pattern consistent.

**Reasoning:**

* Shim hooks keep the repo clean while enabling guardrails like validation before push.
* They should degrade gracefully if `ontos` isn’t installed, ideally warn and no-op.
* Trade-off: relies on global install consistency, which pairs well with Q5.

**Implementation Complexity:** Low

* Effort estimate: ~1–2 days
* Dependencies: none
* Risk: hooks can annoy users if they block unexpectedly; default should be non-blocking unless explicitly enabled

---

### Q7: Auto-Configure MCP Clients

**Recommendation:** Option B for v3.0; later, an explicit opt-in command when MCP ships

**Confidence:** High

**Philosophy Alignment:** Aligns
Touching external config files silently violates “glass box” and can feel invasive.

**Reasoning:**

* Auto-patching user config is a trust boundary. It should never be implicit.
* An explicit `ontos mcp install --client cursor` is a good future compromise.
* Trade-off: docs are friction, but it’s the right friction at this boundary.

**Implementation Complexity:** Low

* Effort estimate: ~1 day once MCP exists
* Dependencies: MCP implementation exists
* Risk: client config formats change often; auto-patching becomes brittle

---

### Q8: Context Slicing Without Sacrificing Lightweight

**Recommendation:** Option A

**Confidence:** Medium

**Philosophy Alignment:** Aligns
Progressive complexity is already a chosen principle. Scaling behavior should be invisible until it’s needed.

**Reasoning:**

* Combine Q3’s compact-by-default when large with explicit “expand”.
* Small projects see the simple full map. Big projects automatically shift to summary-first.
* Trade-off: thresholds and heuristics can be wrong, so offer an override.

**Implementation Complexity:** Medium

* Effort estimate: ~4–5 days
* Dependencies: Q3 approach
* Risk: heuristic tuning becomes a time sink if you over-optimize early

---

### Q9: MCP Security Model

**Recommendation:** Option A (but define a “minimum viable A”)

**Confidence:** High

**Philosophy Alignment:** Aligns
Security-by-default supports “glass box” and prevents Ontos from becoming a silent foot-gun when exposed via protocol.

**Reasoning:**

* Minimum viable: explicit workspace root, strict path allowlist, read-only default, explicit write gating, and audit log of writes.
* Avoid fancy auth at first by using stdio transport and “local invocation only” as the baseline.
* Trade-off: a bit more code, but it avoids liability and scary surprises.

**Implementation Complexity:** Medium

* Effort estimate: ~1 week when MCP starts
* Dependencies: MCP layer exists
* Risk: missing one path traversal edge case or implicit write path becomes a security incident

---

### Q10: Pydantic Requirement

**Recommendation:** Option B

**Confidence:** High

**Philosophy Alignment:** Aligns
Zero-dep core stays sacred. Protocol-facing JSON schema conveniences belong in optional installs.

**Reasoning:**

* Pydantic is great for schema + JSON schema generation, but it’s not worth breaking core philosophy.
* MCP layer is exactly where this belongs.
* Trade-off: you’ll write more manual validation in core, but that’s consistent with “lightweight”.

**Implementation Complexity:** Low

* Effort estimate: ~1–2 days to wire into optional extra later
* Dependencies: MCP implementation + packaging extras
* Risk: dual validation logic drifting unless you keep core schemas as the single source of truth

---

### Q11: Script Reorganization Approach

**Recommendation:** Option A (explicit goal), but don’t “microservice” it, just define clean layers

**Confidence:** High

**Philosophy Alignment:** Aligns
A clean module layout reduces cognitive load and makes “just works” more reliable.

**Reasoning:**

* Packaging without deliberate boundaries tends to preserve tech debt.
* Define a small set of stable modules: core logic, io/filesystem, rendering/output, cli command wiring.
* Trade-off: planning time now, but it prevents months of slow decay.

**Implementation Complexity:** High

* Effort estimate: 1–2 weeks refactor
* Dependencies: test harness strong enough to catch regressions
* Risk: subtle behavior changes that break your current workflow if tests don’t cover real usage paths

---

### Q12: Python vs Node/TS for MCP

**Recommendation:** Option A

**Confidence:** High

**Philosophy Alignment:** Aligns
Splitting languages violates simplicity and increases maintenance burden dramatically for a solo founder.

**Reasoning:**

* Python keeps one codebase, one mental model, and reuses your existing core.
* If MCP ecosystem friction exists, solve it at the edges, not via rewrite.
* Trade-off: you might write more glue code, but you avoid a multi-language product.

**Implementation Complexity:** Low

* Effort estimate: none now
* Dependencies: none
* Risk: if Python MCP tooling truly lags, you may need a thin adapter later, but only after proof

---

### Q13: JSON vs Markdown as Primary Output

**Recommendation:** Option B

**Confidence:** High

**Philosophy Alignment:** Aligns
This is basically the definition of “readable, not retrievable.”

**Reasoning:**

* Markdown is the product. Humans and agents can inspect it directly.
* JSON is an export layer for automation and protocol integration.
* Trade-off: you must keep JSON stable and derived, not drifting into a parallel truth.

**Implementation Complexity:** Low

* Effort estimate: ~1–2 days (pairs with Q1)
* Dependencies: none
* Risk: if you let JSON become “more complete” than Markdown, you’ll accidentally invert the philosophy

---

## D. Cross-Cutting Concerns

### Interdependencies

* Q3 and Q8 should be treated as one design effort. My Q8 answer assumes the Q3 “progressive compaction + expand” approach.
* Q6 and Q5 reinforce each other. Shim hooks become safer if version pinning exists.
* Q13 assumes Q1 is implemented as “export only”, not “dual truth”.

### Priority Recommendation

If you can only implement 3 of my recommendations for v3.0:

1. **Q11 (explicit reorg)** — packaging without structure just calcifies existing pain.
2. **Q4 (git-based detect-and-flag)** — removes real friction without new deps or daemons.
3. **Q1 (JSON output mode)** — tiny effort, unlocks CI, scripting, and future MCP without rework.

### Risk Flag

The biggest risk is a messy migration from executable config and repo-injected scripts to the new global CLI + `.ontos.toml`. Even as a single user, you want a deterministic “upgrade path” and a reversible rollback story, otherwise v3 becomes a productivity dip.

### Philosophy Check

* Tool-specific exports can conflict with universality if they become first-class “the way to use Ontos”. My Q2 recommendation tries to prevent that by making exports template-driven and clearly secondary.
* Context slicing can conflict with “readable” if you over-abstract into indirection. Keep the compact map readable on its own, and make expansion explicit.

