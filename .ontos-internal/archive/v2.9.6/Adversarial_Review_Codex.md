---
id: v2_9_6_adversarial_review_codex
type: strategy
status: draft
depends_on: [v2_9_6_implementation_specification]
concepts: [review, risk, YAGNI, validation]
---

# Adversarial Critic Review (Codex)

**Reviewer:** Codex
**Spec:** `v2.9.6_Implementation_Specification.md`
**Stance:** Default to finding reasons NOT to proceed

## Verdict: REJECT

## Complexity Findings (REQUIRED)
- **Speculative Generality: Found** — `ValidationRule` is pure metadata without runtime consumption; generator emits data with no validation linkage. The new kernel doc is also generated but not integrated into any workflows, making it doc churn without utility.
- **Resume-Driven Development: Found** — A new ontology module + a generator + a generated kernel doc is a three-artifact pipeline for a constants move. This is a heavier process than the problem requires.
- **Premature Abstraction: Found** — Dataclasses are introduced, then immediately converted back into dicts in `ontos_config_defaults.py`. This is extra indirection with compatibility risk and no functional gain.

## Attack Vectors
- **Backward-compat break:** The conversion of `TYPE_DEFINITIONS` uses `allows_depends_on: not td.uses_impacts`, which is not equivalent to the existing semantics (which are based on allowed dependencies). This can change validation logic silently.
- **Status mismatch risk:** The `valid_statuses` per type are hand-authored with no evidence of parity. For example, `strategy` has `rejected`, but `product/atom` omit it while global `status` enum includes it. If current data uses it, validation changes.
- **Type enum contradiction:** The spec says scaffolds can use `type: unknown` but the enum forbids it. That is an immediate inconsistency between assumptions and enforcement.
- **Generator path coupling:** The generator assumes project root via `script_dir.parent.parent`. This hardcodes layout; no test asserts correctness when run from different working directories.

## Demanded Changes
1. **Delete `ValidationRule` and `VALIDATION_RULES`** until they drive actual validation logic. Doc-only metadata is not justified in v2.9.6.
2. **Delete `ontos_generate_ontology_spec.py` and the generated `ontology_spec.md`** from v2.9.6. Reintroduce when the project consumes it.
3. **Delete dataclasses**; keep plain dicts in `ontology.py` to avoid unnecessary type conversion and compatibility risk.
4. **Remove `allows_depends_on` derivation from `uses_impacts`**; preserve exact current dict shape and semantics.
5. **Resolve the `type: unknown` contradiction** by either removing the assumption or adding `unknown` to valid values.

## Residual Concerns
Even if the above deletions are made, the spec still lacks a rigorous parity check. “Zero behavior change” is asserted but not proven. There is no explicit snapshot of current ontology values nor golden tests defined. Without a formal before/after diff of types/statuses/fields and a well-defined golden test fixture, this is a regression risk. The acceptance tests also mention comparing to a “golden master” that does not exist. I would still block until parity is demonstrated.
