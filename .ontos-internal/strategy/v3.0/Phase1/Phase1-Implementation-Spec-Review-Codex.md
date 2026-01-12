# Phase 1 Implementation Spec Review - Codex

**Reviewer:** Codex (Adversarial)  
**Date:** 2026-01-12  
**Spec Version:** 1.0

---

## 1. Alignment Verification

### 1.1 Roadmap Alignment

| Roadmap Requirement (Section 3) | Spec Addresses? | Correctly? | Notes |
|--------------------------------|-----------------|------------|-------|
| `pyproject.toml` with metadata | Yes | Yes | Defined in Section 4.1. |
| Package root `ontos/__init__.py` | Yes | Yes | Defined in Section 4.2. |
| Entry point `ontos/__main__.py` | Yes | Yes | Defined in Section 4.3. |
| Move `core/` modules | Yes | Mostly | "Copy" vs "move" ambiguity; old path retention not specified. |
| Move `ui/` modules | Yes | Mostly | Same "copy vs move" ambiguity. |
| `pip install -e .` works | Yes | Yes | Exit criteria and verification steps. |
| 303 tests pass | Yes | Partially | Roadmap places this in Phase 2; spec adds Phase 1 requirement (scope creep). |
| Golden Master tests pass | Yes | Partially | Spec calls `--fixture all` but checklist later says small/medium only. |

### 1.2 Architecture Alignment

| Architecture Constraint | Spec Compliant? | Evidence |
|------------------------|-----------------|----------|
| Zero-dep core (stdlib only) | No | Architecture Section 3.2 says core is stdlib-only; spec keeps PyYAML-dependent core. |
| Layered architecture respected | No | Spec keeps `core/config.py` with git operations and other I/O. |
| Core cannot import from commands/ui/io | Unclear/No | Spec does not enforce; core list includes modules requiring I/O extraction per architecture. |
| Package structure matches Section 3 | No | Architecture Section 3.1 includes `commands/`, `io/`, `mcp/`, `version.py`; spec omits these. |

### 1.3 Strategy Alignment

| Relevant Strategy Decision | Spec Implements? | Notes |
|---------------------------|------------------|-------|
| Q11: Modular structure (core/, commands/, ui/, mcp/) | Partially | Only core/ui moved; no commands/mcp placeholders or plan. |
| Q12: Python (not Node) | Yes | Entire stack remains Python. |
| Q13: Markdown primary | Yes | No changes; no conflict. |

### 1.4 Alignment Verdict

**Overall Alignment:** Adequate -> Weak  
**Deviations Found:**
- Spec references Roadmap v1.3; approved doc is v1.2 (version mismatch).
- Architecture requires stdlib-only core; spec keeps PyYAML-dependent core without acknowledging deferral.
- Architecture package layout includes `commands/`, `io/`, `mcp/`, `version.py`; spec omits them.

---

## 2. Spec Quality

### 2.1 Completeness

| Aspect | Complete? | Gaps |
|--------|-----------|------|
| All files specified | No | Missing `version.py`, `commands/`, `io/`, `mcp/` placeholders. |
| All tasks listed | No | No task to reconcile Roadmap v1.2 vs v1.3; no task to update workflow file name. |
| All tests defined | Yes | Golden Master fixture scope inconsistent (all vs small/medium). |
| All risks identified | No | Missing: CLI fails outside repo root; PyPI name unresolved; tomllib usage on 3.9. |
| Verification steps clear | Partially | Uses `tomllib` for syntax check (fails on 3.9). |

### 2.2 Implementability

- [x] File paths are specific
- [x] Code is complete (not pseudocode)
- [ ] Order of operations is clear
- [ ] Dependencies between tasks are explicit
- [x] Success criteria are testable
- Ambiguities:
  - "Move" vs "copy" for `.ontos/scripts/ontos` -> risk of duplicate code drifting.
  - CLI assumes `ontos.py` exists at repo root; no project root discovery.
  - `pyproject` verification uses `tomllib`, which doesn’t exist on Python 3.9.
  - CI update references `.github/workflows/tests.yml`, but repo uses `ci.yml`.

### 2.3 Technical Correctness

| Technical Aspect | Correct? | Issues |
|------------------|----------|--------|
| `pyproject.toml` syntax | Yes | Looks valid. |
| Entry point configuration | Mostly | CLI delegates to repo `ontos.py`, which won’t exist for PyPI installs. |
| Import statements | Risky | Removing sys.path injection assumes editable install always. |
| Python version compatibility | No | `tomllib` in verification step fails for 3.9/3.10. |
| Package discovery | Mostly | `include = ["ontos", "ontos.*"]` OK; missing `version.py` and placeholders vs architecture. |

---

## 3. Adversarial Analysis

### 3.1 Assumptions to Challenge

| Assumption in Spec | Why It Might Be Wrong | Impact If Wrong |
|--------------------|----------------------|-----------------|
| CLI can delegate to root `ontos.py` | In PyPI install, repo file doesn’t exist | `ontos` command fails outside repo root. |
| CWD is repo root | Many users run from subdirs | `get_scripts_dir()` fails; CLI exits. |
| `tomllib` is available | Python 3.9 lacks it | Verification step fails for target min version. |
| PyPI package name is `ontos` | Decision still open in roadmap | Install docs may be wrong. |
| Core can remain PyYAML-dependent | Architecture mandates stdlib-only core | Architecture non-compliance for v3.0. |

### 3.2 Failure Modes

| What Could Fail | How | Detection | Recovery |
|-----------------|-----|-----------|----------|
| `ontos` command fails in user projects | No `ontos.py` in repo root | Immediate runtime error | Rewrite CLI to call package code or search root. |
| Tests fail after import cleanup | `sys.path` removals without editable install | CI/local fail | Enforce install step or keep shim in tests. |
| Verification step crashes on 3.9 | `tomllib` import | Immediate | Use `tomli` fallback. |
| Golden Master mismatch | `--fixture all` assumes large fixture exists | Test fails | Align fixtures or use small/medium only. |

### 3.3 Edge Cases Not Addressed

| Edge Case | Why It Matters | Recommendation |
|----------|----------------|----------------|
| Running CLI from subdirectory | Common workflow | Add repo root discovery (walk up to `.ontos/`). |
| PyPI install in non-repo context | Global CLI goal | CLI should fail gracefully with clear guidance. |
| Duplicate `ontos` package in `.ontos/scripts/ontos` | Drift risk | Decide: delete old copy or keep shim with explicit guidance. |
| Windows paths | Best-effort support in architecture | Add note or test for path handling in CLI. |

### 3.4 What's the Architect Not Seeing?

- The global CLI story is broken: current `ontos.cli` depends on repo `ontos.py`.
- Core purity violation: spec claims "no I/O" but keeps git operations and YAML parsing in core.
- Version governance mismatch: spec uses Roadmap v1.3 while review requires v1.2.
- Workflow file name mismatch: spec updates `tests.yml`, but CI uses `ci.yml`.

---

## 4. Critical Assessment

### 4.1 Strongest Concerns

1. CLI delegation to repo `ontos.py` breaks the "global CLI + local data" promise.
2. Architecture non-compliance: core is not stdlib-only and still performs I/O.
3. Spec references unapproved roadmap version (v1.3 vs v1.2).

### 4.2 What Would You Do Differently?

| Spec's Approach | Alternative Approach | Why Alternative Might Be Better |
|----------------|----------------------|---------------------------------|
| CLI delegates to repo `ontos.py` | CLI calls package logic directly or shells to `.ontos/scripts/` after repo root discovery | Aligns with global CLI goal and avoids missing `ontos.py`. |
| Omit commands/io/mcp stubs | Add empty package stubs (`commands/`, `io/`, `mcp/`, `version.py`) | Keeps structure aligned with architecture without behavior changes. |
| Verify `pyproject` with `tomllib` | Use `tomli` fallback for 3.9/3.10 | Matches min Python version support. |

### 4.3 Uncomfortable Questions

1. If `ontos` is installed from PyPI and no repo `ontos.py` exists, how does `ontos map` work?
2. Are we accidentally locking in a layout where the CLI cannot find repo root unless the user is in that directory?
3. Why are we citing Roadmap v1.3 in a spec that must align to v1.2?

### 4.4 Scope Assessment

| Item in Spec | Actually Phase 1? | If No, When? |
|--------------|-------------------|--------------|
| CI workflow overhaul | No | Phase 1 or Phase 4? Unclear; roadmap doesn’t require it. |
| "All 303 tests pass" | No (roadmap puts in Phase 2) | Phase 2 |
| `ontos` CLI help output | Marginal | Phase 4 (full CLI) |

**Scope creep detected:** Yes  
**Items that should be removed:** CI `tests.yml` rewrite (rename to actual CI file or defer).  
**Items missing that should be added:** Placeholder packages per architecture (`commands/`, `io/`, `mcp/`, `version.py`) or explicit deferral note.

---

## 5. Summary

### 5.1 Verdict

| Aspect | Rating |
|--------|--------|
| Alignment with approved docs | Weak |
| Spec completeness | Adequate |
| Technical correctness | Adequate |
| Implementability | Adequate |
| Risk coverage | Weak |

**Overall Recommendation:** Request Revision

### 5.2 Blocking Issues

1. CLI delegation relies on repo `ontos.py`, breaking `pip install ontos` and global CLI promise.
2. Architecture mismatch: stdlib-only core not addressed or deferred.
3. Roadmap version mismatch (v1.3 vs required v1.2).

### 5.3 Major Issues

1. Missing `commands/`, `io/`, `mcp/`, `version.py` placeholders from architecture.
2. `tomllib` verification step fails on Python 3.9 (min version).
3. CI update references `tests.yml` (non-existent) instead of `ci.yml`.

### 5.4 Top 3 Improvements

1. Fix CLI to find repo root and avoid dependency on `ontos.py`.
2. Add architecture stubs or explicitly document deferral with rationale.
3. Correct version references and verification commands for Python 3.9+.

### 5.5 What This Spec Does Well

It provides concrete file-level templates and a clear task sequence for moving the package layout without functional changes.

---

*End of Review - Codex*
