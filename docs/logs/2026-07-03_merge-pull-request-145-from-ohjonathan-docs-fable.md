---
id: log_20260703_merge-pull-request-145-from-ohjonathan-docs-fable
type: log
status: active
event_type: project-ontos-audit-doctor-rce
source: cli
branch: main
created: 2026-07-03
---

# project-ontos-audit-doctor-rce

## Goal

Fix issue #147 so the documented `ontos doctor` diagnostic path no longer executes
unmanaged commands sourced from a repo-committed `.cursor/mcp.json`, and correct the
SECURITY.md description of MCP write-tool exposure.

## Key Decisions

- Treat project-scoped Cursor MCP configs as untrusted for doctor diagnostics unless
  the command resolves to the Ontos-managed launcher.
- Preserve managed-launcher probing behavior for trusted Ontos launcher configs while
  returning a skipped inspection result for unmanaged project configs.
- Proceed under the provider-limited-review-exception path after GPT-family Codex CLI
  dispatch was blocked by model access and Jonathan authorized fallback continuation.
- Defer all release actions to the maintainer: no commit, tag, push, PR, merge, release,
  or issue closure was performed.

## Alternatives Considered

- Removing all project-scope Cursor probing from `ontos doctor`; rejected because the
  narrower managed-launcher gate preserves useful diagnostics for Ontos-owned configs.
- Treating the GPT-family dispatch blockage as a stop condition; rejected because the
  dispatch explicitly routes CLI unavailability to provider-limited fallback after
  maintainer authorization.

## Impacts

- `ontos doctor` skips direct MCP initialize probes for unmanaged project Cursor configs,
  closing the documented arbitrary command execution path.
- The new regression test reproduces the hostile `python3 -c ... serve --workspace ...`
  shape and asserts no marker file is written.
- SECURITY.md now documents the actual read-only flag behavior and mutable MCP write tools.
- Strict P3 is not certified for this deliverable; fallback artifacts are warning-only and
  re-adjudication remains queued for a future working GPT-family substrate.

## Testing

- PASS: `.venv/bin/python -m pytest tests/test_doctor_mcp_probe_regression.py -q`
- PASS: `git diff --check`
- PASS: `scripts/llm-dev verify manifests/project-ontos-audit-doctor-rce.yaml`
- FAIL: `.venv/bin/python -m pytest tests/ -q` has one environment-sensitive existing
  failure in `tests/commands/test_doctor_phase4.py::TestDoctorCommand::test_returns_exit_code_0_when_checks_pass`
  because the active workspace currently reports Ontos activation warnings.
- FAIL: `bash .llm-dev/framework/scripts/verify-all.sh` fails in framework fixtures
  `v1_10_0-agy-substrate-fixture.py` and `verify-d6-gate.sh(strict-p3-fixtures)`.
