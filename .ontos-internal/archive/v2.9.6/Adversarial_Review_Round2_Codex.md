---
id: v2_9_6_adversarial_review_round2_codex
type: strategy
status: draft
depends_on: [v2_9_6_implementation_specification]
concepts: [review, risk, YAGNI, validation]
---

# Adversarial Critic Review (Codex) — Round 2

**Reviewer:** Codex
**Spec:** `v2.9.6_Implementation_Specification.md`
**Review Round:** 2
**Stance:** Default to finding reasons NOT to proceed

## Verdict: REJECT

## Complexity Findings (REQUIRED)
- **Speculative Generality: Found** — `FieldDefinition` remains metadata without a proven consumer; the generator + `ontology_spec.md` is still a nonfunctional pipeline not wired into CI or runtime validation.
- **Resume-Driven Development: Found** — A new core module + generator + generated kernel doc is a three-part system for a constants move. The sys.path hack adds machinery instead of fixing packaging.
- **Premature Abstraction: Found** — Dataclasses are still converted back to dicts, so the abstraction does not reduce duplication; the “frozen” claim is undermined by mutable list fields.

## Attack Vectors
- **Immutability illusion:** `@dataclass(frozen=True)` does not prevent mutation of `List` fields. `valid_statuses` and `can_depend_on` can be mutated in-place, so the “prevents mutation” rationale is false.
- **Required-field mismatch:** `depends_on` is `required=True` with `applies_to` set. If validation treats `required` as global and ignores `applies_to`, logs will fail validation because they cannot have `depends_on`. The spec does not show how validation reads `FieldDefinition`.
- **Side-effect import fix:** The sys.path injection in `ontos_config_defaults.py` changes module resolution order and can mask packaging problems or cause shadowing.
- **Single-source claim is false:** Manual and Agent Instructions remain unchanged, so type/status definitions are still duplicated. Adding a new source does not consolidate existing ones.
- **“Implemented” status in a proposal:** The spec is marked `status: active` and claims “IMPLEMENTED,” which blurs review, spec, and verification boundaries. That’s an audit risk.

## Demanded Changes
1. Remove the doc generator and `ontology_spec.md` from v2.9.6; they add process complexity without runtime value.
2. If immutability is a goal, replace list fields with tuples (or drop dataclasses). Otherwise, remove the “frozen” rationale.
3. Remove the sys.path mutation; fix packaging/import paths explicitly or document a supported invocation path.
4. Either update Manual/Agent Instructions to match `ontology.py` or remove the “single source” success criterion.
5. Define how `FieldDefinition.applies_to` and `required` are interpreted by the validator, or drop `FieldDefinition` until a consumer exists.

## Residual Concerns
Even if the above deletions are made, parity is still asserted rather than demonstrated. The “verification script” is not a permanent test, and the intentional behavior changes (`auto-generated`, `scaffold`, `pending_curation`) are justified verbally but not tied to failing tests or a documented bug. The “implemented” claim in a draft proposal remains a governance risk.
