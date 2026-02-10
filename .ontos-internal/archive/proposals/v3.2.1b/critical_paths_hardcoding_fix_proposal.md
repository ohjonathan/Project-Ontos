---
id: v3_2_1_critical_paths_hardcoding_fix
type: strategy
status: draft
depends_on: [v3_2_1_activation_resilience_proposal, v3_2_1_tiered_context_map_exploration]
concepts: [context-map, activation, contributor-mode, user-mode, hardcoding, path-leakage]
---

# v3.2.1: Critical Paths Hardcoding Fix

**Author:** Antigravity  
**Date:** 2026-02-01  
**Status:** Draft  
**Severity:** High (affects all consumer projects)

---

## 1. Problem Statement

### Observed Failure

When activating Ontos in `finance-engine-2.0` (a consumer project), the AI agent attempted to explore directories that do not exist:

```
Error while analyzing directory
Cannot list directory
logs
which does not exist.
Error while analyzing directory
Cannot list directory
.ontos-internal
which does not exist.
```

The Ontos CLI itself ran correctly and only scanned the 177 documents in `docs/` as specified in `.ontos.toml`. However, the **agent's post-CLI exploration** attempted to access `.ontos-internal` and a root-level `logs/` directory.

### Root Cause Analysis

The root cause is in `ontos/commands/map.py`, lines 203-208:

```python
# Critical Paths
cp_lines = ["### Critical Paths"]
cp_lines.append("- **Entry:** `docs/reference/Ontos_Manual.md`")
cp_lines.append("- **Strategy:** `.ontos-internal/strategy/`")
cp_lines.append("- **Logs:** `.ontos-internal/logs/`")
```

These paths are **hardcoded to Project-Ontos's internal structure** and are output to the "Critical Paths" section of every `Ontos_Context_Map.md` regardless of whether:

1. The project is Project-Ontos (contributor mode) or a consumer project (user mode)
2. The paths actually exist in the target project
3. The project's `.ontos.toml` specifies different paths

### Impact

| Impact Area | Severity | Description |
|-------------|----------|-------------|
| **Agent Confusion** | High | Agents read the context map and attempt to explore non-existent paths, wasting time and tokens |
| **Error Noise** | Medium | Error messages ("Cannot list directory") reduce signal-to-noise ratio during activation |
| **Latency** | Medium | Failed directory listings add ~2-5 seconds to activation in consumer projects |
| **Trust Erosion** | Low | Users may perceive Ontos as buggy when they see errors during what should be a clean activation |

### Evidence

1. **Diagnostic Report**: `/Users/jonathanoh/Dev/finance-engine-2.0/docs/strategy/Ontos_Activation_Diagnostic_Report.md`
2. **CLI Output Analysis**: The Ontos CLI correctly used `logs_dir = "docs/logs"` from `.ontos.toml`, but the context map still contained `.ontos-internal/logs/`
3. **finance-engine-2.0 config**: `.ontos.toml` specifies `logs_dir = "docs/logs"`, but context map ignores this

---

## 2. Design Goals

1. **Config-Driven Paths** — Critical Paths should reflect the actual `.ontos.toml` configuration
2. **Mode-Aware Output** — Only show `.ontos-internal` paths when running in contributor mode
3. **Graceful Degradation** — If a path doesn't exist, either omit it or mark it as optional
4. **Zero Breaking Changes** — Existing workflows must continue to work

---

## 3. Proposed Changes

### 3.1 Pass Config to `_generate_tier1_summary()`

**Current signature:**
```python
def _generate_tier1_summary(
    docs: Dict[str, DocumentData],
    config: Dict[str, Any],
    options: GenerateMapOptions = None
) -> str:
```

The `config` dict is already passed but not fully utilized for path generation.

### 3.2 Dynamic Critical Paths Generation

**Replace lines 203-208 with:**

```python
# Critical Paths - derive from config
cp_lines = ["### Critical Paths"]

# Entry point - check if manual exists, otherwise use docs_dir
docs_dir = config.get("docs_dir", "docs")
manual_path = f"{docs_dir}/reference/Ontos_Manual.md"
cp_lines.append(f"- **Entry:** `{docs_dir}/` (doc root)")

# Logs - use config
logs_dir = config.get("logs_dir", f"{docs_dir}/logs")
cp_lines.append(f"- **Logs:** `{logs_dir}/`")

# Strategy - only if .ontos-internal exists (contributor mode)
if config.get("is_contributor_mode", False):
    cp_lines.append("- **Strategy:** `.ontos-internal/strategy/`")
```

### 3.3 Add `is_contributor_mode` to Config

**In `ontos/io/config.py` or `map_command()`:**

```python
# Detect contributor mode by checking for .ontos-internal
is_contributor_mode = (project_root / ".ontos-internal").exists()
gen_config["is_contributor_mode"] = is_contributor_mode
```

### 3.4 Update `gen_config` Construction in `map_command()`

**Current (line 629-633):**
```python
gen_config = {
    "project_name": project_root.name,
    "version": config.ontos.version,
    "allowed_orphan_types": config.validation.allowed_orphan_types,
}
```

**Proposed:**
```python
gen_config = {
    "project_name": project_root.name,
    "version": config.ontos.version,
    "allowed_orphan_types": config.validation.allowed_orphan_types,
    "docs_dir": config.paths.docs_dir,
    "logs_dir": config.paths.logs_dir,
    "is_contributor_mode": (project_root / ".ontos-internal").exists(),
}
```

---

## 4. Implementation Spec

### Files to Modify

| File | Change |
|------|--------|
| `ontos/commands/map.py` | 1. Update `gen_config` to include path info and mode detection<br>2. Update `_generate_tier1_summary()` to use dynamic paths |
| `tests/commands/test_map.py` | Add tests for dynamic Critical Paths generation |

### Detailed Code Changes

**`map.py` - Update `map_command()` (around line 629):**

```python
# Build config dict for generation
is_contributor_mode = (project_root / ".ontos-internal").exists()

gen_config = {
    "project_name": project_root.name,
    "version": config.ontos.version,
    "allowed_orphan_types": config.validation.allowed_orphan_types,
    "docs_dir": str(config.paths.docs_dir),
    "logs_dir": str(config.paths.logs_dir),
    "is_contributor_mode": is_contributor_mode,
}
```

**`map.py` - Update `_generate_tier1_summary()` (lines 203-208):**

```python
# Critical Paths - derive from config, not hardcoded
cp_lines = ["### Critical Paths"]
docs_dir = config.get("docs_dir", "docs")
logs_dir = config.get("logs_dir", f"{docs_dir}/logs")

cp_lines.append(f"- **Docs Root:** `{docs_dir}/`")
cp_lines.append(f"- **Logs:** `{logs_dir}/`")

# Only show .ontos-internal paths in contributor mode
if config.get("is_contributor_mode", False):
    cp_lines.append("- **Strategy:** `.ontos-internal/strategy/`")
    cp_lines.append("- **Reference:** `.ontos-internal/reference/`")
```

---

## 5. Verification Plan

### Automated Tests

1. **Test: User mode context map does NOT contain `.ontos-internal`**
   - Create a temp project without `.ontos-internal`
   - Run `ontos map`
   - Assert context map does not contain `.ontos-internal`

2. **Test: Contributor mode context map DOES contain `.ontos-internal`**
   - Create a temp project with `.ontos-internal` directory
   - Run `ontos map`
   - Assert context map contains `.ontos-internal/strategy/`

3. **Test: Critical Paths reflect `.ontos.toml` config**
   - Create project with `logs_dir = "custom/logs"`
   - Run `ontos map`
   - Assert context map contains `custom/logs/`

### Manual Verification

1. In `finance-engine-2.0`, run `ontos map --sync-agents`
2. Verify `Ontos_Context_Map.md` shows `docs/logs/` not `.ontos-internal/logs/`
3. Run full activation and confirm no "Cannot list directory" errors

---

## 6. Alternatives Considered

| Alternative | Rejected Because |
|-------------|------------------|
| Remove Critical Paths section entirely | Valuable for agent orientation; should fix, not remove |
| Add `.ontos-internal` to skip patterns | Doesn't fix the context map output; just hides the symptom |
| Document the issue in AGENTS.md | Workaround, not a root cause fix |
| Update Knowledge Items to warn about this | Helps Antigravity but not other agents |

---

## 7. Regression Risks

| Risk | Mitigation |
|------|------------|
| Contributor mode detection fails | Use defensive check: `(project_root / ".ontos-internal").exists()` is safe |
| Config paths could be `None` | Use `.get()` with defaults |
| Existing tests may hardcode expected paths | Update test fixtures to match new behavior |

---

## 8. Open Questions

1. **Should Critical Paths validate path existence?** Currently, paths are listed even if they don't exist. Should we add existence checks and omit missing paths?

2. **Should we add a "mode" indicator to the context map header?** E.g., `> Mode: Contributor` or `> Mode: User`. This would help agents understand the project type at a glance.

3. **Should AGENTS.md also surface the mode?** Adding a "Project Mode: User/Contributor" field to the synced stats could prevent cross-context contamination.

---

## 9. Decision Requested

Approve this proposal to proceed with implementation. Estimated effort: **2-3 hours** including tests.

---

## Appendix A: Full Trace of Issue

```
Session: finance-engine-2.0 (consumer project)
Timestamp: 2026-02-01

1. User runs: "Activate Ontos"
2. CLI executes correctly:
   - ontos map --sync-agents → 177 docs, paths from .ontos.toml ✓
   - ontos doctor → 8 passed, 0 failed ✓
   - ontos agents --force → AGENTS.md synced ✓

3. Agent reads Ontos_Context_Map.md
4. Agent sees "Critical Paths" section:
   - Strategy: .ontos-internal/strategy/ ← WRONG
   - Logs: .ontos-internal/logs/ ← WRONG

5. Agent attempts to list .ontos-internal → Error (doesn't exist)
6. Agent attempts to list logs → Error (should be docs/logs)

Root Cause: Hardcoded paths in map.py lines 206-207
```

---

## Appendix B: Related Work

- **v3.2.1 Activation Resilience Proposal**: Addresses trigger phrases and compaction recovery, but not path hardcoding
- **v3.2.1 Tiered Context Map Exploration**: Establishes the 3-tier architecture, but Critical Paths content was not scrutinized
- **finance-engine-2.0 Diagnostic Report**: Initial problem report that led to this proposal
