---
id: v3_1_tech_debt_wrapper_commands
type: tech-debt
status: open
depends_on: [phase_v3_0_4_implementation_spec]
concepts: [tech-debt, wrapper-commands, native-migration, pythonpath]
---

# Tech Debt: Wrapper Command Migration

**Created:** 2026-01-19
**Source:** v3.0.4 Implementation (PR #50)
**Priority:** P1 for v3.1

---

## Summary

The v3.0.4 fix for wrapper commands required adding `package_root` to PYTHONPATH, perpetuating the legacy wrapper architecture. This tech debt should be resolved in v3.1 by migrating all wrapper commands to native implementations.

---

## Current State (v3.0.4)

**Wrapper commands:** `verify`, `query`, `consolidate`, `scaffold`, `stub`, `promote`, `migrate`

**Architecture:**
```
CLI → _cmd_wrapper() → subprocess.run() → legacy Python script
                              ↓
                    PYTHONPATH manipulation required
                    (project_root + package_root)
```

**Why PYTHONPATH is needed:**
- `project_root` (CWD): For `ontos_config.py` imports
- `package_root` (install dir): For `ontos.core.*` imports

---

## Tech Debt Items

| Item | Description | Impact |
|------|-------------|--------|
| PYTHONPATH pollution | Two paths added to PYTHONPATH per subprocess | Minor import shadowing risk (B3) |
| Subprocess overhead | Each wrapper command spawns Python subprocess | Performance cost |
| Dual architecture | Native vs wrapper commands behave differently | Maintenance burden |
| Error handling | Wrapper errors are harder to diagnose | User experience |

---

## Resolution: v3.1 Native Migration

**Target:** Convert all 7 wrapper commands to native implementations.

| Command | Migration Complexity | Notes |
|---------|---------------------|-------|
| `verify` | Medium | Core validation logic |
| `query` | Medium | Document querying |
| `consolidate` | Low | Graph consolidation |
| `scaffold` | Low | Template generation |
| `stub` | Low | Stub generation |
| `promote` | Low | Status promotion |
| `migrate` | Medium | Schema migration |

**Benefits:**
1. Eliminates PYTHONPATH manipulation entirely
2. Consistent error handling across all commands
3. Better performance (no subprocess overhead)
4. Unified codebase (no legacy scripts)

---

## References

- v3.0.4 Spec v1.2, Section 4.1: Documents `package_root` deviation
- v3.0.4 Spec v1.2, Section 2.2: "Migrating wrapper commands to native implementations — Deferred to v3.1+"
- v3.0.4 Spec v1.2, Section 7.1: "Full resolution requires v3.1 native migration"
- PR #50: Chief Architect decision approving deviation

---

*Added during v3.0.4 D.5.1 phase as forward reference for v3.1 planning.*
