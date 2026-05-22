# D.5 verifier review — `project-ontos-github-issues-115-117`

You are the **Verifier** on Phase D.5 of deliverable `project-ontos-github-issues-115-117` for repo `ohjonathan/Project-Ontos`. Family: `claude-opus`.

Verifier (lens: 'Does the implementation match the spec and pass its own gates?'). Validate that the landed code actually implements the spec, that the targeted test suite passes, and that the cardinality/scope gates hold. Findings only if the implementation diverges from the spec or any gate.

Phase D.5 verifies the IMPLEMENTATION END-TO-END after any D.4 fix. Confirm the spec invariants hold in the landed code and tests pass.

## Strict-P3 verdict shape (MANDATORY)

Your stdout response IS the verdict artifact. Output ONLY the verdict markdown — no preamble, no closing notes. The first character of stdout must be `-` (the opening frontmatter fence).

The verdict MUST contain ALL of:

1. YAML frontmatter fenced by `---` lines with these keys (non-empty strings):
   - `phase: D.5`
   - `role: verifier`
   - `family: claude-opus`
   - `deliverable_id: project-ontos-github-issues-115-117`
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
id: project-ontos-github-issues-115-117-D.5-claude-opus-verifier
deliverable_id: project-ontos-github-issues-115-117
phase: D.5
role: verifier
family: claude-opus
status: completed
---

# D.5 Verifier — claude-opus

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
id: project-ontos-github-issues-115-117-spec
deliverable_id: project-ontos-github-issues-115-117
type: atom
status: active
phase: A
role: spec-author
family: codex
depends_on:
  - ontos_manual
  - ontology_spec
  - ontos_agent_instructions
---

# Spec — project-ontos-github-issues-115-117

This spec covers three open GitHub issues against `ohjonathan/Project-Ontos`:

- **Closes #115** — MCP `get_context_bundle` returns schema-invalid `_ontos_warning` before `activate`.
- **Closes #116** — Document MCP host reload requirement after `pipx upgrade ontos`.
- **Closes #117** — Activation `usable_with_warnings` is loud + low-signal: false-positive `depends_on`, anonymous orphan / depth / log-field warnings, narrow type/status vocabulary, 11,163 spurious `body.bare_id_token` link-check matches, and `ontos doctor` severity drift.

The Pre-A triage report classified all three as **In-Scope** with `direct-run` evidence and routed them to one integrated implementation track. See `docs/reviews/project-ontos-github-issues-115-117/pre-a-triage-report.md`.

## 0. Cross-cutting invariants

- Conservative repair behavior must be preserved: every code path that today
  falls back to a safe default (e.g., `DocumentType.UNKNOWN`) keeps doing so when
  every extension below cannot resolve the input; the original raw value is
  surfaced as diagnostic context, not dropped.
- Public MCP success schemas remain `additionalProperties: false`. Any new
  diagnostic context must land in already-declared fields (`warnings` list)
  or via explicit schema additions, never as an undeclared key.
- `verify-lifecycle.sh --mode strict-p3 manifests/project-ontos-github-issues-115-117.yaml` must pass at D.6.

## 1. Issue #115 — MCP `get_context_bundle` schema-safe pre-activate warning

### 1.1 Current behavior

`ontos/mcp/server.py:763-766` injects `validated["_ontos_warning"] = "Ontos activation not performed this MCP session; call activate first."` into every read-tool result when `cache.activation_performed` is `False`.

`ontos/mcp/schemas.py:372-382` `output_schema_for(tool_name)` adds an `_ontos_warning` property to the JSON schema **only when** `tool_name in READ_WARNING_TOOL_NAMES`. That set (schemas.py:332-341) covers `activate, workspace_overview, context_map, get_document, list_documents, query, health, refresh` — **but not `get_context_bundle`**. The `GetContextBundleResponse` model (schemas.py:249-258) is a `StrictModel` (`additionalProperties: false`) that already declares a `warnings: List[str]` field. The injection therefore makes the runtime payload reject the schema.

Reported error from Johnny-OS smoke: `Additional properties are not allowed ('_ontos_warning' was unexpected)`.

### 1.2 Contract

A `get_context_bundle` call **before** `activate` returns a schema-valid response whose `warnings` list **includes** an activation-not-performed entry. The response does not carry an `_ontos_warning` key.

### 1.3 Implementation

- Add a new set `WARNINGS_LIST_TOOL_NAMES = {"get_context_bundle"}` adjacent to `READ_WARNING_TOOL_NAMES` in `ontos/mcp/schemas.py`.
- In `ontos/mcp/server.py:_invoke_read_tool` (lines 755-767), when the pre-activate warning is being attached:
  - If `tool_name in READ_WARNING_TOOL_NAMES`: preserve the legacy `validated["_ontos_warning"] = …` injection (schema advertises the key).
  - Else if `tool_name in WARNINGS_LIST_TOOL_NAMES`: append the activation-not-performed string to the existing `validated["warnings"]` list (initializing to `[]` if missing — but `GetContextBundleResponse.warnings` is required so the key is always present).
  - Else: emit nothing — undeclared keys must never appear.
- The warning string remains exactly: `"Ontos activation not performed this MCP session; call activate first."`
- Update `output_schema_for(tool_name)` only if needed (no change required for `get_context_bundle` since `warnings` is already in its schema).

### 1.4 Tests

- `tests/mcp/test_schemas.py`: assert `GetContextBundleResponse.model_fields["warnings"]` exists and that the rendered output schema for `get_context_bundle` continues to forbid `additionalProperties`.
- `tests/mcp/test_bundler.py` (new test case): invoke `get_context_bundle` against a cache where `activation_performed=False`; assert the response validates against `validate_success_payload("get_context_bundle", …)`, that no `_ontos_warning` key is present, and that `warnings` contains the activation-not-performed string.
- `tests/mcp/test_server_integration.py` regression: confirm tools in `READ_WARNING_TOOL_NAMES` still receive `_ontos_warning` (backwards compatibility).

### 1.5 Acceptance check (manifest cardinality)

`G-cardinality-1` already gates: `python -c "from ontos.mcp.schemas import GetContextBundleResponse as M; assert 'warnings' in M.model_fields"` → `ok`.

## 2. Issue #117 — Activation / link-check signal hardening (single integrated track)

### 2.1 `depends_on` resolution (preserve doc-id behavior, add safe path fallback)

#### 2.1.1 Current behavior

`ontos/core/graph.py:build_graph()` builds `existing_ids = set(docs.keys())` (line 68) and reports `BROKEN_LINK` for any `dep_id not in existing_ids` (lines 82-99). It never consults the filesystem. The reporter's evidence shows 10 false positives where `depends_on:` entries point to workspace-rooted *paths* that exist on disk but are not loaded doc ids.

#### 2.1.2 Contract

For each declared `depends_on` entry, resolve in order:

1. Match against the loaded doc-id set (`docs.keys()`) — if hit, edge is resolved as today.
2. Treat as a workspace-relative path: build `candidate = workspace_root / dep_id`. If `candidate` is the filepath of a loaded doc, edge resolves to that doc's id.
3. Same as (2) but treat as a path relative to the declaring document's directory: `candidate = doc.filepath.parent / dep_id`.
4. If `candidate` from (2) or (3) exists on disk as a real file but is **not** a loaded doc, the edge is an **external resolved dependency** — emit a `warning`-severity entry (not an `error`), keep the message clear, and do **not** corrupt the graph (no synthetic node).
5. Otherwise (no doc match, no path on disk in any of (2)/(3)) the edge is **broken** — keep today's `error`-severity behavior, including the existing candidate-suggestion message.

Existing `depends_on: [some-doc-id]` style entries are unaffected (rule 1 hits first).

#### 2.1.3 Implementation

- Extend `build_graph(docs, severity_map, workspace_root=None)` with a new optional `workspace_root: Optional[Path]` argument. When provided, the resolver tries rules 2/3/4. When `None`, behavior is byte-identical to today (back-compat).
- Add a helper `_resolve_depends_on_path(dep_id, doc, docs_by_path, workspace_root)` that:
  - Returns `(resolved_doc_id, severity)` on rule-2/3 doc match → `(target_id, "edge")`.
  - Returns `(None, "external")` on rule-4 file-exists-not-loaded.
  - Returns `(None, "broken")` otherwise.
- Build `docs_by_path = {d.filepath.resolve(): d.id for d in docs.values()}` once before the inner loop.
- For `"external"` results, append a `ValidationError` of a new `error_type` `ValidationErrorType.OUT_OF_SCOPE_DEPENDENCY` with `severity="warning"`, message `"External dependency resolved from disk: '{dep_id}' (declared in {doc_id})"`, and `doc_id` / `filepath` populated.
- Wire `workspace_root` through from the activation / context-map orchestration: `ontos/commands/activate.py` already knows the workspace root; pass it down to `build_graph`.

#### 2.1.4 Tests

- `tests/core/test_graph.py`: add cases covering
  (a) classic doc-id `depends_on` (resolves rule 1 — regression),
  (b) workspace-relative path pointing at a loaded doc (resolves rule 2 → edge to that doc),
  (c) declaring-doc-relative path pointing at a loaded doc (resolves rule 3),
  (d) workspace-relative path pointing at an existing-but-not-loaded file (rule 4 → warning, NOT error, no graph corruption),
  (e) workspace-relative path pointing at a missing file (rule 5 → broken, error severity preserved).
- `tests/commands/test_validation.py` or `tests/test_validation.py`: an integration test against a fixture mimicking the `company-os` reporter case (a doc with `depends_on:` pointing at `.llm-dev/framework/framework.md` / `docs/strategy/...` etc.).

### 2.2 Warning enrichment (`rule_id`, `document_id`, `file_path`)

#### 2.2.1 Current behavior

`ontos/core/types.py:94-101` already gives `ValidationError` `doc_id` and `filepath` fields, but `ontos/mcp/tools.py:_validation_issues()` (lines 620-627) drops them and emits only `{severity, message}`. `_normalize_warnings()` (lines 602-610) also appends bare-string `snapshot_warnings` with no doc context. The activation payload `warnings[]` list (tools.py:148-163) inherits this thin shape.

#### 2.2.2 Contract

Every activation warning that originates from a known document carries `rule_id`, `document_id`, and `file_path`. Bare snapshot warnings carry `rule_id` (derived from their source class) when available; `document_id` and `file_path` remain absent for warnings that genuinely have no doc context.

#### 2.2.3 Implementation

- Update `_validation_issues()` in `ontos/mcp/tools.py` to emit:
  ```python
  {
      "severity": issue.severity,
      "rule_id": issue.error_type.value,   # e.g., "orphan", "depth", "broken_link", "schema"
      "message": issue.message,
      "document_id": issue.doc_id,         # always present (may be empty string)
      "file_path": issue.filepath,         # always present (may be empty string)
  }
  ```
- Extend the MCP `WarningEntry` model (or whichever shape lives in `ontos/mcp/schemas.py` for activation warnings) to optionally accept `rule_id`, `document_id`, `file_path`. Keep them optional so back-compat clients that ignore them are unaffected.
- For snapshot bare-string warnings, route through a small helper that classifies known prefixes (e.g., `"Log missing fields:"` → `rule_id="schema.log_missing_fields"`, `"Invalid frontmatter field"` → `rule_id="schema.invalid_frontmatter"`) so the channel becomes parseable.
- Human-readable CLI output (`ontos/commands/activate.py`) prints `[{rule_id}] {message} ({document_id} @ {file_path})` when those fields are present, falling back to the bare message otherwise.

#### 2.2.4 Tests

- `tests/core/test_validation.py`: orphan / depth / log-field cases now serialize to a dict containing `document_id` and `file_path`.
- `tests/mcp/test_activation.py`: the MCP `activate` response carries the new fields and remains schema-valid.

### 2.3 Type / status vocabulary widening with conservative repair

#### 2.3.1 Current behavior

`ontos/core/types.py:31-55` defines `DocumentType` (8 values) and `DocumentStatus` (11 values). `ontos/core/frontmatter.py:212-240` and `242-270` silently fall back to `UNKNOWN` for any out-of-vocab input. The reporter measured 82/163 docs (50%) typed `unknown` on a real workspace.

#### 2.3.2 Contract

- Extend `DocumentType` with lifecycle types observed in real engineering workspaces: `HANDOFF = "handoff"`, `TRACKER = "tracker"`, `RETRO = "retro"`, `REVIEW = "review"`, `SPEC = "spec"`, `REPORT = "report"`, `ADR = "adr"`, `POLICY = "policy"`.
- Extend `DocumentStatus` with: `PROPOSED = "proposed"`, `READY = "ready"`, `COMPLETED = "completed"` (sibling alias of `COMPLETE`), `REVISED = "revised"`, `IN_LIFECYCLE = "in-lifecycle"`.
- When an input still fails to map after the extension, conservative repair returns `UNKNOWN` (preserving today's behavior) **and** preserves the raw input as a diagnostic field for the validator to surface (`document_id`, `original_value`, `field`, `allowed_values`).

#### 2.3.3 Implementation

- Add the new enum members in `ontos/core/types.py` (string values must match user-facing frontmatter values).
- `normalize_type()` / `normalize_status()` in `ontos/core/frontmatter.py`: keep the `try/except` and `UNKNOWN` fallback, but always invoke the `on_error` callback with a tuple that includes the **original value** so the validator can surface it.
- Validator (`ontos/io/files.py:report_enum_error`) records `original_value`, then emits a warning whose message includes the original value (the field is preserved through `_validation_issues()` via the enrichment in §2.2).
- Documentation: extend the type/status enumeration tables in `docs/reference/Ontos_Manual.md` and `docs/reference/ontology_spec.md` to list the new values and the conservative-repair behavior. Update `Migration_v3_to_v4.md` with a "lifecycle artifact types" subsection.

#### 2.3.4 Tests

- `tests/core/test_frontmatter_repair.py`: parameterized cases for each new type and status (positive — value preserved), plus one unknown-vocab case (fallback to `UNKNOWN` + original value surfaced).
- `tests/core/test_validation.py`: assertion that the warning emitted for the unknown-vocab case carries the original value in its message.

### 2.4 `body.bare_id_token` precision (require known IDs or explicit sigils)

#### 2.4.1 Current behavior

`ontos/core/body_refs.py:_iter_generic_id_candidates()` (lines 650-660) walks every prose token through `_looks_like_doc_id()` and reports a bare-id-token match for any token that contains `_` or `.` or has a digit. The reporter measured **11,163** matches across 163 documents (≈70 per doc) — overwhelmingly false positives.

#### 2.4.2 Contract

In **generic mode** (`known_ids is None`), `scan_body_references()` emits `BARE_ID_TOKEN` matches **only** for tokens that appear inside an explicit `[[doc-id]]` wikilink sigil. Markdown link target detection (`_find_markdown_link_targets`) is preserved unchanged. In **known-ids mode** (`known_ids` is a non-empty set), `BARE_ID_TOKEN` matches resolve against the known set exactly as today. In **rename mode** (`rename_target` set), behavior is unchanged.

#### 2.4.3 Implementation

- In `_scan_normal_text_segment()` (body_refs.py:369-447), change the generic-mode branch (line 422-423):
  ```python
  else:
      bare_candidates = _iter_wikilink_id_candidates(segment_text)
  ```
- Add a new helper `_iter_wikilink_id_candidates(text)` that yields tokens found inside `[[…]]` spans (already detected by `_WIKILINK_RE`). The yielded tuples retain `(start, end, normalized_id)` shape.
- Remove or guard `_iter_generic_id_candidates` so it's only invoked under an opt-in flag — keep the function for any opt-in callers.
- Update `_find_unsupported_spans` reasoning: wikilink spans are no longer treated as "unsupported" in generic mode; they're the new generic-mode source.

#### 2.4.4 Tests

- `tests/core/test_body_refs.py` (or extend the existing equivalent): generic mode against prose containing `snake_case_words`, `dotted.tokens`, `digits42`, `v3.2.1` → zero `BARE_ID_TOKEN` matches.
- Known-ids mode: same prose with `known_ids={"snake_case_words"}` → matches `snake_case_words` exactly.
- Generic mode with explicit `[[my-doc-id]]` sigil → emits one `BARE_ID_TOKEN` match for `my-doc-id`.
- `tests/commands/test_link_check.py`: a fixture mimicking a small prose-heavy doc; assert `body.bare_id_token` count drops from O(per-prose-token) to O(wikilink-sigil).

### 2.5 README / template scanning skip

#### 2.5.1 Current behavior

`docs/logs/README.md` and `_template.md`-named files are scanned as data documents. The reporter shows `README.md` triggers the "Log missing fields: branch" warning despite being a README, not a log.

#### 2.5.2 Contract

Files whose stem is `README` or whose name ends with `_template.md` are excluded from typed-doc validation. They may still be indexed in the file inventory but receive no log-schema or orphan validation. If such a file declares an explicit `id:` frontmatter field, it opts back in to validation (escape hatch).

#### 2.5.3 Implementation

- Document loader in `ontos/io/files.py` (around the existing `report_enum_error` callback) gains a new `_is_validation_excluded(path: Path) -> bool` helper. Excluded files are loaded into the doc inventory with a sentinel `validation_excluded=True` (new field on `DocumentData` or recorded in the loader's side state).
- `validate_log_schema()` and `detect_orphans()` skip `validation_excluded` docs.
- The escape hatch: if the file already declared an `id:` field, `_is_validation_excluded` returns `False` (treat as a regular doc).

#### 2.5.4 Tests

- `tests/io/test_files.py` or new test: a `docs/logs/README.md` fixture (no `id`) → not in validation; a `docs/logs/README.md` fixture (with `id: logs_readme`) → in validation.

### 2.6 `ontos doctor` severity alignment

#### 2.6.1 Current behavior

`ontos/commands/doctor.py:_run_doctor_command()` (lines 758-814) sets the exit code from `result.failed > 0`. It does not consult `ontos activate` or `ontos link-check` health.

#### 2.6.2 Contract

When activation reports any `error`-severity entry, `ontos doctor` exit code is **non-zero** even if no other check failed. Warnings alone (no errors) keep doctor at exit 0 — same as today.

#### 2.6.3 Implementation

- Inside `_run_doctor_command()`, after the existing checks, invoke the activation pipeline (reuse the same code path as `ontos activate`) and inspect its `warnings[]` list.
- If any entry has `severity == "error"`, increment `result.failed` (or set a new `result.activation_errors > 0` flag the exit-code calculation considers).
- The doctor JSON output gains an `activation: {status, error_count, warning_count}` block.

#### 2.6.4 Tests

- `tests/commands/test_doctor_phase4.py`: a fixture workspace with a real broken `depends_on` → doctor exit 1, `activation.error_count > 0`. A clean workspace → doctor exit 0.

## 3. Issue #116 — Document MCP host reload requirement after upgrade

### 3.1 Content

Add a "Restarting MCP hosts after upgrading Ontos" section that explains:

- Long-lived stdio MCP hosts (Claude Code, Cursor, antigravity, etc.) spawn `ontos serve` as a child process and keep it alive across `pipx upgrade ontos`.
- After `pipx upgrade ontos`, `pip install --upgrade ontos`, or `pipx install --force 'ontos[mcp]'`, the running MCP child still reports the old `serverInfo.version`.
- Users must restart their MCP host (or reload the Ontos extension/plugin) to pick up the new version. The CLI command (`ontos --version`) shows the new version immediately because each invocation is a fresh process.
- One-liner verification: a fresh `ontos serve --workspace … --read-only` started manually reports the new version on `serverInfo`, confirming the binary is correct and the host process just needs recycling.

### 3.2 Touchpoints

- `README.md` — add a short "After upgrading Ontos" subsection under the MCP section.
- `docs/reference/Ontos_Manual.md` — a full subsection inside the MCP chapter.
- `docs/reference/Migration_v3_to_v4.md` — add a "Restart MCP hosts after upgrading" subsection.
- `docs/releases/v4.5.0.md` (new file) — release-note bullet pointing to the new doc subsection.

### 3.3 Wording target

Direct, imperative, one-paragraph. Example:

> **Restart your MCP host after upgrading Ontos.** Long-lived MCP hosts (Claude Code, Cursor, Antigravity) spawn `ontos serve` once and keep that child process alive across upgrades. After `pipx upgrade ontos`, `pip install --upgrade ontos`, or `pipx install --force 'ontos[mcp]'`, restart the MCP host (or reload the Ontos plugin) so it picks up the new version. The CLI (`ontos --version`) shows the new version immediately because each CLI invocation is a fresh process.

### 3.4 Tests

Docs-only changes have no pytest coverage. Verification at D.6: `grep -lE 'Restart.*MCP host' README.md docs/reference/Ontos_Manual.md docs/reference/Migration_v3_to_v4.md docs/releases/v4.5.0.md` returns all four paths.

## 4. Out of scope

The following surface area is **not** addressed by this deliverable (deferred or explicitly excluded):

- Workspace-extensible custom type vocabularies via `.ontos.toml [schema] extra_types = […]`. The lifecycle types extension in §2.3 handles the bulk of real cases; per-workspace extension can be a follow-up.
- Per-type status vocabularies. §2.3 extends the canonical set; per-type slicing is deferred.
- Optional `ontos doctor` detection of stale running server versions (#116 mentions it as optional). The current scope ships docs; auto-detection requires an MCP child-process inspection facility that does not yet exist.
- Fixes to the 75 long-standing data-quality issues under `.ontos-internal/` that the legacy `.ontos/scripts/ontos_generate_context_map.py --strict` pre-commit hook surfaces. These are pre-existing, predate this deliverable, and are not what the issues report.
- An `ontos diagnose --warning-class <X>` triage helper (mentioned in #117's "Suggested fixes" section 8). Useful but additive; deferred.

## 5. Verification at D.6

1. `scripts/llm-dev verify manifests/project-ontos-github-issues-115-117.yaml` exits 0.
2. `scripts/llm-dev verify-lifecycle --mode strict-p3 manifests/project-ontos-github-issues-115-117.yaml` exits 0 (all B.1 / D.2 / D.5 receipts present and hash-bound).
3. `bash .llm-dev/framework/scripts/verify-d6-gate.sh docs/reviews/project-ontos-github-issues-115-117/final-approval.md` exits 0.
4. `.venv/bin/python -m pytest -q` exits 0 (gate `G-test-2`).
5. Manual smoke against the read-only `company-os` reproduction tree (`/Users/jonathanoh/ontos-issue-tree/company-os-ontos-rca-2026-05-22/`):
   - `ontos activate --json` no longer reports the 10 false-positive broken-dependency errors.
   - Orphan / depth / log-field warnings now carry `document_id` and `file_path` (or include them in the message string when the schema layer requires it).
   - `ontos link-check` reports a sharply lower `body.bare_id_token` count (target: < 10 across the 163-doc corpus, vs 11,163 today).
   - `ontos doctor` exits non-zero when activation reports hard errors.
6. PR opened against `main` with `Closes #115`, `Closes #116`, `Closes #117` in the body.

## 6. References

- `docs/reference/Ontos_Manual.md` (`ontos_manual`)
- `docs/reference/ontology_spec.md` (`ontology_spec`)
- `docs/reference/Ontos_Agent_Instructions.md` (`ontos_agent_instructions`)
- External reproduction inventory: `/Users/jonathanoh/ontos-issue-tree/company-os-ontos-rca-2026-05-22/`
- Prior v4.4 lifecycle: `docs/specs/project-ontos-v44-agentic-activation-resilience-spec.md`

```
