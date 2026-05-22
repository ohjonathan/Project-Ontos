---
id: project-ontos-github-issues-115-117-triage-report
deliverable_id: project-ontos-github-issues-115-117
phase: "-A.triage"
role: triage-author
family: codex
triage_input: docs/reviews/project-ontos-github-issues-115-117/github-issues-input.md
evidence_labels_used: [direct-run, static-inspection]
status: completed
---

# Triage Report — project-ontos-github-issues-115-117

## 1. Context header
- **Findings input:** `docs/reviews/project-ontos-github-issues-115-117/github-issues-input.md`
- **Date:** 2026-05-22
- **Triage Author family:** codex (orchestrator-authored under codex assignment;
  Pre-A.triage is not strict-P3 receipt-bound per
  `lifecycle-receipt-inventory.schema.yaml` `phase ∈ {B.1, B.2, D.2, D.5}`)
- **Overall verdict:** Proceed to Phase A with approved scope

## 2. Findings inventory

Three findings, sourced from `gh issue list --state open --limit 200` against
`ohjonathan/Project-Ontos` (live snapshot captured at execution start). No
duplicates. External RCA evidence captured by the reporter at
`/Users/jonathanoh/ontos-issue-tree/company-os-ontos-rca-2026-05-22/` is the
read-only reproduction input.

| # | Title | Source |
|---|---|---|
| 115 | MCP `get_context_bundle` returns schema-invalid `_ontos_warning` before activate | bug report (Johnny-OS smoke) |
| 116 | Document MCP host reload requirement after pipx upgrade | doc gap (Johnny-OS smoke) |
| 117 | Activation `usable_with_warnings`: false-positive `depends_on`, anonymous orphan warnings, 11k spurious body refs, narrow type/status schema | RCA report against live `company-os` workspace |

## 3. Per-finding dispositions

### Finding #115 — MCP `get_context_bundle` schema rejection

| Field | Value |
|---|---|
| Disposition | **In-Scope** |
| Evidence label | direct-run |
| Fast-patch? | No (touches MCP success schema + warning routing across read-only tools) |
| Phase routing | Phase A spec required (small surface, but the contract change must be specified explicitly so future tool additions follow the same rule) |
| Rationale | The MCP SDK rejects the tool response. `get_context_bundle` is the documented entry point AI agents call before/around `activate` (per `Ontos_Manual.md`), so a hard schema rejection blocks the documented usage pattern. The fix lives in the declared output schema (`ontos/mcp/schemas.py` `GetContextBundleResponse.warnings: List[str]`) plus the runtime injection at `ontos/mcp/server.py:755-767`; preferred remediation is to append the activation-not-performed entry to the already-declared `warnings` list and stop emitting an undeclared `_ontos_warning` key for `get_context_bundle`. Contract is small but invariant-bearing — full spec is appropriate. |
| Acceptance criteria | A `get_context_bundle` call before `activate` returns a schema-valid response whose `warnings` list contains an activation-not-performed entry; existing `_ontos_warning` opt-in behavior for tools explicitly registered in `READ_WARNING_TOOL_NAMES` is preserved or removed as the spec decides. Regression test in `tests/mcp/test_bundler.py` and / or `tests/mcp/test_schemas.py`. |

### Finding #116 — MCP host reload documentation

| Field | Value |
|---|---|
| Disposition | **In-Scope** |
| Evidence label | direct-run (reporter observed stale `ontos_version: 4.3.0` after `pipx upgrade`); static-inspection (current docs lack the section) |
| Fast-patch? | Doc-only changes typically qualify, but this change touches four files (`README.md`, `docs/reference/Ontos_Manual.md`, `docs/reference/Migration_v3_to_v4.md`, the next release note under `docs/releases/`) and must agree on wording — bundling with the #115 / #117 spec keeps the doc surface consistent. Not fast-patch. |
| Phase routing | Phase A spec required (the wording is normative; future upgrades will rely on this pattern). |
| Rationale | This is a documentation gap caused by the long-lived stdio MCP host model — MCP client processes hold a child process open across `pipx upgrade` boundaries, so users see stale versions until the host is restarted. No code change is mandatory for the documentation track; the optional doctor enhancement (detect CLI/server version mismatch) overlaps cleanly with #117's "doctor severity alignment" track and will be specified together. |
| Acceptance criteria | "Restart MCP hosts after upgrading Ontos" guidance lives in `README.md`, `docs/reference/Ontos_Manual.md`, `docs/reference/Migration_v3_to_v4.md`, and the next release note under `docs/releases/`. Wording covers `pipx upgrade ontos`, `pip install --upgrade ontos`, and `pipx install --force 'ontos[mcp]'`. |

### Finding #117 — Activation diagnostic signal + link-check noise + type/status vocabulary + doctor alignment

| Field | Value |
|---|---|
| Disposition | **In-Scope** |
| Evidence label | direct-run (reporter's `ontos activate --json` + `ontos link-check` against `company-os` SHA `56e9626a00fd3c9c2417682bfb6d20d7d2a8420a`, raw outputs captured under `/Users/jonathanoh/ontos-issue-tree/company-os-ontos-rca-2026-05-22/`); static-inspection (each "broken dependency" file existence-confirmed by `[ -f "$f" ]` loop, all 10 print EXISTS) |
| Fast-patch? | No. Multi-file surface across `ontos/core/graph.py`, `ontos/core/frontmatter.py`, `ontos/core/validation.py`, `ontos/core/types.py`, `ontos/core/body_refs.py`, `ontos/core/link_diagnostics.py`, `ontos/commands/doctor.py`, `ontos/mcp/tools.py`, `ontos/commands/activate.py`, plus tests + docs. |
| Phase routing | Phase A spec required (a coherent contract for `depends_on` resolution, warning enrichment, and type/status handling must be agreed before code lands). |
| Rationale | Activation is the documented "front door" for AI agents adopting Ontos (`docs/reference/Ontos_Agent_Instructions.md`); the current loud-but-low-signal output trains agents and humans to ignore the warning channel, which erodes the agent-friendly property the project is built on. The operator's direction calls for a single integrated track in Phase C covering: (a) `depends_on` path resolution (preserve existing doc-id behavior, add workspace-relative / absolute / declaring-doc-relative path fallback, treat existing non-doc files as external resolved dependencies, not broken graph errors); (b) warning enrichment with `rule_id`, `document_id`, `file_path`, severity, and message in MCP payloads + human output; (c) type/status vocabulary widening — extend or implement preserving repair so lifecycle artifacts (`handoff`, `tracker`, `retro`, `review`, `spec`, `report`, `adr`, `policy`; status `proposed`) survive without being silently demoted to `unknown`, with the original value preserved; (d) `body.bare_id_token` precision — require explicit reference syntax for unknown bare IDs or sharply narrow the generic scanner, preserving known-ID and markdown-link-target detection; (e) README/template scanning skip patterns; (f) `ontos doctor` severity alignment with activation/link-check when hard activation errors are present. |
| Acceptance criteria | After implementation, the same `company-os` reproduction tree (read-only) yields: zero false-positive broken-dependency errors at the workspace-rooted paths shown in `analysis/broken-deps-existence-check.md`; orphan / depth / log-field warnings now carry `document_id` and `file_path` (the new fields land in the public schema where the schema permits, otherwise appended into the message string); `body.bare_id_token` count drops dramatically without breaking known-ID or markdown-link-target detection; `ontos doctor` exits non-zero when activation reports hard errors. Regression tests under `tests/core/test_graph.py`, `tests/core/test_validation.py`, `tests/core/test_frontmatter_repair.py`, `tests/commands/test_link_check.py`, `tests/commands/test_doctor_phase4.py`, and the MCP suites. |

## 4. Adversarial flags raised

The triage author considered the following challenges before declaring the dispositions above. None reaches `direct-run` evidence sufficient to demote any of #115/#116/#117 from In-Scope, per the operator's scope-lock direction.

| # | Challenge considered | Adjudication |
|---|---|---|
| 115 | "Could this be a downstream MCP SDK behavior change (1.27.x), not an Ontos bug?" | The MCP SDK enforces the declared output schema; the output schema is owned by Ontos in `ontos/mcp/schemas.py`. The fix is on the Ontos side. |
| 115 | "Should we treat `_ontos_warning` as a deliberate non-schema diagnostic channel?" | No — the schema declares `additionalProperties: false`, so any additional key is a contract violation. The principled remediation is to use the declared `warnings: List[str]` field, which the spec will specify. |
| 116 | "Is this purely a pipx behavior issue, not an Ontos concern?" | The behavior is inherent to long-lived stdio child processes (any package manager + any stdio host); the user-facing remediation is documentation. Documenting in the migration guide + release note is the smallest principled response. |
| 117 | "Could the broken-dependency errors be a workspace-config issue (relative path base) rather than an Ontos bug?" | The reporter's `[ -f "$f" ]` loop confirms every flagged file exists at the workspace root; `mcp__ontos__workspace_overview` confirms identical workspace path between CLI and MCP. No path-base ambiguity. |
| 117 | "Should the type/status vocabulary remain strict to keep the schema honest?" | Strict vocabulary is the current behavior; the data shows it forces 50% of a real-world workspace into `type: unknown`, which destroys query value. The operator's direction is to widen or implement preserving repair while keeping the conservative repair path. |
| 117 | "Is `body.bare_id_token` worth keeping at all?" | The known-ID and markdown-link-target paths inside `link_diagnostics` are load-bearing. The narrowing should preserve those; only the generic prose scanner needs tightening. |
| 117 | "Will doctor severity alignment cascade into CI noise for existing repos?" | Likely, since most repos that surfaced this issue do already carry pre-existing data-quality issues. Mitigation lives in the spec: the alignment fires only when activation reports `error`-severity entries (hard errors), not on warnings. |

No reviewer challenge crosses the playbook §12.5 blocking threshold; all dispositions stand.

## 5. Phase A scope-lock candidates

The three In-Scope findings advance to Phase A as a single unified spec
(`docs/specs/project-ontos-github-issues-115-117-spec.md`). The spec must
include:

- A "Closes" mapping linking each spec sub-section to issue #115 / #116 / #117.
- The contract for `get_context_bundle` warnings (Section "#115").
- The full text of the MCP host-restart documentation (Section "#116").
- Six sub-sections for #117: depends_on resolution, warning enrichment, type/status widening, `body.bare_id_token` precision, README/template scanning, `ontos doctor` severity alignment.

Manifest gate `G-cardinality-2` already enforces that all three issues are mentioned in the spec (`grep -cE '#11[567]' docs/specs/...spec.md` expects `gte:3`).

## 6. Deferred / Rejected findings

None. The live `gh issue list` snapshot contains exactly the three findings classified above.

## 7. Overall verdict

**Proceed to Phase A with approved scope.**

All three In-Scope findings require a full spec; none qualifies for the
Phase C-direct fast-patch branch (issue #117 alone touches eight Ontos
source files and adds new tests; #115 touches the MCP success schema +
runtime injection point and is invariant-bearing; #116 is multi-file
documentation that benefits from being specified next to the related code
changes).

See `pre-a-triage-verdict.md` for the canonical exit-verdict artifact.
