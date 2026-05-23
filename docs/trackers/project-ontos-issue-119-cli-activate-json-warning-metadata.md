# project-ontos-issue-119-cli-activate-json-warning-metadata — Tracker

| Phase | Owner | Status | Artifact | Evidence | Timestamp |
|-------|-------|--------|----------|----------|-----------|
| 0     | orchestrator | completed | manifests/project-ontos-issue-119-cli-activate-json-warning-metadata.yaml | scripts/llm-dev doctor PASS; scripts/llm-dev verify PASS (4/4) | 2026-05-22 |
| -A.triage | claude-opus (orchestrator-authored) | completed | docs/reviews/.../pre-a-triage-report.md + pre-a-triage-verdict.md | #119 classified In-Scope; verify-pre-a.sh PASS | 2026-05-22 |
| A     | claude-opus (orchestrator-authored) | completed | docs/specs/project-ontos-issue-119-cli-activate-json-warning-metadata-spec.md | G-cardinality-2 (10 `#119` mentions); spec amended post-B.1 to close gemini F1 blocker | 2026-05-22 |
| B.1   | codex / claude-sonnet / gemini | completed | B.1-{family}-{role}.md (×3) | strict-P3 receipts appended; codex Approve, sonnet Approve, gemini Request-changes (1 blocker → closed in spec) | 2026-05-22 |
| B.3   | claude-sonnet (orchestrator-authored) | completed | B.3-verdict.md | Concur; gemini F1 blocker closed inline (§1.3.3 type hint tightened); 3 should-fix items closed in spec amendments | 2026-05-22 |
| C     | claude-opus (orchestrator-authored) | completed | ontos/core/types.py + ontos/commands/activate.py + ontos/mcp/tools.py + tests/commands/test_activate_json_warning_metadata.py + docs/releases/v4.6.0.md | 1330/1330 tests pass; manual smoke confirms `data.validation.warnings[0]` is now a dict with all 5 fields | 2026-05-22 |
| D.1   | codex (orchestrator-authored) | pending |   |   |   |
| D.2   | codex / claude-sonnet / gemini | pending |   |   |   |
| D.3   | claude-sonnet (orchestrator-authored) | pending |   |   |   |
| D.4   | claude-opus (orchestrator-authored) | pending |   |   |   |
| D.5   | codex / claude-sonnet / gemini | pending |   |   |   |
| D.6   | codex (orchestrator-authored) | pending |   |   |   |
| E     | gemini (orchestrator-authored) | pending |   |   |   |
