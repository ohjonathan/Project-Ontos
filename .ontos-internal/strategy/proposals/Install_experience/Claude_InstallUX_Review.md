---
id: claude_install_ux_review
type: atom
status: complete
depends_on: [installation_ux_proposal]
concepts: [ux, installation, dx, architecture-review]
---

# Architectural Review: Installation UX Proposal

**Reviewer:** Claude (Opus 4.5)
**Date:** 2025-12-19
**Documents Reviewed:** Installation_UX_Proposal.md, Ontos_Installation_Experience_Report.md, ontos_init.py, README.md, Ontos_Agent_Instructions.md

---

## Executive Summary

The Installation UX Proposal correctly identifies real friction in the Ontos installation process. However, it over-engineers solutions for problems that could be fixed with documentation edits, and overlooks that key functionality (`--non-interactive`, `--mode`, `--source`) already exists but is poorly discoverable.

**Recommendation:** Fix the documentation first, then add `ontos_activate.py`, then consider `install.sh`. Defer PyPI packaging until user demand materializes.

---

## 1. Testing the Overall Rationale

### 1.1 Where the Rationale is Sound

**The problem is real and well-documented.** The Experience Report provides concrete evidence of friction. The 7+ step manual process, wrong-order uninstall instructions, and duplicate files are legitimate issues that hurt adoption.

**The competitive analysis is valuable.** Comparing against create-react-app, Vite, and pre-commit establishes a clear north star. The "1-2 command" target is reasonable.

**The phased approach is pragmatic.** Separating quick wins (v2.8) from structural changes (v3.0) allows incremental improvement without blocking on a complete rewrite.

### 1.2 Where the Rationale is Weak

**The friction analysis conflates different problem types:**

| Friction Type | Example | Correct Fix |
|---------------|---------|-------------|
| **Broken documentation** | Uninstall command order | Fix the docs (5 min) |
| **Discoverability** | `--non-interactive` not found | Improve `--help`, not new code |
| **Inherent complexity** | Understanding what to copy | Better docs OR install.sh |
| **Design debt** | Duplicate Common_Concepts.md | Clean up source repo |

The proposal treats all friction as if it requires new code. Some issues (like the uninstall order) require only a documentation edit.

**Critical oversight: `--non-interactive` already exists.**

Looking at `ontos_init.py:467-483`, the script **already has** `--non-interactive`, `--mode`, and `--source` flags:

```python
parser.add_argument('--non-interactive', action='store_true', ...)
parser.add_argument('--mode', choices=['automated', 'prompted', 'advisory'], default='prompted', ...)
parser.add_argument('--source', default='', ...)
```

The Experience Report's "Attempt 1" and "Attempt 2" failures were **user error** (not running `--non-interactive`), not missing functionality. This suggests the real problem is **discoverability**, not capability.

**The `curl | bash` pattern has security concerns.**

The proposal positions `curl -fsSL https://ontos.dev/install.sh | bash` as the gold standard, but:
- Many corporate environments block piping curl to bash
- Security-conscious users won't run unsigned scripts from the internet
- This requires hosting infrastructure (ontos.dev domain, HTTPS, uptime)

For a repo-local tool like Ontos, this may be over-engineering.

**Competitive analysis compares apples to oranges.**

| Tool | Distribution Model | Why Different |
|------|-------------------|---------------|
| create-react-app | npm registry (centralized) | Has npm's infrastructure |
| pre-commit | PyPI (centralized) | Has PyPI's infrastructure |
| Ontos | Git repo (decentralized) | No registry, repo-local |

Ontos's distribution model is fundamentally different. The better comparison might be:
- **Husky** (git hooks via npm): `npx husky-init` works because npm does the heavy lifting
- **EditorConfig** (repo-local config): No installer at all, just `.editorconfig`
- **pre-commit** (Python): Requires `pip install pre-commit` first

---

## 2. What I Would Have Done Differently

### 2.1 Start with the Documentation Fix (Day 1)

Before writing any code, I would fix the immediate broken things:

```bash
# 30-minute PR that immediately helps users
1. Fix uninstall command order in Ontos_Manual.md
2. Delete duplicate docs/reference/Common_Concepts.md (keep templates version)
3. Improve --help output in ontos_init.py (the code change is ~20 lines)
4. Update README Quick Start to show --non-interactive option
```

This addresses 50% of the reported friction with near-zero risk.

### 2.2 Reframe the Problem

The proposal frames the problem as "installation requires 8+ steps." I would reframe it as:

> **"Users don't understand Ontos's mental model before they start."**

The friction isn't that copying files is hard—it's that users don't know:
- What Ontos actually installs (tooling vs. generated files vs. documentation)
- Why files come from different locations
- What "Initiate Ontos" means vs. `python3 ontos_init.py`

A **conceptual diagram** in the README might help more than an install script:

```
┌─────────────────────────────────────────────────────────────┐
│  What You Copy (from Project-Ontos repo)                    │
├─────────────────────────────────────────────────────────────┤
│  .ontos/           -> Tooling (scripts, hooks, templates)   │
│  ontos_init.py     -> One-time setup script                 │
└─────────────────────────────────────────────────────────────┘
                              |
                    python3 ontos_init.py
                              |
                              v
┌─────────────────────────────────────────────────────────────┐
│  What Gets Generated (in your project)                      │
├─────────────────────────────────────────────────────────────┤
│  ontos_config.py      -> Your configuration                 │
│  Ontos_Context_Map.md -> The knowledge graph                │
│  docs/                -> Directory structure for docs       │
│  .git/hooks/          -> Pre-push and pre-commit hooks      │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 Prioritize Differently

**Proposal's priority:** `install.sh` -> preview mode -> conflict detection -> CLI refactor

**My priority:**
1. **Fix broken docs** (uninstall order, duplicate files) — immediate
2. **Improve `--help`** — same day
3. **Add `ontos_activate.py`** — eliminates "Initiate Ontos" confusion
4. **Create `install.sh`** — only after above are done
5. **PyPI packaging** — only if community requests it

The CLI refactor (v3.0) should be driven by user demand, not anticipated need.

### 2.4 Question the `install.sh` Approach

Before creating `install.sh`, I would ask: **Who is the installer?**

| Installer Type | Best Experience | Why |
|----------------|-----------------|-----|
| Human developer | README instructions | Can read, adapt, troubleshoot |
| AI agent | Structured prompt in README | Already works (the Quick Start section) |
| CI/CD pipeline | Dockerfile or setup step | Needs deterministic, not interactive |

The Experience Report was generated by an AI agent that **successfully installed Ontos** despite the friction. The agent found the `--non-interactive` flag (eventually) via trial-and-error. A better `--help` output would have prevented all three failed attempts.

For AI agents, the **prompt in the README** is arguably the best UX—they can read it, understand it, and adapt.

---

## 3. Additional Improvements Within Current Structure

### 3.1 Immediate Wins (No Structural Changes)

**A. Add input sequence to `--help`:**

```diff
+ INTERACTIVE MODE PROMPTS:
+   If run without --non-interactive, you'll be asked:
+   1. Choose workflow mode (1-3)
+   2. Enter your name for logs (optional)
```

**B. Add a "dry run" mode:**

```bash
python3 ontos_init.py --dry-run
# Output: Would create: docs/logs/, docs/strategy/, ontos_config.py, ...
```

**C. Add `ontos_activate.py`:**

The Agent Instructions define "Initiate Ontos" as 6 manual steps. This should be a script:

```python
# .ontos/scripts/ontos_activate.py
# Runs steps 1-6, outputs "Loaded: [id1, id2, ...]"
```

This addresses the #1 post-install friction without any structural changes.

### 3.2 Medium-Term Improvements

**A. Consolidate file sources:**

The proposal correctly identifies that files come from multiple locations. Current state:

```
.ontos/                                      -> Copy to target
ontos_init.py                                -> Copy to target
docs/reference/Ontos_Agent_Instructions.md   -> Copy to target docs/reference/
.ontos-internal/reference/Common_Concepts.md -> Copy to target docs/reference/
```

Better structure:

```
.ontos/
├── scripts/
├── hooks/
├── templates/
└── install/                    # NEW: Everything needed for install
    ├── ontos_init.py
    └── docs/
        └── reference/
            ├── Ontos_Agent_Instructions.md
            └── Common_Concepts.md  # Canonical version
```

Then the README becomes: "Copy `.ontos/` and `.ontos/install/ontos_init.py` to your project."

**B. Make `Ontos_Agent_Instructions.md` optional:**

The proposal asks: "Should agent instructions be auto-copied, bundled in context map, or fetched on-demand?"

My answer: **Bundle essential instructions in the context map header.**

The Context Map already has a YAML header. Add:

```markdown
<!--
Ontos Context Map
Generated: 2025-12-19
Mode: User

## Agent Quick Reference
- "Ontos" -> Read this map, load relevant IDs
- "Archive Ontos" -> Run ontos_end_session.py
- "Maintain Ontos" -> Run ontos_maintain.py
-->
```

Now agents don't need a separate Agent Instructions file—the essential commands are in the file they already read.

**C. Add conflict detection to `ontos_init.py`:**

The proposal's conflict detection code (Section 3.2.4) is sound. I would add it, but make it **informational by default**:

```
Existing files detected:
  - docs/ (directory exists, 47 files)
  - .git/hooks/pre-push (Husky hook)

Ontos will:
  - Add subdirectories to docs/ (logs/, strategy/, archive/, reference/)
  - Skip pre-push hook (integrate manually)

Continue? [Y/n]
```

### 3.3 Addressing the Open Questions

**Q1: PyPI packaging - worth it?**

Not yet. PyPI adds maintenance overhead (versioning, releases, dependency management). Ontos's current distribution model (git clone + copy) is fine for early adopters. Revisit after 100+ stars or explicit user requests.

**Q2: Directory structure negotiation?**

Opinionated default (`docs/`) with escape hatch (`DOCS_DIR` config). Don't ask during install—users who care will edit `ontos_config.py`.

**Q3: Existing `docs/` folder?**

Add subdirectories. Don't create `ontos-docs/`. The proposal's "add subdirectories" approach is correct—it's the least surprising behavior.

**Q4: Agent instructions location?**

Bundle in context map header (see 3.2.B above). Reduces file count and ensures agents always have instructions.

**Q5: Contributor vs. User mode detection?**

Detect by presence of `.ontos-internal/`:

```python
if os.path.exists('.ontos-internal'):
    print("Contributor mode detected (Ontos repo itself)")
    mode = 'contributor'
else:
    mode = 'user'
```

---

## 4. Risk Assessment

| Proposed Change | Risk Level | Concern |
|-----------------|------------|---------|
| Fix uninstall docs | None | Pure documentation |
| Improve `--help` | Low | Small code change, high impact |
| Add `ontos_activate.py` | Low | New script, no breaking changes |
| Add `--dry-run` | Low | Additive feature |
| Create `install.sh` | Medium | New distribution channel to maintain |
| Consolidate file locations | Medium | Breaking change for existing instructions |
| PyPI packaging | High | Significant maintenance overhead |
| Full CLI refactor | High | Major rewrite, high risk of scope creep |

---

## 5. Summary

| Aspect | Assessment |
|--------|------------|
| **Problem identification** | Strong. Real friction documented with evidence. |
| **Root cause analysis** | Mixed. Conflates code issues with documentation issues. |
| **Proposed solutions** | Over-engineered. Some problems need docs fixes, not new code. |
| **Phasing** | Good. Quick wins -> structural changes is the right order. |
| **Competitive analysis** | Flawed comparison. Ontos isn't npm-distributed. |
| **Open questions** | Well-framed. Answers provided in Section 3.3. |

---

## 6. Recommended Action Plan

### Immediate (This Week)

| Task | Effort | Impact |
|------|--------|--------|
| Fix uninstall command order in Ontos_Manual.md | 5 min | High |
| Delete duplicate `docs/reference/Common_Concepts.md` | 5 min | Medium |
| Improve `--help` output with input sequence | 30 min | High |
| Update README Quick Start with `--non-interactive` example | 10 min | High |

### Short-Term (v2.8)

| Task | Effort | Impact |
|------|--------|--------|
| Create `ontos_activate.py` script | 2 hours | High |
| Add `--dry-run` flag to `ontos_init.py` | 1 hour | Medium |
| Add conflict detection (informational) | 2 hours | Medium |

### Defer Until Requested

| Task | Reason to Defer |
|------|-----------------|
| `install.sh` bootstrap | Current README prompt works for AI agents |
| PyPI packaging | Maintenance overhead, no proven demand |
| Full CLI refactor | Premature optimization |

---

## 7. Conclusion

The Installation UX Proposal is thorough and well-intentioned, but risks solving problems that don't exist yet while leaving easy wins on the table. The core insight—that installation friction hurts adoption—is correct. The solution set is too ambitious for the problem size.

**Start with the documentation fixes.** They're free, immediate, and address the majority of the friction documented in the Experience Report. The `--non-interactive` flag already exists; users just can't find it.

**The proposal's greatest value** is in identifying the duplicate `Common_Concepts.md` issue and the wrong-order uninstall instructions. Fix those today.

**The proposal's greatest risk** is scope creep toward a PyPI package and full CLI refactor before validating that users actually want that level of polish.
