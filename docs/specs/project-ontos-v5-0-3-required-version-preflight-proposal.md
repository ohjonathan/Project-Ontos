---
id: project_ontos_v5_0_3_required_version_preflight_proposal
type: spec
status: proposed
created: 2026-07-15
owner: Project Ontos Maintainers
depends_on:
  - project_ontos_v5_remediation_release_plan_proposal
concepts:
  - proposals
  - release
  - config
  - schema
  - mcp
  - testing
---

# Project Ontos v5.0.3 Required-Version Preflight Proposal

## 1. Decision Requested

Approve this narrow child to proceed to Phase A for a scope-locked
specification. The child changes only which existing configuration error wins
when an older-but-preflight-aware v5 runtime opens a workspace that declares a
newer Ontos requirement and also contains configuration it cannot understand.

This governance PR does not authorize implementation, accept any v5.1
configuration, or certify the child through Phase A–E.

Requested Template 16 disposition: **Proceed to Phase A**.

## 2. Authority and Evidence

The accepted parent release-plan proposal assigns v5.0.3 one bounded downgrade
preflight in §11.5 and makes it a prerequisite to shipping v5.1-only
configuration. The review baseline is
`main@bd04620376ed6a8d0024e990e04a86da402b9398`.

Direct inspection of the current code establishes that:

- `ontos/io/config.py::load_project_config()` parses `.ontos.toml` through the
  shared TOML loader and then calls `dict_to_config()`;
- `ontos/core/config.py::dict_to_config()` rejects unknown top-level sections
  before callers can evaluate the configured runtime requirement;
- `version_satisfies_requirement()` already defines the public comparison,
  comma-clause, tilde, and wildcard semantics;
- `required_version_incompatibility()` and
  `format_invalid_required_version()` already define actionable diagnostics;
- CLI commands and MCP server/cache paths already converge on
  `load_project_config()`, although their presentation envelopes differ; and
- config loading is read-only.

Issue [#178](https://github.com/ohjonathan/Project-Ontos/issues/178) retains
custody. This child owns only the downgrade-safety/error-precedence slice.

## 3. Problem and Product Value

An adopter may correctly raise `[ontos].required_version` before enabling a
v5.1-only section. A v5.0.3 runtime does not understand that later section. If
strict unknown-section validation fires before the runtime requirement is
checked, the user receives an incidental schema error rather than the actionable
instruction to use a compatible Ontos version.

The desired product behavior is not forward parsing. It is deterministic error
precedence: a declared incompatibility or malformed requirement should be
reported before unrelated unknown-section errors, while absent or compatible
requirements preserve today's strict rejection behavior.

## 4. Goals

- Inspect only `[ontos].required_version` before ordinary strict schema
  conversion.
- Reuse the existing TOML load and existing range evaluator.
- Return one deterministic invalid/incompatible result before unknown v5.1
  section or field errors when applicable.
- Preserve the existing strict loader for absent and compatible requirements.
- Make CLI and MCP configuration-loading paths consume the same preflight
  decision.
- Preserve existing exit/status envelopes except for the intended reason
  precedence.
- Add a focused four-case matrix plus cross-surface parity tests.

## 5. Non-Goals

- No parsing, acceptance, defaulting, validation, or rewriting of a v5.1-only
  section or key.
- No second TOML parser, regex extraction of TOML, or duplicate semver/range
  implementation.
- No weakening of unknown-section or unknown-key validation.
- No mutation of `.ontos.toml`, generated files, locks, Git state, or caches.
- No general compatibility negotiation protocol.
- No full workspace-vocabulary configuration or migration implementation.
- No closure of #178.

## 6. Owned, Composed, and Forbidden Scope

### 6.1 Owned implementation surface

- `ontos/io/config.py` for the one shared preflight placement;
- `ontos/core/config.py` only if Phase A requires a small pure helper that
  delegates to the existing range and diagnostic functions;
- `tests/io/test_config_phase3.py` for the authoritative behavior matrix;
- focused CLI and MCP tests proving shared behavior; and
- `docs/reference/Ontos_Manual.md` for downgrade/error-precedence guidance.

The child also owns its proposal, future Phase A spec, tracker, manifest,
review packet, and retrospective.

### 6.2 Composed authority

The child reads but does not own
`docs/specs/project-ontos-v5-remediation-release-plan-proposal.md`. The parent
defines the exact compatibility boundary and keeps full #178 delivery in v5.1.

### 6.3 Forbidden sibling scope

The child must not modify enum repairs, vocabulary models, canonical document
types/statuses, command-specific or MCP-specific alternative parsers, the TOML
parser, dependency resolution, log paths, or another v5.0.3 child.

## 7. Proposed Contract

### 7.1 One parse and one bounded preflight

1. Locate and read `.ontos.toml` through the existing configuration I/O path.
2. Parse the TOML exactly once with the existing TOML loader.
3. Before legacy normalization or strict section/key validation, inspect only
   whether the parsed root contains table `[ontos]` and key
   `required_version`.
4. Validate that field's type and range through the existing required-version
   functions. Do not interpret any sibling key or any other section.
5. If the preflight returns no reason, pass the same parsed mapping to the
   unchanged strict conversion path. Never re-read or re-parse the file.

Malformed TOML syntax remains the existing parse error because no safe parsed
mapping exists. “Malformed requirement” below means a parsed
`required_version` value with the wrong type or invalid existing range syntax.

### 7.2 Exact behavior matrix

| Case | Requirement state | Later unknown section/field present | Required result |
|---|---|---|---|
| RV-1 | absent | yes or no | Continue to the existing strict loader; unknown configuration still fails normally |
| RV-2 | compatible with the running version | yes or no | Continue to the existing strict loader; compatibility is not permission to accept later schema |
| RV-3 | incompatible with the running version | yes or no | Stop with the existing actionable incompatibility diagnostic before any unknown-section/key diagnostic |
| RV-4 | malformed type or range | yes or no | Stop with the existing deterministic invalid-required-version diagnostic before any unknown-section/key diagnostic |

### 7.3 Shared CLI and MCP behavior

The preflight belongs in the shared configuration load path. CLI and MCP callers
must not independently extract, parse, compare, or format the requirement. Tests
must show that both surfaces identify the same semantic reason and leave
activation/session state unusable when the requirement blocks loading. Their
existing transport envelopes may differ, but neither may substitute an unknown
v5.1-section error for the higher-priority requirement result.

### 7.4 No acceptance side effect

A compatible requirement proves only that the current runtime satisfies the
declared range. It does not prove the runtime understands every table in the
file. Strict schema validation therefore always follows RV-1 and RV-2 and
retains every current unknown-section/key rejection.

## 8. Issue Custody and Dependencies

- #178 remains open after this child ships.
- Completion records only the downgrade/error-precedence checklist item.
- The child must ship before adopters are told to commit v5.1 vocabulary
  sections guarded by a raised required-version range.
- It is independently reversible from the alias, dependency, and log-path
  children.
- This child owns its code, tests, and manual update through merge-readiness.
  Version bumping, packaging, TestPyPI/PyPI publication, and the final v5.0.3
  release decision remain with Project Ontos Maintainers under the existing
  release process after all four v5.0.3 children complete; no unscaffolded
  integration child is implied.

## 9. Safety and Rollback

The preflight is pure and read-only. It must not write the config, generate
artifacts, initialize MCP session state, or leave lock/cache files when it
rejects loading. Error paths must be deterministic regardless of mapping order
in the TOML source.

Rollback is a focused revert of the shared preflight and its tests. Because the
child never accepts or rewrites later configuration, rollback requires no data
migration. Older behavior may return the less useful unknown-section error, but
no workspace bytes change.

## 10. Acceptance Outline for Phase A

Phase A must produce executable, source-anchored criteria covering:

| Area | Required evidence |
|---|---|
| Single parse | Instrumented test proves one existing TOML parse and no regex/second-parser path |
| Four cases | RV-1 through RV-4 with and without a representative unknown v5.1 section/key |
| Existing semantics | Comparator, comma, tilde, wildcard, empty, and malformed range behavior is reused unchanged |
| Strictness | Compatible and absent requirements never suppress unknown-section/key errors |
| Precedence | Invalid/incompatible requirement reasons win deterministically over unknown later schema |
| CLI/MCP parity | Both surfaces consume the same shared decision and report equivalent semantic reasons |
| Purity | All success and failure cases leave config, generated artifacts, locks, caches, and Git state unchanged |
| Custody | #178 records only this slice and stays open |

## 11. Categorized Unknowns

### 11.1 `must-resolve-pre-A`

None. The product problem, exact precedence matrix, centralization boundary, and
non-acceptance invariant are sufficient for a specification pass.

### 11.2 `resolve-during-A`

- Choose the smallest pure helper signature and exact placement between the
  existing TOML load and strict conversion.
- Freeze error/exit mapping for wrong-type requirements across CLI and MCP while
  retaining current public envelopes.
- Identify the representative unknown v5.1 section and key fixtures without
  prematurely defining the full v5.1 schema.
- Define how tests prove a single parse and zero writes without coupling to
  private implementation details unnecessarily.
- Determine whether `None` or empty-string compatibility remains reachable only
  after type handling, and pin that behavior to the current public contract.

### 11.3 `defer`

- Vocabulary tables, aliases, extensions, frozen paths, receipts, and all other
  v5.1 configuration semantics defer to the full #178 children.
- Cross-version schema negotiation beyond actionable required-version
  precedence is not part of this patch.

## 12. Review Questions

### 12.1 Product lens

1. Does the incompatibility-first message give downgraded/mixed-version users
   the most actionable next step without suggesting that v5.0.3 supports v5.1?
2. Is preserving strict errors for compatible and absent requirements clear
   enough to avoid a false promise of forward compatibility?
3. Are wrong-type and malformed-range messages understandable without exposing
   internal parser details?
4. Is the #178 custody handoff explicit enough that users will not read this
   patch as workspace-vocabulary delivery?

### 12.2 Technical lens

1. Can the existing parsed TOML mapping be inspected and then passed unchanged
   to strict conversion, proving a single parser and single read?
2. Are existing required-version functions pure and complete enough to be the
   only range authority?
3. Do all relevant CLI and MCP startup/load paths actually converge on the
   shared loader, or must Phase A name a bounded parity adapter?
4. Can tests prove deterministic precedence independent of TOML table order and
   without weakening syntax errors?

## 13. Exact Template 16 Verdict Set

The non-author GLM reviewer must select exactly one:

- **Proceed to Phase A** — direction and boundary are ready for a detailed
  specification;
- **Revise and re-review** — amend this proposal and repeat Pre-A review;
- **Split into multiple proposals** — split again and send every resulting
  child through Pre-A; or
- **Abandon direction** — stop this child and record why.

No abbreviated verdict is valid lifecycle evidence.

## 14. Recommendation

Return **Proceed to Phase A**. This child fixes an observable downgrade failure
without implementing forward parsing or weakening strict validation. Phase A
should freeze the single-parse placement, four-case matrix, cross-surface reason
parity, and purity gates before any production edit begins.
