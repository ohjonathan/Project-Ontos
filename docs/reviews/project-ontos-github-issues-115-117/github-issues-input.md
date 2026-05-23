---
id: project-ontos-github-issues-115-117-triage-input
type: review
deliverable_id: project-ontos-github-issues-115-117
phase: "-A.triage"
role: triage-input
status: active
captured_at: 2026-05-22
source: gh issue list --state open + /Users/jonathanoh/ontos-issue-tree/company-os-ontos-rca-2026-05-22/
---

# Triage input — Project-Ontos open GitHub issues (live)

This file is the verbatim findings input for Pre-A.triage of deliverable
`project-ontos-github-issues-115-117`. It bundles:

1. The full body of each open GitHub issue at execution start (captured
   via `gh issue view <n>` on 2026-05-22).
2. A pointer to the external read-only RCA evidence collected by the
   reporter at `/Users/jonathanoh/ontos-issue-tree/company-os-ontos-rca-2026-05-22/`.

The triage author classifies each finding (`In-Scope` / `In-Scope + fast-patch`
/ `Deferred` / `Rejected`) in `pre-a-triage-report.md`. Per the operator's
scope-lock direction, #115, #116, and #117 are **In-Scope** unless direct-run
evidence proves an issue is invalid or already fixed.

## Scope lock — live `gh issue list` snapshot

```
gh issue list --state open --limit 200 --json number,title,labels,url,createdAt,updatedAt
```

Captured at execution start; only three open issues exist:

| # | Title | Labels | Created |
|---|---|---|---|
| 115 | MCP get_context_bundle returns schema-invalid `_ontos_warning` before activate | bug | 2026-05-13 |
| 116 | Document MCP host reload requirement after pipx upgrade | documentation | 2026-05-13 |
| 117 | Activation `usable_with_warnings`: false-positive `depends_on` broken deps, anonymous orphan warnings, 11k spurious body refs, and overly narrow type/status schema | (none) | 2026-05-22 |

## Verbatim issue bodies

---

### Issue #115 — MCP get_context_bundle returns schema-invalid `_ontos_warning` before activate
- URL: https://github.com/ohjonathan/Project-Ontos/issues/115
- Labels: `bug`
- Created: 2026-05-13T16:19:55Z

#### Summary

Ontos `4.4.0` exposes `activate`, but `get_context_bundle` before activation returns `_ontos_warning` in `structuredContent`.

#### Actual

The MCP SDK rejects the tool result because the declared output schema has `additionalProperties: false`.

Observed Johnny-OS upgrade smoke error:

```text
Additional properties are not allowed ('_ontos_warning' was unexpected)
```

#### Expected

Tool results should remain schema-valid. Warnings should either be placed in the declared `warnings` field, or the pre-activation state should be surfaced through an MCP-safe error/result shape that conforms to the declared schema.

#### Evidence

During the Johnny-OS Ontos MCP upgrade smoke:
- `pipx upgrade ontos` upgraded Ontos from `4.3.0` to `4.4.0`.
- Raw MCP initialize returned `serverInfo.version=4.4.0` on stdout with empty stderr.
- Calling `get_context_bundle` before `activate` produced `_ontos_warning` in structured content.
- Calling `activate` first made `get_context_bundle` pass.

#### Environment

- macOS
- pipx Ontos `4.4.0`
- MCP SDK `1.27.x`

---

### Issue #116 — Document MCP host reload requirement after pipx upgrade
- URL: https://github.com/ohjonathan/Project-Ontos/issues/116
- Labels: `documentation`
- Created: 2026-05-13T16:20:06Z

#### Summary

After `pipx upgrade ontos`, existing `ontos serve` MCP child processes keep running the old package version.

#### Actual

Stale long-lived `ontos serve` processes continued reporting `4.3.0` after the CLI upgraded to `4.4.0`.

#### Expected

Docs should tell users to restart or reload MCP hosts after upgrading Ontos. Optionally, `ontos doctor` could detect stale running server versions and report a warning when the CLI version and active server versions differ.

#### Evidence

During the Johnny-OS Ontos MCP upgrade smoke:
- `ontos --version` reported `ontos 4.4.0` after `pipx upgrade ontos`.
- The current MCP health response still reported `ontos_version: 4.3.0` until old child processes were recycled.
- New raw `ontos serve --workspace ... --read-only` initialize checks reported `serverInfo.version=4.4.0`.

#### Environment

- macOS
- pipx Ontos upgraded from `4.3.0` to `4.4.0`
- MCP clients using stdio `ontos serve` children

---

### Issue #117 — Activation usable_with_warnings: false-positive depends_on broken deps, anonymous orphan warnings, 11k spurious body refs, and overly narrow type/status schema
- URL: https://github.com/ohjonathan/Project-Ontos/issues/117
- Labels: (none)
- Created: 2026-05-22T03:36:33Z

#### Environment

| Field | Value |
|---|---|
| Machine | `jonathans-mini.lan` ("Jonathan's Mac mini"), macOS 14 (Darwin 25.4.0) |
| company-os repo SHA | `56e9626a00fd3c9c2417682bfb6d20d7d2a8420a` on `main` (clean working tree) |
| Ontos CLI | `4.4.0` |
| CLI path | `/Users/jonathanoh/.local/bin/ontos` → pipx venv |
| Install | `pipx install 'ontos[mcp]'` on Python 3.14.4 |
| MCP activation status | `usable_with_warnings` (CLI and MCP agree) |
| Workspace path (CLI & MCP & health) | `/Users/jonathanoh/company-os` (identical across all sources) |

`.ontos.toml`:

```toml
[ontos]
version = "3.0"

[paths]
docs_dir = "docs"
logs_dir = "docs/logs"
context_map = "Ontos_Context_Map.md"

[scanning]
skip_patterns = ["_template.md", "archive/*", ".git/*", "node_modules/*", "__pycache__/*"]
scan_paths = []
default_scope = "docs"

[validation]
max_dependency_depth = 5
allowed_orphan_types = ["atom"]
```

#### Summary

Running Ontos 4.4.0 against a real, well-populated workspace (163 docs, 50
logs, deep dependency graph) produces an activation payload that is loud but
low-signal:

- **10 `error`-severity "broken dependency" warnings, all of which are false
  positives** — every flagged file exists on disk at the workspace-rooted
  path declared in `depends_on:`.
- **~90 `Document has no incoming dependencies` warnings, none of which carry
  a `document_id` or `file_path`** — agents and humans cannot triage them
  without a separate query.
- **50% of the workspace falls into `type: unknown`** because Ontos's type
  vocabulary is narrower than real-world artifact types (`handoff`,
  `tracker`, `retro`, `review`, `spec`, `report`, `adr`, `policy`).
- **`ontos link-check` reports 11,304 broken references**, of which **11,163
  are `body.bare_id_token`** false positives — Ontos's body-prose
  id-token scanner appears wildly imprecise on natural text.

The activation payload is the front door for AI agents adopting Ontos; the
current signal-to-noise ratio degrades agent decision-making and trains
agents to ignore the warning channel entirely.

#### Warning taxonomy (counts and shapes from this run)

| Class | Severity | Count | Carries doc id / file path? | Likely category |
|---|---|---|---|---|
| Broken `depends_on` for existing file | error | 10 | mentions doc id in message text | **Ontos bug** |
| `Document has no incoming dependencies` | warning | ~90 | **no** | **Ontos diagnostic clarity bug** |
| `Dependency depth N exceeds max 5` | warning | 5 | **no** | diagnostic clarity + threshold |
| `Log missing fields: branch[, ...]` | warning | 16 | **no** | partial repo issue + diagnostic clarity |
| `Log document missing 'concepts'` | warning | 3 | **no** | partial repo issue + diagnostic clarity |
| `invalid frontmatter field 'type'/'status' value '...'` | warning | 11 | yes (path + line) | mixed: repo renames + **schema gap** |
| `link-check.broken_references` (body.bare_id_token) | n/a | **11,163** | structured | **Ontos bug** (body scanner imprecise) |
| `link-check.broken_references` (body.markdown_link_target) | n/a | 131 | structured | ambiguous; needs sampling |
| `link-check.broken_references` (depends_on) | error | 10 | structured | same as row 1 above |
| `link-check.orphans` | n/a | 142 | (summary only) | diagnostic clarity gap |

#### RCA / likely causes

1. **`depends_on` validator never falls back to filesystem.** The validator
   looks up `depends_on` values against the loaded **doc-id** set rather
   than the **file-path** set, so a workspace-rooted *path* never matches a
   *doc id* and always fails. Suggested resolution order: match against
   loaded doc-ids → workspace-relative `stat()` → declaring-doc-relative
   `stat()` → broken.
2. **Warning payloads omit document context.** The schema warnings (invalid
   type/status) already include `file_path:line:col` — the format works and
   is grep-friendly. Orphans, depth warnings, and log-field warnings
   should be brought up to the same standard with `rule_id`, `document_id`,
   `file_path`.
3. **Type vocabulary is narrower than real-world artifact categories.** Real
   artifact types present: `handoff`, `handoff-report`, `tracker`, `retro`,
   `review`, `spec`, `report`, `adr`/`decision`, `policy`. Result: 82/163
   docs (50%) typed `unknown`. Extend vocab OR allow workspace-extensible
   types.
4. **Status vocabulary is too strict.** `proposed`, `ready`, `completed`,
   `revised-after-b.3`, `in-lifecycle` are rejected. Allow per-type status
   sets OR downgrade unknown status to a soft warning while preserving the
   original value in the graph.
5. **Body `bare_id_token` scanner has catastrophic precision against prose.**
   11,163 `body.bare_id_token` false positives across 163 documents (~70
   per doc). Most likely matching arbitrary prose tokens that resemble doc
   ids. Suggested: disable by default, scope to fenced code blocks / link
   targets, or require a sigil (`[[doc-id]]`) before considering a token a
   reference.
6. **README/template files are scanned as data documents.**
   `docs/logs/README.md` triggers "Log missing fields: branch" — the README
   is not a log but its location causes type-classification to treat it as
   one. Suggested: skip `README.md` and `_template.md` in typed subdirs by
   default, or require an `id:` frontmatter field to register as a document.
7. **`ontos doctor` and `ontos activate` disagree.** When `activate` reports
   `usable_with_warnings` with `error`-severity entries, `doctor` should
   reflect that. Today doctor reports `status: warning` with two soft items
   while activate reports 10 hard errors.

#### Reproduction (verbatim from issue body)

1. Clone `company-os` and check out `56e9626a00fd3c9c2417682bfb6d20d7d2a8420a`.
2. With `ontos 4.4.0` installed:
   ```
   cd company-os
   ontos activate --json | jq '.warnings | group_by(.severity) | map({severity: .[0].severity, n: length})'
   ```
3. Observe `error: 10` and `warning: 130+`.
4. Verify each "broken dependency" file exists on disk (all 10 print EXISTS).

If reproduction against the live company-os tree is not feasible, the
evidence captured under
`/Users/jonathanoh/ontos-issue-tree/company-os-ontos-rca-2026-05-22/` includes
the raw JSON for each command.

## External evidence inventory (read-only)

Root: `/Users/jonathanoh/ontos-issue-tree/company-os-ontos-rca-2026-05-22/`

| Path | Contents |
|---|---|
| `preflight/env.txt` | hostname, pwd, SHA, `which ontos`, `ontos --version`, date |
| `preflight/ontos-help.txt` | full `ontos --help` |
| `preflight/ontos-toml.txt` | copy of `.ontos.toml` (the user's workspace config) |
| `preflight/pipx-metadata.json` | pipx install record |
| `preflight/package-metadata.txt` | site-packages METADATA (confirms repo URL) |
| `evidence/ontos-activate.json` (+ `.stderr`, `.exit`) | full activation payload, exit 0 |
| `evidence/ontos-doctor.json` (+ `.stderr`, `.exit`) | doctor output, exit 0, `status: warning` |
| `evidence/ontos-map.json` (+ `.before/.after.txt`, `.exit`) | map output, exit 1, with on-disk Context Map rewrite |
| `evidence/ontos-link-check.json` (+ `.exit`) | 4.8 MB; 11,304 broken refs; exit 1 |
| `evidence/ontos-query-help.txt` / `ontos-export-help.txt` / `ontos-verify-help.txt` | subcommand help |
| `evidence/find-md.txt`, `git-ls-files.txt`, `rg-declared-paths.txt` | filesystem evidence for existence checks |
| `mcp/mcp-health.json` | server uptime, indexed-at, freshness mode |
| `mcp/mcp-parity-summary.md` | CLI vs MCP parity check (identical) |
| `analysis/broken-deps-existence-check.md` | per-path existence proof for all 10 false positives |
| `analysis/depth-warnings.md` | depth warning shapes (no doc id) |
| `analysis/log-missing-fields.md` | log-field warning shapes (no doc id) |
| `analysis/orphans-no-id.md` | ~90 anonymous orphan warning shape |
| `analysis/path-resolution-hypothesis.md` | proposed resolution order for `depends_on` |
| `analysis/schema-narrowness.md` | type/status vocab gap inventory |
| `analysis/workspace-root-and-cache.md` | CLI vs MCP workspace path parity |
| `repro/minimal-repro.md` | step-by-step repro for each bug class |

Treat this directory as read-only reproduction input. Do not mutate `company-os`.
