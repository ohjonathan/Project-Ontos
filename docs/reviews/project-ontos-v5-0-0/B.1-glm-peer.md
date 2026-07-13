---
phase: B.1
role: peer
family: glm
deliverable_id: project-ontos-v5-0-0
status: completed
---

# Ontos 5.0.0 B.1 GLM peer review

Independent peer assessment of Ontos 5.0.0 at product commit
`5678e910ce11ed7a3546822cf3e34d50c5741681` relative to base `454b102`.
Scope: v5 spec, manifest, migration guide, core implementation, focused
contract/safety tests, and bounded read-only verification. Product files were
not modified; evidence review ran against the product commit and the hash-bound
sibling evidence ref `lifecycle-evidence/project-ontos-v5-0-0@7a5c1d4`.

## Method

Read `docs/specs/project-ontos-v5-0-0-spec.md`, `manifests/project-ontos-v5-0-0.yaml`,
`docs/releases/v5.0.0.md`, and the tracker. Examined `ontos/ui/json_output.py`,
`ontos/command_registry.py`, `ontos/core/graph.py`, `ontos/core/body_refs.py`,
`ontos/core/link_diagnostics.py`, `ontos/core/rename_transaction.py`,
`ontos/core/frontmatter_edit.py`, `ontos/core/git.py`, `ontos/io/yaml.py`,
`ontos/commands/rename.py`, `ontos/mcp/rename_tool.py`, `ontos/mcp/tools.py`,
`ontos/mcp/server.py`, and `ontos/mcp/schemas.py`. Read focused tests
`tests/test_cli_contract_v4.py`, `tests/core/test_graph.py`,
`tests/core/test_rename_transaction.py`, `tests/core/test_body_refs.py`,
`tests/core/test_link_diagnostics.py`, `tests/commands/test_rename.py`, and
`tests/mcp/test_rename_document.py`.

## Evidence by contract area

### Schema-4 envelopes — PASS

`ontos/ui/json_output.py:16` defines `COMMAND_ENVELOPE_SCHEMA_VERSION = "4.0"`.
`_emit_command_envelope` (`ontos/ui/json_output.py:288`) emits a top-level
`result` object with `status`, `kind`, `exit_category`, and `diagnostics`
(`basis`, `complete`, `counts`) alongside the retained `data` payload. Execution
status (`status`) is decoupled from domain outcome (`result.status`): a successful
diagnostic command that found issues yields `status:"success"` with
`result.status:"findings"` and exit `1` (`ontos/ui/json_output.py:201-285`).
`_result_status` reconciles an explicit caller value, `_LEGACY_RESULT_STATUS`
aliases, incomplete-count keys, and exit-code fallback
(`ontos/ui/json_output.py:416-453`). `test_cli_contract_v4.py:246` pins the
separation of execution/findings and count basis.

### Exit taxonomy — PASS

`ExitCode` is an `IntEnum` over `{0, 1, 2, 3, 5, 130}` with code 4 deliberately
absent (`ontos/ui/json_output.py:29-37`). `ExitCategory` mirrors the documented
categories (`ontos/ui/json_output.py:40-48`). `_exit_category`
(`ontos/ui/json_output.py:456-476`) maps 130→interrupted, collapse-unknown nonzero
execution failures to `internal`, and never leaks an ad-hoc category.
`test_cli_contract_v4.py:67-74` asserts code 4 stays reserved and that an
undocumented category (`"error"`) is sanitized to `internal`
(`test_cli_contract_v4.py:77-86`). Per-command exit surface in
`docs/releases/v5.0.0.md:82-100` matches the implementation: `query` uses `2`
for input failures and `5` for runtime failures (`test_cli_contract_v4.py:195-230`),
and `rename` maps `commit_failed`/`partial_commit_mismatch` to `INTERNAL` and all
other refusals to `USAGE` (`ontos/commands/rename.py:1397-1401`).

### Command registry — PASS

`ontos/command_registry.py:50-104` is the single declarative source for parser
builders, handlers, aliases, visibility, result kinds, and nested paths.
Duplicate-name detection runs at import time (`ontos/command_registry.py:108-109`).
`command_path` (`ontos/command_registry.py:151-162`) produces canonical
space-separated paths (`mcp install`, `export data`) instead of legacy hyphenated
synthetics, matching `docs/releases/v5.0.0.md:48-59`. `test_cli_contract_v4.py:52-95`
asserts the registry is complete and unique, aliases (`tree`/`map`,
`validate`/`verify`) share their canonical argument contract, and every parser
choice carries a `_handler_name` default.

### Canonical parsing and surgical writes — PASS

`ontos/io/yaml.py` is the canonical frontmatter parser used by
`parse_frontmatter` (`ontos/core/frontmatter.py:22`) and the loader. Mutation paths
use `patch_frontmatter_fields` (`ontos/core/frontmatter_edit.py:60-147`), which
preserves BOM, leading whitespace, dominant line endings, inline comments,
quoting, and ordering; rejects block scalars, anchors/aliases, duplicate
top-level fields, and nested inline collections; and re-validates via
`assert_frontmatter_roundtrip` (`ontos/io/yaml.py:115-130`) and a semantic
equality check before returning. `rename.py` field patching
(`ontos/commands/rename.py:836-1060`) preserves padding around replaced scalars
(`_replace_preserving_padding`, `rename.py:1187-1191`).

### Link lines — PASS

Body-reference locations are physical one-based file lines.
`scan_body_references` (`ontos/core/body_refs.py:111-251`) assigns
`line_no = index + 1` (`body_refs.py:162`), and `link_diagnostics._body_line_offset`
(`ontos/core/link_diagnostics.py:754-796`) reconstructs the frontmatter/leading-
whitespace offset so body-relative scanner coordinates restore to physical file
lines without changing the loader. Wikilink aliases/headings resolve by target:
`_iter_wikilink_id_candidates` (`ontos/core/body_refs.py:824-844`) strips `|Alias`
and `#Heading` to the target part, and rename splices the replacement into the
target range only, retaining display text (`_replacement_for_match`,
`rename.py:1223-1269`). The generic prose-token heuristic that produced ~11k false
positives is opt-in via `include_generic_bare_id_token=False` on the diagnostics
path (`ontos/core/link_diagnostics.py:498-503`).

### MCP and rename durability — PASS

MCP reads, portfolio tools, and writes share one invocation boundary:
`_invoke_boundary` (`ontos/mcp/server.py:835-916`) catches `OntosUserError` and
preserves `exc.code` (`server.py:898-902`). CLI rename acquires `workspace_lock`
before clean-state checking and plan construction
(`ontos/commands/rename.py:168-173`); MCP rename locks, recovers any prior
transaction, then checks git-clean (`ontos/mcp/rename_tool.py:316-329`).
`RenameTransaction.prepare` (`ontos/core/rename_transaction.py:67-105`) journals
exact pre-write bytes via `_atomic_bytes` (O_EXCL, O_NOFOLLOW, fsync + directory
fsync). `recover_rename_transaction` (`rename_transaction.py:115-157`) restores
only touched paths, validates journal shape, refuses symlinks, and proves
containment before writing. CLI and MCP share `build_rename_plan`
(`ontos/commands/rename.py:367-543`), eliminating per-call-site divergence.
Unscoped `git checkout -- .` is not used: the only matches are docstrings and a
test docstring describing what the implementation deliberately avoids
(`ontos/core/git.py:20-21`, `ontos/mcp/rename_tool.py:18`). `rollback_path`
(`ontos/core/git.py:77-152`) proves trackedness before any `git checkout -- <path>`
and never deletes a tracked file. `test_rename_document.py:141-165` AST-guards
that `buffer_write` is the sole mutation channel (no `os.rename`/`buffer_move`).

### Graph traversal — PASS

`detect_cycles` (`ontos/core/graph.py:372-424`) uses an explicit-stack iterative
DFS with canonical cycle rotation. `calculate_depths` (`graph.py:519-581`)
condenses to SCCs (`_strongly_connected_components`, iterative Kosaraju,
`graph.py:584-636`) and runs an iterative Kahn-style topological longest-path.
Path identity is case-aware via `_casefold_path` (`graph.py:45-55`) plus a
collision-fail-closed `_LoadedPathIndex` (`graph.py:67-123`); macOS APFS
case-insensitivity is handled without `os.path.normcase`. Deep corpora are
tested without Python's recursion cliff: 1500-node cycle
(`tests/core/test_graph.py:368-380`) and 2000-node depth chain
(`test_graph.py:615-626`). Path-traversal `depends_on` is contained to the
workspace and falls through to broken-link severity (`graph.py:126-186`), verified
by `test_graph.py:176-198`.

### Repo slimming — PASS

`.ontos/scripts/` is absent at the product commit, and CI no longer invokes
`pytest .ontos/scripts/tests` (`G-scope-1` gate passes). The legacy fork modules
were removed entirely (diff stat shows wholesale deletion of
`.ontos/scripts/ontos/*` and `.ontos/scripts/tests/*`). Package commands own hook
and validation behavior (`ontos/commands/hook.py`, `ontos/commands/verify.py`).

### Evidence isolation — PASS

Raw lifecycle evidence is isolated on
`lifecycle-evidence/project-ontos-v5-0-0@7a5c1d47894568c80305cf126cc2401156adf301`
and hash-bound by `docs/reviews/project-ontos-v5-0-0/evidence-index.yaml`
(schema_version 1, 14 entries). `scripts/verify_lifecycle_evidence_ref.py` checks
both directions: every indexed path's sha256 against the ref, and the ref's tree
against the index for unindexed orphans. At the pinned commit `7a5c1d4`, all 14
indexed entries match (0 sha256 errors, 0 orphans, 0 absent). D.6 is honestly
WITHHELD (`docs/reviews/project-ontos-v5-0-0/final-approval.md:39-57`): product,
docs, and packaging gates pass, but strict-P3 produced no genuine external
receipt. No merge/tag/release/PyPI/issue-closure is authorized by this
deliverable.

## Bounded read-only checks

| Check | Command | Result |
|-------|---------|--------|
| Cardinality | `PYTHONPATH=. python -c 'assert (ontos.__version__,SCHEMA)==("5.0.0","4.0")'` | PASS |
| Legacy fork absent | `test ! -e .ontos/scripts && ! grep -q 'pytest .ontos/scripts/tests' .github/workflows/ci.yml` | PASS |
| Focused contract/safety suite | `pytest tests/test_cli_contract_v4.py tests/core/test_body_refs.py tests/core/test_link_diagnostics.py tests/core/test_graph.py tests/core/test_rename_transaction.py tests/mcp/test_server_integration.py tests/mcp/test_rename_document.py` | 228 passed |
| Complete product suite (G-test-1) | `pytest -q` | 1536 passed in 72s |
| Golden comparison (G-test-2) | `tests/golden/compare_golden_master.py --fixture all` | All comparisons PASS |
| Documentation validation | `ontos map --strict --scope docs` | exit 0 |
| Lifecycle evidence ref (pinned) | sha256 + tree parity against `7a5c1d4` | 14/14 match, 0 orphans |

Documentation validation reports one `invalid_enum` warning for
`docs/reviews/project-ontos-v5-0-0/canary/claude-opus-canary.md:6` (`status:
approved`), but that canary artifact exists only on the lifecycle-evidence
branch (absent at product commit `5678e91`); the product commit's documentation
validation is clean, matching `final-approval.md` gate row 2.

## Findings

### F1 — Portfolio read preactivation warning is partial (LOW)

The migration guide states "Portfolio reads also receive the same pre-activation
warning behavior as workspace reads" (`docs/releases/v5.0.0.md:142-145`).
`_invoke_portfolio_tool` correctly forwards `cache=cache`
(`ontos/mcp/server.py:690-712`), and `_invoke_boundary` reaches
`_attach_pre_activate_warning` (`server.py:891-896`). However, only
`get_context_bundle` is in `WARNINGS_LIST_TOOL_NAMES` (`ontos/mcp/schemas.py:382-384`).
`project_registry` and `search` are in neither `READ_WARNING_TOOL_NAMES`
(`schemas.py:366-376`) nor the warnings-list set, and
`ProjectRegistryResponse`/`SearchResponse` (`schemas.py:249-268`) declare no
`warnings` field. Because the `StrictModel` forbids undeclared keys, the
preactivation reminder is silently dropped for those two tools. This is a
documentation fidelity gap, not a contract defect; the fix is either to add a
`warnings` field to those two schemas or to narrow the docs claim to
`get_context_bundle`.

### F2 — Lifecycle evidence verifier resolves the ref HEAD, not the pinned commit (LOW)

`scripts/verify_lifecycle_evidence_ref.py:38` resolves the evidence REF to its
current HEAD (`git rev-parse --verify {evidence_ref}^{commit}`) rather than the
recorded `evidence_commit` (`7a5c1d4`). Re-running the verifier after the sibling
ref advanced (it now also carries the B.2 canary artifacts at `0c80825`) yields
spurious "unindexed evidence artifact" errors even though the index matched at
the certified commit. The pinned commit verifies cleanly (14/14). This is a
tooling reproducibility nit, not a product-code defect; the script would be more
rigorous if it pinned verification to `evidence_commit`.

### F3 — Stale test docstring references the forbidden rollback (NIT)

`tests/mcp/test_rename_document.py:13-14` and the A3 test docstring at
`tests/mcp/test_rename_document.py:659-663` state that rollback proceeds "via
`git checkout -- .`". The implementation uses the durable byte-for-byte recovery
journal (`ontos/core/rename_transaction.py:111-157`,
`ontos/mcp/rename_tool.py:266-279`), which is the contract the spec mandates
("Unscoped git rollback is forbidden", `docs/specs/project-ontos-v5-0-0-spec.md:36`).
The code is correct; only the test prose is stale.

## Verdict

Approve

Ontos 5.0.0 faithfully implements the v5 structural-release contract across every
examined area: schema-4 envelopes with separated execution/result status, a
reserved exit-4 taxonomy, an authoritative declarative command registry with
canonical nested paths, canonical YAML parsing and surgical frontmatter writes,
physical one-based link lines with alias-preserving rename, a single MCP
invocation boundary that preserves structured error codes, byte-for-byte rename
recovery journals that forbid unscoped rollback, iterative case-aware graph
traversal, complete legacy-fork retirement, and hash-bound evidence isolation.
All bounded read-only checks pass: the 1536-test product suite, the golden
comparison, the focused contract/safety suite (228 tests), cardinality and
scope gates, and lifecycle-evidence parity at the pinned commit. The three
findings are all LOW or NIT and none blocks the release; F1 is a
documentation/schema fidelity gap on two portfolio tools, F2 is a tooling
reproducibility nit, and F3 is stale test prose describing the correct
behavior. D.6 is correctly withheld pending a genuine strict-P3 receipt, and
no maintainer authorization (merge/tag/release/PyPI/issue-closure) is granted
or implied by this review.
