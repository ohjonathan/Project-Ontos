# D.2 Adversarial Review — project-ontos-github-issues-115-117

You are the **Adversarial Review** on Phase D.2 of deliverable `project-ontos-github-issues-115-117` for repo `ohjonathan/Project-Ontos`. Family: `gemini`.

Adversarial reviewer (lens: 'How does this break?'). Attack the landed implementation under hostile or edge-case inputs (concurrency, schema-evasion, regressions). Read the diffs carefully and find issues a unit test would not catch. Do NOT duplicate Peer or Alignment.

Phase D.2 reviews the LANDED IMPLEMENTATION (14 commits on branch codex/project-ontos-github-issues-115-117). Compare the diff against the spec; identify implementation issues, not spec issues. B.1 already closed 2 blockers in commit dd68231 — confirm they remain closed.

## Strict-P3 verdict shape (MANDATORY)

Your stdout response IS the verdict artifact. Output ONLY the verdict markdown — no preamble, no closing notes. The very first three characters of your response MUST be `---` (a YAML frontmatter open fence). Do NOT begin your response with any prose, narration, status update like "I have enough information to ..." or "Here is the verdict ...", planning notes, or markdown commentary. The wrapper's verdict-shape predicate rejects any output that does not begin with `---`.

Stdout must begin with the literal three-dash YAML frontmatter open fence `---` followed by a newline. Do NOT output a bare `-` or `--`; only `---` is a valid opening fence.

The verdict MUST contain:
- YAML frontmatter with `phase: D.2`, `role: adversarial`, `family: gemini`, `deliverable_id: project-ontos-github-issues-115-117`, `status: completed`.
- An ATX `#` heading after the frontmatter.
- A `## Verdict` heading.
- The first non-blank line under `## Verdict` is exactly ONE of: `Approve` | `Request changes` | `Reject` | `Concur`.

## Exact output skeleton

```markdown
---
id: project-ontos-github-issues-115-117-D.2-gemini-adversarial
deliverable_id: project-ontos-github-issues-115-117
phase: D.2
role: adversarial
family: gemini
status: complete
---

# D.2 Adversarial Review — gemini

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

# D.2 Review Packet — project-ontos-github-issues-115-117

Phase D.2 reviews the LANDED IMPLEMENTATION against the spec under three lenses (peer / alignment / adversarial). The packet below contains:

1. The full spec under review.
2. The 14-commit branch log.
3. `git diff --stat main..HEAD` summary.
4. The actual diff for `ontos/mcp/` (issue #115 surface) and `ontos/core/` + `ontos/io/` (issue #117 surface) and `ontos/commands/doctor.py` (severity alignment).
5. Test status: `.venv/bin/python -m pytest -q` reports **1321 passed, 2 skipped** at the head of this branch.

Reviewer scope (D.2): validate the implementation against §0-§3 of the spec. Preserved blockers from B.1 should be re-checked in D.2 (claude-opus F1 graph-edge cleanliness was closed in commit `dd68231` — re-verify in the diff below; gemini F1 path-traversal containment also closed in `dd68231`).

---

## Section 1 — Spec under review

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

## Section 2 — Branch commits (`git log main..HEAD`)

```
046031f feat(phase-b): B.1 three-lens review + B.3 consolidation
dd68231 fix(graph): close B.1 blockers — doc-id edge cleanliness + path-traversal containment
d01cb24 chore(tracker): Phase A + C complete; halt for strict-P3 dispatch authorization
8d19e6e docs(mcp): document MCP host reload requirement after pipx upgrade (#116)
93dc8f9 feat(loader,doctor): README/template skip + activation severity alignment (#117)
6ff7041 fix(link-check): tighten body.bare_id_token to require explicit wikilink sigil (#117)
f8182af feat(types): widen DocumentType/Status for lifecycle artifacts (#117)
d82e39c feat(mcp): enrich validation warnings with rule_id/document_id/file_path (#117)
37fe69f fix(graph): add depends_on path-resolution fallback for workspace files (#117)
801e06d fix(mcp): route pre-activate warning into get_context_bundle.warnings list (#115)
23a423f feat(phase-a): spec for #115/#116/#117 unified implementation
faa19e5 feat(pre-a): triage #115/#116/#117 — all In-Scope, proceed to Phase A
744b206 feat(llm-dev): scaffold deliverable manifest + tracker for #115/#116/#117
5767997 chore: update llm-dev-framework to v1.9.0 and add johnny-os onboarding
```

## Section 3 — Diff stat

```
 .johnny-os.yaml                                    |   17 +
 .llm-dev/config.yaml                               |    2 +-
 .llm-dev/framework                                 |    2 +-
 .ontos-internal/logs/2026-05-11_init.md            |   21 +
 AGENTS.md                                          |   14 +-
 Ontos_Context_Map.md                               | 1398 +++++++-------------
 README.md                                          |   11 +
 ...026-05-11_project-ontos-johnny-os-onboarding.md |   74 ++
 ...026-05-21_update-llm-dev-framework-to-v1-8-0.md |   66 +
 ...026-05-21_update-llm-dev-framework-to-v1-9-0.md |   59 +
 docs/reference/Migration_v3_to_v4.md               |   12 +
 docs/reference/Ontos_Manual.md                     |   19 +
 docs/releases/v4.5.0.md                            |   35 +
 ...b-issues-115-117-B.1-claude-opus-peer.prompt.md |  365 +++++
 ...s-115-117-B.1-claude-sonnet-alignment.prompt.md |  365 +++++
 ...issues-115-117-B.1-gemini-adversarial.prompt.md |  365 +++++
 ...b-issues-115-117-D.2-claude-opus-peer.prompt.md |  365 +++++
 ...s-115-117-D.2-claude-sonnet-alignment.prompt.md |  365 +++++
 ...issues-115-117-D.2-gemini-adversarial.prompt.md |  365 +++++
 ...sues-115-117-D.5-claude-opus-verifier.prompt.md |  365 +++++
 ...es-115-117-D.5-claude-sonnet-verifier.prompt.md |  365 +++++
 ...ub-issues-115-117-D.5-gemini-verifier.prompt.md |  365 +++++
 ...hub-issues-115-117-B.1-claude-opus-peer.raw.txt |   76 ++
 ...-issues-115-117-B.1-claude-opus-peer.stderr.txt |    0
 ...ues-115-117-B.1-claude-sonnet-alignment.raw.txt |   45 +
 ...-115-117-B.1-claude-sonnet-alignment.stderr.txt |    0
 ...b-issues-115-117-B.1-gemini-adversarial.raw.txt |   41 +
 ...ssues-115-117-B.1-gemini-adversarial.stderr.txt |    0
 .../B.1-claude-opus-peer.md                        |   76 ++
 .../B.1-claude-sonnet-alignment.md                 |   45 +
 .../B.1-gemini-adversarial.md                      |   41 +
 .../B.3-verdict.md                                 |   57 +
 .../github-issues-input.md                         |  273 ++++
 .../lifecycle-receipt-inventory.yaml               |   75 ++
 .../pre-a-triage-report.md                         |  115 ++
 .../pre-a-triage-verdict.md                        |   42 +
 ...ntos-github-issues-115-117-dispatch-intent.yaml |   85 ++
 ...ntos-github-issues-115-117-dispatch-result.yaml |  187 +++
 .../project-ontos-github-issues-115-117-spec.md    |  291 ++++
 .../project-ontos-github-issues-115-117.md         |   33 +
 manifests/project-ontos-github-issues-115-117.yaml |  251 ++++
 ontos/commands/doctor.py                           |   55 +
 ontos/core/body_refs.py                            |   48 +-
 ontos/core/frontmatter.py                          |   37 +-
 ontos/core/frontmatter_repair.py                   |   17 +-
 ontos/core/graph.py                                |  157 ++-
 ontos/core/link_diagnostics.py                     |   13 +-
 ontos/core/types.py                                |   35 +-
 ontos/core/validation.py                           |   14 +-
 ontos/io/files.py                                  |   31 +-
 ontos/io/snapshot.py                               |    6 +-
 ontos/mcp/schemas.py                               |   17 +
 ontos/mcp/server.py                                |   30 +-
 ontos/mcp/tools.py                                 |   60 +-
 scripts/llm-dev                                    |  262 +++-
 .../commands/test_agentic_activation_resilience.py |   29 +-
 tests/commands/test_doctor_phase4.py               |   29 +
 tests/core/test_body_refs.py                       |   54 +-
 tests/core/test_frontmatter_repair.py              |  152 ++-
 tests/core/test_graph.py                           |  172 +++
 tests/core/test_link_diagnostics.py                |    6 +-
 tests/mcp/test_activation.py                       |   97 ++
 62 files changed, 7022 insertions(+), 1047 deletions(-)

```

## Section 4a — `ontos/mcp/` diff (issue #115 surface)

```diff
diff --git a/ontos/mcp/schemas.py b/ontos/mcp/schemas.py
index 8ba4917..040c2d5 100644
--- a/ontos/mcp/schemas.py
+++ b/ontos/mcp/schemas.py
@@ -16,6 +16,15 @@ class StrictModel(BaseModel):
 class ValidationIssue(StrictModel):
     severity: str
     message: str
+    # (#117) Optional context fields so agents and humans can triage a warning
+    # without re-running queries. `rule_id` mirrors ValidationError.error_type
+    # (e.g. "orphan", "broken_link", "out_of_scope_dependency"). `document_id`
+    # / `file_path` are populated when the warning originates from a known
+    # document; absent when the warning is a snapshot-level note with no
+    # doc context.
+    rule_id: Optional[str] = None
+    document_id: Optional[str] = None
+    file_path: Optional[str] = None
 
 
 class ValidationPayload(StrictModel):
@@ -340,6 +349,14 @@ READ_WARNING_TOOL_NAMES = {
     "refresh",
 }
 
+# Tools whose declared success schema already carries a `warnings: List[str]`
+# field. For these, the pre-activate reminder is appended to that list rather
+# than injected as an undeclared `_ontos_warning` key — which the MCP SDK
+# rejects when the schema is `additionalProperties: false`. (Issue #115.)
+WARNINGS_LIST_TOOL_NAMES = {
+    "get_context_bundle",
+}
+
 
 def validate_success_payload(tool_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
     """Validate and normalize one tool success payload."""
diff --git a/ontos/mcp/server.py b/ontos/mcp/server.py
index 7fc1b28..48d38f2 100644
--- a/ontos/mcp/server.py
+++ b/ontos/mcp/server.py
@@ -21,9 +21,33 @@ from ontos.io.snapshot import create_snapshot
 from ontos.mcp._types import PortfolioIndexLike
 from ontos.mcp.cache import SnapshotCache
 from ontos.mcp.scanner import slugify
-from ontos.mcp.schemas import ToolErrorEnvelope, output_schema_for, validate_success_payload
+from ontos.mcp.schemas import (
+    READ_WARNING_TOOL_NAMES,
+    WARNINGS_LIST_TOOL_NAMES,
+    ToolErrorEnvelope,
+    output_schema_for,
+    validate_success_payload,
+)
 from ontos.mcp import tools as tool_impl
 
+_PRE_ACTIVATE_WARNING = (
+    "Ontos activation not performed this MCP session; call activate first."
+)
+
+
+def _attach_pre_activate_warning(tool_name: str, validated: Dict[str, Any]) -> None:
+    # Route via the channel each tool's schema declares: legacy
+    # `_ontos_warning` property for READ_WARNING_TOOL_NAMES; the declared
+    # `warnings: List[str]` field for WARNINGS_LIST_TOOL_NAMES. Strict schemas
+    # forbid undeclared keys (#115).
+    if tool_name in READ_WARNING_TOOL_NAMES:
+        validated["_ontos_warning"] = _PRE_ACTIVATE_WARNING
+        return
+    if tool_name in WARNINGS_LIST_TOOL_NAMES:
+        warnings_field = validated.setdefault("warnings", [])
+        if isinstance(warnings_field, list) and _PRE_ACTIVATE_WARNING not in warnings_field:
+            warnings_field.append(_PRE_ACTIVATE_WARNING)
+
 
 DEFAULT_USAGE_LOG_PATH = "~/.config/ontos/usage.jsonl"
 DEFAULT_PORTFOLIO_DB_PATH = Path.home() / ".config" / "ontos" / "portfolio.db"
@@ -761,9 +785,7 @@ def _invoke_read_tool(
         payload = tool_fn(tool_input, **kwargs)
         validated = validate_success_payload(tool_name, payload)
         if tool_name != "activate" and not getattr(cache, "activation_performed", False):
-            validated["_ontos_warning"] = (
-                "Ontos activation not performed this MCP session; call activate first."
-            )
+            _attach_pre_activate_warning(tool_name, validated)
         return _tool_success_result(validated)
     except OntosUserError as exc:
         return _tool_error_result(str(exc))
diff --git a/ontos/mcp/tools.py b/ontos/mcp/tools.py
index 64c272f..084fa4d 100644
--- a/ontos/mcp/tools.py
+++ b/ontos/mcp/tools.py
@@ -602,11 +602,11 @@ def _slugify_workspace_name(raw: str) -> str:
 def _normalize_warnings(
     validation: ValidationResult,
     snapshot_warnings: list[str],
-) -> list[dict[str, str]]:
-    warnings: list[dict[str, str]] = []
+) -> list[dict[str, Any]]:
+    warnings: list[dict[str, Any]] = []
     warnings.extend(_validation_issues(validation.errors))
     warnings.extend(_validation_issues(validation.warnings))
-    warnings.extend({"severity": "warning", "message": message} for message in snapshot_warnings)
+    warnings.extend(_snapshot_issue(message) for message in snapshot_warnings)
     return warnings
 
 
@@ -617,14 +617,58 @@ def _validation_payload(validation: ValidationResult) -> dict[str, Any]:
     }
 
 
-def _validation_issues(issues: list[Any]) -> list[dict[str, str]]:
-    return [
-        {
+def _validation_issues(issues: list[Any]) -> list[dict[str, Any]]:
+    # (#117) Surface document context (rule_id, document_id, file_path) so
+    # downstream agents can triage without a second query. Empty strings are
+    # squashed so the public payload stays compact.
+    enriched: list[dict[str, Any]] = []
+    for issue in issues:
+        record: dict[str, Any] = {
             "severity": issue.severity,
             "message": issue.message,
         }
-        for issue in issues
-    ]
+        rule_id = getattr(issue.error_type, "value", None) if getattr(issue, "error_type", None) else None
+        if rule_id:
+            record["rule_id"] = rule_id
+        doc_id = getattr(issue, "doc_id", "") or ""
+        if doc_id:
+            record["document_id"] = doc_id
+        file_path = getattr(issue, "filepath", "") or ""
+        if file_path:
+            record["file_path"] = file_path
+        enriched.append(record)
+    return enriched
+
+
+# (#117) Bare snapshot strings often originate from the loader and document
+# their own provenance prefix (e.g. "Log missing fields:", "invalid
+# frontmatter field"). Classify the prefix into a rule_id so the channel
+# becomes parseable; bare unknowns get a generic snapshot rule_id.
+_SNAPSHOT_RULE_PREFIXES = (
+    ("Log missing fields:", "schema.log_missing_fields"),
+    ("Log document missing", "schema.log_missing_concepts"),
+    ("invalid frontmatter field 'type'", "schema.invalid_type"),
+    ("invalid frontmatter field 'status'", "schema.invalid_status"),
+    ("invalid frontmatter", "schema.invalid_frontmatter"),
+    ("Impact reference", "impacts.broken"),
+    ("Broken dependency", "broken_link"),
+    ("External dependency resolved from disk", "out_of_scope_dependency"),
+    ("Document has no incoming dependencies", "orphan"),
+    ("Dependency depth", "depth"),
+)
+
+
+def _snapshot_issue(message: str) -> dict[str, Any]:
+    rule_id = "snapshot"
+    for prefix, candidate in _SNAPSHOT_RULE_PREFIXES:
+        if prefix in message:
+            rule_id = candidate
+            break
+    return {
+        "severity": "warning",
+        "rule_id": rule_id,
+        "message": message,
+    }
 
 
 def _ordered_export_payload(

```

## Section 4b — `ontos/core/` + `ontos/io/` diff (issue #117 surface)

```diff
diff --git a/ontos/core/body_refs.py b/ontos/core/body_refs.py
index 273bbc5..be98420 100644
--- a/ontos/core/body_refs.py
+++ b/ontos/core/body_refs.py
@@ -116,6 +116,7 @@ def scan_body_references(
     rename_target: Optional[str] = None,
     known_ids: Optional[set[str]] = None,
     include_skipped: bool = True,
+    include_generic_bare_id_token: bool = True,
 ) -> BodyReferenceScan:
     """Scan markdown body for reference matches.
 
@@ -123,6 +124,14 @@ def scan_body_references(
     - rename mode: `rename_target` is provided and only exact target matches are emitted.
     - link-check mode: `rename_target` is omitted and all candidate references are emitted.
       If `known_ids` is set, candidates are limited to that known set.
+
+    (#117) Generic-mode prose-token matching (the heuristic that flagged
+    11,163 false positives on a 163-doc workspace) is now opt-in via
+    `include_generic_bare_id_token`. When False AND `known_ids` is None
+    AND `rename_target` is None, BARE_ID_TOKEN matches require an explicit
+    `[[id]]` wikilink sigil. Markdown link target detection is unchanged.
+    Known-ID and rename modes are unchanged. Default True preserves
+    back-compat for existing callers.
     """
 
     lines = body.splitlines(keepends=True)
@@ -223,6 +232,7 @@ def scan_body_references(
                     rename_target=rename_target,
                     known_ids=known_ids,
                     line_is_reference_definition=line_is_reference_definition,
+                    include_generic_bare_id_token=include_generic_bare_id_token,
                 )
             )
 
@@ -378,6 +388,7 @@ def _scan_normal_text_segment(
     rename_target: Optional[str],
     known_ids: Optional[set[str]],
     line_is_reference_definition: bool,
+    include_generic_bare_id_token: bool = True,
 ) -> List[BodyReferenceMatch]:
     if line_is_reference_definition:
         return []
@@ -385,7 +396,10 @@ def _scan_normal_text_segment(
     matches: List[BodyReferenceMatch] = []
     link_targets = _find_markdown_link_targets(segment_text)
     occupied = [(item.full_start, item.full_end) for item in link_targets]
-    occupied.extend(_find_unsupported_spans(segment_text))
+    # (#117) Wikilink spans `[[…]]` are no longer treated as unsupported —
+    # they're now the canonical opt-in source for generic-mode bare-id-token
+    # matches when callers disable the prose heuristic.
+    occupied.extend(_find_unsupported_spans(segment_text, include_wikilinks=False))
 
     for link_target in link_targets:
         if rename_target is not None and link_target.normalized_id != rename_target:
@@ -419,8 +433,13 @@ def _scan_normal_text_segment(
     elif known_ids is not None:
         ordered_ids = sorted(known_ids, key=lambda item: (-len(item), item))
         bare_candidates = _iter_known_id_candidates(segment_text, ordered_ids)
-    else:
+    elif include_generic_bare_id_token:
         bare_candidates = _iter_generic_id_candidates(segment_text)
+    else:
+        # (#117) Generic prose-token heuristic disabled — fall back to
+        # explicit `[[id]]` wikilink sigils only. Suppresses the 11k-class
+        # false positives the prose scanner produced on natural text.
+        bare_candidates = _iter_wikilink_id_candidates(segment_text)
 
     for start, end, normalized_id in bare_candidates:
         if _overlaps_any(start, end, occupied):
@@ -705,9 +724,30 @@ def _is_reference_definition_line(line_text: str) -> bool:
     return _REFERENCE_DEF_RE.match(line_text) is not None
 
 
-def _find_unsupported_spans(segment_text: str) -> List[Tuple[int, int]]:
+def _find_unsupported_spans(
+    segment_text: str,
+    *,
+    include_wikilinks: bool = True,
+) -> List[Tuple[int, int]]:
+    patterns = [_REFERENCE_STYLE_RE, _HTML_OR_AUTOLINK_RE]
+    if include_wikilinks:
+        patterns.append(_WIKILINK_RE)
     spans: List[Tuple[int, int]] = []
-    for pattern in (_REFERENCE_STYLE_RE, _WIKILINK_RE, _HTML_OR_AUTOLINK_RE):
+    for pattern in patterns:
         for match in pattern.finditer(segment_text):
             spans.append(match.span())
     return spans
+
+
+def _iter_wikilink_id_candidates(text: str) -> Iterable[Tuple[int, int, str]]:
+    # (#117) Generic-mode opt-in source for BARE_ID_TOKEN: only emit
+    # candidates extracted from explicit `[[id]]` wikilink sigils.
+    for match in _WIKILINK_RE.finditer(text):
+        raw_inner = match.group(0)[2:-2]
+        inner = raw_inner.strip()
+        if not inner:
+            continue
+        offset = raw_inner.index(inner) if inner in raw_inner else 0
+        start = match.start() + 2 + offset
+        end = start + len(inner)
+        yield start, end, inner
diff --git a/ontos/core/frontmatter.py b/ontos/core/frontmatter.py
index ed44907..ca2352b 100644
--- a/ontos/core/frontmatter.py
+++ b/ontos/core/frontmatter.py
@@ -211,26 +211,23 @@ def normalize_depends_on(value, on_warning: Optional[Callable[[str], None]] = No
 
 def normalize_type(value, on_error: Optional[Callable[[str, Any, List[str]], None]] = None) -> Any:
     """Normalize type field to DocumentType enum.
-    
-    Args:
-        value: Raw value from YAML.
-        on_error: Optional callback (message, value, options) for failures.
-        
-    Returns:
-        DocumentType enum (ATOM if invalid).
+
+    Returns DocumentType.UNKNOWN as the conservative-repair fallback when the
+    extended vocabulary cannot match. (#117) The on_error callback receives
+    the original raw value so the validator can surface it instead of
+    silently demoting.
     """
     from ontos.core.types import DocumentType
-    
+
     if isinstance(value, DocumentType):
         return value
-        
-    # Standard string normalization
+
     type_str = 'unknown'
     if isinstance(value, str):
         type_str = value.strip().lower()
     elif isinstance(value, list) and value:
         type_str = str(value[0]).strip().lower()
-        
+
     try:
         return DocumentType(type_str)
     except (ValueError, TypeError):
@@ -239,28 +236,24 @@ def normalize_type(value, on_error: Optional[Callable[[str, Any, List[str]], Non
             on_error(f"Invalid doc type '{type_str}'", type_str, options)
         return DocumentType.UNKNOWN
 
+
 def normalize_status(value, on_error: Optional[Callable[[str, Any, List[str]], None]] = None) -> Any:
     """Normalize status field to DocumentStatus enum.
-    
-    Args:
-        value: Raw value from YAML.
-        on_error: Optional callback (message, value, options) for failures.
-        
-    Returns:
-        DocumentStatus enum (DRAFT if invalid).
+
+    Returns DocumentStatus.UNKNOWN as the conservative-repair fallback when
+    the extended vocabulary cannot match. (#117)
     """
     from ontos.core.types import DocumentStatus
-    
+
     if isinstance(value, DocumentStatus):
         return value
-        
-    # Standard string normalization
+
     status_str = 'unknown'
     if isinstance(value, str):
         status_str = value.strip().lower()
     elif isinstance(value, list) and value:
         status_str = str(value[0]).strip().lower()
-        
+
     try:
         return DocumentStatus(status_str)
     except (ValueError, TypeError):
diff --git a/ontos/core/frontmatter_repair.py b/ontos/core/frontmatter_repair.py
index 6b9469d..e11b706 100644
--- a/ontos/core/frontmatter_repair.py
+++ b/ontos/core/frontmatter_repair.py
@@ -18,25 +18,26 @@ from ontos.io.yaml import parse_frontmatter_content
 
 
 TYPE_REPAIRS: Dict[str, str] = {
+    # (#117) `review`, `retro`, `tracker` are now first-class canonical
+    # types in DocumentType — no repair needed. Aliases that aren't
+    # canonical map to the closest canonical value.
     "proposal": "strategy",
-    "review": "log",
-    "retro": "log",
-    "retrospective": "log",
-    "tracker": "log",
-    "final-report": "log",
-    "final_report": "log",
+    "retrospective": "retro",
+    "final-report": "report",
+    "final_report": "report",
     "verdict": "log",
     "prompt": "log",
     "artifact": "log",
 }
 
 STATUS_REPAIRS: Dict[str, str] = {
-    "completed": "complete",
+    # (#117) `completed`, `ready`, `proposed`, `revised`, `in-lifecycle`
+    # are now first-class canonical statuses. Remaining repairs cover
+    # genuine aliases.
     "passed": "complete",
     "approve": "complete",
     "approved": "complete",
     "final": "complete",
-    "ready": "complete",
     "done": "complete",
     "pr-open": "active",
     "in-review": "active",
diff --git a/ontos/core/graph.py b/ontos/core/graph.py
index d483492..1c18f21 100644
--- a/ontos/core/graph.py
+++ b/ontos/core/graph.py
@@ -9,11 +9,12 @@ Phase 2 Decomposition - Created from Phase2-Implementation-Spec.md Section 4.3
 
 from __future__ import annotations
 from dataclasses import dataclass, field
+from pathlib import Path
 from typing import Dict, List, Set, Optional, Tuple, Union
 
 from ontos.core.types import DocumentData, ValidationError, ValidationErrorType
 from ontos.core.suggestions import suggest_candidates_for_broken_ref
- 
+
 # SEVERITY RATIONALE (v3.3 Track A1)
 # ---------------------------------
 # - ERROR (depends_on): Structural, defines the graph integrity.
@@ -22,6 +23,67 @@ DEPENDS_ON_SEVERITY_DEFAULT = "error"
 IMPACTS_SEVERITY_DEFAULT = "warning"
 DESCRIBES_SEVERITY_DEFAULT = "warning"
 
+# (#117) depends_on entries that resolve to a real file outside the loaded
+# doc set are downgraded to a soft warning. The constant lives here so
+# verify-frontmatter and link-check share the same severity floor.
+OUT_OF_SCOPE_DEPENDENCY_SEVERITY = "warning"
+
+
+def _looks_like_path(dep_id: str) -> bool:
+    # A pure doc-id never contains a path separator or '.md' suffix.
+    return "/" in dep_id or "\\" in dep_id or dep_id.lower().endswith(".md")
+
+
+def _resolve_depends_on_path(
+    dep_id: str,
+    doc: DocumentData,
+    docs_by_resolved_path: Dict[Path, str],
+    workspace_root: Optional[Path],
+    workspace_root_resolved: Optional[Path],
+) -> Tuple[Optional[str], Optional[Path]]:
+    """Try to resolve a `depends_on` entry as a filesystem path.
+
+    Returns (resolved_doc_id, external_path):
+        (id, None) — path resolved to a loaded doc; caller treats as a graph edge.
+        (None, p)  — path exists on disk inside the workspace but is not loaded;
+                      caller treats as an out-of-scope dependency (warning).
+        (None, None) — no path resolution OR resolved path escapes the
+                       workspace; caller falls back to broken-link.
+
+    Containment: any candidate whose resolved path (with symlinks followed)
+    is outside `workspace_root_resolved` is rejected (no fall-through to
+    external-dep emission). This is the gemini-B.1-F1 fix — `Path.resolve`
+    follows symlinks, so a malicious or buggy `depends_on: '../../etc/passwd'`
+    must not leak filesystem state through the activation warnings channel.
+    """
+    if workspace_root is None or not _looks_like_path(dep_id):
+        return None, None
+
+    candidates: List[Path] = []
+    raw = Path(dep_id)
+    if raw.is_absolute():
+        candidates.append(raw)
+    else:
+        candidates.append(workspace_root / raw)
+        doc_dir = doc.filepath.parent if doc.filepath else workspace_root
+        candidates.append(doc_dir / raw)
+
+    for candidate in candidates:
+        try:
+            resolved = candidate.resolve(strict=False)
+        except (OSError, RuntimeError):
+            continue
+        if workspace_root_resolved is not None:
+            try:
+                resolved.relative_to(workspace_root_resolved)
+            except ValueError:
+                continue
+        if resolved in docs_by_resolved_path:
+            return docs_by_resolved_path[resolved], None
+        if candidate.exists():
+            return None, candidate
+    return None, None
+
 
 @dataclass
 class GraphNode:
@@ -51,52 +113,105 @@ class DependencyGraph:
 
 def build_graph(
     docs: Dict[str, DocumentData],
-    severity_map: Optional[Dict[str, str]] = None
+    severity_map: Optional[Dict[str, str]] = None,
+    workspace_root: Optional[Path] = None,
 ) -> Tuple[DependencyGraph, List[ValidationError]]:
     """Build dependency graph from document dictionary.
 
     Args:
         docs: Dictionary mapping doc_id to DocumentData
         severity_map: Optional mapping of error types to severities
+        workspace_root: Optional workspace root. When provided, `depends_on`
+            entries that don't match a loaded doc id are tried as
+            workspace-relative, declaring-doc-relative, or absolute paths
+            before being reported as broken (#117). Loaded-doc-path matches
+            become normal edges; existing-but-not-loaded paths become a
+            soft OUT_OF_SCOPE_DEPENDENCY warning instead of a hard error.
 
     Returns:
-        Tuple of (DependencyGraph, list of broken link errors)
+        Tuple of (DependencyGraph, list of broken/out-of-scope link errors)
     """
     severity_map = severity_map or {}
     graph = DependencyGraph()
-    errors = []
+    errors: List[ValidationError] = []
     existing_ids = set(docs.keys())
     depends_on_severity = severity_map.get(
         "depends_on",
         severity_map.get("broken_link", DEPENDS_ON_SEVERITY_DEFAULT),
     )
     circular_severity = severity_map.get("circular", depends_on_severity)
+    out_of_scope_severity = severity_map.get(
+        "out_of_scope_dependency", OUT_OF_SCOPE_DEPENDENCY_SEVERITY
+    )
+
+    docs_by_resolved_path: Dict[Path, str] = {}
+    workspace_root_resolved: Optional[Path] = None
+    if workspace_root is not None:
+        try:
+            workspace_root_resolved = workspace_root.resolve()
+        except (OSError, RuntimeError):
+            workspace_root_resolved = None
+        for d in docs.values():
+            try:
+                docs_by_resolved_path[d.filepath.resolve()] = d.id
+            except (OSError, RuntimeError):
+                continue
 
     for doc_id, doc in docs.items():
         depends_on = doc.depends_on
-        # Handle enum types
         doc_type = doc.type.value
-        graph.add_node(doc_id, doc_type, str(doc.filepath), depends_on)
-
-        # Check for broken links
+        # (#117) Resolve each declared dep BEFORE building the graph node so
+        # the edges + reverse_edges record doc-id targets, not raw path
+        # strings. Doc-id matches and path-resolved-to-loaded-doc both
+        # become regular edges; out-of-scope or broken entries are dropped
+        # from the edge list and reported as ValidationErrors.
+        resolved_depends_on: List[str] = []
         for dep_id in depends_on:
-            if dep_id not in existing_ids:
-                # Generate candidate suggestions (v3.2)
-                candidates = suggest_candidates_for_broken_ref(dep_id, docs)
-                fix_suggestion = f"Remove '{dep_id}' from depends_on or create the missing document"
-                
-                if candidates:
-                    suggestion_text = ", ".join(c[0] for c in candidates)
-                    fix_suggestion += f". Did you mean: {suggestion_text}?"
-
+            if dep_id in existing_ids:
+                resolved_depends_on.append(dep_id)
+                continue
+
+            resolved_id, external_path = _resolve_depends_on_path(
+                dep_id, doc, docs_by_resolved_path, workspace_root, workspace_root_resolved
+            )
+            if resolved_id is not None:
+                resolved_depends_on.append(resolved_id)
+                continue
+            if external_path is not None:
                 errors.append(ValidationError(
-                    error_type=ValidationErrorType.BROKEN_LINK,
+                    error_type=ValidationErrorType.OUT_OF_SCOPE_DEPENDENCY,
                     doc_id=doc_id,
                     filepath=str(doc.filepath),
-                    message=f"Broken dependency: '{dep_id}' (declared in {doc_id}) does not exist",
-                    fix_suggestion=fix_suggestion,
-                    severity=circular_severity if dep_id == doc_id else depends_on_severity
+                    message=(
+                        f"External dependency resolved from disk: '{dep_id}' "
+                        f"(declared in {doc_id}) exists at "
+                        f"'{external_path}' but is not a loaded document."
+                    ),
+                    fix_suggestion=(
+                        "If the target should be tracked as a doc, add an "
+                        "Ontos frontmatter id; otherwise this can be left as a "
+                        "soft external reference."
+                    ),
+                    severity=out_of_scope_severity,
                 ))
+                continue
+
+            candidates = suggest_candidates_for_broken_ref(dep_id, docs)
+            fix_suggestion = f"Remove '{dep_id}' from depends_on or create the missing document"
+            if candidates:
+                suggestion_text = ", ".join(c[0] for c in candidates)
+                fix_suggestion += f". Did you mean: {suggestion_text}?"
+
+            errors.append(ValidationError(
+                error_type=ValidationErrorType.BROKEN_LINK,
+                doc_id=doc_id,
+                filepath=str(doc.filepath),
+                message=f"Broken dependency: '{dep_id}' (declared in {doc_id}) does not exist",
+                fix_suggestion=fix_suggestion,
+                severity=circular_severity if dep_id == doc_id else depends_on_severity
+            ))
+
+        graph.add_node(doc_id, doc_type, str(doc.filepath), resolved_depends_on)
 
     return graph, errors
 
diff --git a/ontos/core/link_diagnostics.py b/ontos/core/link_diagnostics.py
index eb39e88..e74010e 100644
--- a/ontos/core/link_diagnostics.py
+++ b/ontos/core/link_diagnostics.py
@@ -330,13 +330,20 @@ def run_link_diagnostics(
                 known_ids=active_ids,
                 include_skipped=False,
             )
-            # Pass 2: Generic unknown scan — finds references to IDs that
-            # don't exist (broken reference detection).  Uses the
-            # _looks_like_doc_id filter to suppress false positives.
+            # Pass 2: Generic unknown scan — finds broken references to
+            # IDs that don't exist. (#117) The prose-token heuristic
+            # (`_looks_like_doc_id`) produced ~11k false positives per
+            # 163-doc corpus; it is now disabled by passing
+            # include_generic_bare_id_token=False. Broken markdown link
+            # targets still surface because link_target detection is
+            # independent of the bare-token heuristic. Broken bare
+            # references inside explicit `[[id]]` wikilink sigils still
+            # surface via _iter_wikilink_id_candidates.
             generic_scan = scan_body_references(
                 path=doc.filepath,
                 body=doc.content,
                 include_skipped=False,
+                include_generic_bare_id_token=False,
             )
             # Merge both passes, deduplicating by position.
             seen_positions: set[tuple[int, int]] = set()
diff --git a/ontos/core/types.py b/ontos/core/types.py
index 9b194bf..eb82c7b 100644
--- a/ontos/core/types.py
+++ b/ontos/core/types.py
@@ -29,7 +29,14 @@ class CurationLevel(IntEnum):
 # =============================================================================
 
 class DocumentType(str, Enum):
-    """Document types in the Ontos ontology."""
+    """Document types in the Ontos ontology.
+
+    Canonical types: kernel/strategy/product/atom/log/reference/concept.
+    (#117) Lifecycle artifact types added so real engineering workspaces
+    (handoffs, trackers, retros, reviews, specs, reports, ADRs, policies)
+    are not silently demoted to `unknown`. Conservative repair still
+    falls back to `unknown` when the value matches nothing.
+    """
     KERNEL = "kernel"
     STRATEGY = "strategy"
     PRODUCT = "product"
@@ -37,11 +44,26 @@ class DocumentType(str, Enum):
     LOG = "log"
     REFERENCE = "reference"
     CONCEPT = "concept"
+    HANDOFF = "handoff"
+    TRACKER = "tracker"
+    RETRO = "retro"
+    REVIEW = "review"
+    SPEC = "spec"
+    REPORT = "report"
+    ADR = "adr"
+    POLICY = "policy"
     UNKNOWN = "unknown"
 
 
 class DocumentStatus(str, Enum):
-    """Document lifecycle status."""
+    """Document lifecycle status.
+
+    Canonical statuses: draft/active/deprecated/archived/rejected/complete/
+    auto-generated/scaffold/pending_curation/in_progress.
+    (#117) Lifecycle workflow statuses (proposed, ready, completed,
+    revised, in-lifecycle) added for non-kernel artifacts; `completed` is
+    an alias of `complete` retained to preserve real-world variation.
+    """
     DRAFT = "draft"
     ACTIVE = "active"
     DEPRECATED = "deprecated"
@@ -52,6 +74,11 @@ class DocumentStatus(str, Enum):
     SCAFFOLD = "scaffold"
     PENDING_CURATION = "pending_curation"
     IN_PROGRESS = "in_progress"
+    PROPOSED = "proposed"
+    READY = "ready"
+    COMPLETED = "completed"
+    REVISED = "revised"
+    IN_LIFECYCLE = "in-lifecycle"
     UNKNOWN = "unknown"
 
 
@@ -68,6 +95,10 @@ class ValidationErrorType(Enum):
     CURATION = "curation"
     IMPACTS = "impacts"
     DEPTH = "depth"
+    # (#117) depends_on entry resolved as a path against the filesystem but
+    # the target is not a loaded doc — treat as a soft external dependency
+    # rather than a hard broken-link error.
+    OUT_OF_SCOPE_DEPENDENCY = "out_of_scope_dependency"
 
 
 # =============================================================================
diff --git a/ontos/core/validation.py b/ontos/core/validation.py
index efc7c66..5fb4aec 100644
--- a/ontos/core/validation.py
+++ b/ontos/core/validation.py
@@ -78,13 +78,18 @@ class ValidationOrchestrator:
     def __init__(
         self,
         docs: Dict[str, DocumentData],
-        config: Optional[Dict[str, Any]] = None
+        config: Optional[Dict[str, Any]] = None,
+        workspace_root: Optional[Any] = None,
     ):
         """Initialize with documents and optional config.
 
         Args:
             docs: Dictionary mapping doc_id to DocumentData
             config: Optional configuration dict
+            workspace_root: Optional workspace root for depends_on path
+                resolution. When provided, depends_on entries that look like
+                paths are tried against the filesystem before being reported
+                as broken (#117).
         """
         self.docs = docs
         self.config = config or {}
@@ -92,6 +97,7 @@ class ValidationOrchestrator:
             **REFERENCE_SEVERITY_DEFAULT,
             **self.config.get("severity_map", {}),
         }
+        self.workspace_root = workspace_root
         self.errors: List[ValidationError] = []
         self.warnings: List[ValidationError] = []
 
@@ -121,7 +127,11 @@ class ValidationOrchestrator:
 
     def validate_graph(self) -> None:
         """Validate dependency graph: broken links, cycles, orphans, depth."""
-        graph, broken_link_errors = build_graph(self.docs, severity_map=self.severity_map)
+        graph, broken_link_errors = build_graph(
+            self.docs,
+            severity_map=self.severity_map,
+            workspace_root=self.workspace_root,
+        )
         self.errors.extend([e for e in broken_link_errors if e.severity == "error"])
         self.warnings.extend([e for e in broken_link_errors if e.severity == "warning"])
 
diff --git a/ontos/io/files.py b/ontos/io/files.py
index bbe614a..8271b43 100644
--- a/ontos/io/files.py
+++ b/ontos/io/files.py
@@ -219,6 +219,22 @@ def load_frontmatter(
     return None, None
 
 
+def _is_validation_excluded_by_name(path: Path) -> bool:
+    # (#117) README.md / *_template.md sit alongside data docs in typed
+    # subdirs but rarely declare valid frontmatter; treating them as docs
+    # produces noise like "Log missing fields: branch" on README.md.
+    name = path.name.lower()
+    return name == "readme.md" or name.endswith("_template.md")
+
+
+def _has_explicit_id(doc: DocumentData) -> bool:
+    # An explicit id: in frontmatter opts a README/_template into being
+    # treated as a regular doc. doc.frontmatter holds the raw frontmatter
+    # dict; the loader fills doc.id from path.stem as a fallback, so we
+    # check the raw dict, not doc.id.
+    return isinstance(doc.frontmatter, dict) and "id" in doc.frontmatter
+
+
 def load_documents(
     paths: List[Path],
     frontmatter_parser: Callable[[str], Tuple[Dict[str, Any], str]],
@@ -263,13 +279,22 @@ def load_documents(
                 # content.startswith('---') with no leading whitespace. The leniency handles BOM
                 # artifacts and minor formatting issues in imported/external files.
                 content = raw_bytes.decode('utf-8', errors='replace').lstrip()
-                
+
                 doc, doc_issues = load_document_from_content(path, content, frontmatter_parser)
+
+                # (#117) README.md and *_template.md files are typically not
+                # data docs. Skip them unless they declare an explicit `id:`
+                # frontmatter field (escape hatch for repos that intentionally
+                # track these). Silently drop both the doc and any parser
+                # warnings the file produced so the loader stays quiet.
+                if _is_validation_excluded_by_name(path) and not _has_explicit_id(doc):
+                    continue
+
                 issues.extend(doc_issues)
-                
+
                 if cache and mtime is not None:
                     cache.set(path, doc, mtime)
-            
+
             # Duplicate ID handling
             # Duplicate ID detection is case-sensitive by design.
             # YAML keys are case-sensitive per spec, so 'my_doc' and 'MY_DOC' are distinct IDs.
diff --git a/ontos/io/snapshot.py b/ontos/io/snapshot.py
index d04ed97..a183932 100644
--- a/ontos/io/snapshot.py
+++ b/ontos/io/snapshot.py
@@ -74,13 +74,13 @@ def create_snapshot(
                 )
             filtered_docs[doc_id] = doc
 
-    # Build graph
-    graph, _ = build_graph(filtered_docs)
+    # Build graph (workspace_root threaded for #117 path-fallback resolution).
+    graph, _ = build_graph(filtered_docs, workspace_root=root)
 
     # Run structural validation only (no vocabulary check).
     # Snapshot is an IO-layer operation — vocabulary checking requires
     # project-level config (known_concepts) which is a command-layer concern.
-    orchestrator = ValidationOrchestrator(filtered_docs, {})
+    orchestrator = ValidationOrchestrator(filtered_docs, {}, workspace_root=root)
     validation_result = orchestrator.validate_all()
     
     # Get git commit

```

## Section 4c — `ontos/commands/doctor.py` diff (doctor severity alignment)

```diff
diff --git a/ontos/commands/doctor.py b/ontos/commands/doctor.py
index 5b5d659..541b5d4 100644
--- a/ontos/commands/doctor.py
+++ b/ontos/commands/doctor.py
@@ -346,6 +346,57 @@ def check_context_map(repo_root: Optional[Path] = None) -> CheckResult:
         )
 
 
+def check_activation_health(
+    scope: Optional[str] = None,
+    repo_root: Optional[Path] = None,
+) -> CheckResult:
+    """(#117) Align doctor severity with activation/link-check health.
+
+    Runs the same snapshot + validation pipeline as `ontos activate` and
+    reports `failed` when any hard error-severity entry is present. Warnings
+    alone remain `warning` (today's behavior); a clean snapshot is `success`.
+    """
+    try:
+        from ontos.io.snapshot import create_snapshot
+
+        root = resolve_project_root(repo_root=repo_root)
+        snapshot = create_snapshot(root, include_content=False, scope=scope)
+    except Exception as exc:
+        return CheckResult(
+            name="activation_health",
+            status="warning",
+            message="Activation health check skipped",
+            details=str(exc),
+        )
+
+    errors = snapshot.validation_result.errors
+    warnings_list = snapshot.validation_result.warnings
+    if errors:
+        details = "; ".join(
+            f"[{e.error_type.value}] {e.message}" for e in errors[:5]
+        )
+        return CheckResult(
+            name="activation_health",
+            status="failed",
+            message=(
+                f"{len(errors)} activation error(s), "
+                f"{len(warnings_list)} warning(s) — doctor exit aligns with hard errors"
+            ),
+            details=details,
+        )
+    if warnings_list:
+        return CheckResult(
+            name="activation_health",
+            status="warning",
+            message=f"{len(warnings_list)} activation warning(s); no hard errors",
+        )
+    return CheckResult(
+        name="activation_health",
+        status="success",
+        message="Activation clean (no errors or warnings)",
+    )
+
+
 def check_validation(scope: Optional[str] = None, repo_root: Optional[Path] = None) -> CheckResult:
     """Check 6: No validation errors in current documents."""
     try:
@@ -790,6 +841,10 @@ def _run_doctor_command(options: DoctorOptions) -> Tuple[int, DoctorResult]:
         lambda: check_docs_directory(options.scope, repo_root),
         lambda: check_context_map(repo_root),
         lambda: check_validation(options.scope, repo_root),
+        # (#117) Doctor severity now reflects activation hard-error severity.
+        # If `ontos activate` reports any error-severity entry, this check
+        # contributes a `failed` status and doctor exits non-zero.
+        lambda: check_activation_health(options.scope, repo_root),
         check_cli_availability,
         lambda: check_agents_staleness(repo_root),
         lambda: check_environment_manifests(repo_root),

```

## Section 5 — Test status

Targeted suites: 1320 passed (pre-blocker-fix). After the dd68231 blocker fix that addressed claude-opus B.1 F1 and gemini B.1 F1, the full suite reports 1321 passed, 2 skipped.

```
.venv/bin/python -m pytest -q tests/mcp/ tests/core/ tests/commands/test_link_check.py tests/commands/test_doctor_phase4.py tests/commands/test_agentic_activation_resilience.py
```

End of D.2 packet.

