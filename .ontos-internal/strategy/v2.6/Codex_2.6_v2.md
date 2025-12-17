---
id: codex_2_6_v2_review
type: strategy
status: draft
depends_on: [v2_6_proposals_and_tooling]
concepts: [review, proposals, validation, workflow, lint]
---

# Review: V2.6 Proposals Workflow & Validation (Codex V2)

**Date:** 2025-12-17  
**Reviewer:** Codex  
**Scope:** `.ontos-internal/strategy/proposals/v2.6/v2.6_proposals_and_tooling.md`

---

## Verdict
- **Changes required** — Round 2 addresses most prior gaps, but key enforcement and edge cases remain.

---

## Findings (by risk)

1) Decision history enforcement missing for approvals/rejections  
- The plan requires recording approvals/rejections in `decision_history.md`, but lint only checks `rejected_reason` and archive location. There is no lint to ensure a `status: rejected` (or graduated `status: active` formerly under proposals) has a decision_history row. Without this, rejected/approved decisions can disappear from the ledger. Suggest: lint that any `status: rejected` must have a matching decision_history entry (by slug/id) and that any active doc residing under `proposals/` emits a warning to graduate/move + log.

2) Approval path not enforced  
- Lifecycle says “graduate to strategy/” on approval, but no lint enforces “active + proposals/ path” as invalid. Add a rule: if `status: active` and path includes `proposals/`, warn to move to `strategy/` and log approval.

3) Rejection metadata completeness  
- Required metadata in text is `rejected_reason`, but rejected_date is not enforced. Lint should require both `rejected_reason` and `rejected_date` for `status: rejected`; optionally warn if `rejected_by` missing. Otherwise rejections lack temporal context.

4) Type/status matrix edge cases  
- Matrix allows `kernel`/`draft` but not `archived`—fine; however, logs in archive likely remain `status: active` per current tooling. If `status: archived` is permitted for logs, make sure status indicator covers it, or explicitly disallow and rely on path. Ensure lint errors (not just warns) on invalid type/status combos under `--strict`.

5) Context map inclusion of archived/rejected split unresolved  
- The doc adds `--include-rejected` but leaves `--include-archived` open. Decide and document final flag behavior; default exclusions should still allow discovery via query. If combined flag is chosen later, reflect in tests/UX.

6) Version reminder scope may miss multi-commit pushes  
- Pre-push check looks at `HEAD~1..HEAD`; if multiple commits are pushed, earlier script changes won’t trigger the reminder. Consider diffing against upstream (e.g., `origin/branch..HEAD`) or using staged/working tree changes to avoid false negatives. False positives are acceptable per design; missing reminders are not.

7) Tests need explicit dual-mode coverage for new lint  
- Tests T1–T16 list both modes, but ensure fixtures exercise custom `DOCS_DIR` as well (per prior plan) so validation logic isn’t hardcoded to `docs/`.

---

## What I would do differently
- Add explicit lint to tie lifecycle to the ledger: rejected/approved items must be recorded in `decision_history.md`; rejected must live under `archive/proposals/`; active must not live under `proposals/`. Make invalid type/status and misplaced lifecycle states error under `--strict`.
- Enforce rejection metadata: require `rejected_reason` and `rejected_date`; warn on missing `rejected_by`.
- Strengthen the version reminder to diff against the remote tracking ref to catch multi-commit pushes.
- Settle flag semantics (`--include-rejected`, `--include-archived`, or umbrella) now and align tests/Agent instructions.

---

## Residual questions
- Should logs ever carry `status: archived`, and if so, should the status indicator show `[archived]` to highlight historical items in the map?  
- For approvals, should graduation to `strategy/` be mandatory (with lint), or is staying in `proposals/` with `status: active` acceptable in some workflows? My recommendation: mandate graduation for consistency and discoverability.
