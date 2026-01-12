# Ontos v3.0 Architecture: Chief Architect Response

**Date:** 2026-01-12
**Architecture Version:** 1.1 → 1.2
**Reviews Addressed:** 4 (consolidated from Codex, Claude, Gemini Architectural, Gemini DeepThink)
**Author:** Claude Opus 4.5 (Chief Architect)

---

## 1. Overall Assessment Response

**Reviewer Consensus:** 4/4 approved with changes. 0/4 rejected. 0/4 requested major revision.

**My Reaction:** Gratified but humbled. The unanimous "approve with changes" verdict validates the fundamental architecture while the specific critiques reveal genuine blind spots. The reviewers engaged thoughtfully with a complex document, and their feedback will meaningfully improve the architecture.

**Key Takeaways:**

**What Surprised Me:**
- The unanimity around missing `core/suggestions.py` and `core/tokens.py`. I referenced these in decomposition tables but forgot to add them to the package structure. Classic "curse of knowledge" — I knew they would exist, so I didn't notice they weren't specified.
- Windows hook incompatibility being flagged as Critical by 2 reviewers. I had mentally filed Windows under "best effort" without considering that `#!/bin/sh` shims would literally fail on Windows. This is a real gap for a "Distribution & Polish" release.

**What Confirmed My Thinking:**
- All reviewers praised the ValidationOrchestrator pattern. The decision to move from hard-exits to error collection was controversial internally, but reviewer validation strengthens my confidence.
- The layered architecture (CLI → Commands → Core → I/O) received strong support. No reviewer suggested alternative layering.
- Q11 (script reorganization) and Q13 (Markdown primary) decisions were unanimously confirmed.

**Where I See Blind Spots I Missed:**
1. **Purification work underestimated:** I marked `staleness.py`, `proposals.py`, `history.py` as "EXISTS" implying no changes needed. In reality, these modules contain git subprocess calls that violate core purity. C and D caught this.
2. **Config loading pattern unclear:** I didn't explicitly document how config flows from disk to core. C's Inversion of Control critique is valid — the architecture should be explicit about this.
3. **Line count arithmetic:** The decomposition tables don't add up. 1,904 lines decomposed to ~1,150 leaves ~750 lines unaccounted for. All four reviewers noticed.

---

## 2. Decision Alignment Response

| Q# | Issue Flagged | Consensus | Response | Action |
|----|---------------|-----------|----------|--------|
| Q1 | — | 4/4 ✅ | N/A | None needed |
| Q2 | — | 4/4 ✅ | N/A | None needed |
| Q3 | — | 4/4 ✅ | N/A | None needed |
| Q4 | Confirmation step not in data flow | 3/4 ⚠️ | ✅ Valid — will fix | Add confirmation to Section 5.3 data flow |
| Q5 | Missing `required_version` field | 4/4 ❌ | ✅ Valid — will fix | Add field to `.ontos.toml` schema (Section 6.1) |
| Q6 | Windows hook incompatibility | 2/4 ⚠️ | ✅ Valid — will fix | Change to Python-based shim (Section 8.1) |
| Q7 | "Docs-only" deliverable details missing | 1/4 ⚠️ | ⚠️ Partial — minor | Add brief note; not blocking |
| Q8 | Summarization interface missing | 1/4 ⚠️ | ⚠️ Defer | Address during implementation |
| Q9 | — | 4/4 ✅ | N/A | None needed |
| Q10 | — | 4/4 ✅ | N/A | None needed |
| Q11 | — | 4/4 ✅ | N/A | None needed |
| Q12 | — | 4/4 ✅ | N/A | None needed |
| Q13 | — | 4/4 ✅ | N/A | None needed |

**Q4 Explanation:** The Strategy doc says "Use `git diff` for change detection, require confirmation." The architecture shows git diff detection but omits the confirmation step. This is an oversight. I'll add a confirmation step to the `ontos log` data flow with an `--auto` flag for CI/scripting bypass.

**Q5 Explanation:** The Strategy doc says "Warn on version mismatch." The architecture shows `.ontos.toml` but doesn't include a `required_version` field or describe how version checking works. This is a genuine gap that must be fixed.

**Q6 Explanation:** The shim hook uses `#!/bin/sh` which fails on Windows. While Windows is "best-effort," a shim that literally fails to parse isn't best-effort — it's broken. I'll switch to a Python-based shim that works cross-platform.

---

## 3. Critical Issues Response

### Issue: Core Purity Violations — Consensus: 2/4

**Reviewers Said:** Architecture lists `staleness.py`, `proposals.py`, `history.py` as "EXISTS" (reuse as-is) in `core/`. But these modules perform direct I/O (subprocess git calls, file reads). Moving them to `core/` without refactoring violates the "Functional Core" principle immediately.

**My Assessment:**
- Validity: **Valid**
- Reasoning: The reviewers are correct. I audited the codebase and confirmed:
  - `staleness.py:80-137` (`get_file_modification_date`) calls `subprocess.run(["git", "log", ...])`
  - `proposals.py:168-195` reads files directly with `Path.read_text()`
  - `history.py:45-80` calls git subprocess for commit history

  These violate the "no I/O in core" principle I established.

**Decision:** Accept

**Change:**
- Mark `staleness.py`, `proposals.py`, `history.py` as **REFACTOR** (not EXISTS) in Section 3.2
- Add note: "These modules require I/O extraction. Logic functions will accept data arguments; `io/` modules will handle git subprocess calls and file reads."
- Section(s) Affected: 3.2, 13.1

**Effort:** Low (documentation change). Medium (actual refactoring during implementation).

---

### Issue: Windows Hook Incompatibility — Consensus: 2/4

**Reviewers Said:** The shim hook (Section 8.1) is `#!/bin/sh`. This fails for Windows users, breaking the "Distribution & Polish" promise.

**My Assessment:**
- Validity: **Valid**
- Reasoning: A shell script with `#!/bin/sh` won't execute on Windows Command Prompt or PowerShell. The architecture claims "Windows: best-effort" but a hook that won't parse isn't best-effort — it's non-functional. v3.0 is about distribution polish; this is distribution breakage.

**Decision:** Accept

**Change:**
- Replace `#!/bin/sh` shim with Python-based shim
- The shim will be `#!/usr/bin/env python3` and delegate to `ontos hook pre-push`
- On Windows, Git will invoke Python directly (assuming Python is in PATH, which it must be for Ontos to work anyway)
- Section(s) Affected: 8.1

**Effort:** Low

**New shim pattern:**
```python
#!/usr/bin/env python3
"""Ontos pre-push hook (shim). Delegates to global CLI."""
import subprocess
import sys
try:
    sys.exit(subprocess.call(["ontos", "hook", "pre-push"] + sys.argv[1:]))
except FileNotFoundError:
    print("Warning: ontos not found in PATH. Skipping.", file=sys.stderr)
    sys.exit(0)
```

---

### Issue: Circular Config Dependency — Consensus: 1/4

**Reviewers Said:** Architecture states `core/` MUST NOT import `io/`. However, `core/config.py` needs to load `.ontos.toml`. If it uses `io/toml.py`, it violates layering. If it duplicates parsing logic, it violates DRY.

**My Assessment:**
- Validity: **Valid**
- Reasoning: C identified a real architectural tension. The solution is **Inversion of Control**: `cli.py` loads config via `io/toml.py` and injects the result into `core/` functions. `core/config.py` should only define the `OntosConfig` dataclass and provide defaults — not perform loading.

**Decision:** Accept

**Change:**
- Clarify in Section 6.2: "Config Loading Pattern"
- `cli.py` calls `io/toml.py:load_config()` to get raw dict
- `cli.py` constructs `OntosConfig` dataclass (defined in `core/types.py`)
- `cli.py` passes `OntosConfig` to command functions
- `core/` modules receive config as parameter, never load it themselves
- Section(s) Affected: 6.2 (new subsection), 3.2 (`core/config.py` description)

**Effort:** Low

---

## 4. Major Issues Response

### Issue: Q4 Confirmation Not in Data Flow — Consensus: 3/4

**Reviewers Said:** Strategy decision says "require confirmation." Data flow shows detection but no confirmation step.

**Decision:** Accept

**Reasoning:** The reviewers are right. The `ontos log` data flow must include a confirmation step. I'll add:
1. After detecting changed files, display list to user
2. Ask for confirmation before creating/updating log
3. Provide `--auto` flag to skip confirmation (for CI/scripting)

**Action:** Update Section 5.3 data flow diagram to include confirmation step.

---

### Issue: Algorithm Complexity Mismatch — Consensus: 1/4

**Reviewers Said:** Spec mandates "O(V+E) DFS" for cycle detection. Existing implementation uses `path[path.index(neighbor):]` inside traversal, creating O(N²) complexity.

**Decision:** Accept (as implementation note)

**Reasoning:** D is technically correct. The existing cycle detection in `ontos_generate_context_map.py` is O(V × path_length) due to `path.index()`. For a proper O(V+E) implementation, we need a `visited` set and `in_stack` set pattern. This is an implementation detail, not an architecture issue — but I'll add a note.

**Action:** Add note to `core/graph.py` spec: "Implementation must use standard DFS with O(V+E) complexity. Avoid `path.index()` pattern."

---

### Issue: ValidationOrchestrator Missing Curation Method — Consensus: 1/4

**Reviewers Said:** `ValidationOrchestrator.validate_all()` doesn't show curation validation.

**Decision:** Accept

**Reasoning:** B is correct. Curation level validation is a key feature. The interface should include `validate_curation()`.

**Action:** Add `validate_curation() -> None` to `ValidationOrchestrator` interface in Section 4.1.

---

### Issue: Config Fragmentation Not Resolved — Consensus: 1/4

**Reviewers Said:** Architecture doesn't clarify where validation constants live (Python or TOML).

**Decision:** Defer

**Reasoning:** B raises a valid point, but this is an implementation decision. The architecture correctly specifies `.ontos.toml` for user configuration. Validation constants (like valid status values, type hierarchy) are part of the schema and should remain in Python code (`core/types.py`). This is clear enough from context.

**Action:** None. Implementation will follow natural separation: user config in TOML, system constants in Python.

---

## 5. Completeness Gaps Response

| Gap | Consensus | Decision | Action |
|-----|-----------|----------|--------|
| `core/suggestions.py` missing | 4/4 | ✅ Will add | Add to Section 3.1 with interface spec |
| `core/tokens.py` missing | 4/4 | ✅ Will add | Add to Section 3.1 with interface spec |
| `io/files.py` interface not specified | 2/4 | ✅ Will add | Add public interface to Section 4.1 |
| `io/toml.py` interface not specified | 3/4 | ✅ Will add | Add public interface with write strategy |
| `ontos doctor` data flow missing | 3/4 | ✅ Will add | Add Section 5.4 |
| `ontos hook pre-push` data flow missing | 2/4 | ✅ Will add | Add Section 5.5 |
| `.ontos.toml` missing `required_version` | 4/4 | ✅ Will add | Add to Section 6.1 schema |
| Missing `user.name` config field | 1/4 | ⚠️ Defer | Valid but v3.1 scope |
| Missing scalability config knobs | 1/4 | ⚠️ Defer | Valid but v3.1 scope |
| `ContextMap` type not defined | 1/4 | ⚠️ Defer | Define during implementation |
| Graph summarization interface (Q8) | 1/4 | ⚠️ Defer | Implementation detail |
| `core/constants.py` not specified | 1/4 | ❌ Out of scope | Constants go in `core/types.py` |

### Gap: `core/suggestions.py` and `core/tokens.py`

**What I'll Add:**

```python
# core/suggestions.py — ~200 lines
def suggest_impacts(
    changed_files: List[Path],
    docs: Dict[str, DocumentData],
    git_log: List[CommitInfo]
) -> List[str]:
    """Suggest document IDs that may be impacted by changes."""

def suggest_concepts(
    title: str,
    event_type: str,
    existing_concepts: Set[str]
) -> List[str]:
    """Suggest concepts based on title and event type."""
```

```python
# core/tokens.py — ~50 lines
def estimate_tokens(content: str) -> int:
    """Estimate token count using word-based heuristic (~0.75 tokens/word)."""

def format_token_count(tokens: int) -> str:
    """Format token count for display (e.g., '~2,500 tokens')."""
```

---

### Gap: `io/toml.py` Interface

**What I'll Add:**

```python
# io/toml.py
def load_config(path: Path) -> Dict[str, Any]:
    """Load .ontos.toml file. Returns empty dict if not found."""

def write_config(path: Path, config: Dict[str, Any]) -> None:
    """Write config to .ontos.toml. Uses template to preserve comments."""

def merge_configs(base: Dict, override: Dict) -> Dict:
    """Deep merge two config dicts (override wins)."""
```

**Write Strategy:** Use a template-based approach to preserve comments and formatting. Don't use `toml.dumps()` directly as it strips comments.

---

### Gap: `io/files.py` Interface

**What I'll Add:**

```python
# io/files.py
def scan_documents(
    dirs: List[Path],
    skip_patterns: List[str]
) -> List[Path]:
    """Recursively find .md files, excluding skip patterns."""

def read_document(path: Path) -> Tuple[Dict, str]:
    """Read document, return (frontmatter, content)."""

def get_file_mtime(path: Path) -> Optional[datetime]:
    """Get file modification time (filesystem, not git)."""
```

---

## 6. Consistency Issues Response

| Inconsistency | Resolution |
|---------------|------------|
| "Core is pure" vs core contains transactional writes | **Clarify terminology.** "Core" means stdlib-only, deterministic, no external I/O. `SessionContext` manages write *intents* in core; actual writes happen via `commit()` which is I/O. Will reword Section 1.3. |
| Module specs reference missing modules | **Add missing modules.** `core/suggestions.py` and `core/tokens.py` will be added to Section 3.1. |
| Line counts don't add up (~500-750 unaccounted) | **Acknowledge gap.** Add note to Section 4.2: "Remaining ~500-750 lines will become glue code in `commands/log.py` or be deleted as duplicated logic." |
| `tomli` vs zero-dep claim | **Clarify conditional dependency.** Add note to Section 12.1: "`tomli` is a conditional dependency for Python <3.11 only. On 3.11+, stdlib `tomllib` is used. This maintains zero-dep for modern Python." |
| "molecule" vs "product" terminology | **Use "product".** The architecture uses "product" which is correct. "molecule" was legacy terminology from v1.x. No change needed. |
| Line count (1,625 vs 1,904) | **Correct to 1,904.** The exec summary referenced an outdated count. Will verify and correct in Appendix C. |

---

## 7. Risk Response

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Hidden coupling in God Script decomposition | High | High | **Accept risk with mitigation.** Add Phase 0 to migration: create Golden Master tests capturing current behavior before decomposition. |
| Purity refactoring underestimated | High | High | **Accept risk with mitigation.** Mark modules as REFACTOR, not EXISTS. Add explicit purification tasks to Phase 2. |
| Performance on large doc sets | Medium | Medium | **Accept risk with mitigation.** Add note to profile early. Implement O(V+E) cycle detection as specified. |
| Q4 confirmation unusable or meaningless | High | High | **Mitigate.** Design confirmation to be useful: show changed files, ask for log relevance, provide `--auto` bypass. |
| `@{push}` diff breaks on edge cases | Medium | Medium | **Accept risk.** Document edge cases (first push, no upstream, shallow clones). Provide fallback to `HEAD~10` comparison. |
| CLI startup time > 100ms | Low | Low | **Accept risk.** Profile if issues arise. Lazy imports can fix. |
| Output coupling blocks MCP | Medium | High | **Already mitigated.** `OutputHandler` pattern enables stream injection. v4 MCP work will extend this. |
| Hook breakage during migration | 100% | Medium | **Mitigate.** Add explicit hook replacement instructions to migration guide. `ontos init --force` will regenerate hooks. |

**Risks Accepted Without Mitigation:**
- CLI startup time: Low likelihood, easy to fix if needed.
- `@{push}` edge cases: Acceptable for v3.0; document and improve in v3.1.

---

## 8. Change Proposals Response

### Proposal: Add Missing Modules to Package Structure — From: A, B, C, D

**Problem Identified:** `core/suggestions.py` and `core/tokens.py` are referenced in decomposition tables but missing from package structure.

**Their Proposed Change:** Add module specs to Section 2.1/3.1.

**My Evaluation:**
- Agreement Level: Fully Agree
- Technical Soundness: Sound

**Decision:** Accept

**Implementation:**
- Add `core/suggestions.py` to Section 3.1 with ~200 line estimate and public interface
- Add `core/tokens.py` to Section 3.1 with ~50 line estimate and public interface
- Sections Affected: 3.1, 3.2 (Key Modules table)

---

### Proposal: Windows-Compatible Hooks — From: C, D

**Problem Identified:** `#!/bin/sh` shim fails on Windows.

**Their Proposed Change:**
- C: Python-based shim (`#!/usr/bin/env python3`)
- D: OS detection with `.cmd` wrapper

**My Evaluation:**
- Agreement Level: Fully Agree
- Technical Soundness: Both approaches sound; Python shim is simpler

**Decision:** Accept with C's approach

**Implementation:**
- Replace Section 8.1 shim with Python-based shim
- Single shim works on all platforms (requires Python in PATH, which Ontos needs anyway)
- Sections Affected: 8.1

---

### Proposal: Strict IO/Core Separation Plan — From: C, D

**Problem Identified:** Modules marked "EXISTS" in core contain I/O operations.

**Their Proposed Change:**
- Mark `staleness.py`, `proposals.py`, `history.py` as "REFACTOR"
- Create corresponding `io/` modules
- Core functions accept data objects, not fetch data

**My Evaluation:**
- Agreement Level: Fully Agree
- Technical Soundness: Sound

**Decision:** Accept

**Implementation:**
- Change module status from EXISTS to REFACTOR in Section 3.2
- Add purification note to each module
- Add `io/git.py` functions for git subprocess calls
- Sections Affected: 3.2, 4.1

---

### Proposal: Invert Config Loading Control — From: C

**Problem Identified:** `core/config.py` loading TOML creates layering violation.

**Their Proposed Change:**
1. Define `OntosConfig` dataclass in `core/types.py`
2. `cli.py` calls `io/toml.py:load_config()`
3. `cli.py` injects config into commands/core

**My Evaluation:**
- Agreement Level: Fully Agree
- Technical Soundness: Sound (standard IoC pattern)

**Decision:** Accept

**Implementation:**
- Add Section 6.4: "Config Loading Pattern"
- Clarify `core/config.py` only provides defaults, not loading
- Sections Affected: 6.2 (new subsection), 3.2 (config.py description)

---

### Proposal: Golden Master Testing Before Decomposition — From: D (A similar)

**Problem Identified:** High regression risk when splitting God Scripts.

**Their Proposed Change:** Add Phase 0 to migration: create integration tests capturing v2 behavior.

**My Evaluation:**
- Agreement Level: Fully Agree
- Technical Soundness: Sound (standard characterization testing)

**Decision:** Accept

**Implementation:**
- Add "Phase 0: Golden Master Testing" to Section 13.2
- Tests capture: stdout, file artifacts, exit codes
- v3 commands must produce identical output
- Sections Affected: 13.2

---

### Proposal: De-scope v3.0 CLI Surface — From: A

**Problem Identified:** Many commands in CLI surface increase QA burden.

**Their Proposed Change:** Limit v3.0 to `init`, `map`, `log`, `doctor`, `hook`, `--json`. Move others to v3.1+.

**My Evaluation:**
- Agreement Level: Disagree
- Technical Soundness: Sound reasoning, but I disagree with the conclusion

**Decision:** Reject

**Reasoning:** The commands in the CLI surface (`verify`, `query`, `migrate`, `consolidate`, `promote`, `scaffold`, `stub`) already exist in v2.x as separate scripts. v3.0 is reorganizing them into a unified CLI, not creating new functionality. De-scoping would mean keeping parallel entry points (`ontos verify` and `ontos_verify.py`), which is worse. The commands are thin wrappers around existing core logic.

**Alternative:** None needed. Current scope is appropriate.

---

### Proposal: Explicit Validator Modules — From: A

**Problem Identified:** ValidationOrchestrator could become a dumping ground.

**Their Proposed Change:** Split into `validators/frontmatter.py`, `validators/schema.py`, etc.

**My Evaluation:**
- Agreement Level: Partially Agree
- Technical Soundness: Sound for large systems

**Decision:** Defer

**Reasoning:** The concern is valid, but premature. The validation logic is ~3,850 lines across 8 modules currently. `ValidationOrchestrator` is meant to *orchestrate* existing validators, not contain all logic. If it grows unwieldy during implementation, we can extract. Adding a `validators/` directory now adds complexity without proven benefit.

**What Would Change My Mind:** If `validation.py` exceeds 500 lines during implementation.

---

### Proposal: Add `ontos check` Command — From: A

**Problem Identified:** Q4 confirmation mechanism unclear.

**Their Proposed Change:** Add `ontos check` command with `--confirm` flag that writes a stamp artifact.

**My Evaluation:**
- Agreement Level: Partially Agree
- Technical Soundness: Adds complexity

**Decision:** Accept with Modifications

**What I'm Taking:** The confirmation mechanism concept.

**What I'm Changing:** Instead of a new `ontos check` command, I'll add confirmation to `ontos log` flow directly. The `--auto` flag bypasses confirmation (for CI). No stamp artifact needed — the log file itself is the artifact.

**Why:** Simpler. One command does detection + confirmation + logging. Separate `check` command is over-engineering for current needs.

---

## 9. Split Opinions Resolution

| Topic | Position 1 | Position 2 | My Resolution |
|-------|------------|------------|---------------|
| Core purity severity | C, D: Critical (architectural rot) | A, B: Not flagged | **Position 1.** The architecture claims "Functional Core" as a principle. Violating it immediately creates technical debt. Mark as Critical. |
| Windows support urgency | C, D: Critical for v3.0 | A, B: Not flagged | **Position 1.** A hook that fails to parse isn't "best-effort" — it's broken. Fix in v3.0. |
| Config loading pattern | C: IoC required | A, B, D: Not addressed | **Position C.** The IoC pattern is correct. Will document explicitly. |

---

## 10. Unique Insights Response

| Insight | From | Response |
|---------|------|----------|
| CWD vs Git Root resolution | C | ✅ Great catch. CLI must detect repo root from any subdirectory. Will add note to Section 2.6 design constraints. |
| `input()` in core blocks MCP | C | ✅ Great catch. Will add to Section 12.3 behavioral constraints: "Core modules MUST NOT call `input()`. User interaction is UI layer responsibility." |
| Output stream injection for MCP | D | ✅ Valuable. `OutputHandler` already supports this pattern. Will add note to v4.0 extension points (Section 11). |
| `user.name` config field | D | ⚠️ Valid but deferring. Session attribution is important but v3.1 scope. |
| Async variants for MCP readiness | B | ⚠️ Interesting but premature. v3.0 is synchronous. Async is v4 concern. |
| `ContextMap` JSON type definition | A | ⚠️ Valid. Will define during implementation. Adding placeholder note. |

---

## 11. Architecture Change Log

### Critical Fixes (Before Any Implementation)

- [ ] **Add `core/suggestions.py` spec** — Section 3.1
  - What: Add module with `suggest_impacts()`, `suggest_concepts()` interface
  - Why: Referenced in decomposition but missing from structure
  - From: A, B, C, D (unanimous)

- [ ] **Add `core/tokens.py` spec** — Section 3.1
  - What: Add module with `estimate_tokens()`, `format_token_count()` interface
  - Why: Referenced in decomposition but missing from structure
  - From: A, B, C, D (unanimous)

- [ ] **Add Q5 version pinning** — Section 6.1
  - What: Add `required_version` field to `.ontos.toml` schema; add version checking description
  - Why: Strategy decision Q5 not implemented
  - From: A, B, C, D (unanimous)

- [ ] **Add Q4 confirmation step** — Section 5.3
  - What: Add user confirmation to `ontos log` data flow; add `--auto` flag for CI bypass
  - Why: Strategy decision Q4 "require confirmation" not in architecture
  - From: A, B, D

- [ ] **Fix Windows hook incompatibility** — Section 8.1
  - What: Replace `#!/bin/sh` shim with Python-based shim
  - Why: Shell shim fails on Windows
  - From: C, D

- [ ] **Mark impure modules as REFACTOR** — Section 3.2
  - What: Change `staleness.py`, `proposals.py`, `history.py` status from EXISTS to REFACTOR
  - Why: These modules contain I/O that violates core purity
  - From: C, D

### Major Changes (Should Complete Before Implementation)

- [ ] **Add `io/toml.py` interface spec** — Section 4.1
  - What: Define `load_config()`, `write_config()`, `merge_configs()` with write strategy note
  - Why: Config loading flow depends on this
  - From: A, B, C

- [ ] **Add `io/files.py` interface spec** — Section 4.1
  - What: Define `scan_documents()`, `read_document()`, `get_file_mtime()`
  - Why: File operations interface not specified
  - From: A, B

- [ ] **Add `ontos doctor` data flow** — New Section 5.4
  - What: Add data flow diagram showing check sequence
  - Why: Key v3.0 feature needs specification
  - From: A, B, C

- [ ] **Add `ontos hook pre-push` data flow** — New Section 5.5
  - What: Add data flow diagram for hook dispatch
  - Why: Critical path for git integration
  - From: A, B

- [ ] **Clarify "Functional Core" principle** — Section 1.3
  - What: Reword to "stdlib-only, deterministic, no external I/O"; clarify SessionContext.commit() is I/O layer
  - Why: Current wording creates confusion about transactional writes
  - From: A, C, D

- [ ] **Acknowledge line count gap** — Section 4.2
  - What: Add note: "Remaining ~500-750 lines will become glue code or be deleted"
  - Why: Decomposition arithmetic doesn't add up
  - From: A, B, C, D (unanimous)

- [ ] **Add Golden Master testing phase** — Section 13.2
  - What: Add "Phase 0" before Phase 1: create characterization tests
  - Why: High regression risk in God Script decomposition
  - From: D, A

- [ ] **Add config IoC pattern** — Section 6.2
  - What: Add "Config Loading Pattern" explaining cli.py loads, injects into commands/core
  - Why: Config flow unclear; potential layering violation
  - From: C

- [ ] **Add `validate_curation()` to ValidationOrchestrator** — Section 4.1
  - What: Add method to interface
  - Why: Curation validation missing from orchestrator spec
  - From: B

### Minor Updates (Can Do During Implementation)

- [ ] **Clarify `tomli` dependency** — Section 12.1
  - What: Add note: "Conditional for Python <3.11 only"
  - Why: Apparent conflict with zero-dep claim

- [ ] **Add repo root detection constraint** — Section 2.6
  - What: Add: "CLI must detect repo root from any subdirectory"
  - Why: CWD vs git root is real usability issue
  - From: C

- [ ] **Add input() ban to constraints** — Section 12.3
  - What: Add: "Core modules MUST NOT call `input()`"
  - Why: Blocks MCP and headless operation
  - From: C

- [ ] **Add O(V+E) implementation note** — Section 4.1 (graph.py)
  - What: Add note about proper DFS implementation
  - Why: Existing code is O(N²)
  - From: D

- [ ] **Correct line count in Appendix C** — Appendix C
  - What: Verify and correct 1,625 to 1,904 if needed
  - Why: Inconsistency flagged

### Additions (New Content)

- [ ] **Section 5.4: `ontos doctor` data flow** — New
  - What: Complete data flow diagram

- [ ] **Section 5.5: `ontos hook` data flow** — New
  - What: Hook dispatch data flow

- [ ] **Section 6.4: Config Loading Pattern** — New
  - What: IoC pattern documentation

### Deferred (Valid But Not Now)

- [ ] `ContextMap` type definition — Reason: Define during implementation; not blocking
- [ ] Graph summarization interface — Reason: Q8 implementation detail
- [ ] Scalability config knobs — Reason: v3.1 feature
- [ ] `user.name` config field — Reason: v3.1 feature
- [ ] Explicit `validators/` directory — Reason: Premature; reassess if validation.py > 500 lines
- [ ] Async variants — Reason: v4.0 concern

### Rejected Proposals (With Reasoning)

| Proposal | From | Rejection Reasoning |
|----------|------|---------------------|
| De-scope v3.0 CLI surface | A | Commands already exist as v2.x scripts. Reorganizing them is v3.0's job. Keeping parallel entry points is worse. |
| Explicit `validators/` directory | A | Premature optimization. ValidationOrchestrator orchestrates, doesn't contain all logic. Reassess if issues arise during implementation. |
| Separate `ontos check` command | A | Over-engineering. Confirmation integrated into `ontos log` with `--auto` flag is simpler. |

---

## 12. Architecture Confidence Assessment

**Before Review:** 7/10 — Confident in overall structure but aware of potential gaps

**After Review:** 8/10 — Increased confidence

**What Increased Confidence:**
- All reviewers validated the fundamental architecture (layering, ValidationOrchestrator, God Script decomposition)
- 10+ of 13 strategy decisions correctly implemented
- No reviewer suggested alternative architectures
- Issues are completeness gaps, not design flaws

**What Decreased Confidence:**
- The "EXISTS" vs "REFACTOR" oversight is embarrassing. I should have audited modules for I/O before marking them.
- Windows hook failure is a real gap I didn't think through.

**Remaining Uncertainties:**
- Whether ~500-750 unaccounted lines will reveal hidden coupling
- Whether Q4 confirmation UX will be useful or annoying
- Whether performance targets will hold on 100+ doc sets

---

## 13. Final Reflection

**Most Valuable Feedback:** C's Inversion of Control critique. It forced me to think through config flow explicitly, which will prevent a real layering violation.

**Biggest Blind Spot Discovered:** Marking I/O-containing modules as "EXISTS" (reuse as-is). I knew these modules needed some work, but I didn't explicitly audit them for I/O violations. The reviewers did.

**Disagreements I'm Confident About:**
- Rejecting CLI scope reduction. The commands exist; reorganizing them is the job.
- Deferring `validators/` directory. Adding structure without proven need is premature.

**Disagreements I'm Less Certain About:**
- Deferring `ContextMap` type definition. A's point about JSON contract clarity is valid. I'm betting we can define it during implementation, but it might cause rework.

**Process Improvement:** For future architecture reviews, I should:
1. Audit all "EXISTS" modules for principle violations before review
2. Test architectural claims on Windows/Linux/macOS explicitly
3. Provide line-by-line decomposition accounting, not just ranges

---

## 14. Next Steps

### 1. Immediate (before sharing updated architecture)

- [ ] Create v1.2 architecture document with all Critical Fixes applied
- [ ] Verify line counts in Appendix C
- [ ] Run spell-check on updated document

### 2. Before Implementation Begins

- [ ] Apply all Major Changes
- [ ] Create Phase 0 Golden Master test fixtures
- [ ] Review updated architecture with founder

### 3. Implementation Watch Items

- [ ] Monitor `validation.py` size — extract to `validators/` if > 500 lines
- [ ] Profile cycle detection early — ensure O(V+E) complexity
- [ ] Test hooks on Windows during Phase 4

### 4. Follow-up Reviews Needed

- [ ] After Phase 2 (decomposition): Review actual module boundaries
- [ ] After Phase 4 (CLI): Review user-facing command UX

---

*End of Chief Architect Response*

*Response generated by Claude Opus 4.5 — 2026-01-12*
*Reviews addressed: Codex (A), Claude (B), Gemini Architectural (C), Gemini DeepThink (D)*
