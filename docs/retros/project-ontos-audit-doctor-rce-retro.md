---
id: project-ontos-audit-doctor-rce-retro
type: retro
status: complete
deliverable_id: project-ontos-audit-doctor-rce
family: codex
depends_on:
  - project_ontos_audit_remediation_2026_07_dispatch_147
  - meta-orchestrator-kickoff
---

# Retro — project-ontos-audit-doctor-rce

## Goal

Remove the `ontos doctor` arbitrary-code-execution path from repo-committed Cursor MCP config and correct SECURITY.md's MCP write-tool description.

## Outcome

Implemented a doctor-only unmanaged project-probe guard, added a hostile regression plus managed-launcher positive test, and corrected SECURITY.md.

## Lifecycle Backing

- Dispatch: `docs/handoffs/project-ontos-audit-remediation-2026-07-dispatch-147-doctor-rce.md`
- Meta-cycle kickoff: `docs/handoffs/2026-07-03-audit-remediation-meta-orchestrator-kickoff.md`
- Manifest: `manifests/project-ontos-audit-doctor-rce.yaml`
- Tracker: `docs/trackers/project-ontos-audit-doctor-rce.md`
- Spec: `docs/specs/project-ontos-audit-doctor-rce-spec.md`
- Review board: `docs/reviews/project-ontos-audit-doctor-rce/`
- Ontos session log: `docs/logs/2026-07-03_merge-pull-request-145-from-ohjonathan-docs-fable.md`

## Provider-Limited Exception

`p3_exception`: warning-only. Strict P3 is not certified because GPT-family dispatch was blocked by model access. Jonathan authorized `provider-limited-review-exception` on 2026-07-03. GPT-family B.1, D.2, and D.5 remain queued for re-adjudication when a working `gpt-*` model is available.

## Testing

- PASS: `.venv/bin/python -m pytest tests/test_doctor_mcp_probe_regression.py -q`
- PASS: `git diff --check`
- PASS: `scripts/llm-dev verify manifests/project-ontos-audit-doctor-rce.yaml`
- FAIL: `.venv/bin/python -m pytest tests/ -q` with one existing activation-warning-count failure.
- FAIL: `bash .llm-dev/framework/scripts/verify-all.sh` with unrelated framework fixture failures in `v1_10_0-agy-substrate-fixture.py` and `verify-d6-gate.sh(strict-p3-fixtures)`.

## Release Actions

All release actions are deferred to the maintainer: commit, tag, push, PR, merge, release, and issue closure.
