# B.1 peer review — `project-ontos-issue-119-cli-activate-json-warning-metadata`

You are the **Peer Review** on Phase B.1 of deliverable `project-ontos-issue-119-cli-activate-json-warning-metadata` for repo `ohjonathan/Project-Ontos`. Family: `codex`.

Peer reviewer (lens: 'Is this good?'). Check design quality, completeness, implementability, prose-diagram alignment, test strategy. Do NOT duplicate Alignment (compliance with prior decisions) or Adversarial (hostile inputs).

Phase B.1 reviews the SPEC ARTIFACT before implementation. Validate the spec; do not review code.

## Strict-P3 verdict shape (MANDATORY)

Your stdout response IS the verdict artifact. Output ONLY the verdict markdown — no preamble, no closing notes. The very first three characters of your response MUST be `---` (a YAML frontmatter open fence). Do NOT begin your response with any prose, narration, status update like "I have enough information to ..." or "Here is the verdict ...", planning notes, or markdown commentary. The wrapper's verdict-shape predicate rejects any output that does not begin with `---`.

Stdout must begin with the literal three-dash YAML frontmatter open fence `---` followed by a newline. Do NOT output a bare `-` or `--`; only `---` is a valid opening fence.

The verdict MUST contain ALL of:

1. YAML frontmatter fenced by `---` lines with these keys (non-empty strings):
   - `phase: B.1`
   - `role: peer`
   - `family: codex`
   - `deliverable_id: project-ontos-issue-119-cli-activate-json-warning-metadata`
   - `status: completed`
2. At least one ATX `#` heading after the frontmatter.
3. A `## Verdict` heading.
4. The first non-blank line beneath `## Verdict` is EXACTLY ONE of:
   - `Approve` — no blocking findings.
   - `Request changes` — at least one blocker.
   - `Reject` — the artifact is fundamentally broken.
   - `Concur` — used by meta-consolidators only.

After the verdict line, add a `## Findings` section with one entry per finding. Each finding has Severity (`blocker` | `should-fix` | `nit`), Evidence (`direct-run` | `static-inspection` | `not-run`), Where, Issue, Recommendation.

## Exact output skeleton

```markdown
---
id: project-ontos-issue-119-B.1-codex-peer
deliverable_id: project-ontos-issue-119-cli-activate-json-warning-metadata
phase: B.1
role: peer
family: codex
status: complete
---

# B.1 Peer Review — codex

## Verdict

Approve

## Summary

<1-2 sentence overall judgement.>

## Findings

### [F1] <Short title>
- **Severity:** blocker | should-fix | nit
- **Evidence:** direct-run | static-inspection
- **Where:** <file:line or spec section>
- **Issue:** <what is wrong or missing>
- **Recommendation:** <concrete change>

### [F2] ... (repeat as needed; omit section if no findings)

## Notes
<Any final notes; can be empty.>
```

Be honest. If you find no blocking issues, write `Approve` and explain your scrutiny under Findings or Notes. If you find blockers, write `Request changes` and itemize each blocker.

## Artifact under review

```markdown
---
id: project-ontos-issue-119-cli-activate-json-warning-metadata-spec
deliverable_id: project-ontos-issue-119-cli-activate-json-warning-metadata
type: atom
status: active
phase: A
role: spec-author
family: claude-opus
depends_on:
  - ontos_manual
  - ontology_spec
  - ontos_agent_instructions
  - project-ontos-github-issues-115-117-spec
---

# Spec — project-ontos-issue-119-cli-activate-json-warning-metadata

This spec covers one open GitHub issue against `ohjonathan/Project-Ontos`:

- **Closes #119** — `ontos activate --json` should expose structured warning metadata (`severity`, `rule_id`, `message`, `document_id`, `file_path`), matching the MCP enrichment that landed in PR #118 / v4.5.0.

The Pre-A triage report classified #119 as **In-Scope** with `direct-run` evidence (PR #118 D.6 final-approval explicitly recorded the deferral) plus `static-inspection` of the current `ontos/commands/activate.py` flattening. See `docs/reviews/project-ontos-issue-119-cli-activate-json-warning-metadata/pre-a-triage-report.md`.

This deliverable is a **focused follow-up** to deliverable `project-ontos-github-issues-115-117`. The parity contract was specified there in §2.2.2 (MCP side); this spec carries that contract forward to the CLI side and consolidates the shared serialization logic onto the `ValidationError` dataclass itself.

## 0. Cross-cutting invariants

- MCP behavior is preserved bit-for-bit. The existing `_validation_issues` shape — `{severity, message, rule_id?, document_id?, file_path?}` with empty `document_id`/`file_path` squashed — remains the exact wire format MCP emits. `tests/mcp/test_activation.py` must pass without modification.
- The MCP success schema (`ValidationIssue` at `ontos/mcp/schemas.py:16-27`) is unchanged. `additionalProperties: false` and the optional-context-field invariant from §2.2.2 of the prior spec are preserved.
- The `ontos activate` human-readable output (the non-`--json` path through `format_activation_output()` at `ontos/commands/activate.py:144-168`) is **untouched**. It only consumes `payload["summary"]` counts and never iterates the restructured `payload["validation"]` lists.
- MCP-only behavior (`_snapshot_issue()`, `_SNAPSHOT_RULE_PREFIXES` at `ontos/mcp/tools.py:643-671`) is preserved. CLI activation has no snapshot warning channel; the prefix classification stays MCP-side.
- The `_not_usable()` path at `ontos/commands/activate.py:181-205` continues to emit empty `validation.errors` and `validation.warnings` lists — its semantics are unaffected by the element-shape change.
- Conservative repair behavior elsewhere in the codebase (e.g., `DocumentType.UNKNOWN` fallback, `original_value` preservation) is **out of scope** and must not be modified.
- `verify-lifecycle.sh --mode strict-p3 manifests/project-ontos-issue-119-cli-activate-json-warning-metadata.yaml` must pass at D.6.

## 1. Issue #119 — CLI `ontos activate --json` warning metadata parity

### 1.1 Current behavior

[ontos/commands/activate.py:96-105](ontos/commands/activate.py:96) constructs the validation portion of the activation JSON payload by **flattening** each `ValidationError` instance to just its `.message`:

```python
validation_errors = []
validation_warnings = []
if docs:
    content, validation = generate_context_map(
        docs,
        gen_config,
        GenerateMapOptions(max_dependency_depth=config.validation.max_dependency_depth),
    )
    validation_errors = [issue.message for issue in validation.errors]
    validation_warnings = [issue.message for issue in validation.warnings]
```

The resulting JSON payload at [ontos/commands/activate.py:114-140](ontos/commands/activate.py:114) emits:

```json
{
  "validation": {
    "errors":   ["message text", ...],
    "warnings": ["message text", ...]
  }
}
```

In contrast, the MCP `activate` tool — which consumes the same `ValidationResult` (loaded from the cache snapshot in `ontos/mcp/tools.py`) — runs each `ValidationError` through the private `_validation_issues()` helper at [ontos/mcp/tools.py:620-640](ontos/mcp/tools.py:620), producing the enriched dict shape specified in §2.2.2 of the prior deliverable:

```json
{
  "severity": "warning",
  "rule_id": "orphan",
  "message": "Document has no incoming dependencies",
  "document_id": "model_a_bronze_sourcepacket_review",
  "file_path": "docs/reviews/model_a_bronze_sourcepacket_review.md"
}
```

CLI automation that wants to triage by rule, document, or path must therefore either re-parse the message string (brittle) or duplicate the MCP call (wasteful). PR #118 D.6 final-approval explicitly recorded this CLI/MCP consistency gap as a non-blocking deferral — that deferral is the entire scope of #119.

### 1.2 Contract

Every CLI activation warning and error emitted in the JSON payload carries the same enriched shape MCP already produces:

```json
{
  "severity": "warning|error",
  "message": "human-readable text",
  "rule_id": "orphan|depth|schema|broken_link|out_of_scope_dependency|...",
  "document_id": "doc-id-when-known",
  "file_path": "docs/path/to/file.md"
}
```

Field rules (identical to MCP):

| Field | Rule |
|---|---|
| `severity` | always present; verbatim copy of `ValidationError.severity` (`"error"` / `"warning"` / `"info"`). |
| `message` | always present; verbatim copy of `ValidationError.message`. |
| `rule_id` | present when `ValidationError.error_type` is set; the value is `error_type.value` from `ValidationErrorType` (e.g. `"orphan"`, `"depth"`, `"schema"`, `"broken_link"`, `"out_of_scope_dependency"`). Absent when `error_type` is falsy. |
| `document_id` | present when `ValidationError.doc_id` is a non-empty string. Empty / missing `doc_id` → field absent (squashed). |
| `file_path` | present when `ValidationError.filepath` is a non-empty string. Empty / missing `filepath` → field absent (squashed). |

The squashing rule keeps the public payload compact and matches the MCP contract bit-for-bit, so CLI consumers and MCP consumers see identical record shapes for the same underlying `ValidationError`.

#### 1.2.1 Schema break (intentional)

The `validation.errors` and `validation.warnings` keys retain their names and their position in the payload, but their **element shape changes from `str` to `dict`**:

| Before (`ontos<=4.5.0`) | After (this deliverable) |
|---|---|
| `payload.data.validation.warnings: list[str]` | `payload.data.validation.warnings: list[dict]` |
| `payload.data.validation.errors: list[str]` | `payload.data.validation.errors: list[dict]` |

This is a **deliberate breaking change** to the CLI JSON contract. The Pre-A triage adjudicated this against the alternative of dual-emitting (a `warnings_structured` sibling key) and rejected the alternative on the grounds that it bakes an undesirable historical shape into the contract. Downstream consumers — including the user's Johnny-OS smoke tooling — must update their parsers.

The change is called out:

- in this spec (here, §1.2.1),
- in the PR body when #119 lands,
- in the next release note under `docs/releases/` if a release notes directory is in use (verify at C-phase via `ls docs/releases/`).

The unchanged top-level envelope (`status`, `code`, `message`, `data` wrapper from `ontos/ui/json_output.py`) means CLI consumers that already JSON-decode the response keep working — only the inner `validation.errors[i]` / `validation.warnings[i]` element type changes.

### 1.3 Implementation

#### 1.3.1 Shared serialization on the dataclass

Add a public `to_dict()` method to `ValidationError` in [ontos/core/types.py:124-133](ontos/core/types.py:124). This follows the existing pattern set by `DocumentLoadIssue.to_dict()` at [ontos/io/files.py:36](ontos/io/files.py:36) (which CLI already calls via `[issue.to_dict(root=project_root) for issue in load_result.issues]` in `activate.py:125`):

```python
# ontos/core/types.py — added to @dataclass ValidationError
def to_dict(self) -> Dict[str, Any]:
    record: Dict[str, Any] = {"severity": self.severity, "message": self.message}
    rule_id = getattr(self.error_type, "value", None) if self.error_type else None
    if rule_id:
        record["rule_id"] = rule_id
    if self.doc_id:
        record["document_id"] = self.doc_id
    if self.filepath:
        record["file_path"] = self.filepath
    return record
```

The field mapping (`doc_id` → `document_id`, `filepath` → `file_path`) preserves the public-facing key names already established by the MCP `_validation_issues` helper, while the internal dataclass fields keep their existing names. The empty-string squashing rule lives on the dataclass itself so both call sites get it for free.

#### 1.3.2 CLI consumer

Replace the flattening at [ontos/commands/activate.py:104-105](ontos/commands/activate.py:104):

```python
# Before
validation_errors = [issue.message for issue in validation.errors]
validation_warnings = [issue.message for issue in validation.warnings]

# After
validation_errors = [issue.to_dict() for issue in validation.errors]
validation_warnings = [issue.to_dict() for issue in validation.warnings]
```

No other line in `ontos/commands/activate.py` requires changes — the payload assembly at lines 114-140 keeps its existing structure, and `format_activation_output()` (lines 144-168) never touches these lists.

#### 1.3.3 MCP consumer (refactor onto the shared method)

Refactor `_validation_issues()` in [ontos/mcp/tools.py:620-640](ontos/mcp/tools.py:620) to use the new dataclass method:

```python
def _validation_issues(issues: list[Any]) -> list[dict[str, Any]]:
    # (#119) Reuse ValidationError.to_dict() so CLI + MCP share the
    # exact same serialization. Snapshot bare strings still use
    # _snapshot_issue() (MCP-only).
    return [issue.to_dict() for issue in issues]
```

`_normalize_warnings()`, `_validation_payload()`, `_snapshot_issue()`, and `_SNAPSHOT_RULE_PREFIXES` are unchanged. The MCP `ValidationIssue` schema (`ontos/mcp/schemas.py:16-27`) is unchanged — the wire format produced by `to_dict()` is bit-identical to the prior `_validation_issues` output, so the schema validation continues to pass.

#### 1.3.4 No other modules touched

The implementation surface is exactly three files:

- `ontos/core/types.py` (one method added)
- `ontos/commands/activate.py` (two lines swapped)
- `ontos/mcp/tools.py` (one helper body collapsed)

Plus the test surface in §1.4.

### 1.4 Tests

#### 1.4.1 New CLI test file — `tests/commands/test_activate_json_warning_metadata.py`

Build temp workspaces using the same pattern as [tests/commands/test_agentic_activation_resilience.py](tests/commands/test_agentic_activation_resilience.py), invoke `ontos --json activate` (or call `activate_command` / `run_activation` directly), parse the JSON envelope, and assert on the structured payload. Required cases:

| # | Case | Assertions |
|---|---|---|
| 1 | **Orphan warning** | One doc with `depends_on: []` and no other doc referencing it. `validation.warnings` contains one record with `rule_id == "orphan"`, `severity == "warning"`, populated `document_id`, populated `file_path`, and a non-empty `message`. |
| 2 | **Depth warning** | A `depends_on` chain that exceeds `max_dependency_depth`. `validation.warnings` contains a record with `rule_id == "depth"`, populated `document_id` / `file_path`. |
| 3 | **Schema warning** | A doc with invalid `type:` or `status:` (or missing required fields). `validation.warnings` (or `.errors`, depending on severity in the validator) contains a record with `rule_id == "schema"` and populated `document_id` / `file_path`. *(Note: finer-grained snapshot rule_ids like `schema.log_missing_fields` are MCP-only by design and out of scope; CLI reports the structured enum value `schema`.)* |
| 4 | **Out-of-scope dependency** | A doc with `depends_on:` pointing at a workspace-relative path that exists on disk but is not loaded as a doc. `validation.warnings` contains a record with `rule_id == "out_of_scope_dependency"`. |
| 5 | **Empty context squashed** | Construct a synthetic `ValidationError(error_type=ValidationErrorType.ORPHAN, doc_id="", filepath="", message="m", severity="warning", fix_suggestion="")` and call `.to_dict()` directly. Assert the returned dict contains `severity` and `message` but **not** `document_id` and **not** `file_path` (squashed). `rule_id` is present (`"orphan"`). |
| 6 | **Error parity** | Force an error-severity `ValidationError` into the result (e.g. a broken `depends_on`). Assert it appears under `validation.errors` (not `.warnings`) with the same field shape and `severity == "error"`. |
| 7 | **`_not_usable()` path unchanged** | Trigger the `_not_usable()` branch (no docs loaded and no existing context map). Assert `data.validation.errors == []` and `data.validation.warnings == []`. |

The same test file can include a parity assertion: feeding a `ValidationResult` to `ValidationError.to_dict()` (CLI path) and to `_validation_issues()` (MCP path) yields identical lists.

#### 1.4.2 MCP regression — `tests/mcp/test_activation.py`

The existing `test_validation_issues_enriches_with_rule_id_document_id_file_path` and `test_validation_issues_drops_empty_context_fields` cases must pass unchanged. They are the load-bearing regression coverage for MCP behavior. No edits required; verifying they remain green is the test for the MCP refactor.

#### 1.4.3 Existing CLI regression — `tests/commands/test_agentic_activation_resilience.py`

The existing CLI test asserts `payload["data"]["status"]`, `payload["data"]["map"]["refreshed"]`, `payload["data"]["loaded_ids"]` (per the prior exploration). These keys are untouched; the test must continue to pass.

#### 1.4.4 Existing MCP context-map regression — `tests/mcp/test_context_map.py`

The assertion at [tests/mcp/test_context_map.py:30](tests/mcp/test_context_map.py:30) (`assert payload["validation"]["errors"] == []`) compares against the empty list, which is shape-neutral. No change required.

### 1.5 Acceptance check (manifest cardinality)

`G-cardinality-1` gates: `python -c "from ontos.core.types import ValidationError; assert callable(getattr(ValidationError, 'to_dict', None))"` → `ok`.

`G-cardinality-2` gates: `grep -c '#119'` against this spec returns ≥1 (this spec mentions `#119` multiple times — header, §1, §1.2.1, §1.2 acceptance criteria mapping).

## 2. Out of scope

The following items are **not** part of #119 and must not be touched:

- The MCP `_snapshot_issue()` bare-string prefix classifier and `_SNAPSHOT_RULE_PREFIXES` table — MCP-only by design.
- The MCP `ValidationIssue` schema (`ontos/mcp/schemas.py`) — the wire format is unchanged, so the schema doesn't need to change.
- The `get_context_bundle` pre-activate warning channel from issue #115 — preserved.
- The `ontos doctor` severity alignment from issue #117 — preserved.
- The `body.bare_id_token` precision change from issue #117 — preserved.
- The `depends_on` resolution rules and `OUT_OF_SCOPE_DEPENDENCY` validator emission from issue #117 — already in place; #119 only **serializes** the resulting `ValidationError` to JSON; it does not re-spec the validation rules themselves.
- The ontology-engine repo, the `.llm-dev/framework/` submodule contents, and any unrelated Ontos graph hygiene drift on the existing 204 validation warnings.

## 3. Verification

End-to-end gates, run from the repo root after Phase C lands:

```bash
scripts/llm-dev doctor
scripts/llm-dev verify manifests/project-ontos-issue-119-cli-activate-json-warning-metadata.yaml
scripts/llm-dev verify-lifecycle manifests/project-ontos-issue-119-cli-activate-json-warning-metadata.yaml
.venv/bin/python -m pytest -q tests/commands/test_activate_json_warning_metadata.py tests/commands/test_agentic_activation_resilience.py tests/mcp/test_activation.py tests/mcp/test_context_map.py
.venv/bin/python -m pytest -q
ontos activate --json | jq '.data.validation'
```

Last command (manual smoke) demonstrates the new shape against the live repo's 204-warning state. The `ontos-validate` pre-commit hook may fail unrelated to this change due to historical graph hygiene noise — if so, commit with `SKIP=ontos-validate` and document the skip in the tracker (per the orchestrator brief).

```
