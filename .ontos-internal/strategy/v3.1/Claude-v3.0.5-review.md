I'll fetch the PyPI page and then dig into the actual code to give you a thorough analysis.Let me try the JSON API instead:Let me search for the GitHub repository instead:Let me search more specifically for your ontos package:Let me look for your specific GitHub repo:Now let me read through the key files to understand the architecture:Now let me look at the curation and staleness modules to understand the core value proposition:Now let me look at the config structure:Now let me check the GitHub repo for the README and additional context:Now I have a complete picture. Let me compile the thorough analysis:

---

# Ontos v3.0.5 - Comprehensive Analysis

## Executive Summary

Ontos is a **local-first documentation management system** that creates a portable knowledge graph from markdown files with YAML frontmatter. The core value proposition is "portable context for the agentic era" - maintaining project context that survives AI tool switches, prototype rewrites, and team handoffs.

---

## Strengths

### 1. **Strong Architectural Foundation**

The codebase demonstrates solid software engineering:

- **Clean separation of concerns**: `ontos.core` (pure logic, no I/O) vs `ontos.io` (file operations) vs `ontos.ui` (output formatting) vs `ontos.commands` (orchestration)
- **Dependency injection pattern**: Functions accept optional callbacks for git operations rather than hardcoding I/O, making the core logic testable
- **Transaction-aware SessionContext**: Two-phase commit with temp-then-rename atomic writes, file locking with stale detection
- **Schema versioning**: Forward-compatible document evolution with `SCHEMA_DEFINITIONS` and `check_compatibility()`

### 2. **Minimal Dependencies**

Only requires `pyyaml` (and `tomli` for Python <3.11). This is rare and valuable - most tools in this space pull in heavy frameworks.

### 3. **Clear Philosophy & Position**

The README is one of the best I've seen for a solo developer package:

- Articulates the problem clearly ("context dies in three ways")
- Explicitly states what Ontos is NOT (not RAG, not zero-effort, not a cloud service)
- Honest about current limitations ("Known Issues" section)

### 4. **Thoughtful UX Decisions**

- `ontos init` asks for hook consent before installing
- `ontos doctor` provides 8 health checks with actionable remediation
- Graceful degradation (3-method fallback for finding repo root, hook invocation)
- Backup creation before force-overwrites

### 5. **Git-Native Design**

- Hooks for pre-commit/pre-push validation
- Staleness detection based on git commit dates (not unreliable filesystem mtime)
- Everything travels with `git clone`

### 6. **Honest Self-Assessment**

The "Known Issues" table that says `scaffold` is "❌ Broken" shows maturity. You're not hiding problems.

---

## Criticisms & Risks

### 1. **Legacy Script Architecture is Technical Debt**

The `_cmd_wrapper` pattern in `cli.py` that shells out to `_scripts/*.py` via `subprocess.run()` is a red flag:

```python
def _cmd_wrapper(args) -> int:
    # ...
    result = subprocess.run(cmd, capture_output=True, text=True, env=_get_subprocess_env())

```

**Problems:**

- Breaks `.ontos.toml` configuration (your own docs acknowledge this)
- Creates two execution paths for the same functionality
- Makes debugging harder (errors in legacy scripts don't propagate cleanly)
- The `ontos_config.py` import pattern is brittle

**Recommendation:** Prioritize porting `scaffold`, `verify`, `query`, `consolidate` to native commands before adding features. The wrapper pattern should be a migration bridge, not a permanent architecture.

### 2. **The MCP Story is Incomplete**

You have an `ontos/mcp/__init__.py` that's essentially empty (512 bytes). The `[mcp]` optional dependency exists but there's no actual MCP server implementation.

This matters because your v4.0 vision says "MCP as primary interface." The gap between current state and that vision is large.

**Risk:** Competitors in the context engineering space (CTX, Claude Code's built-in memory, Cursor's project context) are shipping MCP integrations now.

### 3. **"Magic Defaults" Creates Discovery Problems**

The `from_repo` factory and implicit config resolution make it hard to understand what Ontos is actually doing:

```python
# What config is this using? Where is repo_root?
config = load_project_config()

```

This is fine for users but makes debugging harder. Consider verbose mode output that shows resolved paths.

### 4. **Schema Versioning is Premature Optimization**

You have 5 schema versions (1.0 through 3.0) but:

- Current schema is 2.2 (`CURRENT_SCHEMA_VERSION = "2.2"`)
- Package version is 3.0.5
- Some schema versions (3.0) reference fields (`implements`, `tests`, `deprecates`) that don't appear elsewhere in the codebase

This suggests the schema roadmap outpaced implementation. Users seeing `ontos_schema: 3.0` in their docs but running Ontos v3.0.5 might be confused.

### 5. **The "Activation" Flow is Fragile**

The AGENTS.md approach relies on AI agents voluntarily reading and following instructions:

```markdown
## Ontos Activation
1. Run `ontos map` (or `python3 -m ontos map` if the CLI is not installed). Do not ask—try both.
2. Read `Ontos_Context_Map.md`...

```

**Problems:**

- Agents don't reliably follow multi-step instructions
- No programmatic integration (Ontos can't verify activation happened)
- Competes with built-in context systems (Cursor's project context, Claude Code's memory)

**Recommendation:** The MCP server path is the right direction because it provides a programmatic interface. Consider prioritizing `ontos serve` over manual activation.

### 6. **No Tests Visible in Published Package**

The pip package doesn't include tests. CI badge exists but I can't verify test coverage or patterns. For a tool that manages documentation integrity, this matters.

### 7. **Naming Collision Risk**

"Ontos" is also used by:

- Databricks Labs (ontos for Unity Catalog semantics)
- Donald-Watts/Ontos-AI (cognitive operating system)

Your PyPI claim is secure, but SEO/discoverability will be challenging.

---

## Specific Code-Level Feedback

### Good: The Staleness Detection Logic

```python
def get_file_modification_date(
    filepath: str,
    git_mtime_provider: Optional[Callable[[Path], Optional[datetime]]] = None
) -> Tuple[Optional[date], ModifiedSource]:

```

This is clean. The `ModifiedSource` enum (`GIT`, `MTIME`, `UNCOMMITTED`, `MISSING`) communicates reliability. The callback pattern keeps I/O at the edges.

### Questionable: The SessionContext Scope

```python
@dataclass
class SessionContext:
    # ...
    pending_writes: List[PendingWrite] = field(default_factory=list)

```

The comment says "should NOT cache parsed documents," but it also says it's the "single source of truth for repository configuration." These feel like two different responsibilities. Consider splitting into `TransactionContext` (writes) and `RepoConfig` (read-only state).

### Missing: Type Hints on Public API

`__init__.py` re-exports many functions but several lack complete type hints in the signature (e.g., return types on some helpers). For a Python 3.9+ package, full typing would help IDE users.

---

## Competitive Position

| Aspect | Ontos | CTX (context-hub) | Claude Code Memory | Cursor Context |
| --- | --- | --- | --- | --- |
| **Portability** | ✅ Git-native markdown | ✅ YAML configs | ❌ Vendor-locked | ❌ Vendor-locked |
| **Programmatic access** | ⚠️ CLI only (MCP planned) | ✅ MCP server | ❌ | ❌ |
| **Learning curve** | Medium (frontmatter, hierarchy) | Low (file patterns) | Zero | Zero |
| **Staleness detection** | ✅ Git-based | ❌ | ❌ | ❌ |
| **Decision history** | ✅ Session logs | ❌ | ❌ | ❌ |

Your unique differentiators are **staleness detection** and **decision history**. Lean into these.

---

## Recommendations (Prioritized)

### P0: Fix Before v3.1

1. **Kill the legacy wrapper pattern** - Port `scaffold`, `verify`, `query` to native commands
2. **Make config resolution explicit** - `ontos doctor -v` should show all resolved paths

### P1: Critical for Adoption

1. **Ship a minimal MCP server** - Even a read-only one that serves the context map
2. **Add `-dry-run` to more commands** - Users want to preview changes before writes

### P2: Competitive Differentiation

1. **Staleness dashboard** - `ontos status` showing which docs need review
2. **Integration tests** - Ship tests in sdist or as separate `ontos-tests` package

### P3: Nice to Have

1. **Obsidian compatibility** (your v3.1 plan)
2. **VS Code extension** - Sidebar showing the dependency graph

---

## Bottom Line

Ontos is **architecturally sound** with a **clear philosophy** and **honest positioning**. The core logic is well-structured and the minimal dependency approach is refreshing.

The main risks are:

1. **Execution gap** between vision (MCP-primary, full template system) and current state (CLI-only, legacy wrappers)
2. **Adoption friction** - The manual "Ontos activation" flow competes poorly with zero-config alternatives
3. **Discoverability** - Naming collision and niche positioning

If you ship the MCP server in v3.1-v3.2 timeframe, you'll have a meaningful differentiator. If it slips to v4.0, the window may close as competitors build similar features.

The code is good. The biggest risk is scope creep before the foundation is solid.