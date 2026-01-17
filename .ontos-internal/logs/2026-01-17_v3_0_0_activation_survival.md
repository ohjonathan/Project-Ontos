---
id: log_20260117_v3_0_0_activation_survival
type: log
status: active
event_type: feature
branch: v3.0.0
source: Antigravity (Gemini CLI, powered by Gemini 2.5 Pro)
impacts: [ontos_agent_instructions, agents_command, doctor_staleness]
concepts: [activation, agents, pypi, cli]
---

# v3.0.0 Activation Survival Implementation

## 1. Goal

Implement v3.0.0 "Activation Survival" features to make Ontos discoverable and usable by AI agents.

## 2. Summary

This session implemented the full v3.0.0 feature set:

**Core Features:**
- New `ontos agents` command generating AGENTS.md and .cursorrules
- Export command renamed to `agents` with deprecation warning
- Init exit code changed to 0 for already-initialized projects
- Init auto-generates AGENTS.md on success
- Doctor includes `check_agents_staleness` for stale AGENTS.md detection
- PyPI publishing workflow with OIDC trusted publishers

**Data Cleanup (D.4b):**
- Fixed 37 broken `depends_on` references in strategy/archive docs
- Removed stale refs to ontology_spec, master_plan_v4, technical_architecture, etc.
- `ontos map --strict` now exits 0

**Testing:**
- 22 new agents command tests
- 4 new doctor staleness tests
- Updated doctor tests for 8-check count
- All 421 tests pass

## 3. Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| `find_repo_root()` returns None | Changed from cwd fallback | Prevents arbitrary file writes |
| Doctor uses max() for log mtime | Changed from sorted()[0] | O(n) performance vs O(n log n) |
| README includes git+ fallback | Added | Pre-PyPI installation path |
| Agent Instructions v3.0 | Updated from v2.8 references | CLI now uses `ontos` not `python3 ontos.py` |

## 4. Files Changed

**Code:**
- `ontos/commands/agents.py` — New command implementation
- `ontos/commands/doctor.py` — Added check_agents_staleness
- `ontos/commands/init.py` — Auto-gen AGENTS.md, exit code 0
- `ontos/cli.py` — Registered agents command

**Tests:**
- `tests/commands/test_agents.py` — 22 new tests
- `tests/commands/test_doctor_phase4.py` — 4 staleness tests + mock updates

**Docs:**
- `README.md` — git+ fallback install
- `docs/reference/Ontos_Agent_Instructions.md` — v3.0 CLI commands

**Data Cleanup (36 files):**
- `.ontos-internal/analysis/*.md` — Removed broken depends_on
- `.ontos-internal/archive/**/*.md` — Removed stale refs
- `.ontos-internal/strategy/**/*.md` — Removed stale refs

## 5. Verification

- All 421 tests pass
- `ontos map --strict` exits 0
- `ontos agents --force` creates AGENTS.md
- `ontos doctor` shows agents_staleness check
- CI: 18/18 checks pass

## 6. Next Steps

- D.6 re-approval from Chief Architect (Codex)
- Merge PR #47 to main
- Tag v3.0.0 release
- Publish to PyPI
