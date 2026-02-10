---
id: v3_2_backlog
type: strategy
status: active
depends_on: [v3_1_0_track_b_final_approval_chief_architect]
concepts: [backlog, v3.2, planning, deferred-items]
---

# Ontos v3.2 Backlog

**Created:** 2026-01-22
**Source:** Deferred items from v3.1.0 Track B review and v3.2.2 maintain review
**Updated:** 2026-02-10

---

## Deferred from v3.1.0

These items were identified during Track B code review but deferred as non-blocking.

| ID | Issue | Priority | Source | Description |
|----|-------|----------|--------|-------------|
| X-H2 | `consolidate --count 0` | P2 | Codex D.2b | `--count 0` should either error or have defined semantics (keep all/none) |
| X-M1 | stub validation | P2 | Codex D.2b | `stub` accepts invalid type/id combinations silently |
| X-M2 | scaffold error messaging | P2 | Codex D.2b | `scaffold` silent on permission denied, invalid paths |
| X-M3 | migrate schema handling | P2 | Codex D.2b | `migrate` ignores unsupported schema versions |
| X-M4 | query cycle detection | P2 | Codex D.2b | `query --health` doesn't detect/report dependency cycles |

---

## Item Details

### X-H2: `consolidate --count 0` Semantics

**Current behavior:** Returns success with no logs processed (unclear intent)

**Expected:** Either:
- Error: "count must be >= 1"
- Defined: `--count 0` means "archive all logs"

**Files:** `ontos/commands/consolidate.py`

---

### X-M1: stub Type/ID Validation

**Current behavior:** Accepts any string for `--type` and `--id`

**Expected:**
- Validate `--type` against known types (kernel, strategy, product, atom, log)
- Validate `--id` format (no spaces, valid characters)

**Files:** `ontos/commands/stub.py`

---

### X-M2: scaffold Error Messaging

**Current behavior:** Silent success on permission denied or invalid paths

**Expected:**
- Clear error message on permission denied
- Warning on non-existent paths
- Error on invalid file types

**Files:** `ontos/commands/scaffold.py`

---

### X-M3: migrate Unsupported Schema Handling

**Current behavior:** Ignores files with unknown schema versions

**Expected:**
- Warn about unsupported schema versions
- Option to force migration with `--force`

**Files:** `ontos/commands/migrate.py`

---

### X-M4: query --health Cycle Detection

**Current behavior:** Reports orphans and connectivity but not cycles

**Expected:**
- Detect dependency cycles in the document graph
- Report cycles in health output with involved documents

**Files:** `ontos/commands/query.py`, `ontos/core/graph.py`

---

## Deferred from v3.2.2 Maintain Review

These items were explicitly deferred during the v3.2.2 `ontos maintain` cross-check because they are non-blocking or policy/process decisions.

| ID | Issue | Priority | Source | Description |
|----|-------|----------|--------|-------------|
| X-M5 | unknown `--skip` behavior | P2 | v3.2.2 maintain review | `ontos maintain --skip unknown_task` warns and exits success; decide whether unknown names should be hard errors. |
| X-M6 | proposal lifecycle status (resolved) | P3 | v3.2.2 maintain review | Resolved on 2026-02-10: `v3_2_2_maintain_command_proposal` marked `status: complete`. |
| X-M7 | command import layering cleanup | P3 | v3.2.2 maintain review | Re-evaluate command-to-command imports in `maintain.py` and potential extraction of shared orchestration utilities. |
| X-M8 | `_parse_bool` empty-string semantics | P3 | v3.2.2 maintain review | Define whether empty/unknown values should default silently or produce explicit warnings/errors. |
| X-M9 | `TaskResult.status` type strictness | P3 | v3.2.2 maintain review | Tighten `TaskResult.status` from free-form `str` to constrained literal/enum for stronger static checks. |

---

## New Features (v3.2.2 Planned)

| ID | Feature | Priority | Mode | Description |
|----|---------|----------|------|-------------|
| F-M1 | `ontos retrofit` | P1 | Maintenance | Library-wide update for Obsidian sync, lint-fixing, and standardization. |
| F-M2 | `ontos rename` | P1 | Integrity | Atomic renaming of docs including all graph references (depends_on). |
| F-M3 | `ontos link-check` | P2 | Diagnostics | Find broken depends_on and markdown/wikilink references. |
| F-M4 | `doctor --repair` | P2 | UX | Interactive fix for project setup issues identified by doctor. |

---

---

## Notes

- Deferred items are P2-P3 and non-blocking
- None are blocking for normal operation
- **v3.2.2 Planning**: See `.ontos-internal/strategy/proposals/v3.2.2/maintain_command_review.md` for review context.

---

*v3.2 Backlog — Created 2026-01-22*
