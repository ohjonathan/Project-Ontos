---
id: codex_2_6_v3_review
type: strategy
status: draft
depends_on: [v2_6_proposals_and_tooling]
concepts: [review, proposals, validation, workflow, lint]
---

# Review: V2.6 Proposals Workflow & Validation (Codex V3)

**Date:** 2025-12-17  
**Reviewer:** Codex  
**Scope:** `.ontos-internal/strategy/proposals/v2.6/v2.6_proposals_and_tooling.md` (Round 3)

---

## Verdict
- **Changes required (minor)** — Round 3 closes most gaps; remaining risks are ledger validation fidelity and approval ledger symmetry.

---

## Findings

1) Decision-history validation is heuristic and asymmetric  
- The plan now checks that rejected proposals appear in `decision_history.md`, but matching is via a slug heuristic (`doc_id` → hyphenated) and only for rejections. If the ledger uses a different slug (common), this yields false warnings/false negatives. Also, approvals are not validated at all—an approved proposal could graduate without a ledger entry.  
**Recommendation:** Match by explicit frontmatter field (e.g., `id` or `slug` column value) or by archive/path link, not inferred slug. Add a corresponding check for approved/graduated proposals so both outcomes are captured in the ledger.

2) Error plumbing not fully specified for hard errors  
- Type/status violations are defined as hard errors, but the plan assumes an `errors` collection and exit path without stating how it integrates into `ontos_generate_context_map.py` (which currently uses warnings).  
**Recommendation:** Ensure `errors` is declared/propagated and causes a non-zero exit; add tests to confirm context-map generation fails on invalid type/status.

3) Active-in-proposals lint should also assert ledger entry  
- The new warning for `status: active` under `proposals/` nudges graduation, but without a ledger check approvals can still be missed.  
**Recommendation:** Combine the warning with a ledger requirement: approved items must both move to `strategy/` and have an APPROVED row in `decision_history.md`.

---

## What I would do differently
- Use explicit identifiers for ledger validation (frontmatter `id` or an explicit `slug` column) to avoid heuristics and false positives.  
- Add symmetry: enforce ledger presence for both REJECTED and APPROVED outcomes.  
- Specify and test the hard-error plumbing in context-map generation (errors list, exit code) so the type/status matrix actually blocks invalid docs.***
