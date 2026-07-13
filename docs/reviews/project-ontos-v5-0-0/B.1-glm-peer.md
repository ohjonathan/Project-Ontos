---
phase: B.1
role: peer
family: glm
deliverable_id: project-ontos-v5-0-0
status: completed
---

# Ontos 5.0.0 B.1 GLM peer review

Independent peer assessment of Ontos 5.0.0 at product commit
`5678e910ce11ed7a3546822cf3e34d50c5741681` ("fix: align v5 command contracts")
relative to base `454b102` ("Log v4.7.1 release session"). The review reads the
v5 spec, manifest, migration guide, core implementation, and focused
contract/safety tests, then runs bounded read-only checks. No product files
were modified; dependencies were installed into an isolated venv outside the
workspace, and the v5 branch's product code (`ontos/`, `tests/`) is byte-identical
between the reviewed head `5678e91` and the current checkout, so the suite
results apply directly to the reviewed head.

Scope items examined: schema-4 command envelopes, exit taxonomy, declarative
command registry, canonical YAML parsing and surgical frontmatter writes,
physical one-based link lines and wikilink alias/heading resolution, MCP and
rename durability (lock-before-plan, recovery journal, no unscoped git
rollback), iterative graph traversal with case-sensitive path identity, legacy
fork/repo slimming, and hash-bound evidence isolation on a sibling ref.

## Method and bounded read-only checks

All checks ran read-only against the working tree (product code identical to
`5678e91`). Python 3.14.6 in an isolated venv with `pyyaml`, `tomli_w`,
`pytest`, `mcp`, and `pydantic`.

| Check | Command | Result |
|---|---|---|
| Cardinality (version/schema) | `PYTHONPATH=. python -c 'import ontos; from ontos.ui.json_output import COMMAND_ENVELOPE_SCHEMA_VERSION as s; assert (ontos.__version__,s)==("5.0.0","4.0")'` | PASS — version `5.0.0`, schema `4.0` |
| Exit taxonomy | `ExitCode` enum | PASS — `[0,1,2,3,5,130]`; code `4` reserved (absent) |
| Registry invariant | `command_registry.COMMAND_SPECS` | PASS — 27 commands, no dup (import-time guard), canonical paths `mcp install` / `export data` / `tree`→`map` |
| Focused contract/safety suite | `pytest tests/test_cli_contract_v4.py tests/core/test_body_refs.py tests/core/test_link_diagnostics.py tests/core/test_graph.py tests/core/test_rename_transaction.py tests/mcp/test_server_integration.py tests/mcp/test_rename_document.py` | PASS — 228 passed |
| Golden master comparison (G-test-2) | `python tests/golden/compare_golden_master.py --fixture all` | PASS — `medium` + `small`, 5.0.0 metadata |
| Full product suite (G-test-1 / D.2) | `PYTHONPATH=. python -m pytest -q` | PASS — 1536 passed, 1 warning (expected `emit_error` DeprecationWarning) |
| Repo slimming (G-scope-1) | `test ! -e .ontos/scripts` + CI grep | PASS — `.ontos/scripts` absent, CI no longer invokes it; 43 legacy scripts deleted |
| No unscoped git rollback | `grep -rn "git checkout -- \." ontos/core/rename_transaction.py ontos/mcp/rename_tool.py` | PASS — none; recovery uses exact-byte `recover_rename_transaction` |
| Live envelope smoke | `ontos link-check/env/export data/--json` | PASS — schema 4.0, `result` block present, `--json` before/after subcommand equivalent (only `timings_ms` differs), usage failure emits exactly one envelope, exit 2 |
| Evidence isolation | sha256-verify indexed artifacts at recorded `evidence_commit` `7a5c1d4` | PASS — 14/14 hashes match, 0 orphans, 0 missing |

Migration-guide claims verified live: schema-4 envelope with `result.status` /
`result.kind` / `result.exit_category` / `result.diagnostics`; nested canonical
`command` path (`export data`); global `--json` works before or after the
subcommand; JSON mode writes exactly one envelope to stdout with empty stderr;
`env --json` returns a structured object in `data` (`$schema`, `manifests`,
`onboarding_steps`, ...).

## Evidence: strengths

**Schema-4 envelopes and exit taxonomy** — `ontos/ui/json_output.py:16` pins
`COMMAND_ENVELOPE_SCHEMA_VERSION = "4.0"`. `ExitCode` (`:29-37`) defines
`0/1/2/3/5/130` and omits `4`, matching the reserved-code contract.
`_exit_category` (`:456-476`) collapses unknown/reserved nonzero codes to
`internal` rather than leaking ad-hoc values, and `_diagnostics_payload`
(`:361-405`) derives `basis`/`complete`/`counts` from `data.summary` or direct
count keys while `_numeric_counts` (`:408-413`) excludes booleans and negative
values. Live `link-check --json` produced the documented `result` block with
`diagnostics.complete: true` and a `data.summary`-backed counts map.

**Declarative command registry** — `ontos/command_registry.py:50-104` is the
single source of truth for parser builders, handlers, aliases, visibility,
result kinds, and nested paths. An import-time dedup guard (`:107-109`) raises
on duplicate top-level names. `command_path` (`:151-161`) returns canonical
space-joined paths for nested commands (`mcp install`, `export data`) and
resolves hidden aliases (`tree`/`validate`/`agent-export`) without
hyphen-synthesizing.

**Canonical parsing and surgical writes** — `ontos/io/yaml.py:57-83`
(`split_frontmatter_text`) recognizes only unindented `---` fences so a
literal `---` inside a YAML scalar is never a delimiter, and
`assert_frontmatter_roundtrip` (`:115-130`) fails closed unless serialized
frontmatter reloads exactly. `ontos/core/frontmatter_edit.py:60-147`
(`patch_frontmatter_fields`) preserves BOM, leading whitespace, comments,
quoting, ordering, and line endings, and explicitly rejects duplicates
(`:99-100`), block scalars/anchors/aliases (`:169-179`), and collection
comments that would be discarded (`:191-192`). `read_utf8_for_mutation`
(`:241-246`) strictly UTF-8-decodes mutation targets and surfaces
`InvalidDocumentEncodingError` rather than silently corrupting bytes.

**Physical link lines and wikilink resolution** — `ontos/core/body_refs.py`
uses 1-based line indices (`:161-162`) over the body, and
`link_diagnostics.py:504,512-518` adds `_body_line_offset(doc)`
(`link_diagnostics.py:754-796`) to reconstruct the physical file line,
matching the migration guide's "remove consumer-side frontmatter-line offset."
Alias/heading wikilinks (`[[id|Alias]]`, `[[id#Heading]]`) resolve the target
while keeping display text out of the target stream (`body_refs.py:824-844`),
and alias/heading spans are explicitly excluded from being treated as additional
targets (`body_refs.py:479-486`). Code-fence (`:271-307`) and inline-code
(`:310-367`) zone handling is CommonMark-aware.

**MCP and rename durability** — Both surfaces lock before clean-check and plan
construction: CLI `rename.py:171-173` (lock → recover → locked-plan) and MCP
`rename_tool.py:316-330` (lock → recover → clean check → plan). On commit
failure both restore via `RenameTransaction.rollback` →
`recover_rename_transaction` (`rename_transaction.py:111-112,115-158`), which
validates journal shape, rejects symlinks (`:146-147`), re-checks workspace
containment (`:142-145`), and restores only touched paths via atomic
`_atomic_bytes` (`:41-59`, using `O_EXCL`+`O_NOFOLLOW`+`fsync` of file and
directory). There is no unscoped `git checkout -- .`; planned-vs-committed set
equality is verified (`rename.py:336-339`, `rename_tool.py:504-516`). The lock
substrate (`ontos/core/locking.py`) is TOCTOU-hardened: no-follow directory
walks reject symlinks/reparse points in every parent segment (`:217-280`,
`:283-429`), the stable directory inode is flock-ed so unlinking the visible
lockfile cannot split coordination (`:65-99`), and the open handle is
re-verified against the visible path while held (`:163-197`).

**Iterative graph traversal** — `ontos/core/graph.py` `detect_cycles`
(`:372-424`) uses an explicit frame stack (no recursion cliff) with
deterministic canonical cycle rotation (`:436-446`). `calculate_depths`
(`:519-581`) runs over SCCs from iterative Kosaraju (`:584-636`), so cycles do
not corrupt depth. Path identity uses NFC-normalized `casefold`, not
`os.path.normcase`, with an explicit rationale that `normcase` is an identity
no-op on macOS case-insensitive APFS (`:45-55`). `_LoadedPathIndex`
(`:67-123`) is collision-aware (exact / casefolded / inode) and fail-closed
(`None` = ambiguous) rather than last-wins, and `_resolve_depends_on_path`
(`:147-186`) rejects any resolved path that escapes the workspace root after
symlink resolution (the gemini-B.1-F1 containment fix).

**MCP error boundary and pre-activation warnings** —
`ontos/mcp/server.py:835-916` (`_invoke_boundary`) is the single telemetry,
policy, validation, warning, and error boundary. It preserves
`OntosUserError.code` in the structured envelope (`:898-902`), handles
`OntosInternalError` and generic `Exception` separately, and attaches
pre-activation warnings to both read and portfolio tool results
(`:891-896`) — confirming the migration guide's "portfolio reads receive the
same pre-activation warning behavior as workspace reads."

**`graph_stats.by_type` open map** — `ontos/mcp/tools.py:63-107`
(`build_canonical_snapshot_view`) seeds every canonical ontology type with zero
and retains extension/unknown values encountered, then asserts
`sum(by_type.values()) == total_count` (`:97-99`), satisfying the
"exhaustive open map whose values sum to total" contract.

**Repo slimming and evidence isolation** — `.ontos/scripts/` and its CI
execution are removed; package commands own hook/validation behavior. The
lifecycle evidence is hash-bound on sibling ref `lifecycle-evidence/project-ontos-v5-0-0`.
At the recorded `evidence_commit` `7a5c1d4`, all 14 indexed artifacts
(`evidence-index.yaml` at `5678e91`, `schema_version: 1`) match their recorded
sha256 with zero orphans and zero missing entries. Strict-P3 is honestly
attempted and withheld: `lifecycle-receipt-inventory.yaml` carries
`receipts: []`, `attempt-summary.md` records the provider `Execution error`
without synthesis, and `final-approval.md` marks D.6 `WITHHELD` — no receipt
was fabricated.

## Findings

### F1 — Stale/misleading comments around rename git-clean and rollback (Low)

Several comments describe pre-v5 or otherwise inaccurate behavior on the
rename durability surface. The code is correct in every case; only the
documentation contradicts the implementation or the migration guide.

- `ontos/core/git.py:19-21` — module docstring states the multi-file
  `rename_tool` rollback "runs `git checkout -- .` over the whole workspace."
  This is exactly the behavior the v5 migration guide removes
  (`docs/releases/v5.0.0.md:189-191`: "Ontos no longer executes an unscoped
  `git checkout -- .` rollback"). The v5 `rename_tool.py` restores via
  `recover_rename_transaction` (exact bytes, touched paths only); the
  docstring is stale and misrepresents a safety-critical property.
- `ontos/mcp/rename_tool.py:423-426` — comment claims git clean-state "was
  already enforced by `_preflight` before we acquired `workspace_lock()`" and
  that "re-checking here would false-positive because `.ontos.lock` is now an
  untracked file." Both clauses are wrong: `_preflight`
  (`rename_tool.py:168-211`) performs no git check (the actual check is at
  `:323`, inside the lock, after `recover_rename_transaction` at `:322`), and
  `is_workspace_clean` (`ontos/core/git.py:65`) already ignores `.ontos.lock`
  and `.ontos/transactions/` via `internal_paths`, so a post-lock re-check
  would not false-positive. The real reason for `check_git=False` is simply to
  avoid a redundant second check.
- `ontos/commands/rename.py:388-389,397-400` — `build_rename_plan` docstring
  repeats the same inaccurate "MCP enforces before acquiring `workspace_lock()`"
  / "post-lock check would false-positive" framing.

Severity: Low. Documentation only; no behavioral impact. The CLI calls
`build_rename_plan` with the default `check_git=True` after acquiring the lock
(`rename.py:171` then `:634`), which works precisely because
`is_workspace_clean` ignores `.ontos.lock`. Recommend correcting the three
comment sites to match the actual lock→recover→clean→plan sequencing and the
v5 no-unscoped-rollback contract.

### F2 — Envelope `result.exit_category` diverges from `exit_code` on incomplete-load runs (Low / Informational)

For `link-check --json --scope docs` on this repository, the envelope reports
`exit_code: 0` (clean) alongside `result.status: "incomplete"` (one
`load_warning`) which collapses to `result.exit_category: "findings"`
(`ontos/ui/json_output.py:464-469`). `link-check`'s own exit gate
(`link_diagnostics.py:973-986`) returns `0` for a load-warnings-only run
(only duplicates/broken/orphans/unallowlisted-file-deps drive `1`/`3`), while
`ExitCategory` (`json_output.py:40-48`) has no `incomplete` member, so the
catch-all maps "incomplete" to `findings`. A consumer that maps process exits
exclusively via `result.exit_category` would therefore classify a clean exit-0
diagnostic as "findings." This is the explicitly-tested, by-design contract
(`tests/test_cli_contract_v4.py:271-282`; `tests/commands/test_link_check.py:244-245,325`),
and the migration guide mitigates it by directing consumers to branch on
`result.status` for outcome quality. Severity: Low/Informational — documented
and tested, but the `exit_code=0` / `exit_category=findings` divergence on
load-warning-only runs is a mild semantic wart; consider either documenting the
divergence in the migration guide or adding a distinct `incomplete` exit
category.

### F3 — Strict-P3 lifecycle attempt head precedes the reviewed head (Informational)

The strict-P3 attempt was run against product head `8f4fc884...` ("feat!:
prepare Ontos 5.0.0 structural release") — one commit before the reviewed
head `5678e91` ("fix: align v5 command contracts"). `5678e91` changed product
code under `ontos/` (`cli.py`, `json_output.py`, `link_diagnostics.py`,
`server.py`, `config.py`, and ~20 command modules) plus tests, and is covered
by the passing product gates (1536-unit suite + golden master) but not by any
successful strict-P3 receipt — that attempt failed with an empty receipt
inventory, which is honestly withheld (`final-approval.md:42-46`,
`docs/releases/v5.0.0.md:18-22`). Separately, the post-`5678e91` rerun-staging
commits (`e707c4a`..`55e538a`) moved the `lifecycle-evidence/project-ontos-v5-0-0`
sibling ref from `7a5c1d4` to `55e538a` and removed the in-tree
`evidence-index.yaml`; this is outside the reviewed diff
(`454b102..5678e91`) and explains why `verify_lifecycle_evidence_ref.py` exiting
nonzero against the current tree is a rerun-staging artifact rather than an
evidence-integrity defect at the reviewed head (all 14 artifacts verify
cleanly against `7a5c1d4`). Severity: Informational. Consistent with the
transparent D.6 withholding; no product-code defect.

## Verdict

Approve

Ontos 5.0.0 at `5678e91` faithfully implements the v5 structural-release
contract: schema-4 command envelopes with a result/diagnostics block, a
reserved-code exit taxonomy, a declarative command registry with canonical
nested paths, canonical YAML parsing and surgical byte-preserving frontmatter
writes, physical one-based link lines with correct alias/heading handling,
durable MCP/CLI rename (lock-before-plan, exact-byte recovery journal, no
unscoped git rollback) under a TOCTOU-hardened cross-platform lock, iterative
case-sensitive graph traversal, removal of the legacy fork and its CI
execution, and hash-bound evidence isolation on a sibling ref. All bounded
read-only checks pass: the focused contract/safety suite (228), the golden
master comparison, the full product suite (1536), and cardinality/scope gates;
evidence artifacts verify cleanly (14/14 sha256) at the recorded
`evidence_commit`. The strict-P3 withholding is honest and transparent
(`receipts: []`, no synthesis). The three findings are non-blocking: two are
stale/inaccurate comments and a tested envelope edge case (Low), and one is
lifecycle head-drift context (Informational). None is a product-code defect
that blocks the structural release's quality or completeness. Recommend
correcting the F1 comment sites and optionally addressing F2 in a follow-up;
neither gates release authorization, which remains a maintainer decision
outside this B.1 peer verdict.
