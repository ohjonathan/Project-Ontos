---
id: v3_1_1_init_improvements_proposal
type: strategy
status: draft
depends_on: [mission, philosophy, constitution, v3_0_technical_architecture]
concepts: [init, scaffold, directory-structure, onboarding, type-hierarchy]
---

# v3.1.1 Proposal: `ontos init` Improvements

**Author:** Claude Opus 4.5
**Date:** 2026-01-22
**Status:** Draft (pending multi-LLM review)
**Scope:** Two changes to the `ontos init` command

---

## 1. Motivation

When a user runs `ontos init` for the first time, two gaps exist:

1. **Incomplete directory structure.** The init command creates `docs/strategy/`, `docs/reference/`, `docs/logs/`, and `docs/archive/`, but does NOT create `docs/kernel/`, `docs/product/`, or `docs/atom/`. This is inconsistent with the document type hierarchy (kernel, strategy, product, atom, log) that is central to Ontos. New users don't get a clear signal about where to put different types of documents.

2. **No bridge to scaffolding.** After `ontos init`, users with existing markdown files must separately discover and run `ontos scaffold` to tag them. There's no prompt or guidance during init. This creates a gap in the onboarding flow.

---

## 2. Proposed Changes

### 2.1 Full Type Hierarchy Directories

**Current behavior** (`ontos/commands/init.py:105-111`):

```python
dirs = [
    config.paths.docs_dir,          # "docs"
    config.paths.logs_dir,          # "docs/logs"
    f"{config.paths.docs_dir}/strategy",
    f"{config.paths.docs_dir}/reference",
    f"{config.paths.docs_dir}/archive",
]
```

**Proposed behavior:**

```python
dirs = [
    config.paths.docs_dir,          # "docs"
    config.paths.logs_dir,          # "docs/logs"
    f"{config.paths.docs_dir}/kernel",
    f"{config.paths.docs_dir}/strategy",
    f"{config.paths.docs_dir}/product",
    f"{config.paths.docs_dir}/atom",
    f"{config.paths.docs_dir}/reference",
    f"{config.paths.docs_dir}/archive",
]
```

**Rationale:**
- Maps 1:1 to the Ontos type ranking: kernel (0), strategy (1), product (2), atom (3)
- `logs/` already exists (via `config.paths.logs_dir`)
- `reference/` and `archive/` are retained as utility directories (not types, but organizational)
- Path-based type inference in `ontos scaffold` uses patterns like `/kernel/`, `/strategy/`, `/product/`, `/atom/` -- having these directories present means files placed in them will be correctly typed

**Also update:** The `_create_directories()` helper function at line 172-182 has a duplicate directory list that must be kept in sync.

---

### 2.2 Interactive Scaffold Integration

After directory creation, `ontos init` will optionally run `ontos scaffold` on existing untagged markdown files.

#### 2.2.1 New `InitOptions` Fields

```python
@dataclass
class InitOptions:
    path: Path = None
    force: bool = False
    interactive: bool = False  # Reserved for v3.1
    skip_hooks: bool = False
    yes: bool = False
    scaffold: bool = False      # NEW: Force scaffold without prompt
    no_scaffold: bool = False   # NEW: Suppress scaffold prompt entirely
```

#### 2.2.2 New CLI Flags

In `ontos/cli.py`, add a mutually exclusive group to the init subparser:

```python
scaffold_group = p.add_mutually_exclusive_group()
scaffold_group.add_argument("--scaffold", action="store_true",
                            help="Auto-scaffold untagged files (uses docs/ scope)")
scaffold_group.add_argument("--no-scaffold", action="store_true",
                            help="Skip scaffold prompt")
```

#### 2.2.3 Behavioral Matrix

| Condition | Result |
|-----------|--------|
| `--no-scaffold` | Skip entirely, no output |
| `--scaffold` | Force scaffold with `docs_dir` as scope, no prompt |
| Non-TTY (CI) | Skip silently (same as `--no-scaffold`) |
| TTY, no untagged files | Skip silently, no prompt shown |
| TTY, untagged files exist | Show count, prompt for confirmation + scope |

#### 2.2.4 Interactive Flow (TTY with untagged files)

```
Found 5 untagged markdown file(s).
Would you like to scaffold them? [y/N] y

Where should we scan?
  (1) docs/ directory only
  (2) Entire repository
  (3) Custom path
Choice [1]: _
```

- Default choice is `1` (docs/ only) -- safest option
- Choice `2` scans project root, respects `.ontosignore` patterns
- Choice `3` prompts for a path (relative to project root)

#### 2.2.5 Execution Order

The scaffold step is inserted between directory creation (step 5) and context map generation (step 6):

```
Step 4: Create .ontos.toml
Step 5: Create directory structure (full type hierarchy)
Step 5.5: Scaffold integration (NEW)
Step 6: Generate initial context map
Step 7: Install hooks
Step 8: Generate AGENTS.md
```

This ordering ensures:
- Type directories exist before scaffold runs (path-based type inference works correctly)
- Scaffolded files get frontmatter BEFORE map generation picks them up
- Map will include newly scaffolded documents in its output

#### 2.2.6 Non-Fatal Design

Scaffold failure during init is non-fatal (prints warning, does not change exit code). This matches the existing pattern used by `_generate_agents_file()`.

```python
def _run_scaffold(project_root: Path, paths: List[Path]) -> None:
    """Run scaffold on given paths. Non-fatal on failure."""
    try:
        from ontos.commands.scaffold import ScaffoldOptions, scaffold_command
        options = ScaffoldOptions(paths=paths, apply=True, dry_run=False)
        exit_code, message = scaffold_command(options)
        if exit_code != 0:
            print(f"Warning: Scaffold: {message}", file=sys.stderr)
    except Exception as e:
        print(f"Warning: Could not run scaffold: {e}", file=sys.stderr)
```

#### 2.2.7 Error Handling

| Scenario | Behavior |
|----------|----------|
| `EOFError` during prompt | Skip scaffold, continue init |
| `KeyboardInterrupt` during prompt | Skip scaffold, continue init (NOT abort) |
| `KeyboardInterrupt` during `scaffold_command` | Outer `except KeyboardInterrupt` triggers, cleanup runs |
| Invalid custom path | Warn, fall back to docs_dir |
| `find_untagged_files` raises | Skip scaffold silently |
| `scaffold_command` returns non-zero | Warn, continue init |

---

## 3. Files to Modify

| File | Changes |
|------|---------|
| `ontos/commands/init.py` | Expand dirs list, add `InitOptions.scaffold`/`no_scaffold`, add `_prompt_scaffold()`, add `_run_scaffold()`, insert call in `init_command` |
| `ontos/cli.py` | Add `--scaffold`/`--no-scaffold` to `_register_init`, pass fields in `_cmd_init` |
| `tests/commands/test_init_phase3.py` | Update directory assertions to include `kernel/`, `product/`, `atom/` |

## 4. New Files

| File | Purpose |
|------|---------|
| `tests/commands/test_init_scaffold.py` | Tests for scaffold integration (see Section 6) |

---

## 5. Key Design Decisions

### D1: `--yes` does NOT auto-scaffold

The `--yes` flag means "accept defaults." For hooks, the default is to install them. For scaffold, the default is to NOT scaffold (because it modifies user files). Therefore `--yes` alone does not trigger scaffold. Users who want fully automated init use `--yes --scaffold`.

### D2: `--scaffold` defaults to `docs_dir` scope

When `--scaffold` is passed (non-interactive), it scans `config.paths.docs_dir` only. This is the safest default for CI/scripting. Whole-repo scanning is only available through the interactive prompt.

### D3: Scaffold uses `apply=True` during init

Since the user already confirmed via the interactive prompt (or via `--scaffold` flag), there's no point in a dry-run. Scaffold applies immediately.

### D4: `reference/` and `archive/` are retained

These directories don't map to document types but serve organizational purposes:
- `reference/` holds shared reference material (typed as `atom` or `strategy` in frontmatter)
- `archive/` holds deprecated/consolidated logs

They're kept alongside the type directories for backwards compatibility.

### D5: Cleanup on abort includes scaffolded files?

**Decision needed.** If Ctrl+C happens AFTER scaffold has committed (written frontmatter to files), should we attempt to undo the scaffold writes? Current plan: NO -- `SessionContext.commit()` is atomic (writes all buffered files), and once committed, the files have been modified. The cleanup only removes newly created directories and config files, not modified content.

---

## 6. Test Plan

### Directory Tests

```python
def test_init_creates_full_type_hierarchy(git_repo):
    """Init creates all type directories."""
    init_command(InitOptions(path=git_repo, skip_hooks=True, no_scaffold=True))
    for subdir in ['kernel', 'strategy', 'product', 'atom', 'logs', 'reference', 'archive']:
        assert (git_repo / "docs" / subdir).is_dir()
```

### Scaffold Integration Tests

| Test | Scenario | Expected |
|------|----------|----------|
| `test_no_scaffold_flag_skips` | `--no-scaffold` | No prompt, no scaffold |
| `test_scaffold_flag_forces` | `--scaffold` with existing untagged file | File gets frontmatter, no prompt |
| `test_non_tty_skips` | Non-TTY env | No prompt, no scaffold |
| `test_no_untagged_skips` | TTY, all files tagged | No prompt shown |
| `test_prompt_decline` | User answers 'n' | No scaffold |
| `test_prompt_accept_docs_scope` | User answers 'y', '1' | Only docs/ scanned |
| `test_prompt_accept_repo_scope` | User answers 'y', '2' | Entire repo scanned |
| `test_prompt_custom_path` | User answers 'y', '3', path | Custom path scanned |
| `test_eof_skips_gracefully` | EOFError during prompt | Init succeeds, no scaffold |
| `test_keyboard_interrupt_skips` | Ctrl+C during prompt | Init succeeds, scaffold skipped |
| `test_scaffold_failure_nonfatal` | `scaffold_command` raises | Init succeeds with warning |
| `test_invalid_custom_path` | Non-existent path entered | Falls back to docs/ with warning |

---

## 7. Open Questions for Reviewers

### Q1: Should init create a starter `kernel/mission.md` stub?

When `kernel/` is created, it's empty. Should init also create a minimal `docs/kernel/mission.md` stub (L1) to guide users toward documenting their project's mission? This would make the "Activate Ontos" flow immediately useful even before the user writes anything.

**Arguments for:** Reduces time-to-value. A mission doc is always needed. Matches the "opinionated defaults" philosophy.
**Arguments against:** Violates "intent over automation." Users should consciously create kernel docs. An empty stub might feel like busywork.

### Q2: Should the scaffold prompt show a preview before applying?

Current plan: if user says 'y' to scaffold, we apply immediately. Should we instead show a dry-run preview (list of files + inferred types) and ask for a second confirmation?

**Arguments for:** Less surprising. Users see exactly what will be modified.
**Arguments against:** Extra friction. The scaffold is non-destructive (only adds frontmatter, doesn't modify content). Users can always run `ontos scaffold` with dry-run later to verify.

### Q3: Exclusion patterns for whole-repo scanning

When user picks "Entire repository" scope, the scan uses `.ontosignore` patterns. Should we also hardcode additional exclusions (like `node_modules/`, `vendor/`, `.venv/`, `__pycache__/`) that are almost never wanted? Or rely solely on `.ontosignore`?

**Current behavior:** `find_untagged_files` already skips hidden directories (except `.ontos*`). It delegates to `scan_documents` which uses `.ontosignore`. No hardcoded exclusions for common dependency directories.

**Risk:** A fresh project won't have `.ontosignore` yet. Running whole-repo scan could pick up markdown files inside `node_modules/`.

### Q4: Should `--scaffold` accept an optional path argument?

Instead of always defaulting to `docs_dir`, should `--scaffold` accept an optional positional argument for scope?

```bash
ontos init --scaffold            # Default: docs/
ontos init --scaffold=.          # Entire repo
ontos init --scaffold=notes/     # Custom path
```

This would give CLI users the same scope flexibility as interactive users.

### Q5: `reference/` directory -- keep, rename, or remove?

`reference/` doesn't map to any document type. Options:
1. **Keep as-is** (current plan) -- backwards compatible, useful as a catch-all
2. **Remove from init** -- users create it manually if needed
3. **Rename to `shared/`** -- clearer purpose (shared concepts referenced by multiple docs)

### Q6: Should type directories be configurable in `.ontos.toml`?

Currently `docs_dir` and `logs_dir` are configurable. Should the type subdirectories also be configurable? e.g.:

```toml
[paths]
kernel_dir = "docs/kernel"
strategy_dir = "docs/strategy"
product_dir = "docs/product"
atom_dir = "docs/atom"
```

**Arguments for:** Flexibility for non-standard project layouts.
**Arguments against:** Over-engineering. Most users will use defaults. Adds complexity to config, init, and scaffold.

---

## 8. Compatibility Notes

- **Existing projects:** Running `ontos init` on an already-initialized project returns exit code 0 ("already initialized"). The new directories will NOT be retroactively created for existing projects. Users would need to create them manually or re-init with `--force`.
- **Backwards compatibility:** No breaking changes. The new directories are additive. The scaffold prompt is opt-in (skipped in non-TTY, suppressible with `--no-scaffold`).
- **Config version:** No `.ontos.toml` schema change needed. The directory structure is derived from `docs_dir`, not stored explicitly.

---

## 9. Implementation Sequence

1. Add `kernel/`, `product/`, `atom/` to directory list (both locations in init.py)
2. Add `scaffold`/`no_scaffold` fields to `InitOptions`
3. Implement `_prompt_scaffold()` function
4. Implement `_run_scaffold()` function
5. Insert scaffold step in `init_command` flow (between steps 5 and 6)
6. Update `_register_init` and `_cmd_init` in cli.py
7. Update existing directory tests
8. Add new scaffold integration tests
9. Run full test suite to verify no regressions
