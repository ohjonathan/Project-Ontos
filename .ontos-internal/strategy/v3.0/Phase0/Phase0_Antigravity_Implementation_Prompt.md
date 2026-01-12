# Antigravity Development Prompt: Phase 0 Golden Master Implementation

**Generated:** 2026-01-12
**For:** Antigravity IDE
**Purpose:** Continue Phase 0 implementation from crash recovery point

---

## Context

You are implementing **Phase 0 of the Ontos v3.0 Migration** - the Golden Master Testing infrastructure. This creates a safety net before decomposing the God Scripts (`ontos_end_session.py` at 1,904 lines and `ontos_generate_context_map.py` at 1,295 lines).

**Spec File:** `.ontos-internal/strategy/v3.0/Phase0/phase0_implementation_spec.md` (v1.1)

---

## Current Progress

| Task | Status |
|------|--------|
| `tests/golden/__init__.py` | ✅ Complete |
| `tests/golden/fixtures/small/` (5 files) | ✅ Complete |
| `tests/golden/fixtures/medium/` (25 files) | ⚠️ **Partial (9/25)** |
| `tests/golden/fixtures/large/` (100+ files) | ❌ Not started |
| `tests/golden/capture_golden_master.py` | ❌ Not started |
| `tests/golden/compare_golden_master.py` | ❌ Not started |
| `.github/workflows/golden-master.yml` | ❌ Not started |
| `tests/golden/README.md` | ❌ Not started |

**Medium Fixture - Already Created (9 files):**
- `kernel/mission.md`, `kernel/philosophy.md`, `kernel/constitution.md`
- `strategy/core_architecture.md`, `strategy/api_design.md`, `strategy/database_schema.md`
- `strategy/security_model.md`, `strategy/deployment_strategy.md`, `strategy/testing_plan.md`

---

## Remaining Medium Fixture Files (16 files)

Create these files in `tests/golden/fixtures/medium/`:

### 1. `.ontos-internal/strategy/documentation_guide.md`
```markdown
---
id: documentation_guide
type: strategy
status: active
depends_on: [mission]
---
# Documentation Guide
Standards for project documentation.
```

### 2. `.ontos-internal/strategy/rejected_proposal.md`
```markdown
---
id: rejected_proposal
type: strategy
status: rejected
depends_on: [core_architecture]
rejected_reason: "Superseded by api_design approach"
---
# Rejected: GraphQL API
This proposal was rejected in favor of REST.
```

### 3. `.ontos-internal/strategy/proposals/feature_a.md`
```markdown
---
id: feature_a
type: strategy
status: draft
depends_on: [api_design]
---
# Draft: Feature A
Proposed new capability (under review).
```

### 4. `.ontos-internal/strategy/proposals/feature_b.md`
```markdown
---
id: feature_b
type: strategy
status: active
depends_on: [api_design, security_model]
---
# Feature B
Approved and in development.
```

### 5. `.ontos-internal/strategy/proposals/deprecated_idea.md`
```markdown
---
id: deprecated_idea
type: strategy
status: deprecated
depends_on: [core_architecture]
---
# Deprecated: Old Approach
No longer recommended; kept for historical reference.
```

### 6. `.ontos-internal/strategy/proposals/complete_feature.md`
```markdown
---
id: complete_feature
type: strategy
status: complete
depends_on: [api_design]
---
# Complete: Feature C
Successfully implemented and deployed.
```

### 7. `.ontos-internal/atom/schema.md`
```markdown
---
id: medium_schema
type: atom
status: active
depends_on: [database_schema]
---
# Schema Definition
Technical schema specifications.
```

### 8. `.ontos-internal/atom/validation_rules.md`
```markdown
---
id: validation_rules
type: atom
status: active
depends_on: [medium_schema]
---
# Validation Rules
Input validation and constraints.
```

### 9. `.ontos-internal/atom/common_concepts.md`
```markdown
---
id: common_concepts
type: atom
status: active
depends_on: [mission]
concepts: [architecture, api, testing]
---
# Common Concepts
Shared terminology and definitions.
```

### 10. `.ontos-internal/atom/dual_mode_matrix.md`
```markdown
---
id: dual_mode_matrix
type: atom
status: active
depends_on: [core_architecture]
---
# Dual Mode Matrix
Configuration options by environment.
```

### 11. `.ontos-internal/logs/2025-01-01_initial-setup.md`
```markdown
---
id: log_20250101_initial_setup
type: log
status: active
event_type: feature
concepts: [setup, architecture]
impacts: [core_architecture]
---
# Initial Setup
## Goal
Set up the project structure.
## Changes Made
- Created initial documentation structure
## Raw Session History
` ``text
abc1234 - Initial commit
` ``
```

### 12. `.ontos-internal/logs/2025-01-15_api-design.md`
```markdown
---
id: log_20250115_api_design
type: log
status: active
event_type: feature
concepts: [api, rest]
impacts: [api_design, security_model]
---
# API Design Session
## Goal
Design the REST API.
## Changes Made
- Defined API endpoints
## Raw Session History
` ``text
def5678 - Add API design doc
` ``
```

### 13. `.ontos-internal/logs/2025-02-01_security-hardening.md`
```markdown
---
id: log_20250201_security
type: log
status: active
event_type: feature
concepts: [security, auth]
impacts: [security_model]
---
# Security Hardening
## Goal
Implement security measures.
## Changes Made
- Added authentication
## Raw Session History
` ``text
ghi9012 - Security update
` ``
```

### 14. `.ontos-internal/logs/2025-02-15_rejected-exploration.md`
```markdown
---
id: log_20250215_rejected
type: log
status: active
event_type: exploration
concepts: [graphql, api]
impacts: [rejected_proposal]
---
# GraphQL Exploration
## Goal
Evaluate GraphQL as alternative.
## Changes Made
- Rejected in favor of REST
## Raw Session History
` ``text
jkl3456 - Mark proposal rejected
` ``
```

### 15. `.ontos-internal/logs/2025-03-01_feature-complete.md`
```markdown
---
id: log_20250301_complete
type: log
status: active
event_type: feature
concepts: [release]
impacts: [complete_feature]
---
# Feature C Complete
## Goal
Finalize Feature C.
## Changes Made
- Marked as complete
## Raw Session History
` ``text
mno7890 - Feature complete
` ``
```

### 16. `.ontos.toml`
```toml
[ontos]
version = "3.0"

[paths]
docs_dir = ".ontos-internal"
logs_dir = ".ontos-internal/logs"
context_map = "Ontos_Context_Map.md"

[scanning]
skip_patterns = ["_template.md", "archive/*"]

[validation]
strict = false
```

---

## After Medium Fixture: Create Scripts

### File: `tests/golden/capture_golden_master.py`

Copy the complete script from the spec file Section 3.1 (lines 656-1030). Key points:
- `PROJECT_ROOT = SCRIPT_DIR.parent.parent` (tests/golden/ → project root)
- Includes `normalize_output()`, `normalize_context_map()`, `normalize_session_log()`
- Git user config: `-c user.name=Golden Master -c user.email=test@example.com`
- Captures stdout, stderr, exit_code, context_map, session_log

### File: `tests/golden/compare_golden_master.py`

Copy the complete script from the spec file Section 4.1 (lines 1038-1378). Key points:
- Imports normalization functions from `capture_golden_master`
- Compares stderr and session_log (v1.1 additions)
- Returns exit code 0 on pass, 1 on fail

---

## After Scripts: Create CI and README

### File: `.github/workflows/golden-master.yml`

Copy from spec Section 5.1 (lines 1386-1426). Key points:
- Triggers on push to main, v3.0, v3.0.*
- Matrix: Python 3.9, 3.10, 3.11, 3.12
- Uploads artifacts on failure

### File: `tests/golden/README.md`

Copy from spec Section 5.2 (lines 1430-1508).

---

## Large Fixture (Defer or Generate)

The large fixture (100+ docs) can be:
1. **Deferred** - implement after small/medium work
2. **Generated** - write a simple Python script to generate 100+ docs programmatically

Recommended: Defer until capture/compare scripts are verified working on small/medium.

---

## Verification Steps

After all files are created:

```bash
# 1. Run capture on small fixture
python tests/golden/capture_golden_master.py --fixture small

# 2. Verify baselines created
ls -la tests/golden/baselines/small/

# 3. Run comparison (should pass)
python tests/golden/compare_golden_master.py --fixture small

# 4. Repeat for medium
python tests/golden/capture_golden_master.py --fixture medium
python tests/golden/compare_golden_master.py --fixture medium
```

---

## Implementation Order

1. Complete medium fixture (16 remaining files)
2. Create `capture_golden_master.py`
3. Create `compare_golden_master.py`
4. Test capture/compare on small fixture
5. Test capture/compare on medium fixture
6. Create `.github/workflows/golden-master.yml`
7. Create `tests/golden/README.md`
8. (Optional) Create large fixture

---

## Watch Out For

1. **Nested code blocks in logs**: The log files have triple-backtick code blocks inside them. Make sure they're properly escaped.
2. **Directory creation**: Create `strategy/proposals/` subdirectory before creating files in it.
3. **Git imports**: The `compare_golden_master.py` imports from `capture_golden_master.py` - ensure `__init__.py` exists (already done).

---

*End of Antigravity Prompt*
