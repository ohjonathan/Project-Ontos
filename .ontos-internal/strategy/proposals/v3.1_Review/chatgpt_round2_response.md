---
id: chatgpt_round2_response
type: strategy
status: draft
depends_on: [chatgpt_analysis_response, v3_2_backlog]
concepts: [review, feedback, architecture, acceptance-criteria, ci-guardrails]
---

# Response to ChatGPT Round 2

**Context:** ChatGPT reviewed our response, validated the approach, and
tightened 5 areas. This document records what we're adopting, where we
agree, and the few places we diverge.

---

## Adopted: All 5 Tightenings

### T1: Import Boundary Enforcement

You're right -- "enforce the pipeline" is vague without a mechanism.

**Adopted approach:**
- Add a CI test that greps for disallowed imports (commands importing
  from `io.*` directly, `io` importing from `commands`)
- Mark internal modules with `_` prefix where appropriate
- Single public API module for doc I/O + parsing + normalization

**Acceptance criterion:** CI fails if a command file contains
`from ontos.io` or `import ontos.io`.

### T2: Acceptance Criteria for Every Roadmap Item

Point taken. Vague intentions ship vague results. We'll rewrite every
v3.2 backlog item with "done when..." definitions. See the consolidated
remediation plan for the full list.

### T3: sdist/Packaging as First-Class CI Check

We downplayed it. You're right that sdist users exist and broken sdists
erode trust.

**Adopted approach:**
- CI step: build wheel + sdist -> install each into fresh venv -> run
  smoke suite
- Smoke suite = subset of tests that verify core CLI commands work
  from installed package (no repo structure assumptions)

**Acceptance criterion:** CI has a job called `test-installed` that runs
after `build` and exercises `ontos --version`, `ontos map --help`, and
a small golden-master subset.

### T4: Deprecation Path for Legacy Removal

Fair point on not hard-breaking users silently.

**Adopted approach (modified):**
- v3.2: `_cmd_wrapper()` and `_get_subprocess_env()` emit deprecation
  warnings if somehow invoked (belt-and-suspenders)
- v3.2: Remove PYTHONPATH injection from `cli.py`. Legacy scripts in
  `_scripts/` get a deprecation notice in their docstrings.
- v3.3: Delete `_scripts/` entirely

**Why not `ontos legacy <name>`:** The user base is too small to justify
a compatibility shim. The native commands have been the only documented
interface since v3.0. A CHANGELOG entry and deprecation warning are
sufficient.

### T5: Log YAML Escaping Tests

Agree. Adding test cases for:
- Concepts with spaces: `"user authentication"`
- Concepts with colons: `"auth: oauth2"`
- Concepts with brackets: `"list [a, b]"`
- Concepts with commas: `"one, two"`

**Acceptance criterion:** `test_log.py` has a parametrized test that
round-trips these values through the log command and verifies the output
parses back correctly via PyYAML.

---

## Adopted: All 5 Open Question Answers

### Q1: Three-Stage Pipeline (parse -> normalize -> validate)

Adopted as-is. The separation gives us:
- `parse_frontmatter()` -> lossless, syntax-only
- `normalize_frontmatter()` -> defaults, type canonicalization
- `validate_frontmatter()` -> business rules, policy checks

Commands that only need parsing stop after step 1. Full validation is
opt-in per-command.

### Q2: Orphan = Structural + Severity by Type

Adopted. One definition ("no incoming edges"), mapped to severity:
- kernel/strategy with no incoming edges: INFO (they're roots by design)
- product/atom with no incoming edges: WARN (default) or ERROR (strict)
- Configurable via `.ontos.toml` or CLI flag

### Q3: Golden Tests as Integration (Hermetic Subset as Package)

Adopted. Split:
- **Package tests:** Small hermetic golden suite using
  `importlib.resources` for fixtures. Runs post-install.
- **Integration tests:** Full fixture corpus, CI-only.

### Q4: Config Migration: Warn + Provide `ontos migrate-config`

Adopted with one modification:
- Detect `ontos_config.py` -> emit one-time warning with actionable hint
- Add `ontos migrate-config` command that generates `.ontos.toml` from
  the python config
- **No python config execution by default** (security). If we ever
  re-add it, require explicit opt-in.

### Q5: `lint` as Thin Alias of `doctor` with CI Defaults

Adopted:
- `ontos doctor` = user-friendly diagnostics (local dev)
- `ontos lint` = `ontos doctor --ci --format json` (CI enforcement)
- Same engine, different defaults. No drift.

---

## Adopted: Architecture Guardrails (Non-Negotiable)

This is the most important suggestion in the entire review cycle.

**CI enforcement rules:**
1. `commands/` can import from `core/`, NOT from `io/`
2. `io/` cannot import from `commands/`
3. One frontmatter entrypoint (re-exports from `core/frontmatter.py`)
4. One config loader (re-exports from `io/config.py`)

**Implementation:** A test file (`test_architecture.py`) that:
- Walks all `.py` files in each layer
- Parses imports (AST-based, not grep -- more reliable)
- Asserts boundary rules hold

**Acceptance criterion:** `pytest tests/test_architecture.py` passes and
is part of the standard CI run.

---

## Where We Diverge (Minor)

### `ontos legacy <name>` Compatibility Command

We're skipping this. Reasoning:
- No evidence of users relying on legacy script execution post-v3.0
- The native CLI has been the only documented interface for 2 months
- Adding a compatibility command adds surface area we'd need to maintain
  and then deprecate again

Instead: CHANGELOG note in v3.2, deprecation warning if code paths are
somehow triggered, hard removal in v3.3.

---

## Offer Accepted

> "If you want, paste your tentative v3.2 backlog and I'll rewrite it
> into crisp tickets with acceptance criteria."

Yes. We'll take you up on this once the consolidated remediation plan is
finalized. The backlog will include items from both the Gemini review
(messaging, GitHub Action, LLM scaffold) and your review (pipeline
unification, architecture guardrails, packaging).

---

*Response prepared 2026-01-22. Ontos v3.1.0.*
