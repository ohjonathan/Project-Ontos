---
id: project-ontos-issue-119-B.3-verdict
deliverable_id: project-ontos-issue-119-cli-activate-json-warning-metadata
phase: B.3
role: meta-consolidator
family: claude-sonnet
status: completed
---

# B.3 Meta-Consolidation — claude-sonnet

## Verdict

Concur

## Summary

B.1's three-lens board (codex peer / claude-sonnet alignment / gemini adversarial) reviewed the Phase A spec. One blocker-grade finding landed (gemini F1: `_validation_issues` type hint should be `list[ValidationError]`, not `list[Any]`, to make the homogeneity contract explicit). The blocker is closed in the same spec by tightening §1.3.3's type hint and adding a comment justifying the contract — no implementation change required because the input was already homogeneous; gemini correctly flagged that the implicit contract was load-bearing and should be made explicit.

Three should-fix / nit findings also addressed by spec amendment before advancing to C: codex F1 (tighten test fixtures against actual validator behavior — orphan needs non-allowed-orphan type, schema better via log fields, error-parity via synthetic/cycle), codex F2 (release-note wording — the "exactly three files" claim now reads "runtime implementation surface" and documents the docs/releases touchpoint), and sonnet F1 (mandate the CLI/MCP parity assertion as Case 8 instead of optional "can include"). All four amendments live inside §1.3.3, §1.3.4, and §1.4.1 of the spec — no scope change.

## Blocker closure summary

| Lens | Finding | Disposition | Where |
|---|---|---|---|
| gemini | F1 (§1.3.3 `_validation_issues` type hint = `list[Any]` masks the homogeneity contract) | **Closed** — spec §1.3.3 now declares `list[ValidationError]` and adds a comment citing the two call sites (`_normalize_warnings`, `_validation_payload`) that pass `validation.errors` / `validation.warnings` (both `List[ValidationError]`). The wire format is unchanged. | spec §1.3.3 |

## Should-fix closures (B.3 inline, no separate fix-summary needed pre-C)

| Lens | Finding | Disposition |
|---|---|---|
| codex | F1 (test plan under-specified vs validator behavior) | **Closed** — spec §1.4.1 cases 1/3/6 now name concrete fixtures: orphan uses a non-allowed-orphan type + `allowed_orphan_types: []` override; schema uses a log doc missing required fields; error-parity uses a synthetic injected `ValidationError(severity="error", ...)` or a cycle-creating fixture (whichever the validator naturally emits with `error` severity). |
| codex | F2 (release-note requirement conflicts with "exactly three files") | **Closed** — spec §1.3.4 splits "runtime implementation surface" (three files) from "documentation surface" (spec, PR body, `docs/releases/`); the release-note bullet is explicitly within scope. |
| claude-sonnet | F1 (parity assertion is advisory `can include`, leaves §0 bit-identical invariant without direct regression coverage) | **Closed** — spec §1.4.1 promotes the parity assertion to Case 8 (`Mandatory`) and specifies the exact assertion shape (CLI and MCP serialization of the same `ValidationResult` yield identical lists). |

## Preserved nits (carried into D.2 for re-verification against landed code)

None blocker-grade. The B.1 board's nit-level findings are absorbed into the C-phase implementation by reading the amended spec; D.2 will re-verify the implementation honors them.

## Phase advance

B.3 endorses advance to **Phase C (implementation)**. The blocker is closed in the spec; all should-fix / nit items are absorbed by the C-author working from the amended spec. D.2 will re-apply the three-lens board against the landed implementation.

Next gates:
- `scripts/llm-dev verify manifests/project-ontos-issue-119-cli-activate-json-warning-metadata.yaml` — re-run after spec amendments; expected PASS (G-cardinality-2 still has 10 `#119` mentions in the spec).
- C-phase smoke check: `.venv/bin/python -m pytest -q tests/commands/test_activate_json_warning_metadata.py tests/commands/test_agentic_activation_resilience.py tests/mcp/test_activation.py tests/mcp/test_context_map.py` — must pass before D.1.

## Sources

- `docs/reviews/project-ontos-issue-119-cli-activate-json-warning-metadata/B.1-codex-peer.md`
- `docs/reviews/project-ontos-issue-119-cli-activate-json-warning-metadata/B.1-claude-sonnet-alignment.md`
- `docs/reviews/project-ontos-issue-119-cli-activate-json-warning-metadata/B.1-gemini-adversarial.md`
- Spec amendments live in `docs/specs/project-ontos-issue-119-cli-activate-json-warning-metadata-spec.md` §1.3.3, §1.3.4, §1.4.1.
