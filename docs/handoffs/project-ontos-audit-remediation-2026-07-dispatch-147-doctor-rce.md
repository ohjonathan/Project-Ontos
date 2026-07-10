---
id: project_ontos_audit_remediation_2026_07_dispatch_147
type: handoff
status: active
meta_cycle_id: project-ontos-audit-remediation-2026-07
deliverable_id: project-ontos-audit-doctor-rce
output_class: O7
date: 2026-07-03
depends_on: []
---

# One-shot implementation-orchestrator dispatch — #147 doctor RCE

You are **Codex** acting as the implementation orchestrator for deliverable
`project-ontos-audit-doctor-rce` (GitHub issue
[#147](https://github.com/ohjonathan/Project-Ontos/issues/147), milestone "Audit Release
N — hotfix" → **v4.7.1** per the O6 decision at
`docs/handoffs/project-ontos-audit-remediation-2026-07-release-line-decision.md`).
Run the full Template 00 lifecycle (Phase 0 → E). This is a Template-02-style one-shot
dispatch emitted from the meta-cycle kickoff
`docs/handoffs/2026-07-03-audit-remediation-meta-orchestrator-kickoff.md` §10.5. Your
Phase-C write lease is defined by the O5 scope-lock manifest in
`docs/trackers/project-ontos-audit-remediation-release-line.md`. This deliverable runs
concurrently with #146 on the v4.7.1 line; the two leases do not overlap.

## Deliverable id

`deliverable_id: project-ontos-audit-doctor-rce`

Use this exact id everywhere (manifest, tracker, spec, review-board filenames, retro).
No inference from slug or title.

## User goal

Running `ontos doctor` — a documented troubleshooting command — in a cloned untrusted
repository never executes a command sourced from a repo-committed `.cursor/mcp.json`.
Root cause (audit `D4b-trust-1`, P1·sec, CONFIRMED end-to-end by all three PR-145
reviewers): `probe_mcp_initialize` at `ontos/core/mcp_shared.py:375` runs
`subprocess.run([command, *args])` with `command`/`args` taken verbatim from the
repo-local config, reached unconditionally via `check_cursor_mcp`
(`ontos/commands/doctor.py:924`) → `inspect_cursor_ontos_config(scope='project')` →
`probe_mcp_initialize` (`ontos/core/cursor_mcp.py:262`); padding ignored tokens
(`python3 -c '<payload>' serve --workspace /tmp`) satisfies every shape check while
executing arbitrary code. Fix: do not execute repo-sourced commands during read-only
diagnostics — drop the live probe for project-scoped configs, or gate it behind explicit
opt-in and only probe when the resolved `command` equals Ontos's own launcher
(`resolve_ontos_launcher()`), rejecting any non-managed form. Also fold in `D4b-trust-2`
(P2): correct `SECURITY.md:51`, which claims the v4.0 MCP tools are read-only while the
server ships 5 write tools gated only by the non-default `--read-only` flag.

## Lifecycle ownership and role split

By default, the implementation orchestrator owns the slice lifecycle end-to-end:
implementation, deterministic validation, external board dispatch, receipt/artifact
collection, finding fixes, redispatch, Phase D.6, and Phase E. Meta Orchestrator authored
this handoff as control-plane guidance; it does not run the board unless this slice
explicitly delegates that execution role.

Role split: lifecycle dispatcher/operator; implementation author/fix-author; external
review/verifier/final-approval seats. Guard: The implementation orchestrator may run
external board dispatches as dispatcher, but must not count its own family as a
review/verifier seat. (Author family here is codex; the three non-author review families
are claude, gemini, and gpt.)

## Worktree Isolation

If any other slice/session may be active, do not use the shared/root checkout for
implementation or board execution. The shared/root checkout
`/Users/jonathanoh/Developer/workspaces/Project-Ontos` is meta/control-plane only. Use the
dedicated slice worktree
`/Users/jonathanoh/Developer/workspaces/Project-Ontos-worktrees/project-ontos-audit-doctor-rce`.

- Do not run `git checkout` or `git switch` in the shared/root checkout.
- Before long-running board dispatch, provider-limited fallback, rebase, push/force-push, or lifecycle verification, run `git status --short --branch` and confirm this worktree is on the expected branch/head.
- If the expected worktree does not exist, create or request it via `git worktree add`; do not substitute the shared/root checkout.
- Lock files may help coordinate operators, but dedicated worktrees are the concurrency boundary.

This matters concretely here: #146 (`project-ontos-audit-serializer-corruption`) runs on
the same v4.7.1 release line and its lease is disjoint from yours, so the two slices must
not share a checkout.

## Exact artifact list through Phase E

Repo house conventions apply (specs are `<id>-spec.md`; reviews under
`docs/reviews/<id>/`); the Phase 0 manifest pins the final paths.

- Phase 0: `manifests/project-ontos-audit-doctor-rce.yaml` +
  `docs/trackers/project-ontos-audit-doctor-rce.md`.
- Phase A: `docs/specs/project-ontos-audit-doctor-rce-spec.md`.
- Phase B.1: `docs/reviews/project-ontos-audit-doctor-rce/B.1-{claude-sonnet-peer,gemini-adversarial,gpt-alignment}.md`
  (three non-author families; author family = codex) plus the dispatch-intent/result
  YAMLs beside them.
- Phase B.3: `docs/reviews/project-ontos-audit-doctor-rce/B.3-verdict.md`.
- Phase C: implementation confined to your O5 lease — `ontos/core/mcp_shared.py`,
  `ontos/core/cursor_mcp.py`, `ontos/commands/doctor.py`, `SECURITY.md` — plus the new
  regression test `tests/test_doctor_mcp_probe_regression.py`. NO-TOUCH: `ontos/mcp/`
  proper (leased to #153/#154), `ontos/core/schema.py` and `ontos/io/yaml.py` (leased to
  #146, running concurrently on this same release line), and every other deliverable's
  paths per the O5 manifest.
- Phase D.2: `docs/reviews/project-ontos-audit-doctor-rce/D.2-{claude-sonnet-peer,gemini-adversarial,gpt-alignment}.md`;
  D.3: `D.3-verdict.md`; D.4 (conditional, only if D.3 preserves blockers):
  `D.4-fix-summary.md`; D.5: `D.5-{claude,gemini,gpt}-verifier.md` triple; D.6:
  `final-approval.md` (Template 07 gate incl. the Release-action split table).
- Phase E: `docs/retros/project-ontos-audit-doctor-rce-retro.md` — its lifecycle-backing
  inventory MUST cite
  `docs/handoffs/2026-07-03-audit-remediation-meta-orchestrator-kickoff.md` (P18;
  hollow-backing violation otherwise) — and the Ontos session log via
  `.venv/bin/ontos log -e project-ontos-audit-doctor-rce`.

## Strict-provider path

When all three non-author family CLIs (`claude`, `gemini`, `gpt`) are dispatchable,
dispatch real external workers via
`bash .llm-dev/framework/scripts/dispatch-family-review.sh` for each of B.1, D.2, and
D.5. Verify with `bash .llm-dev/framework/scripts/verify-family-dispatch.sh
--require-complete` and `bash .llm-dev/framework/scripts/verify-lifecycle.sh
manifests/project-ontos-audit-doctor-rce.yaml --mode strict-p3`.

Final response status string (exact): `strict_p3_review_complete`.

## Provider-limited fallback path

`provider-limited-review-exception` is **NOT pre-authorized** for this deliverable (O6
decision log entry 6). If strict cross-provider dispatch is unavailable in your session
(any of the three non-author family CLIs cannot be dispatched — partial 2-of-3 dispatch
is fallback by definition, never a strict path):

1. **Halt the review phase** and request `provider-limited-review-exception`
   authorization from the maintainer (Jonathan), recording his grant in your
   per-deliverable tracker before proceeding.
2. Once authorized, continue through D.6 and E under fallback labeling: every B.1 / B.3 /
   D.2 / D.3 / D.5 artifact carries `provider_limited_fallback: true`,
   `strict_p3_gap: "<reason>"`, `canonical_p3_evidence: false`, and
   `fallback_authorization_ref: <tracker entry recording the grant>` in frontmatter, and
   opens with the canonical banner snippet
   (`templates/03-review-board-peer.md § Provider-limited fallback labeling`).
3. Phase D.4 fix-author and Phase D.6 final-approval remain **non-fallback** honest work;
   the Phase E retro records the warning-only `p3_exception` block.

**D.6 and E continuation is not optional under provider-limited fallback.** "Do not
fabricate evidence" is a labeling rule, not a stop condition.

Final response status string (exact): `provider_limited_fallback_complete; strict P3 not certified; maintainer release actions deferred`.

## Stop-only path

You may stop ONLY when a work prerequisite is missing — for example: audit section
`D4b-trust-1` is absent from `docs/reviews/2026-07-02-fable-repo-audit.md`;
`probe_mcp_initialize` no longer exists in `ontos/core/mcp_shared.py` at dispatch time;
the O5 scope-lock manifest at
`docs/trackers/project-ontos-audit-remediation-release-line.md` is missing or your lease
has been reassigned; or your Phase 0 manifest is malformed and `verify-schema.sh` refuses
it. **CLI unavailable is NOT a stop condition** — it routes to the provider-limited
fallback path above. Surface the missing prerequisite to the user and halt; do not
silently truncate the lifecycle.

## Validation commands

Run these exact commands as the session's final mechanical attestation:

```bash
.venv/bin/python -m pytest tests/ -q
.venv/bin/python -m pytest tests/test_doctor_mcp_probe_regression.py -q
git diff --check
bash .llm-dev/framework/scripts/verify-all.sh
```

If running under the strict-provider path, additionally:

```bash
bash .llm-dev/framework/scripts/verify-lifecycle.sh manifests/project-ontos-audit-doctor-rce.yaml --mode strict-p3
```

`tests/test_doctor_mcp_probe_regression.py` is authored in Phase C and MUST reproduce the
audit's end-to-end exploit shape in a temporary repo: write a hostile `.cursor/mcp.json`
with `command=python3, args=[-c, <payload that writes a marker file>, serve, --workspace,
<abs path>]`, run `ontos doctor` against it, and assert the command completes **without
spawning the payload** (the marker file is absent). Include a positive case that an
Ontos-managed launcher config still probes as intended.

## Commit / tag / push / merge / issue-closure policy

Release actions in this dispatch are maintainer-deferred (Template 07 § Release-action
split). You are forbidden from performing the following; a row flips to "performed in
session" only with explicit user authorization recorded in your per-deliverable tracker:

| Action | Performed in session? | Deferred to maintainer? |
|--------|------------------------|--------------------------|
| `git commit` | no | yes — deferred to maintainer (out of scope) |
| `git tag` | no | yes — deferred to maintainer (out of scope) |
| `git push` | no | yes — deferred to maintainer (out of scope) |
| PR creation / merge | no | yes — deferred to maintainer (out of scope) |
| GitHub release | no | yes — deferred to maintainer (out of scope) |
| Issue closure (#147) | no | yes — deferred to maintainer (out of scope) |

git commit, git tag, and git push are deferred to the maintainer (out of scope) for this
dispatch. The session leaves the working tree for the maintainer to review, stage, commit,
and tag after the lifecycle gate passes.

## Final response status language

At session end, emit ONE of the following two strings verbatim:

- Strict path: `strict_p3_review_complete`.
- Fallback path: `provider_limited_fallback_complete; strict P3 not certified; maintainer release actions deferred`.

Downstream automation matches these strings exactly; paraphrase is forbidden.
