---
id: codex_2_6_v1_review
type: strategy
status: draft
depends_on: [v2_6_proposals_and_tooling]
concepts: [review, proposals, validation, workflow, lint]
---

# Review: V2.6 Proposals Workflow & Validation (Codex V1)

**Date:** 2025-12-17  
**Reviewer:** Codex (Architect)  
**Scope:** `.ontos-internal/strategy/proposals/v2.6_proposals_and_tooling.md`

---

## Verdict
- **Changes required** — core ideas are sound, but validation wiring and lifecycle enforcement need tightening to prevent regressions.

---

## Findings (by risk)

1) Status validation not fully wired  
- Plan adds `VALID_STATUS` to config, but does not confirm generators/linters consume it. Without explicit use in `ontos_generate_context_map.py`/validators, invalid statuses will still pass silently. Ensure status checks read the new enum and add tests in both modes (incl. custom `DOCS_DIR`).

2) Stale detection brittle without git history  
- Stale lint relies on git last-modified; new/untracked proposals will yield no date and skip warning. Fall back to filesystem mtime or treat “no git date” as stale so first-run installs surface old drafts.

3) Rejected workflow unenforced  
- Entirely manual; nothing checks that `status: rejected` docs were moved to `archive/proposals/` or recorded in `decision_history.md`. Add lint: if `status: rejected` and path ≠ archive/proposals, warn/error; also require rejection metadata and a decision_history entry to keep rejections discoverable.

4) Orphan skipping hides bad dependencies  
- Blanket “skip orphan check for drafts” prevents noise but masks drafts that other docs depend on. Prefer: skip only if no other doc depends on the draft; if depended-on, enforce orphan/dependency validation.

5) Concepts template drift risk  
- Proposal doesn’t state that proposal templates reuse canonical `.ontos-internal/reference/Common_Concepts.md`. If templates diverge, tagging and linting fragment. Reuse the canonical source (or a single shared template) to keep vocab aligned.

6) Rejected visibility trade-off unresolved  
- Default exclusion from the context map makes past rejections harder to find; inclusion bloats tokens. Recommend: default exclude, add `--include-rejected` flag, and ensure `ontos_query.py` can surface rejected proposals by concept/slug to keep them discoverable without loading them every activation.

---

## Recommendations
- Wire status validation explicitly: use `VALID_STATUS` in generation/lint, add tests for valid/invalid statuses in contributor/user modes with custom `DOCS_DIR`.  
- Harden stale lint: git date || filesystem mtime; treat missing timestamp as stale to prompt triage.  
- Add lint for rejected docs: enforce location under `archive/proposals`, required rejection metadata, and presence of a decision_history entry.  
- Refine orphan handling for drafts: skip only when nothing depends on them; otherwise validate.  
- Use canonical Common_Concepts as the template source to avoid vocabulary drift.  
- Expose rejected discoverability via query flag/CLI option while keeping default map lean.
