Your plan is mostly pointed at the right problems. But it still has a few “looks-clean-on-paper, still-regresses in code” failure modes. Fix these now or you’ll be back here again in 3.3.

## The 5 biggest gaps I’d fix before coding anything

### 1) Your layer boundaries are internally inconsistent

You reference config in `ontos/core/config.py` (P1-2) but your architecture guardrail calls the “one config loader” `io/config.py` (P2-4). That’s a boundary contradiction baked into the plan.  

Action:

* Split **config schema/types** vs **config loading** explicitly.

  * `core/config_schema.py` (dataclasses, defaults, validation)
  * `io/config_loader.py` (read `.ontos.toml`, decode into schema)
* Update P2-4 guardrails to enforce *the new truth*.

### 2) “core calls io” is still murky because `io/yaml.py` is not I/O

Your plan says `core/frontmatter.py` is the entrypoint and `io/yaml.py` becomes “internal helpers called by core.”  That means `io/yaml.py` is really a **codec**, not I/O. Keeping it under `io/` invites future boundary leaks.

Action (choose one):

* Rename/move: `ontos/codec/yaml.py` (or `formats/yaml.py`) and reserve `io/` for filesystem concerns.
* Or keep it where it is, but then your boundary test must allow `core -> io.yaml` while still forbidding `commands -> io.*`. That’s workable, but document the exception and test it.

### 3) Your pipeline still has a loophole (“parse-only”) unless you outlaw it

You earlier accepted “commands that only need parsing stop after step 1” in your Round 2 response. If you leave that door open, you’ll recreate drift. The remediation plan *doesn’t* explicitly close it. 

Action:

* Make `parse_only` an explicit, rare mode (flag or separate API).
* Default for all commands: **parse + normalize always**.
* Validation: policy-driven (warn vs error) but only after normalize.
* Add an architecture test: commands may not call `parse_frontmatter` directly. They must call the pipeline entrypoint (or `build_index` that applies it).

### 4) “Centralize scanning/indexing” is too vague to implement correctly

P2-8 says “single index builder” and “commands don’t call scan_documents individually.”  That’s directionally right, but it’s missing the spec that prevents reintroducing subtle inconsistencies.

Action: define a `DocumentIndex` contract up front:

* Inputs: `(project_root, config, *, mode)` where mode controls strictness.
* Outputs must include:

  * `files_scanned`, `files_skipped` (with reasons), `parse_errors`, `normalized_docs`, `violations`
  * deterministic ordering of docs (path sort)
* One authoritative place where skip patterns are applied (including generated file exclusions).
* Add a test that monkeypatches the underlying scanner and asserts it’s invoked once per command execution.

### 5) You’re carrying scope creep into v3.2

LLM scaffold and a reusable GitHub Action are “nice,” but they’re also the easiest way to delay the architectural cleanup. Your plan puts both inside v3.2 execution order.  

Action:

* Move P3-1 (LLM scaffold) to post-v3.2 unless you can do it in <1 day without touching core.
* For the GitHub Action (P3-2), ship a **workflow snippet** first. Only make an action when the CLI output schema + exit codes are stable.

---

## Ticket-by-ticket critique and upgrades

### P1-2 Skip Generated Files: make it correct across path forms

Current plan: append `config.paths.context_map`, `AGENTS.md`, `.cursorrules` into a list. 

Hidden footguns:

* `config.paths.context_map` may be absolute while scanner yields relative paths.
* You’re mixing glob patterns (`skip_patterns`) with literal filenames (not equivalent).
* You only mention `map`, but the same “generated files leak into graph” can hit `doctor`, `query`, etc.

Upgrade:

* Normalize every candidate to a project-root-relative POSIX path *and* keep a basename fallback.
* Treat generated exclusions as their own concept in config: `scanning.generated_paths` (resolved literals), separate from `skip_patterns` (globs).
* Acceptance test: `ontos map` + `ontos doctor` both never include `AGENTS.md` / context map, regardless of configured context map path.

### P2-1 Unify project root resolution: codify precedence

You want a single helper returning `(project_root, config)` and no `Path.cwd()` usage. 

Missing: precedence rules.

* What wins: `--root`, env var, `.ontos.toml` location, git root, nearest marker file?

Upgrade:

* Define: `--root` > explicit `ONTOS_ROOT` env > nearest `.ontos.toml` walking up > git root walking up > error.
* Add tests for:

  * running inside nested subdir
  * running outside any repo (should error cleanly)
  * ambiguous situations (two `.ontos.toml` in parents)

### P2-2 `.ontos.toml` authoritative config: be ruthless

Plan: remove all `ontos_config` imports; warn if `ontos_config.py` exists. 

Given “user base = you,” I’d simplify:

* Don’t warn forever. Warn once per run is noise. Prefer: warn only when `--verbose` OR only in `doctor`.
* If you keep the file around for old repos, explicitly ignore it (never import).

Also: your Deferred table says `migrate-config` deferred to v3.3.  If you ever bring it back, it must be AST-based conversion (no execution). Otherwise it reintroduces repo-local code execution risk.

### P2-3 Frontmatter pipeline: specify invariants and error objects

You’ve got the right 3-stage split. 

What’s missing is the enforceable contract:

* Parse errors must be structured (file, line/col if possible), not “print and continue.”
* Normalize must:

  * canonicalize `describes` to a list
  * canonicalize `concepts` to list
  * resolve `type` into a stable representation
  * preserve unknown fields somewhere (extras) so you don’t destroy user metadata
* Validate must be pure business rules (no I/O, no mutation)

Add acceptance criteria beyond “one validate_describes exists”:

* A doc that fails YAML parse still appears in results as `DocError` with stable error code.
* A doc with extra frontmatter keys survives a parse-normalize-write round-trip without dropping those keys (or explicitly document that you drop them).

### P2-4 Architecture guardrails: expand the rules or it won’t hold

You’re doing AST-based import boundary checks. Good. 

But the rules are too small. Add these:

* `core/` cannot import from `commands/` (currently only `io` is forbidden from `commands`)
* `commands/` may import from `app/` (if you add it), and *only that* for orchestration
* Forbid “backdoors”: `importlib.import_module("ontos.io...")`, `__import__`, and `sys.path` mutation in package code

Also, make “one frontmatter entrypoint” real:

* Force commands to import `ontos.core.frontmatter` (or `ontos.app.pipeline`) and forbid direct imports of helper modules (`core.validation`, `io.yaml`, etc). Otherwise people will still bypass the intended entrypoint.

### P2-5 Log YAML safety: broaden the tests

Good target. 

Add test cases you *will* hit:

* Unicode: `"오지승"`, smart quotes
* Multiline strings
* Leading/trailing whitespace
* Strings that look like YAML scalars: `"yes"`, `"no"`, `"2026-01-22"`, `"1e3"`

And enforce determinism:

* serialization order stable (or explicitly not guaranteed, but then golden tests become flaky)

### P2-6 Type coercion audit: stop fighting Python, give yourself an “Unknown”

Your plan tries to eliminate `hasattr(doc.type, "value")` by ensuring `type` is always an enum. 

The missing reality: users (future you) will write bad `type:` values. Normalization should not crash.

Upgrade:

* Add `DocumentType.UNKNOWN` to the enum.
* Normalization maps any unrecognized string to `UNKNOWN` + issue.
* Validation:

  * `doctor`: warning
  * `map --strict` or `lint`: error
* Acceptance criteria:

  * No runtime `AttributeError` possible from `doc.type`
  * Bad types still produce a map/doctor output with a clear diagnostic

### P2-7 Dead code removal: tighten “done when”

This is fine, but “lines 632–700” will drift. 

Upgrade:

* “Done when” = `grep -R "_cmd_wrapper" ontos/` is empty, same for `_get_subprocess_env`
* Packaging check: `_scripts/` is not installed in wheels (or is installed but inert and documented). Decide explicitly.

### P2-9 Orphan policy: define the graph model precisely

You define orphan as “no incoming edges” with severity by type. 

Ambiguity: what counts as an “edge”?

* `describes` edges?
* markdown links?
* both?
* does referencing a concept count as incoming for docs?

Upgrade:

* Write the edge definition in one place (core graph builder).
* Separate:

  * **broken references** (edge points to missing node)
  * **orphans** (node exists but has no inbound edges of the chosen type)
* Add fixtures:

  * kernel mission doc should be INFO orphan by design
  * a product doc should WARN if nobody references it
  * strict mode flips WARN to ERROR only for configured types

---

## Missing tickets I’d add (high leverage)

1. **Exit codes + JSON schema stability**
   You’re building `lint`, CI, and an action. That’s impossible without stable exit codes and a versioned JSON output schema. Add a P2 ticket:

* `doctor/lint` returns:

  * 0 = no errors
  * 1 = errors present
  * 2 = internal crash
* `--format json` schema versioned (`output_schema: 1`)

This is the foundation for P3-2 and P3-3. 

2. **Trust boundary documentation**
   You previously noted “repo-local code execution” risk (hooks, config). Make it a real deliverable:

* README “Security / Trust boundary” section
* “Ontos never executes repo-local Python” as a hard rule

3. **Deterministic map output**
   If you ever golden-test CLI output, nondeterministic ordering will burn you. Make ordering deterministic by default (path sort, stable node IDs).

---

## Suggested revised execution order (tighter, less rework)

Your ordering is close, but I’d insert a “Step 0” and demote scope-creep. 

**Step 0 (before P2-4):** Decide module layout for config + YAML codec, update plan to remove contradictions.

Then:

1. P2-4 guardrails (reflect the *final* layer truth)
2. P2-1 root+config resolution (everything depends on it)
3. P2-8 centralized index (forces one scanning source of truth)
4. P2-3 pipeline (plugs into index)
5. P2-5 log YAML (now uses pipeline)
6. P2-6 type coercion + orphan policy (now graph/index are stable)
7. P2-7 dead code removal
8. P3-5 packaging smoke tests
9. P3-3 lint alias + docs (staleness/version FAQ)
10. Defer P3-1 and P3-2 unless you’re intentionally shipping them for adoption

---

If you implement the upgrades above, this remediation plan becomes “actually closes the loopholes” rather than “fixes the obvious offenders.” The contradictions around config + io/core boundaries are the one thing I’d force you to clean up before you start coding.
