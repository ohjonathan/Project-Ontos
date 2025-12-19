---
id: codex_v2_7_phil_review_v1
type: strategy
status: complete
depends_on: []
concepts: [documentation, ontology, bidirectional, verification, triggers]
---

# Codex Review — v2.7 Documentation Ontology (Philosophy)

Date: 2025-12-18  
Author: Codex (technical co-founder lens)  
Scope: Philosophical review of `v2.7_documentation_ontology` prior to implementation proposal

---

## 1) Evaluation of the Current Philosophy

- **Strong core model:** Treating user-facing docs as “second-order atoms” and introducing `documents` (doc → atom) with a computed `documented_by` inverse is the right semantic split from `depends_on`.
- **Source-of-truth clarity needed:** Proposal hints at “frontmatter + manifest.” We should pick one canonical source (frontmatter) and treat any manifest as generated to avoid drift.
- **Trigger design is sensible but noisy risk:** Version bump as primary trigger is good; Archive Ontos / push as fallback for non-versioned projects could spam without filters.
- **Bidirectionality stance is correct:** Single declaration with computed inverse avoids dual maintenance; we should define conflict handling if other sources ever appear.
- **Doc hierarchy assumption:** Keeping user-facing docs as peers is fine; allow cross-references without implying dependency chains.
- **Coverage semantics:** Encouraging over-specification is good, but we should clarify partial coverage vs completeness to avoid false confidence.
- **Section-level tracking:** Valuable but high complexity; start at document-level to keep the ontology stable.
- **Verification gap:** No clear path for “doc reviewed and still current” after an atom changes; relying on mtime would be brittle.
- **Identity & churn:** Needs an explicit stance that `documents` targets stable IDs; renames require an intentional migration step.

## 2) What I Would Do Differently (Philosophically)

- **Canonize frontmatter as the only source:** Docs declare `documents`; context map derives `documented_by`. Any manifest is generated, never hand-edited.
- **Minimal v2.7 surface:** Ship document-level `documents`, version-bump trigger, Archive Ontos fallback as warning-only, and a lightweight verification flag (`doc_verified_at`, optional `verified_by`).
- **Type discipline:** Keep docs as `type: atom` but tag with a concept like `documentation` to distinguish from code atoms in tooling.
- **Noise controls:** Trigger only when changed atoms have ≥1 inbound `documented_by`; optionally ignore files marked `documents: []` to avoid false positives.
- **Naming discipline:** Use `documents` (verb) and `documented_by` (derived noun); forbid dual declaration or mixing with `depends_on`.
- **Defensive defaults:** If a doc lists an unknown atom ID, fail generation; if an atom has docs but no versioning, warn but do not block by default.

## 3) Technical/Workload Implications (If Implemented Later)

- **Schema/validation:** Allow `documents` on doc atoms; validate IDs exist, types are permitted, and no cycles with `depends_on`. Treat `documents` as doc→atom only.
- **Context map updates:** Compute and surface `documented_by`; lint unknown IDs and orphaned links; render staleness candidates (atom newer than doc unless verified).
- **Hooks / Archive Ontos:** Add staleness checks at version bump and Archive Ontos; honor `doc_verified_at` to suppress repeated prompts; warning-only by default to limit friction.
- **Docs & instructions:** Update Ontos Manual and Agent Instructions to define `documents`, verification workflow, and expected triggers.
- **Migration pass:** Add `documents` to Ontos Manual, README, Agent Instructions once schema lands; optional backfill for other user-facing docs.

## 4) Recommendations Before Moving to Implementation Proposal

- Decide **single source of truth** (frontmatter) and declare manifests as generated artifacts.
- Lock **verification semantics**: adopt `doc_verified_at` (+ optional `verified_by`) instead of relying on file mtimes.
- Start **document-level only**; defer section-level until we see real-world need and can enforce structured anchors.
- Define **identity/rename policy**: IDs are stable; renames require updating `documents` references via a migration step.
- Keep **triggers scoped**: version bump primary; Archive Ontos/push as warning-only fallback with filters to avoid noise.

If we align on the above, I’d support drafting the v2.7 implementation proposal with a minimal, low-noise surface and clear verification workflow.
