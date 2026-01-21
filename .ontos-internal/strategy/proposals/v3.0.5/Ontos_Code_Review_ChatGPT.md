## Ontos feedback report for the chief architect

### Context you gave me

* Target user today: you, plus solo devs and small teams.
* Non-negotiable: it should feel safe to try in any repo.
* Direction: you want it to become a real ecosystem tool, but licensing is undecided.

This aligns with what Ontos claims it’s for on PyPI: small teams switching between AI tools, projects that outlive prototypes, portable context living in-repo. ([PyPI][1])

---

## What’s working and worth doubling down on

### 1) The thesis is crisp and differentiated

“Readable, not retrievable.” Deterministic graph traversal instead of embeddings is a real stance, and it matches the failure mode everyone hits: context drift and re-explaining across tools. ([PyPI][1])

### 2) The hierarchy model is actually useful

Kernel / strategy / product / atom is a strong mental model for survivability across rewrites. That’s the right way to talk about “decisions outlive code.” ([PyPI][1])

### 3) The “agent activation” path is smart

Generating `AGENTS.md` and `.cursorrules` is the right kind of glue. Also, AGENTS.md is clearly becoming a broader convention across repos, so leaning into that format is strategically smart. ([PyPI][1])

### 4) The roadmap is directionally correct

Obsidian compatibility, `ontos deinit`, templates, daemon mode, MCP interface. These are exactly what turns a personal workflow into an ecosystem tool. ([PyPI][1])

---

## The biggest blockers right now

### 1) Licensing posture blocks “ecosystem tool” by default

PyPI flags the project as “Other/Proprietary License (Proprietary)” and the README says PRs are not accepted because it’s proprietary. ([PyPI][1])

For small teams, that creates three immediate problems:

* Company compliance scanners reject it.
* Community can’t fix sharp edges.
* Integrations won’t happen organically.

You can absolutely keep it proprietary while you figure things out, but then it’s not an “ecosystem tool” yet. It’s a private product with public code.

**Constructive move**: pick an interim license that matches your current intent.

* If you want feedback and adoption now: use a source-available license that explicitly permits internal/commercial use but restricts resale. Or go permissive for the core.
* If you want to keep maximum optionality: at least make usage rights explicit in plain English on PyPI and README, not just “Proprietary.”

### 2) “Safe to try” conflicts with `init` behavior

PyPI says `ontos init` “installs git hooks” and generates files. ([PyPI][1])
That’s a lot of side effects for a first run. It’s exactly what triggers distrust.

**Constructive move**:

* Make “no surprises” the default.

  * `ontos init` should default to zero hooks, or prompt interactively.
  * Add `ontos init --plan` that prints every file change before writing.
  * Add `ontos deinit` as a first-class uninstall, and ship it soon. ([PyPI][1])

### 3) Command surface area vs stability is mismatched

The README includes a “Known Issues (v3.0.2)” section that says `verify`, `query`, `consolidate` are broken and that several commands ignore `.ontos.toml`. ([PyPI][1])
Also it still says “tracked for v3.0.3” even though 3.0.4 is released. ([PyPI][1])

This is a trust killer because a new user reads “Quick Start” and “Workflow,” then immediately sees “some commands are broken.”

**Constructive move**:

* Hide broken commands in the CLI help unless `ONTOS_EXPERIMENTAL=1`.
* If a command is broken, don’t let it crash. Print a clean “disabled” message with the recommended replacement.
* Update the Known Issues text to match the current release reality.

### 4) Branding collision risk: “ontos” is already a name people will confuse

There’s at least one other notable project named Ontos in the wild, and search results regularly surface the Databricks “ontos” repo. ([GitHub][2])
That’s not fatal, but it *will* create confusion and SEO friction, especially as you try to become “the standard.”

**Constructive move**:

* Decide whether you want to own “ontos” as the pip name long term.
* If yes, invest early in identity: consistent “Project Ontos” phrasing, clearer tagline, and explicit “not the Databricks Ontos” note in docs if needed.
* If no, now is the only cheap time to rename.

---

## Technical and dev risks worth calling out hard

### A) Determinism needs to be enforced, not implied

You explicitly claim determinism. ([PyPI][1])
That means:

* stable ordering of traversal and outputs
* stable formatting of generated files
* stable behavior across OS and Python versions

**Concrete improvements**

* Canonical sort order for every output.
* Golden-file tests for `Ontos_Context_Map.md`, `AGENTS.md`, `.cursorrules`.
* `ontos doctor --strict` should fail on any nondeterministic output diffs.

### B) Repo scanning will become noisy in real repos

If you crawl too broadly you will ingest junk Markdown and slow down. If you crawl too narrowly you miss context. This needs a principled default and a predictable ignore mechanism.

**Concrete improvements**

* Strong default ignore list: `.git`, `node_modules`, `.venv`, `dist`, `build`, `.tox`, caches, vendor dirs.
* A visible “effective config” view: `ontos config --resolved`.
* `ontos map --explain` prints why each file was included or excluded.

### C) ID collisions and duplicate docs need loud handling

If doc IDs default to filenames or frontmatter, collisions are inevitable in bigger projects. Silent overwrite is deadly.

**Concrete improvements**

* Hard error on ID collision with both file paths printed.
* Optional namespace rule: `docs/strategy/*.md` auto-prefixes `strategy:`.

### D) Subprocess wrappers and legacy behavior create “two Ontos”

Your own Known Issues section says multiple commands ignore `.ontos.toml` and recommends using “native” commands instead. ([PyPI][1])
That’s basically admitting architectural split-brain.

**Concrete improvements**

* Pick the “blessed core” command set and make it small: `init`, `map`, `doctor`, `log`, `agents`.
* Everything else becomes either:

  * implemented in-process using the same config object and output model, or
  * moved to `ontos legacy ...`, or
  * removed until stable.

### E) Hooks should be predictable and reversible

Hooks are fine, but only if they’re obviously controlled by the user.

**Concrete improvements**

* Default off, opt-in on.
* Make them run the same checks as `doctor --strict`.
* `ontos hooks install|remove|status`.

### F) Secret leakage risk is real

You already warn users to scan for secrets and even suggest tools like gitleaks and trufflehog. ([PyPI][1])
Good, but if you want serious adoption, add guardrails.

**Concrete improvements**

* Optional built-in redaction patterns for logs.
* A “never include these paths” list in config.
* `ontos log --confirm` prints a diff-like preview.

### G) Release hygiene matters more than people think

3.0.4 released Jan 19, 2026 and flagged Alpha on PyPI. ([PyPI][1])
Fast patch cadence is fine, but only if docs and changelog stay perfectly aligned.

**Concrete improvements**

* Docs versioned per release tag.
* The PyPI long description should match the exact release, not “sometimes future.”

---

## Strategy: how to become an ecosystem tool without locking yourself in

### The most pragmatic path

1. **Open the spec, even if you keep the implementation closed**

   * Publish the frontmatter schema as a spec.
   * Publish the map format rules.
   * Treat `AGENTS.md` integration as a stable contract.

This lets others build tooling around Ontos without needing your code.

2. **Make the core engine permissively licensed, keep premium features closed**

   * Core: parsing, validation, map generation, determinism, config.
   * Paid / closed: advanced templates, UI, daemon, enterprise policy packs, IDE plugins, hosted “context review” service.

This is the normal “open-core” route and it matches your current uncertainty.

3. **If you stay proprietary for now, at least accept PRs for non-core**

   * docs
   * examples
   * templates
   * editor integration configs

That gets you ecosystem momentum without giving away your secret sauce.

---

## Recommended execution plan

### Phase 0: “Safe to try” baseline, 1–2 weeks

* `init` defaults to no hooks
* `--plan` preview for all write commands
* `deinit` shipped
* broken commands hidden or gracefully disabled
* update Known Issues text so it matches reality ([PyPI][1])

### Phase 1: “Trustable core,” 2–6 weeks

* enforce determinism with golden tests
* strict validation and collision detection
* scanning defaults + explain mode
* unify config behavior across all commands

### Phase 2: “Ecosystem hooks,” 6–12 weeks

* spec docs
* template system
* plugin interface
* Obsidian compatibility and one editor integration done end-to-end ([PyPI][1])

---