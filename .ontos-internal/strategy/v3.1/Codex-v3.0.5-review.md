I pulled the current PyPI release (v3.0.5) and reviewed both the published project description plus the shipped source distribution. Ontos is positioning itself as “portable context” for AI assisted development, implemented as a repo local markdown graph with deterministic traversal rather than embeddings or RAG. ([PyPI](https://pypi.org/project/ontos/))

## What’s strong

**Clear product philosophy and constraints**

- The “not RAG / not cloud / deterministic output” stance is crisp and differentiating. You’re basically saying: this is *infrastructure for shared project memory*, not an AI feature. ([PyPI](https://pypi.org/project/ontos/))
- The workflow framing with “Ontos / Archive Ontos / Maintain Ontos” is genuinely good UX because it maps to how people actually work with agents. ([PyPI](https://pypi.org/project/ontos/))

**The architecture is more disciplined than most early CLIs**

- There’s a real separation between `core/` pure logic and `io/` side effects, with a deliberate “inject callbacks” style in a bunch of places. That makes testing and future refactors way easier than a typical “everything imports everything” CLI.
- Minimal runtime deps. PyPI claims Python 3.9+ and the footprint is small, which is consistent with shipping a CLI that people can adopt without dependency drama. ([PyPI](https://pypi.org/project/ontos/))

**The core graph idea is solid**

- Document ontology is intentionally small (kernel/strategy/product/atom/log), which is the right instinct. Small taxonomies beat big ones early.
- The dependency graph validation work is real: broken links, cycle detection, depth calculations, orphan logic. This is where deterministic systems usually fall apart, and you’ve invested in it.

**Repo integration is pragmatic**

- Hooks and generated agent files (`AGENTS.md`, `.cursorrules`) are the right integration surface today, and you’ve put them behind explicit commands (`ontos agents`, `ontos hook`, etc.). ([PyPI](https://pypi.org/project/ontos/))

## The biggest risks and sharp edges

**1) The “alpha + rapid patch train” problem**

You shipped 3.0.1 → 3.0.5 in five days. That screams “high churn” to outsiders, even if the changes are reasonable. ([PyPI](https://pypi.org/project/ontos/))

If you want adoption, you need a story for stability: what’s locked, what’s experimental, what breaks.

**2) Wrapper commands are currently a credibility hit**

Your own “Known Issues” section is blunt: several commands delegate to legacy scripts, some require legacy flags, and `scaffold` is outright broken in the unified CLI. ([PyPI](https://pypi.org/project/ontos/))

That’s not just a bug list. It creates user mistrust because people can’t tell what’s “real v3” vs “compat mode”.

**3) Config fragmentation**

You explicitly note legacy wrapper commands don’t honor `.ontos.toml` yet. ([PyPI](https://pypi.org/project/ontos/))

In the codebase, you can also feel multiple generations of configuration patterns living side by side. That’s a classic source of “works in my repo, breaks in yours”.

**4) Docs may not match what users installed**

You warn that GitHub docs may describe unreleased behavior. ([PyPI](https://pypi.org/project/ontos/))

That’s honest, but it’s also a support trap: users copy a command from docs, it fails, they bounce.

**5) Packaging and test ergonomics**

The sdist includes a fairly large test suite, but running it in a clean environment fails during collection because some tests import old “repo injected script” module names and expect repo paths that aren’t present. That’s not fatal for end users, but it *is* a red flag to contributors and advanced adopters who try `pytest` to build trust.

**6) Frontmatter parsing is a potential footgun**

Your YAML frontmatter parsing approach is simple and fast, but it’s the kind of thing that breaks on edge cases:

- `--` showing up in content
- files starting with a BOM or whitespace
- people using Obsidian style frontmatter variations
    
    You already call out Obsidian compatibility as a next step. ([PyPI](https://pypi.org/project/ontos/))
    
    This area will matter a lot once real repos hit it.
    

**7) The MCP story is currently confusing**

Roadmap says “v4.0 MCP as primary interface”. ([PyPI](https://pypi.org/project/ontos/))

But the package already exposes an `mcp` extra and a placeholder module. That’s fine internally, but externally it reads like a half feature. I’d either ship a minimal real MCP server soon or hide it until it’s real.

## What I’d improve next, in order

**A. Make v3 feel coherent: kill the wrapper cliff**

- Fix `scaffold` in unified CLI first since it’s explicitly “broken”. ([PyPI](https://pypi.org/project/ontos/))
- Pick a policy: either fully support wrapper commands with the same UX guarantees, or clearly label them “compat only” and push users to the native set.

**B. Unify configuration behavior**

- `.ontos.toml` should be the single source of truth for *every* command, including wrappers. ([PyPI](https://pypi.org/project/ontos/))
- If a wrapper can’t honor config yet, it should still *read config* and warn “this field is ignored by legacy mode” rather than silently diverging.

**C. Docs that match the installed version**

- Host versioned docs, or at least make the PyPI page link to “docs for v3.0.5” and keep “main branch docs” separate. You already know this risk, you’re just choosing to live with it. ([PyPI](https://pypi.org/project/ontos/))

**D. Tighten parsing and scanning**

- Deduplicate scan results and make scanning rules more explicit. Scanning both `docs_dir` and repo root is convenient, but it can get expensive and surprising in monorepos.
- Harden frontmatter parsing with a stricter “frontmatter must be the first block in file” rule and a more robust terminator detection.

**E. Polish the public contract**

- Decide what “stable API” means. Right now Ontos is a CLI product, so treat the CLI as the contract, not internal Python imports.
- Standardize JSON output across commands and wrappers. Users building automations will care about this a lot.

**F. Make contributor trust easy**

- Either (1) make `pytest` pass from the sdist, or (2) stop shipping tests in the sdist and document “run tests from GitHub repo”. Right now it’s in the uncomfortable middle.

## A realistic “what you’re building toward” critique

The deterministic “context graph” idea is strong, but the long term risk is taxonomy sprawl plus workflow sprawl. You’ll win if you stay opinionated:

- small ontology
- strict validation
- predictable outputs
- boring file formats
    
    And you’ll lose if it turns into a kitchen sink of agent integrations.
    

If you want, paste your `.ontos.toml` schema and one generated `Ontos_Context_Map.md` from a real repo and I’ll review the UX from the user’s perspective. That’s usually where the next set of problems becomes obvious fast.