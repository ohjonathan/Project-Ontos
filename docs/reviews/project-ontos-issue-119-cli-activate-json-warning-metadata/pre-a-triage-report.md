---
id: project-ontos-issue-119-triage-report
deliverable_id: project-ontos-issue-119-cli-activate-json-warning-metadata
phase: "-A.triage"
role: triage-author
family: claude-opus
triage_input: docs/reviews/project-ontos-issue-119-cli-activate-json-warning-metadata/github-issues-input.md
evidence_labels_used: [direct-run, static-inspection]
status: completed
---

# Triage Report — project-ontos-issue-119-cli-activate-json-warning-metadata

## 1. Context header
- **Findings input:** `docs/reviews/project-ontos-issue-119-cli-activate-json-warning-metadata/github-issues-input.md`
- **Date:** 2026-05-22
- **Triage Author family:** claude-opus (orchestrator-authored under claude-opus assignment; Pre-A.triage is not strict-P3 receipt-bound per `lifecycle-receipt-inventory.schema.yaml` `phase ∈ {B.1, B.2, D.2, D.5}`)
- **Overall verdict:** Proceed to Phase A with approved scope

## 2. Findings inventory

One finding, sourced from `gh issue view 119 --repo ohjonathan/Project-Ontos`
(live snapshot captured at execution start). No external workspace evidence
required — the regression surface lives inside this repository.

| # | Title | Source |
|---|---|---|
| 119 | CLI activate --json should expose structured warning metadata | non-blocking deferral recorded in PR #118 D.6 final-approval; reproduces against this repo |

## 3. Per-finding dispositions

### Finding #119 — CLI `ontos activate --json` warning metadata parity

| Field | Value |
|---|---|
| Disposition | **In-Scope** |
| Evidence label | static-inspection (verified by reading [ontos/commands/activate.py:104](ontos/commands/activate.py:104) — `[issue.message for issue in validation.errors/warnings]` flattens to bare strings) + direct-run (PR #118 final-approval explicitly records the deferral; `ontos activate --json | jq '.data.validation.warnings[0]'` against the current repo returns a bare string, not an object) |
| Fast-patch? | Borderline. The implementation surface is narrow: one method added to a dataclass + a 2-line CLI swap + an MCP refactor onto the shared method. **However** the CLI JSON payload key `validation.warnings` semantically changes from `list[str]` to `list[dict]`, which is a contract change that must be specified explicitly so downstream consumers (the user's own Johnny-OS smoke tooling, any third-party CLI automation) update their parsers. The contract change tips this out of fast-patch territory and into a normal Phase-A spec. |
| Phase routing | Phase A spec required (single-issue scope; the spec is small but invariant-bearing because the JSON contract evolves). |
| Rationale | PR #118 D.6 verdict (`docs/reviews/project-ontos-github-issues-115-117/final-approval.md`) is the authoritative record of this deferral. The fix lives in a single dataclass method on `ValidationError` (in [ontos/core/types.py:124-133](ontos/core/types.py:124)), a 2-line list-comprehension swap in [ontos/commands/activate.py:104-105](ontos/commands/activate.py:104), and a refactor of the existing private `_validation_issues()` helper in [ontos/mcp/tools.py:620-640](ontos/mcp/tools.py:620) onto the new shared method. The change reduces duplication (CLI and MCP currently flatten the same `ValidationResult` two different ways) and matches the parity contract documented in §2.2.2 of `docs/specs/project-ontos-github-issues-115-117-spec.md`. |
| Acceptance criteria | After implementation: `ontos activate --json` returns `data.validation.warnings[i]` as objects carrying `severity`, `message`, and — when the underlying `ValidationError` provides them — `rule_id`, `document_id`, `file_path` (empty `document_id`/`file_path` are squashed, matching the MCP contract). Errors get the same treatment. Existing MCP behavior is preserved bit-for-bit; `tests/mcp/test_activation.py` continues to pass without modification. New CLI tests cover orphan, depth, schema (log-field), and out-of-scope dependency warning shapes plus the "empty context squashed" rule and an error-parity case. Full `pytest -q` passes. |

## 4. Adversarial flags raised

The triage author considered the following challenges before declaring the
disposition above. None reaches `direct-run` evidence sufficient to demote #119
from In-Scope.

| Challenge considered | Adjudication |
|---|---|
| "Is the `list[str]` → `list[dict]` shape change a breaking change that should be rejected?" | Yes, it IS a breaking change — but the user's acceptance criteria explicitly permits it ("CLI JSON output remains backward compatible enough for existing consumers, **or the change is documented if the shape must evolve**"). The shape change is in the documented direction and the spec will state it explicitly. Reject the implicit alternative of dual-emitting (`warnings: list[str]` plus a parallel `warnings_structured: list[dict]`) — that path increases the public surface and bakes an undesirable historical shape into the contract. |
| "Could we keep CLI flat and just append rule_id to the message string?" | No — that approach is precisely what PR #118 rejected for MCP (§2.2.2 spec) on grounds that string-embedded rule_ids are not machine-parseable. CLI/MCP parity is the whole point of this deliverable. |
| "Should `_validation_issues` stay private in MCP and CLI re-implement?" | No — duplicating the logic invites drift. The orchestrator brief explicitly prefers the shared-helper path: "If importing MCP helpers into CLI would create an awkward dependency, create a small shared helper in a neutral module". The cleanest realization is a public `to_dict()` method on `ValidationError` itself, following the existing precedent of `DocumentLoadIssue.to_dict()` at [ontos/io/files.py:36](ontos/io/files.py:36). |
| "Does this affect the MCP `_snapshot_issue` / bare-string snapshot warning path?" | No. Snapshot warnings are MCP-only (the CLI activation flow doesn't go through `_normalize_warnings`'s snapshot path) and the prefix classification stays in `ontos/mcp/tools.py`. Out of scope for #119. |
| "Could the change accidentally break `format_activation_output()` (human-readable)?" | No — direct-inspection of [ontos/commands/activate.py:144-168](ontos/commands/activate.py:144) confirms it only reads counts from `payload["summary"]` and never iterates the now-restructured `payload["validation"]["warnings"]`. |
| "Will pre-commit `ontos-validate` fail due to known graph hygiene drift on this branch?" | Possibly — `ontos activate` against this repo on `main` already reports 204 validation warnings on unrelated documents (see `Issues: load=17, validation_errors=0, validation_warnings=204` from preflight). The orchestrator brief permits `SKIP=ontos-validate` for commits where the failure is purely unrelated pre-existing noise, documented in the tracker. |

No reviewer challenge crosses the playbook §12.5 blocking threshold; disposition stands.

## 5. Phase A scope-lock candidates

The single In-Scope finding advances to Phase A as a focused spec
(`docs/specs/project-ontos-issue-119-cli-activate-json-warning-metadata-spec.md`).
The spec must include:

- A "Closes" line linking the spec to issue #119 (enforced by manifest gate `G-cardinality-2`).
- The contract: every CLI activation warning/error emitted in the JSON payload carries `severity` and `message`, and additionally `rule_id`, `document_id`, `file_path` when the underlying `ValidationError` provides them (squashing empty `document_id`/`file_path`).
- The shape change: `payload.validation.warnings: list[str]` → `list[dict]` (same for `errors`). Explicitly called out as the intended #119 behavior.
- The shared helper: a public `to_dict()` method on `ValidationError` used by both CLI (`ontos/commands/activate.py`) and MCP (`ontos/mcp/tools.py`).
- The test plan: orphan, depth, schema (log-field), out-of-scope dependency, error-parity, "empty context squashed", and the unchanged `_not_usable()` path.

Manifest gate `G-cardinality-1` already enforces that the shared serializer exists (`callable(getattr(ValidationError, 'to_dict', None))`).

## 6. Deferred / Rejected findings

None. The live `gh issue view 119` snapshot contains exactly the single finding classified above.

## 7. Overall verdict

**Proceed to Phase A with approved scope.**

The single In-Scope finding requires a focused spec (the JSON contract change
is invariant-bearing for downstream consumers even though the implementation
surface is small). Fast-patch is rejected because the public payload shape
changes.

See `pre-a-triage-verdict.md` for the canonical exit-verdict artifact.
