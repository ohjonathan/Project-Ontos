---
id: project_ontos_audit_doctor_rce_tracker
type: tracker
status: active
deliverable_id: project-ontos-audit-doctor-rce
issue: 147
release: v4.7.1
depends_on:
  - project_ontos_audit_remediation_2026_07_dispatch_147
  - project_ontos_audit_remediation_release_line_tracker
---

# project-ontos-audit-doctor-rce — Tracker

| Phase | Owner | Status | Artifact | Evidence | Timestamp |
|-------|-------|--------|----------|----------|-----------|
| 0 | codex orchestrator | completed | manifests/project-ontos-audit-doctor-rce.yaml | `python3 -m ontos activate` usable_with_warnings; `scripts/llm-dev doctor` PASS; O5 lease checked for `ontos/core/mcp_shared.py`, `ontos/core/cursor_mcp.py`, `ontos/commands/doctor.py`, `SECURITY.md`, `tests/test_doctor_mcp_probe_regression.py` | 2026-07-03 |
| A | codex spec-author | completed | docs/specs/project-ontos-audit-doctor-rce-spec.md | Direct inspection of `probe_mcp_initialize`, `inspect_cursor_ontos_config`, `check_cursor_mcp`, audit `D4b-trust-1` and `D4b-trust-2` | 2026-07-03 |
| B.1 | claude-sonnet / gemini / gpt | completed under fallback | docs/reviews/project-ontos-audit-doctor-rce/B.1-*.md | Strict GPT-family dispatch blocked: `gpt-5`, `gpt-4o`, `gpt-4-turbo`, `gpt-5-codex`, `gpt-4.1`, `gpt-4.1-mini`, `gpt-4.1-nano`, and `gpt-4o-mini` rejected by Codex+ChatGPT account; evidence sha256 `1d48eacf1dd290c4a020fe18c151f6f3737fac1152000beb2d974f07819bb14e`; provider-limited fallback authorized | 2026-07-03 |
| B.3 | codex meta-consolidator | completed under fallback | docs/reviews/project-ontos-audit-doctor-rce/B.3-verdict.md | Approve with no preserved blockers; strict P3 not certified | 2026-07-03 |
| C | codex implementation-author | completed | `ontos/core/mcp_shared.py`, `ontos/core/cursor_mcp.py`, `ontos/commands/doctor.py`, `SECURITY.md`, `tests/test_doctor_mcp_probe_regression.py` | New regression passes: `.venv/bin/python -m pytest tests/test_doctor_mcp_probe_regression.py -q`; SECURITY.md corrected | 2026-07-03 |
| D.2 | claude-sonnet / gemini / gpt | completed under fallback | docs/reviews/project-ontos-audit-doctor-rce/D.2-*.md | Warning-only fallback reviews; no blockers preserved | 2026-07-03 |
| D.3 | codex meta-consolidator | completed under fallback | docs/reviews/project-ontos-audit-doctor-rce/D.3-verdict.md | Approve with no preserved blockers; D.4 skipped by dispatch rule | 2026-07-03 |
| D.5 | claude / gemini / gpt | completed under fallback | docs/reviews/project-ontos-audit-doctor-rce/D.5-*-verifier.md | Warning-only fallback verifiers; targeted regression passes; GPT verifier blocked as strict evidence | 2026-07-03 |
| D.6 | codex final-approval | completed with caveat | docs/reviews/project-ontos-audit-doctor-rce/final-approval.md | Targeted regression PASS; manifest PASS; diff-check PASS; full suite FAILS one pre-existing activation-warning-count test; `verify-all` FAILS two framework fixtures; release actions deferred | 2026-07-03 |
| E | codex retro | completed | docs/retros/project-ontos-audit-doctor-rce-retro.md; docs/logs/2026-07-03_merge-pull-request-145-from-ohjonathan-docs-fable.md | Lifecycle backing cites dispatch and meta-cycle kickoff; provider-limited exception recorded; Ontos session log filled | 2026-07-03 |
| fallback authorization | Jonathan | granted | this chat + tracker note | User message: "I atheltize authorize provider-limited-review-exception for project-ontos-audit-doctor-rce"; applies to GPT-family dispatch blockage recorded in `docs/reviews/project-ontos-audit-doctor-rce/gpt-model-access-blockage.md` | 2026-07-03 |

## Notes

- Release actions were maintainer-deferred through Phase E (no commit, tag, push, PR, merge, release, or issue closure in the implementation session).
- **Release-action authorization, 2026-07-09 (Jonathan, explicit).** Template 07 rows flipped to "performed": `git commit`, `git push`, and PR creation, executed from branch `audit/147-doctor-rce-and-meta-cycle`. Rows still deferred to the maintainer: **PR merge**, `git tag`, GitHub release, and issue closure (#147 closes on merge of the PR). No strict-P3 certification was obtained; this deliverable ships under `provider_limited_fallback_complete`.
- Final `bash .llm-dev/framework/scripts/verify-all.sh` exited 1 on framework fixture checks `v1_10_0-agy-substrate-fixture.py` and `verify-d6-gate.sh(strict-p3-fixtures)`; these appear unrelated to #147 and are recorded for D.6 caveat handling.
- **[corrected 2026-07-09]** `TestDoctorCommand.test_returns_exit_code_0_when_checks_pass` was recorded here as a "pre-existing environment-sensitive failure". The mechanism named was right (it observes activation warnings from the audit docs in the workspace) but the conclusion was wrong: those docs were untracked at the time, so base `c8672e9` is green and the failure appears only once they are committed. External review of PR #160 caught this. Root cause was `status: draft-for-review` (not a valid Ontos status) in the #146 spec, plus three orphaned docs. Fixed; the test passes on a clean checkout of the corrected head.
- **[added 2026-07-09]** This deliverable has **no strict-P3 receipts**. Its 11 review artifacts carry `provider_limited_fallback: true` labels but were authored in-session, not dispatched through `dispatch-family-review.sh`; `docs/reviews/project-ontos-audit-doctor-rce/lifecycle-receipt-inventory.yaml` has an empty `receipts[]`. `verify-lifecycle --mode provider-limited-fallback` does not certify this deliverable. The completion claim is label-only and receipts were intentionally not reconstructed.
- **[added 2026-07-09]** The original Phase C fix was incomplete. `is_ontos_managed_launcher()` only compared the executable and an empty launcher prefix, so any argv running Ontos's own binary passed the gate; a repo config could smuggle `scaffold --apply` (or a duplicate `--workspace`) past the `serve` preflight. Replaced with exact-argv validation (`is_ontos_managed_serve_argv`) and safe-by-default probe flags, with three added regression tests.
- Fallback authorization granted 2026-07-03 by Jonathan in chat: "I atheltize authorize provider-limited-review-exception for project-ontos-audit-doctor-rce".
