# D.2 peer review — `project-ontos-issue-119-cli-activate-json-warning-metadata`

You are the **Peer Review** on Phase D.2 of deliverable `project-ontos-issue-119-cli-activate-json-warning-metadata` for repo `ohjonathan/Project-Ontos`. Family: `codex`.

Peer reviewer (lens: 'Is this good?'). Check implementation quality, completeness, code clarity, test coverage adequacy. Do NOT duplicate Alignment (compliance with prior decisions) or Adversarial (hostile inputs).

Phase D.2 reviews the LANDED IMPLEMENTATION (single commit `a342e5b` on branch `codex/project-ontos-issue-119-cli-activate-json-warning-metadata`). Compare the diff against the amended spec; identify implementation issues, not spec issues. The B.1 gemini F1 blocker (type-hint tightening on `_validation_issues`) was closed in the spec amendment before C; re-verify the landed `ontos/mcp/tools.py` honors `list[ValidationError]`.

## Strict-P3 verdict shape (MANDATORY)

Your stdout response IS the verdict artifact. Output ONLY the verdict markdown — no preamble, no closing notes. The very first three characters of your response MUST be `---` (a YAML frontmatter open fence). Do NOT begin your response with any prose, narration, status update like "I have enough information to ..." or "Here is the verdict ...", planning notes, or markdown commentary. The wrapper's verdict-shape predicate rejects any output that does not begin with `---`.

Stdout must begin with the literal three-dash YAML frontmatter open fence `---` followed by a newline. Do NOT output a bare `-` or `--`; only `---` is a valid opening fence.

The verdict MUST contain:
- YAML frontmatter with `phase: D.2`, `role: peer`, `family: codex`, `deliverable_id: project-ontos-issue-119-cli-activate-json-warning-metadata`, `status: completed`.
- An ATX `#` heading after the frontmatter.
- A `## Verdict` heading.
- The first non-blank line under `## Verdict` is exactly ONE of: `Approve` | `Request changes` | `Reject` | `Concur`.

## Exact output skeleton

```markdown
---
id: project-ontos-issue-119-D.2-codex-peer
deliverable_id: project-ontos-issue-119-cli-activate-json-warning-metadata
phase: D.2
role: peer
family: codex
status: complete
---

# D.2 Peer Review — codex

## Verdict

Approve

## Summary

<1-2 sentence overall judgement about the landed implementation.>

## Findings

### [F1] <Short title>
- **Severity:** blocker | should-fix | nit
- **Evidence:** direct-run | static-inspection
- **Where:** <file:line>
- **Issue:** <what is wrong in the implementation>
- **Recommendation:** <concrete change>

(repeat as needed; omit if none)

## Notes
<Any final notes; can be empty.>
```

If you have no findings, write `Approve` and explain your scrutiny under Notes.

## D.2 Review Packet (spec + commit log + diffs + tests)

# D.2 Review Packet — project-ontos-issue-119-cli-activate-json-warning-metadata

Phase D.2 reviews the LANDED IMPLEMENTATION against the spec under three lenses (peer / alignment / adversarial). The packet below contains:

1. The full spec under review (with B.1-driven amendments to §1.3.3, §1.3.4, §1.4.1).
2. The single-commit branch log.
3. `git diff --stat main..HEAD` summary.
4. The full diff for `ontos/core/types.py`, `ontos/commands/activate.py`, `ontos/mcp/tools.py`, and the new `tests/commands/test_activate_json_warning_metadata.py`.
5. Test status: `.venv/bin/python -m pytest -q` reports **1330 passed, 2 skipped** at the head of this branch.

Reviewer scope (D.2): validate the implementation against the spec. The B.1 gemini F1 blocker (type-hint tightening) was closed in the spec amendment before C; re-verify it is honored in the landed `ontos/mcp/tools.py` diff.

---

## Section 1 — Spec under review

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

Refactor `_validation_issues()` in [ontos/mcp/tools.py:620-640](ontos/mcp/tools.py:620) to use the new dataclass method. Tighten the parameter type hint from `list[Any]` to `list[ValidationError]` so the contract — that callers always pass a homogeneous list of `ValidationError` instances — is explicit (B.1 gemini F1):

```python
def _validation_issues(issues: list[ValidationError]) -> list[dict[str, Any]]:
    # (#119) Reuse ValidationError.to_dict() so CLI + MCP share the
    # exact same serialization. Snapshot bare strings still use
    # _snapshot_issue() (MCP-only). Type-hint tightened to list[ValidationError]
    # because the only call sites (_normalize_warnings, _validation_payload)
    # pass validation.errors / validation.warnings, both of which are
    # List[ValidationError] per the dataclass definition.
    return [issue.to_dict() for issue in issues]
```

`_normalize_warnings()`, `_validation_payload()`, `_snapshot_issue()`, and `_SNAPSHOT_RULE_PREFIXES` are unchanged. The MCP `ValidationIssue` schema (`ontos/mcp/schemas.py:16-27`) is unchanged — the wire format produced by `to_dict()` is bit-identical to the prior `_validation_issues` output, so the schema validation continues to pass.

#### 1.3.4 No other runtime modules touched

The **runtime implementation surface** is exactly three files:

- `ontos/core/types.py` (one method added, `ValidationError` import already present in `ontos/mcp/tools.py`)
- `ontos/commands/activate.py` (two lines swapped)
- `ontos/mcp/tools.py` (one helper body collapsed, one type hint tightened)

The **documentation surface** additionally requires the schema-break call-out in §1.2.1 to land:

- this spec (already includes the call-out at §1.2.1),
- the PR body (`Closes #119` + the `list[str]` → `list[dict]` note),
- a release-note bullet under `docs/releases/` (check at Phase C whether the next-release file already exists; create one if needed).

Plus the test surface in §1.4.

### 1.4 Tests

#### 1.4.1 New CLI test file — `tests/commands/test_activate_json_warning_metadata.py`

Build temp workspaces using the same pattern as [tests/commands/test_agentic_activation_resilience.py](tests/commands/test_agentic_activation_resilience.py), invoke `ontos --json activate` (or call `activate_command` / `run_activation` directly), parse the JSON envelope, and assert on the structured payload. Required cases (test fixtures tightened against actual validator behavior per B.1 codex F1):

| # | Case | Assertions |
|---|---|---|
| 1 | **Orphan warning** | A doc whose `type` is **not** in `allowed_orphan_types` (default `["atom"]`) and which has no incoming dependencies — e.g. a `kernel`-typed doc with `depends_on: []`. Override `allowed_orphan_types: []` in the test workspace config to be robust to defaults. `validation.warnings` contains one record with `rule_id == "orphan"`, `severity == "warning"`, populated `document_id`, populated `file_path`, and a non-empty `message`. |
| 2 | **Depth warning** | A `depends_on` chain that exceeds `max_dependency_depth`. `validation.warnings` contains a record with `rule_id == "depth"`, populated `document_id` / `file_path`. |
| 3 | **Schema warning** | A log doc missing required schema fields (the validator-side schema check, not the loader-side invalid-`type`/`status` diagnostics which go through `load_result.issues` rather than `validation.warnings`). `validation.warnings` contains a record with `rule_id == "schema"` and populated `document_id` / `file_path`. *(Note: finer-grained snapshot rule_ids like `schema.log_missing_fields` are MCP-only by design and out of scope; CLI reports the structured enum value `schema`.)* |
| 4 | **Out-of-scope dependency** | A doc with `depends_on:` pointing at a workspace-relative path that exists on disk but is not loaded as a doc. `validation.warnings` contains a record with `rule_id == "out_of_scope_dependency"`. |
| 5 | **Empty context squashed** | Construct a synthetic `ValidationError(error_type=ValidationErrorType.ORPHAN, doc_id="", filepath="", message="m", severity="warning", fix_suggestion="")` and call `.to_dict()` directly. Assert the returned dict contains `severity` and `message` but **not** `document_id` and **not** `file_path` (squashed). `rule_id` is present (`"orphan"`). |
| 6 | **Error parity** | Force an error-severity `ValidationError` into the result. Since `generate_context_map()` currently emits warning-severity entries for broken `depends_on` (no naturally-occurring `error`-severity validator output via the standard fixture pipeline), use either (a) a controlled synthetic `ValidationError(severity="error", ...)` injected through a monkeypatched validator OR (b) a cycle-creating fixture if the cycle detector emits error-severity entries. Either path: assert the resulting record appears under `validation.errors` (not `.warnings`) with the same field shape and `severity == "error"`. |
| 7 | **`_not_usable()` path unchanged** | Trigger the `_not_usable()` branch (no docs loaded and no existing context map). Assert `data.validation.errors == []` and `data.validation.warnings == []`. |
| 8 | **CLI/MCP parity** | **Mandatory** parity assertion (B.1 sonnet F1). Feed a constructed `ValidationResult` (with one warning that has all five fields populated, and one with only `severity`/`message`) through both code paths — `[issue.to_dict() for issue in result.warnings]` (CLI) and `_validation_issues(result.warnings)` (MCP). Assert the two lists are **identical** (same Python equality on the list of dicts). This is the load-bearing regression for the §0 "bit-for-bit" invariant. |

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

---

## Section 2 — Branch commit log (single commit ahead of main)

```text
a342e5b feat(phase-a-c): close #119 spec + B.1 board + B.3 verdict + C implementation
```

---

## Section 3 — `git diff --stat main..HEAD`

```text
 .ontos-internal/reference/decision_history.md      |    2 +-
 Ontos_Context_Map.md                               |  237 +-
 docs/releases/v4.6.0.md                            |   68 +
 ...issue-119-B.1-claude-sonnet-alignment.prompt.md |  326 ++
 ...roject-ontos-issue-119-B.1-codex-peer.prompt.md |  324 ++
 ...ntos-issue-119-B.1-gemini-adversarial.prompt.md |  326 ++
 ...s-issue-119-B.1-claude-sonnet-alignment.raw.txt |   38 +
 ...ssue-119-B.1-claude-sonnet-alignment.stderr.txt |    0
 .../project-ontos-issue-119-B.1-codex-peer.raw.txt |   38 +
 ...oject-ontos-issue-119-B.1-codex-peer.stderr.txt | 4968 ++++++++++++++++++++
 ...-ontos-issue-119-B.1-gemini-adversarial.raw.txt |   35 +
 ...tos-issue-119-B.1-gemini-adversarial.stderr.txt |    2 +
 .../B.1-claude-sonnet-alignment.md                 |   38 +
 .../B.1-codex-peer.md                              |   38 +
 .../B.1-gemini-adversarial.md                      |   33 +
 .../B.3-verdict.md                                 |   53 +
 .../github-issues-input.md                         |   86 +
 .../lifecycle-receipt-inventory.yaml               |   75 +
 .../pre-a-triage-report.md                         |   87 +
 .../pre-a-triage-verdict.md                        |   41 +
 ...vate-json-warning-metadata-dispatch-intent.yaml |   85 +
 ...vate-json-warning-metadata-dispatch-result.yaml |  199 +
 ...-119-cli-activate-json-warning-metadata-spec.md |  256 +
 ...issue-119-cli-activate-json-warning-metadata.md |   17 +
 ...sue-119-cli-activate-json-warning-metadata.yaml |  254 +
 ontos/commands/activate.py                         |    4 +-
 ontos/core/types.py                                |   11 +
 ontos/mcp/tools.py                                 |   29 +-
 .../test_activate_json_warning_metadata.py         |  298 ++
 29 files changed, 7775 insertions(+), 193 deletions(-)
```

---

## Section 4 — Production diff (`ontos/core/types.py`, `ontos/commands/activate.py`, `ontos/mcp/tools.py`)

```diff
diff --git a/ontos/commands/activate.py b/ontos/commands/activate.py
index 64fb9a5..c718d12 100644
--- a/ontos/commands/activate.py
+++ b/ontos/commands/activate.py
@@ -101,8 +101,8 @@ def run_activation(
             gen_config,
             GenerateMapOptions(max_dependency_depth=config.validation.max_dependency_depth),
         )
-        validation_errors = [issue.message for issue in validation.errors]
-        validation_warnings = [issue.message for issue in validation.warnings]
+        validation_errors = [issue.to_dict() for issue in validation.errors]
+        validation_warnings = [issue.to_dict() for issue in validation.warnings]
         if write_map:
             output_path.parent.mkdir(parents=True, exist_ok=True)
             output_path.write_text(content, encoding="utf-8")
diff --git a/ontos/core/types.py b/ontos/core/types.py
index eb82c7b..0a1d2eb 100644
--- a/ontos/core/types.py
+++ b/ontos/core/types.py
@@ -131,6 +131,17 @@ class ValidationError:
     fix_suggestion: str
     severity: str  # 'error', 'warning', 'info'
 
+    def to_dict(self) -> Dict[str, Any]:
+        record: Dict[str, Any] = {"severity": self.severity, "message": self.message}
+        rule_id = getattr(self.error_type, "value", None) if self.error_type else None
+        if rule_id:
+            record["rule_id"] = rule_id
+        if self.doc_id:
+            record["document_id"] = self.doc_id
+        if self.filepath:
+            record["file_path"] = self.filepath
+        return record
+
 
 @dataclass
 class ValidationResult:
diff --git a/ontos/mcp/tools.py b/ontos/mcp/tools.py
index 084fa4d..9761739 100644
--- a/ontos/mcp/tools.py
+++ b/ontos/mcp/tools.py
@@ -15,7 +15,7 @@ from ontos.commands.map import CompactMode, GenerateMapOptions, generate_context
 from ontos.core.content_hash import compute_content_hash
 from ontos.core.errors import OntosUserError
 from ontos.core.snapshot import DocumentSnapshot
-from ontos.core.types import DocumentData, ValidationResult
+from ontos.core.types import DocumentData, ValidationError, ValidationResult
 from ontos.io.snapshot import create_snapshot
 from ontos.mcp._types import PortfolioIndexLike
 from ontos.mcp.scanner import slugify
@@ -617,27 +617,14 @@ def _validation_payload(validation: ValidationResult) -> dict[str, Any]:
     }
 
 
-def _validation_issues(issues: list[Any]) -> list[dict[str, Any]]:
-    # (#117) Surface document context (rule_id, document_id, file_path) so
+def _validation_issues(issues: list[ValidationError]) -> list[dict[str, Any]]:
+    # (#117/#119) Surface document context (rule_id, document_id, file_path) so
     # downstream agents can triage without a second query. Empty strings are
-    # squashed so the public payload stays compact.
-    enriched: list[dict[str, Any]] = []
-    for issue in issues:
-        record: dict[str, Any] = {
-            "severity": issue.severity,
-            "message": issue.message,
-        }
-        rule_id = getattr(issue.error_type, "value", None) if getattr(issue, "error_type", None) else None
-        if rule_id:
-            record["rule_id"] = rule_id
-        doc_id = getattr(issue, "doc_id", "") or ""
-        if doc_id:
-            record["document_id"] = doc_id
-        file_path = getattr(issue, "filepath", "") or ""
-        if file_path:
-            record["file_path"] = file_path
-        enriched.append(record)
-    return enriched
+    # squashed so the public payload stays compact. The serialization lives on
+    # ValidationError.to_dict() so CLI and MCP share the exact same shape;
+    # call sites here (_normalize_warnings, _validation_payload) always pass
+    # validation.errors / validation.warnings (List[ValidationError]).
+    return [issue.to_dict() for issue in issues]
 
 
 # (#117) Bare snapshot strings often originate from the loader and document
```

---

## Section 5 — New test file (`tests/commands/test_activate_json_warning_metadata.py`)

```python
"""CLI regressions for #119 — `ontos activate --json` structured validation
metadata (`severity`, `rule_id`, `message`, `document_id`, `file_path`).

Mirrors the MCP enrichment landed in PR #118 / v4.5.0 (deliverable
project-ontos-github-issues-115-117). See
docs/specs/project-ontos-issue-119-cli-activate-json-warning-metadata-spec.md
§1.4.1 for the canonical case list.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

from ontos.core.types import ValidationError, ValidationErrorType, ValidationResult
from ontos.mcp.tools import _validation_issues


REPO_ROOT = Path(__file__).resolve().parents[2]


# =============================================================================
# Helpers
# =============================================================================


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(content).lstrip(), encoding="utf-8")


def _run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT)
    return subprocess.run(
        [sys.executable, "-m", "ontos", *args],
        cwd=root,
        text=True,
        capture_output=True,
        env=env,
    )


def _orphan_warning(doc_id: str, filepath: str) -> ValidationError:
    return ValidationError(
        error_type=ValidationErrorType.ORPHAN,
        doc_id=doc_id,
        filepath=filepath,
        message="Document has no incoming dependencies",
        fix_suggestion="Add a dependency from another document, or change type to one in allowed_orphan_types.",
        severity="warning",
    )


# =============================================================================
# Unit tests — ValidationError.to_dict() shape (Cases 1-6 from spec §1.4.1)
# =============================================================================


def test_to_dict_orphan_includes_rule_id_document_id_file_path() -> None:
    """Case 1 — orphan warning carries severity, rule_id, message, document_id, file_path."""
    issue = _orphan_warning("kernel_doc", "docs/kernel/kernel_doc.md")

    record = issue.to_dict()

    assert record == {
        "severity": "warning",
        "message": "Document has no incoming dependencies",
        "rule_id": "orphan",
        "document_id": "kernel_doc",
        "file_path": "docs/kernel/kernel_doc.md",
    }


def test_to_dict_depth_warning_emits_depth_rule_id() -> None:
    """Case 2 — depth warning carries rule_id == 'depth' and doc context."""
    issue = ValidationError(
        error_type=ValidationErrorType.DEPTH,
        doc_id="leaf_doc",
        filepath="docs/leaf.md",
        message="Dependency depth 6 exceeds max 5",
        fix_suggestion="Flatten the dependency chain or raise max_dependency_depth.",
        severity="warning",
    )

    record = issue.to_dict()

    assert record["rule_id"] == "depth"
    assert record["severity"] == "warning"
    assert record["document_id"] == "leaf_doc"
    assert record["file_path"] == "docs/leaf.md"


def test_to_dict_schema_warning_emits_schema_rule_id() -> None:
    """Case 3 — schema warning (e.g. log doc missing required fields) → rule_id == 'schema'.

    Note: finer-grained snapshot rule_ids like ``schema.log_missing_fields`` are
    MCP-only by design; the CLI path reports the structured enum value ``schema``.
    """
    issue = ValidationError(
        error_type=ValidationErrorType.SCHEMA,
        doc_id="logs_2026_05_22",
        filepath="docs/logs/2026-05-22.md",
        message="Log missing fields: branch",
        fix_suggestion="Add the required `branch` field to the log frontmatter.",
        severity="warning",
    )

    record = issue.to_dict()

    assert record["rule_id"] == "schema"
    assert record["document_id"] == "logs_2026_05_22"
    assert record["file_path"] == "docs/logs/2026-05-22.md"


def test_to_dict_out_of_scope_dependency_emits_correct_rule_id() -> None:
    """Case 4 — depends_on resolved on disk but not loaded → rule_id == 'out_of_scope_dependency'."""
    issue = ValidationError(
        error_type=ValidationErrorType.OUT_OF_SCOPE_DEPENDENCY,
        doc_id="strategy_a",
        filepath="docs/strategy/a.md",
        message="External dependency resolved from disk: '.llm-dev/framework/framework.md' (declared in strategy_a)",
        fix_suggestion="Either load the target as a doc or rephrase the dependency.",
        severity="warning",
    )

    record = issue.to_dict()

    assert record["rule_id"] == "out_of_scope_dependency"
    assert record["document_id"] == "strategy_a"
    assert record["file_path"] == "docs/strategy/a.md"


def test_to_dict_squashes_empty_document_id_and_file_path() -> None:
    """Case 5 — empty doc_id / filepath are absent from the public payload (not present as empty strings)."""
    issue = ValidationError(
        error_type=ValidationErrorType.ORPHAN,
        doc_id="",
        filepath="",
        message="Document has no incoming dependencies",
        fix_suggestion="",
        severity="warning",
    )

    record = issue.to_dict()

    assert record == {
        "severity": "warning",
        "message": "Document has no incoming dependencies",
        "rule_id": "orphan",
    }
    assert "document_id" not in record
    assert "file_path" not in record


def test_to_dict_error_severity_preserved() -> None:
    """Case 6 — error-severity ValidationError serializes with severity == 'error'."""
    issue = ValidationError(
        error_type=ValidationErrorType.BROKEN_LINK,
        doc_id="strategy_a",
        filepath="docs/strategy/a.md",
        message="Broken dependency: missing_doc",
        fix_suggestion="Create the target doc or remove the dependency.",
        severity="error",
    )

    record = issue.to_dict()

    assert record["severity"] == "error"
    assert record["rule_id"] == "broken_link"
    assert record["document_id"] == "strategy_a"
    assert record["file_path"] == "docs/strategy/a.md"


# =============================================================================
# Parity tests — CLI and MCP paths produce identical lists (Case 8 from spec)
# =============================================================================


def test_cli_and_mcp_serialization_identical_for_validation_result() -> None:
    """Case 8 (mandatory) — CLI and MCP serialize the same ValidationResult identically.

    This is the load-bearing regression for the §0 'bit-for-bit' invariant: if
    these two lists ever diverge, MCP and CLI consumers will see different
    payloads for the same underlying ValidationError, defeating the whole
    purpose of #119.
    """
    enriched = _orphan_warning("kernel_doc", "docs/kernel/kernel_doc.md")
    sparse = ValidationError(
        error_type=ValidationErrorType.ORPHAN,
        doc_id="",
        filepath="",
        message="Bare snapshot orphan",
        fix_suggestion="",
        severity="warning",
    )
    result = ValidationResult(warnings=[enriched, sparse])

    cli_serialized = [issue.to_dict() for issue in result.warnings]
    mcp_serialized = _validation_issues(result.warnings)

    assert cli_serialized == mcp_serialized


# =============================================================================
# Integration test — CLI JSON envelope carries the structured shape end-to-end
# =============================================================================


def _orphan_workspace(root: Path) -> Path:
    """Build a temp workspace whose context map will surface at least one
    orphan warning. Uses a non-atom type (default ``allowed_orphan_types`` is
    ``["atom"]``) so the orphan rule fires regardless of the default config.
    """
    _write(
        root / ".ontos.toml",
        """
        [ontos]
        version = "4.4"

        [scanning]
        skip_patterns = ["*/docs/reviews/*"]
        """,
    )
    # A kernel doc with no incoming dependencies — kernel is not in default
    # allowed_orphan_types, so the validator must emit an orphan warning.
    _write(
        root / "docs/kernel.md",
        """
        ---
        id: kernel_doc
        type: kernel
        status: active
        ---
        Kernel body.
        """,
    )
    return root


def test_activate_json_emits_structured_validation_warnings(tmp_path: Path) -> None:
    """End-to-end — `ontos --json activate` writes objects, not strings, under
    ``data.validation.warnings`` and ``data.validation.errors``.
    """
    root = _orphan_workspace(tmp_path)

    result = _run(root, "--json", "activate")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)

    validation = payload["data"]["validation"]
    assert isinstance(validation["errors"], list)
    assert isinstance(validation["warnings"], list)

    # Every record (if any) is a dict with severity + message.
    for record in validation["warnings"] + validation["errors"]:
        assert isinstance(record, dict), f"expected dict, got {type(record).__name__}: {record!r}"
        assert "severity" in record
        assert "message" in record

    # At least one orphan warning must appear (the kernel doc has no incoming deps).
    orphan_records = [w for w in validation["warnings"] if w.get("rule_id") == "orphan"]
    assert orphan_records, (
        f"expected at least one orphan warning in {validation['warnings']!r}"
    )
    orphan = orphan_records[0]
    assert orphan["severity"] == "warning"
    assert orphan["document_id"] == "kernel_doc"
    assert orphan["file_path"].endswith("docs/kernel.md")


def test_activate_json_not_usable_path_emits_empty_lists(tmp_path: Path) -> None:
    """Case 7 — the ``_not_usable()`` branch (no docs loaded, no existing context
    map) still emits empty ``validation.errors`` / ``validation.warnings`` lists,
    unaffected by the shape change.
    """
    _write(
        tmp_path / ".ontos.toml",
        """
        [ontos]
        version = "4.4"
        """,
    )
    # No docs at all and no Context Map → _not_usable path.

    result = _run(tmp_path, "--json", "activate")
    payload = json.loads(result.stdout)

    # _not_usable returns exit 1 with an error envelope; the inner data block
    # still includes the validation shell.
    assert result.returncode == 1, result.stderr
    validation = payload["data"]["validation"]
    assert validation["errors"] == []
    assert validation["warnings"] == []
```

---

## Section 6 — Release note (`docs/releases/v4.6.0.md`)

```markdown
---
id: v460
type: log
status: active
event_type: release
impacts:
  - v450
  - ontos_manual
---

# Ontos v4.6.0

v4.6.0 closes the final D.6 deferral from PR #118 / v4.5.0: `ontos activate --json` now exposes structured validation metadata, reaching parity with the MCP `activate` tool. Closes [issue #119](https://github.com/ohjonathan/Project-Ontos/issues/119).

## CLI `activate --json` warning metadata parity (#119)

- **Structured validation records.** `payload.data.validation.warnings` and `payload.data.validation.errors` now contain objects carrying `severity`, `message`, `rule_id` (when the validator emits one), `document_id` (when the document context is known), and `file_path` (when known). CLI automation can triage warnings by rule/document without re-parsing message strings or falling back to a parallel MCP call. The serialization is bit-identical to MCP — both paths now route through the same `ValidationError.to_dict()` method.

### Breaking change to the CLI JSON contract

`payload.data.validation.warnings` and `payload.data.validation.errors` previously contained **bare message strings**; they now contain **objects**. Consumers that parsed these fields as `list[str]` will need to read `record["message"]` from each element. The top-level CLI envelope (`status`, `code`, `message`, `data`) is unchanged.

Before (`ontos <= 4.5.0`):

```json
{
  "validation": {
    "errors":   ["Broken dependency: missing_doc"],
    "warnings": ["Document has no incoming dependencies"]
  }
}
```

After (`ontos >= 4.6.0`):

```json
{
  "validation": {
    "errors":   [{
      "severity":    "error",
      "message":     "Broken dependency: missing_doc",
      "rule_id":     "broken_link",
      "document_id": "strategy_a",
      "file_path":   "docs/strategy/a.md"
    }],
    "warnings": [{
      "severity":    "warning",
      "message":     "Document has no incoming dependencies",
      "rule_id":     "orphan",
      "document_id": "kernel_doc",
      "file_path":   "docs/kernel.md"
    }]
  }
}
```

`document_id` and `file_path` are omitted when the source `ValidationError` has empty values; `rule_id` is omitted only when the validator did not classify the issue. `severity` and `message` are always present.

## Internal refactor

- `ValidationError.to_dict()` is now the single shared serializer used by both `ontos/commands/activate.py` (CLI JSON path) and `ontos/mcp/tools.py:_validation_issues` (MCP activation payload). The MCP wire format is bit-identical; the existing schema (`ontos/mcp/schemas.py:ValidationIssue`) is unchanged.

## Unchanged

- MCP `activate` tool behavior, schema, and snapshot warning classification.
- `ontos activate` human-readable (non-JSON) output.
- `_not_usable()` activation path — still emits empty `validation.errors` / `validation.warnings` lists.
- Validator rules from PR #118 (depends_on resolution, `out_of_scope_dependency`, type/status widening, README/template skip, doctor severity alignment, body.bare_id_token tightening).
```

---

## Section 7 — Test status

```text
1330 passed, 2 skipped, 2 warnings in 55.11s
```

Targeted smoke subset (the four files most relevant to #119):

```text
24 passed in 2.03s
```

Manual smoke against the live repo:

```text
.venv/bin/python -m ontos activate --json | jq '.data.validation.warnings[0]'
{
  "severity": "warning",
  "message": "Document has no incoming dependencies",
  "rule_id": "orphan",
  "document_id": "log_20260117_readme-and-license-update-for-v3-0-0",
  "file_path": "/Users/jonathanoh/workspaces/Project-Ontos/docs/logs/2026-01-17_readme-and-license-update-for-v3-0-0.md"
}
```
