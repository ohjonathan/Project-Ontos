# Independent GLM governance-docs review — Project Ontos v5 remediation

You are an independent non-author governance-docs reviewer, family `glm`, for
the Phase 0 child-scaffolding change under
`project-ontos-v5-remediation-release-plan`. The author and structural
orchestrator family is `codex`; halt if you consider yourself part of that
family.

Work read-only except for the one review artifact below. Record the exact
reviewed commit from `git rev-parse HEAD`. Confirm every reviewed governance
document is committed at that HEAD with no tracked diff; dispatcher-created
capture files under this review directory may appear during the run but are not
part of the reviewed tree. Read:

- `docs/specs/project-ontos-v5-remediation-release-plan-proposal.md`;
- `manifests/project-ontos-v5-remediation-release-plan.yaml`;
- `docs/trackers/project-ontos-v5-remediation-release-plan.md`;
- the canonical Round 1 GLM verdict, historical dispatch intent, dispatch
  result, and Template 16 validation under
  `docs/reviews/project-ontos-v5-remediation-release-plan/`;
- `docs/reviews/project-ontos-v5-remediation-release-plan/.prompts/pre-a-glm-proposal-review.prompt.md`
  and the immutable captured prompt
  `docs/reviews/project-ontos-v5-remediation-release-plan/.prompts/project-ontos-v5-remediation-release-plan-pre-a-glm-review.r1.c20260715T024932Z.87251.5f65fa1f77376b0e9a5caabd6290f677.md`;
- `docs/reviews/project-ontos-v5-remediation-release-plan/.raw/project-ontos-v5-remediation-release-plan-pre-a-glm-review.r1.c20260715T024932Z.87251.5f65fa1f77376b0e9a5caabd6290f677.raw.txt`
  and its matching
  `docs/reviews/project-ontos-v5-remediation-release-plan/.raw/project-ontos-v5-remediation-release-plan-pre-a-glm-review.r1.c20260715T024932Z.87251.5f65fa1f77376b0e9a5caabd6290f677.stderr.redacted.txt`
  capture;
- `docs/reviews/project-ontos-v5-remediation-release-plan/phase-0-live-issue-audit.md`;
- all six `docs/specs/project-ontos-*-proposal.md` child proposals created by
  this Phase 0 change;
- the matching six `manifests/project-ontos-*.yaml` child manifests; and
- the matching six `docs/trackers/project-ontos-*.md` child trackers.

The six exact child IDs are:

1. `project-ontos-v5-remediation-board-hygiene`;
2. `project-ontos-issue-165-audit-registry`;
3. `project-ontos-v5-0-3-dependency-resolver`;
4. `project-ontos-v5-0-3-log-paths`;
5. `project-ontos-v5-0-3-built-in-status-alias`; and
6. `project-ontos-v5-0-3-required-version-preflight`.

Run read-only checks as useful. At minimum inspect whether:

- the parent terminates at Pre-A on the exact Round 1 Split disposition and
  never claims parent Phase A–E certification;
- all six proposal/manifest/tracker triples exist and each child remains
  blocked before Phase A pending its own non-author Template 16 verdict;
- every child is `user_facing: true`, has Product seats in B.1, B.2, and D.2,
  and points `pre_a.artifact_path` to its proposal-verdict output;
- `sibling_deliverable_ids` is empty until a real reciprocal parallel pair is
  scheduled;
- each proposal has a concrete owned scope, forbidden sibling scope, custody,
  rollback boundary, acceptance outline, categorized unknowns, and scoped
  v5/v6 watch item;
- board hygiene does not perform live GitHub mutations in this PR;
- #165 preserves exactly 91 Fable plus nine R2 records and never conflates its
  audit IDs with #174 runtime finding IDs;
- resolver, log-path, alias, and required-version children remain independently
  reversible and do not silently absorb sibling scope;
- the preflight uses only the existing TOML load and required-version range
  semantics and never interprets or accepts the v5.1-only schema, while #178
  stays open for complete v5 delivery;
- the parent #178 custody wording names both v5.0.3 slices and the clarified
  v5.0.3 wording no longer suggests a fifth standalone product change; and
- the Round 1 Template 16/F35 reconciliation is technically accurate and does
  not misrepresent the generic wrapper status as a completed strict receipt;
- the historical worker exit, captured hashes, artifact provenance, evidence
  labels, `shape_invalid` status, and `auth-401-403` classification are
  represented accurately; and
- the diff from `c4607f05d43688bcc9472575d310f0be468a74cf` to the reviewed HEAD
  changes only the authorized closeout, evidence reconciliation, live audit,
  six child governance scaffolds, and generated `Ontos_Context_Map.md` /
  `AGENTS.md` sync—not the accepted release strategy.

Run this pinned verifier and report its actual result; a nonzero result is
expected for the historical non-certifying packet and must be reconciled, not
silently ignored:

```sh
bash .llm-dev/framework/scripts/verify-family-dispatch.sh --allow-pending \
  --intent docs/reviews/project-ontos-v5-remediation-release-plan/pre-a-glm-dispatch-intent.yaml \
  --result docs/reviews/project-ontos-v5-remediation-release-plan/pre-a-glm-dispatch-result.yaml \
  --manifest manifests/project-ontos-v5-remediation-release-plan.yaml
```

Write the complete review to exactly:

`docs/reviews/project-ontos-v5-remediation-release-plan/phase-0-glm-governance-review.md`

Use this frontmatter:

```yaml
---
id: project-ontos-v5-remediation-release-plan-phase-0-glm-governance-review
type: review
deliverable_id: project-ontos-v5-remediation-release-plan
phase: 0.docs
role: peer
family: glm
evidence_labels_used:
  - static-inspection
  - direct-run
status: completed
---
```

After the frontmatter, include an H1, the reviewed commit, scope and checks,
actionable findings with severity and exact file/section locators, and a concise
residual-risk section. End with this exact generic verdict shape:

```markdown
## Verdict
Approve
```

Use `Request changes` instead of `Approve` if any material scope, lifecycle,
Product-seat, custody, or evidence blocker remains. The first non-blank line
under `## Verdict` must be the bare verdict word with no punctuation. Do not
edit any proposal, tracker, manifest, parent artifact, code, or GitHub issue.
`Approve` means only that this supplemental docs review passed; it has
recommendation-only authority and cannot authorize merge, parent Phase A–E, or
child implementation.
