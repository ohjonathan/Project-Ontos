---
id: project-ontos-issue-119-triage-input
type: review
deliverable_id: project-ontos-issue-119-cli-activate-json-warning-metadata
phase: "-A.triage"
role: triage-input
status: active
captured_at: 2026-05-22
source: gh issue view 119 --repo ohjonathan/Project-Ontos
---

# Triage input — Project-Ontos GitHub issue #119 (verbatim)

This file is the verbatim findings input for Pre-A.triage of deliverable
`project-ontos-issue-119-cli-activate-json-warning-metadata`. The single
finding is the unfinished CLI-side parity work explicitly deferred from
PR #118 / v4.5.0 (deliverable `project-ontos-github-issues-115-117`,
D.6 final approval).

## Scope lock — single open follow-up issue

```
gh issue view 119 --repo ohjonathan/Project-Ontos --json number,title,body,state,url
```

Captured at execution start; one finding:

| # | Title | State | URL |
|---|---|---|---|
| 119 | CLI activate --json should expose structured warning metadata | OPEN | https://github.com/ohjonathan/Project-Ontos/issues/119 |

## Verbatim issue body

---

### Issue #119 — CLI activate --json should expose structured warning metadata
- URL: https://github.com/ohjonathan/Project-Ontos/issues/119
- State: OPEN

#### Summary

Follow-up from PR #118 / v4.5.0: the MCP `activate` tool now enriches activation warnings with structured metadata (`rule_id`, `document_id`, `file_path`), but the CLI JSON path still flattens warnings to bare message strings.

#### Background

PR #118 closed #117's main activation-diagnostic issues for the MCP/agent-facing path and recorded this as a non-blocking D.6 deferral. The remaining consistency gap is `ontos activate --json`: warnings such as orphan/depth/log-field diagnostics are still harder to triage from CLI automation than from MCP payloads.

#### Expected behavior

`ontos activate --json` should preserve structured warning metadata where available:

- `severity`
- `rule_id`
- `message`
- `document_id`
- `file_path`

For warnings without document context, `document_id` / `file_path` may be omitted or empty, but `rule_id` should still be present when the source class is known.

#### Acceptance criteria

- CLI JSON output remains backward compatible enough for existing consumers, or the change is documented if the shape must evolve.
- Activation warnings emitted from known documents include `rule_id`, `document_id`, and `file_path` in the JSON payload.
- Existing MCP activation warning enrichment remains unchanged and schema-valid.
- Tests cover at least orphan, dependency-depth, log-field, and broken/out-of-scope dependency warning shapes.

#### References

- Follow-up from PR #118: https://github.com/ohjonathan/Project-Ontos/pull/118
- Original issue context: #117
- D.6 final approval deferral: `docs/reviews/project-ontos-github-issues-115-117/final-approval.md`

## Carried-forward evidence (read-only)

The prior deliverable's review folder is the load-bearing precedent for #119:

| Path | Relevance |
|---|---|
| `docs/reviews/project-ontos-github-issues-115-117/final-approval.md` | D.6 verdict explicitly recording CLI `ontos activate --json` enrichment as a non-blocking deferral. |
| `docs/specs/project-ontos-github-issues-115-117-spec.md` | §2.2.2 documents the MCP activation warning contract this deliverable carries forward to the CLI. |
| `ontos/mcp/tools.py` | Lines 620–640 contain the `_validation_issues()` helper that is the parity baseline. |
| `tests/mcp/test_activation.py` | Asserts the MCP warning shape (`severity`, `rule_id`, `document_id`, `file_path`) that the CLI must mirror. |
| `ontos/core/types.py` | Lines 124–133 define `ValidationError`, the dataclass shared by both code paths. |
| `ontos/commands/activate.py` | Lines 104–105 are the current CLI flattening point (`issue.message` strings only). |

No external workspace reproduction tree is required; the regression evidence
lives entirely inside this repository.
