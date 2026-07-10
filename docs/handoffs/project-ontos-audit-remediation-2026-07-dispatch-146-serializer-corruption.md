---
id: project_ontos_audit_remediation_2026_07_dispatch_146
type: handoff
status: active
meta_cycle_id: project-ontos-audit-remediation-2026-07
deliverable_id: project-ontos-audit-serializer-corruption
output_class: O7
date: 2026-07-03
depends_on: []
---

# One-shot implementation-orchestrator dispatch — #146 serializer corruption

You are **Codex** acting as the implementation orchestrator for deliverable
`project-ontos-audit-serializer-corruption` (GitHub issue
[#146](https://github.com/ohjonathan/Project-Ontos/issues/146), milestone "Audit Release
N — hotfix" → **v4.7.1** per the O6 decision at
`docs/handoffs/project-ontos-audit-remediation-2026-07-release-line-decision.md`).
Run the full Template 00 lifecycle (Phase 0 → E). This is a Template-02-style one-shot
dispatch emitted from the meta-cycle kickoff
`docs/handoffs/2026-07-03-audit-remediation-meta-orchestrator-kickoff.md` §10.5. Your
Phase-C write lease is defined by the O5 scope-lock manifest in
`docs/trackers/project-ontos-audit-remediation-release-line.md`.

## Deliverable id

`deliverable_id: project-ontos-audit-serializer-corruption`

Use this exact id everywhere (manifest, tracker, spec, review-board filenames, retro).
No inference from slug or title.

## User goal

`ontos promote`, `ontos migrate`, and the MCP `promote_document` tool never corrupt user
frontmatter: a file that is valid before a write is valid — and semantically identical —
after it. Concretely, all four confirmed corruption modes from audit finding
`D2b-roundtrip-3` (P0, double-confirmed; `docs/reviews/2026-07-02-fable-repo-audit.md`)
are gone: embedded double quotes in colon-containing strings no longer produce
unparseable YAML; comma-containing list items no longer re-split on reload; quoted
scalars no longer flip type (`"4.10"`→`4.1`, `"007"`→`7`, `"no"`→`False`); `#`-leading
values no longer reload as null. Root cause is the hand-rolled `_serialize_field()` in
`ontos/core/schema.py:370` (no escaping). Fix by serializing scalars/lists with
`yaml.safe_dump` — the unused `dump_yaml` in `ontos/io/yaml.py` already exists — and
adding a re-parse assertion before every rewrite on the three affected write paths:
`ontos/commands/promote.py:141` (via `curation.py:416`), `ontos/commands/migrate.py:204`,
and `ontos/mcp/writes.py:627` (autonomous, no human in the loop). This also unblocks the
`ontos log` corruption fix (`D3b-structure-1`, issue #148) once `log.py` later routes
through the shared serializer — do not fix `log.py` here; it is not in your lease.

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
`/Users/jonathanoh/Developer/workspaces/Project-Ontos-worktrees/project-ontos-audit-serializer-corruption`.

- Do not run `git checkout` or `git switch` in the shared/root checkout.
- Before long-running board dispatch, provider-limited fallback, rebase, push/force-push, or lifecycle verification, run `git status --short --branch` and confirm this worktree is on the expected branch/head.
- If the expected worktree does not exist, create or request it via `git worktree add`; do not substitute the shared/root checkout.
- Lock files may help coordinate operators, but dedicated worktrees are the concurrency boundary.

This matters concretely here: #147 (`project-ontos-audit-doctor-rce`) runs on the same
v4.7.1 release line and its lease is disjoint from yours, so the two slices must not share
a checkout.

## Exact artifact list through Phase E

Repo house conventions apply (they refine kickoff §10.5 field 3's generic paths: specs
are `<id>-spec.md`, reviews live under `docs/reviews/<id>/`); the Phase 0 manifest pins
the final paths.

- Phase 0: `manifests/project-ontos-audit-serializer-corruption.yaml` +
  `docs/trackers/project-ontos-audit-serializer-corruption.md`.
- Phase A: `docs/specs/project-ontos-audit-serializer-corruption-spec.md`.
- Phase B.1: `docs/reviews/project-ontos-audit-serializer-corruption/B.1-{claude-sonnet-peer,gemini-adversarial,gpt-alignment}.md`
  (three non-author families; author family = codex) plus the dispatch-intent/result
  YAMLs beside them.
- Phase B.3: `docs/reviews/project-ontos-audit-serializer-corruption/B.3-verdict.md`.
- Phase C: implementation confined to your O5 lease — `ontos/core/schema.py`,
  `ontos/io/yaml.py`, `ontos/commands/promote.py`, `ontos/commands/migrate.py`,
  `ontos/mcp/writes.py`, plus minimal call-site changes in `ontos/core/frontmatter*.py`
  if strictly required — and the new regression test
  `tests/test_frontmatter_roundtrip_regression.py`. NO-TOUCH: `ontos/core/body_refs.py`,
  `ontos/cli.py`, `ontos/commands/log.py`, the rest of `ontos/mcp/`,
  `.pre-commit-config.yaml`, `.ontos/scripts/`, and every other deliverable's paths
  (leased to #147/#151–#157 per the O5 manifest).
- Phase D.2: `docs/reviews/project-ontos-audit-serializer-corruption/D.2-{claude-sonnet-peer,gemini-adversarial,gpt-alignment}.md`;
  D.3: `D.3-verdict.md`; D.4 (conditional, only if D.3 preserves blockers):
  `D.4-fix-summary.md`; D.5: `D.5-{claude,gemini,gpt}-verifier.md` triple; D.6:
  `final-approval.md` (Template 07 gate incl. the Release-action split table).
- Phase E: `docs/retros/project-ontos-audit-serializer-corruption-retro.md` — its
  lifecycle-backing inventory MUST cite
  `docs/handoffs/2026-07-03-audit-remediation-meta-orchestrator-kickoff.md` (P18;
  hollow-backing violation otherwise) — and the Ontos session log via
  `.venv/bin/ontos log -e project-ontos-audit-serializer-corruption`.

## Strict-provider path

When all three non-author family CLIs (`claude`, `gemini`, `gpt`) are dispatchable,
dispatch real external workers via
`bash .llm-dev/framework/scripts/dispatch-family-review.sh` for each of B.1, D.2, and
D.5. Verify with `bash .llm-dev/framework/scripts/verify-family-dispatch.sh
--require-complete` and `bash .llm-dev/framework/scripts/verify-lifecycle.sh
manifests/project-ontos-audit-serializer-corruption.yaml --mode strict-p3`.

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
`D2b-roundtrip-3` is absent from `docs/reviews/2026-07-02-fable-repo-audit.md`;
`ontos/core/schema.py` no longer contains `_serialize_field` at dispatch time; the O5
scope-lock manifest at `docs/trackers/project-ontos-audit-remediation-release-line.md`
is missing or your lease has been reassigned; or your Phase 0 manifest is malformed and
`verify-schema.sh` refuses it. **CLI unavailable is NOT a stop condition** — it routes to
the provider-limited fallback path above. Surface the missing prerequisite to the user
and halt; do not silently truncate the lifecycle.

## Validation commands

Run these exact commands as the session's final mechanical attestation:

```bash
.venv/bin/python -m pytest tests/ -q
.venv/bin/python -m pytest tests/test_frontmatter_roundtrip_regression.py -q
git diff --check
bash .llm-dev/framework/scripts/verify-all.sh
```

If running under the strict-provider path, additionally:

```bash
bash .llm-dev/framework/scripts/verify-lifecycle.sh manifests/project-ontos-audit-serializer-corruption.yaml --mode strict-p3
```

`tests/test_frontmatter_roundtrip_regression.py` is authored in Phase C and MUST assert
the full `serialize_frontmatter → parse_frontmatter_content` round-trip on the four
corruption fixtures from the audit's verification evidence:
`{'title': 'Q3 plan: "final" version'}` (embedded quotes),
`{'depends_on': ['design_v1,final']}` (comma re-split),
`{'version': '4.10', 'build': '007', 'flag': 'no'}` (type flips), and
`{'note': '#42 follow-up'}` (comment-null) — each must round-trip byte-semantically
intact.

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
| Issue closure (#146) | no | yes — deferred to maintainer (out of scope) |

git commit, git tag, and git push are deferred to the maintainer (out of scope) for this
dispatch. The session leaves the working tree for the maintainer to review, stage, commit,
and tag after the lifecycle gate passes.

## Final response status language

At session end, emit ONE of the following two strings verbatim:

- Strict path: `strict_p3_review_complete`.
- Fallback path: `provider_limited_fallback_complete; strict P3 not certified; maintainer release actions deferred`.

Downstream automation matches these strings exactly; paraphrase is forbidden.
