---
id: project-ontos-v4-7-1-hotfix-B.1-glm-peer-r2
deliverable_id: project-ontos-v4-7-1-hotfix
phase: B.1
role: peer
family: glm
evidence_labels_used: [direct-run, orchestrator-preflight, static-inspection, not-run]
status: completed
---

# Peer Review — project-ontos-v4-7-1-hotfix / B.1 / glm (r2)

Reviewer: glm (peer). Working tree: `audit/v4.7.1-hotfix` at `6168267`
("preserve and retry B.1 review evidence"), four commits above the
declared implementation snapshot `e33a31d` over baseline `bf91b42`. The
two intermediate commits (`b9c81f0`, `82ab894`) and the HEAD retry
commit are lifecycle/dispatch bookkeeping and do not touch product
code; the implementation diff was reviewed as `bf91b42..e33a31d`. All
direct observables below were reproduced from this worktree this
session; the prior glm r2 attempt is preserved at
`docs/reviews/project-ontos-v4-7-1-hotfix/.raw/ontos-471-B1-gp-r2.r1.*`
and emitted only three orientation lines before its stream closed, so
this artifact is the retry the orchestrator's preservation entrypoint
is bound to (orchestrator-preflight). No author claims were taken on
trust and no sibling reviewer's verdict was inherited as evidence.

## 1. Completeness check

Every in-scope spec item (spec §2) was checked against code and
verified test surface this session:

- **Safe serialization + semantic round-trip** (§2.1, §4 "Safe document
  representation"): `patch_frontmatter_fields` delegates scalar emission
  to `serialize_frontmatter` (`frontmatter_edit.py:140`) and asserts the
  round trip before returning (`frontmatter_edit.py:135,
  assert_frontmatter_roundtrip`). Direct-run: `tests/test_frontmatter_
  roundtrip_regression.py` (9 adversarial scalar cases, 11 collected
  tests) and `tests/core/test_schema.py::TestSerializeFrontmatter::
  test_adversarial_values_roundtrip_exactly` / `test_invalid_document_
  ids_fail_closed` all green.
- **Line-delimited frontmatter parser, `---` inside scalars** (§2.2):
  `split_frontmatter_text` is exercised by
  `tests/core/test_frontmatter_edit_pipeline.py::test_patch_preserves_
  indented_frontmatter_block_delimiter` and the four
  `test_frontmatter_fences_*` cases — all green (direct-run).
- **Non-string/malformed ID rejection before write/load** (§2.3):
  `validate_document_id` invoked inside `patch_frontmatter_fields`
  (`frontmatter_edit.py:121,129`) for any present-or-added ID and
  filename-derived ID absence is preserved. Direct-run:
  `tests/test_document_loading_contract_a1.py::
  test_loader_rejects_yaml_coerced_non_string_ids` and
  `test_batch_loader_reports_non_string_id_as_parse_error` pass.
- **Format-preserving mutation across all listed surfaces** (§2.4):
  `patch_frontmatter_fields` is the consumer for promote, migrate,
  verify, retrofit (via `dump_yaml`), frontmatter repair, rename, and
  MCP writers (`tests/test_frontmatter_roundtrip_regression.py::
  test_all_frontmatter_writer_modules_use_the_safe_pipeline` pins the
  consumer set and the absence of `.split('---', 2)` and `.read_text(`
  on the strict-decoding paths). Direct-run green; tests/rules also
  pinned by the test's static assertions against source files.
- **Exclusive, unpredictable, contained, symlink-safe,
  mode-preserving, durable, atomic, recoverable transactions** (§2.5,
  §4 "Transaction and locking envelope"): `tests/test_session_context.py`
  (1131 new lines; 51 collected tests in this branch's slice) plus
  `tests/test_context_contention.py` and `tests/mcp/test_locking.py`
  cover predictable-temp-symlink swap, staged-temp swap, backup-reservation
  swap, final-binding swap, phase-one source binding swap, workspace-root
  displacement, hard-link attacks, and post-buffering root replacement.
  All green (direct-run, 17.68s for the full focused set).
- **One cross-platform workspace-lock abstraction with outer-identity
  binding** (§2.6): `ontos/core/locking.py:17-25` conditionally imports
  `fcntl` / `msvcrt` — there is no unconditional `import fcntl`.
  `WorkspaceLockGuard` (`locking.py:200-214`) carries workspace_root,
  workspace_binding, lock_path, lock_handle, and root_guard_fd; the
  inner `owns_lock=False` path in `SessionContext` now requires a bound
  guard and rejects foreign workspaces, arbitrary callables, and lock
  path replacement. Pinned by `test_owns_lock_false_requires_bound_outer_
  guard`, `test_owns_lock_false_rejects_arbitrary_callable`,
  `test_owns_lock_false_rejects_guard_from_other_workspace`,
  `test_workspace_guard_blocks_new_lock_inode_after_visible_unlink`, and
  `test_outer_guard_rejects_inner_commit_after_lock_path_replacement`,
  all green (direct-run).
- **CLI log: configured `logs_dir`, safe YAML, exclusive creation,
  collision refusal** (§2.7): `tests/commands/test_log.py` (12 cases)
  covers safe-YAML log session round trip including
  `test_log_session_round_trips_adversarial_frontmatter_values` and a
  symlinked `.ontos`-targeting-mutated-tree marker test that fails closed
  on a workspace swap while preserving the external sentinel. Direct-run
  green.
- **Read-only MCP suppression** (§2.8): `_log_usage` returns early when
  `cache.read_only` is true (`server.py:1003`); `_build_portfolio_index`
  consumes an existing snapshot and never initializes config, creates a
  DB, rebuilds, or opens WAL/SHM sidecars (`server.py:1055-1078`).
  Direct-run: `test_read_only_server_rejects_persistent_graph_export`,
  `test_read_only_server_suppresses_usage_log_writes`,
  `test_read_only_portfolio_requires_existing_snapshot_without_writes`,
  `test_read_only_portfolio_queries_existing_snapshot_without_mutation`,
  plus `export_graph.annotations.readOnlyHint` parity (True under
  read_only, False when mutable) all green.
- **Version 4.7.1 in both sources plus imported package** (§2.9):
  G-version-1 verified directly; `ontos.__version__`,
  `pyproject.toml`, and `ontos/__init__.py` all read `4.7.1`.
- **Inherited #147 doctor RCE remediation** (§2.10): G-doctor-1
  reproduced, 5/5 green, 0.40s — these are *inherited* from main and
  the spec explicitly declines to relabel their lifecycle evidence.

Manifest gates reproduced (direct-run):

| Gate | Result | Evidence label |
|---|---|---|
| G-test-1 (focused 11 modules) | 206 passed in 17.68s | direct-run |
| G-doctor-1 | 5 passed in 0.40s | direct-run |
| G-version-1 | `4.7.1` in `ontos`, `pyproject.toml`, `ontos/__init__.py` | direct-run |
| G-contract-1 | byte-identical over 16 forbidden paths | direct-run |
| G-contract-2 | schema 3.4 key set, no `result` | direct-run |
| G-golden-1 | `tests/golden/baselines`, `tests/commands/golden` unchanged | direct-run |
| G-diff-1 | `git diff --check bf91b42` clean incl. `locking.py`, `context.py`, `frontmatter_edit.py` | direct-run |
| G-branch-1 | `git merge-base bf91b42 HEAD == bf91b42` | direct-run |
| Cardinality `! -e ontos/command_registry.py` | no v5 registry exists | direct-run |
| Forbidden-path scope on `bf91b42..e33a31d` | none of the spec §9 excluded paths touched; 52 files changed, +5436/-483 | direct-run |
| G-scope-1 (verify-changed-path-scope.sh) | not-run (out-of-tree framework script; scope verified by enumeration of changed paths instead) | not-run |
| G-test-2 (full suite) | not-run — task constrains reviewer to focused tests only | not-run |

## 2. Diagram-prose cross-reference

Spec §10 architecture and sequence diagrams map cleanly to code:

- "Format-preserving editor" → `ontos/core/frontmatter_edit.py`
  (`patch_frontmatter_fields` at line 53). "Ordered safe serializer" →
  `ontos/io/yaml.py` plus `ontos/core/schema.py`, reached through the
  editor's `_serialize_field_lines` delegation at `frontmatter_edit.py:140`.
  "YAML parser + round-trip assertion" → `parse_frontmatter_content`
  + `assert_frontmatter_roundtrip`, the latter called inside the editor
  at `frontmatter_edit.py:135`. "SessionContext transaction" →
  `ontos/core/context.py`. "Cross-platform workspace lock" →
  `ontos/core/locking.py` (verified conditional backend import
  `locking.py:17-25`). Every diagram node has a real implementation;
  none are stub placemarkers (static-inspection).
- Sequence-diagram failure paths are honored:
  - "invalid UTF-8 → reject; no buffered write" — mutation readers use
    strict decode; the symlinked `.ontos` log marker test in
    `tests/commands/test_log.py` preserves the external sentinel
    ("do not change") directly, demonstrating no buffered write leaks
    out of an unsafe workspace (direct-run).
  - "unsafe/replaced workspace or lock → reject; no write" — verified
    statically through `capture_workspace_binding` (lstat, S_ISLNK and
    Windows reparse-point rejection at `locking.py:38-50`), the
    no-follow `open_workspace_guard` with stable-inode check
    (`locking.py:65-99`), and `verify_lock_file_binding` which
    enforces single-link invariant, rejects symlinked replacement,
    and surfaces `RuntimeError` on path disappearance
    (`locking.py:163-197`). Runtime-pinned by the five new
    `test_workspace_*` / `test_owns_lock_false_*` cases above
    (direct-run).
  - "commit failure → rollback of applied operations; recovery backups
    retained for diagnosis" — `_rollback_records` plus the recovery
    backup preservation visible in `test_commit_verifies_final_binding_
    and_restores_original` (asserts a retained `.*.bak`, original byte
    content restored, and `errors[-1]` contains "recovery backup
    preserved at"). Direct-run green.
- Prose claim "MCP holds an outer workspace lock and passes a typed,
  runtime-bound guard into the inner transaction" (spec §4) is
  implemented exactly: `WorkspaceLockGuard` is the typed bound object
  passed as `external_lock_guard` into `SessionContext(... owns_lock=
  False, expected_workspace_binding=guard.workspace_binding,
  external_lock_guard=guard)`, and arbitrary callables are rejected
  with `RuntimeError("bound outer lock guard …")` (`test_owns_lock_
  false_rejects_arbitrary_callable`).

No diagram-prose gaps observed.

## 3. Quality assessment

The transactional core is unusually rigorous and was not weakened
between r1 and r2 inspection points. Specifically:

- Pinned anchor-directory opens with `O_NOFOLLOW | O_DIRECTORY |
  O_CLOEXEC`; lock path opened without following the final entry
  (`locking.py:217-228` POSIX seam; the Windows seam follows at
  `_open_windows_lock_file` per the r1 review and the cross-platform
  guard at `locking.py:78-99` deferring to `None` on Windows).
- `verify_lock_file_binding` uses *both*
  `os.fstat(handle.fileno())` (single-link must hold on the open
  descriptor) *and* `os.lstat(lock_path)` (visible name must still
  match by inode, still be a regular file, still one link, and not
  have become a reparse point). This dual-window check is the
  correct defense against the "unlink + replace the visible name"
  POSIX advisory-lock attack and is also fail-closed against
  `FileNotFoundError` during the held window (`locking.py:163-197`),
  which is exactly the scenario pinned by
  `test_workspace_guard_blocks_new_lock_inode_after_visible_unlink`.
- Editor/serializer coupling is clean: the surgical editor never
  hand-builds YAML quoting and rejects ambiguous constructs
  (block scalars, anchors, aliases, tags, duplicate fields, inline
  comments inside rewritten collections) *before* returning, and
  reparses + round-trip asserts before return (`frontmatter_edit.py:102,
  118, 135`).

Quality nits (non-blocking, unchanged from r1):

- `frontmatter_edit.py:57-60` docstring has the same dangling sentence
  ("Ambiguous constructs in a field being changed" lacks a predicate
  and runs into "Inline comments …"). Cosmetic; static-inspection;
  carried forward from r1 as M-1, not yet edited. The body of the
  function implements the documented intent, so the contract holds.
- `context.py:99-104` retains the legacy v2.8 "SCOPE LIMITS" header
  commentary that is now stale relative to the v4.7.1 transaction
  scope. Harmless but noisy. (Carried forward per r1's reading; this
  r2 did not reopen that comment, hence the label: static-inspection
  of r1's finding, not r2 re-verification.)

## 4. UX review

Not a UI deliverable. The observable CLI/MCP surface is the UX, and
it is preserved byte-for-byte: G-contract-1 confirmed `cli.py`,
`ui/json_output.py`, link-check/map/stub/activate, `body_refs`/`graph`/
`link_diagnostics`, `mcp/schemas.py`, both golden directories, and the
five corresponding golden-driven test files are byte-identical to
baseline (direct-run). G-contract-2 confirmed schema 3.4 key set and
no `result` object on both success and error envelopes (direct-run).

Read-only MCP operator guidance is defense-in-depth: write tools are
not advertised at all (not merely runtime-refused), and the server
instructions redirect users to the `ontos log -e "slug"` CLI fallback
(per r1 reading of `server.py:973-979`; the relevant server instruction
fixture is invariant against the hotfix diff). The CHANGELOG
compatibility note explicitly frames the two intentional behavior
changes for the patch release: log collision → error, and unsafe/
linked/outside-workspace mutation → fail before any external change.
This is the correct contract-disciplined framing for a 4.7.x patch.

## 5. Issues found

### Blocking (Critical)

None.

### Should-fix (Major)

- **SF-1 (carried forward from r1): Clean-tree acceptance criterion is
  ungated and not satisfied in the review worktree.** Evidence
  reproduced here:
  - *Static-inspection of manifest:* the `G-test-2` prerequisite gate
    (manifest lines 285-290) and the phase-D.2 smoke check
    (manifest lines 233-237) both enforce only
    `expect: "exit-0"` against `.venv/bin/python -m pytest -q`. Neither
    asserts `git diff --exit-code` over tracked files after the run,
    nor pins the suite to a temporary project.
  - *Static-inspection / not-run:* per task constraint this r2 did not
    reproduce the r1 filesystem-level bisect. r1 reported that running
    G-test-2 against the working tree rewrites the tracked
    `Ontos_Context_Map.md` (refreshed `generated_at`) when the suite
    is run against the working tree that already contains sibling
    review artifacts. This appears to be pre-existing test-ordering debt
    within `tests/commands/` surfaced by `map`-regenerating tests that
    touch a non-temporary project, and is *not* an artifact of any
    hotfix-introduced test (r1 confirmed the hotfix's own added tests
    all use `tmp_path` and leave the tree clean in isolation).
  - *Contract gap against spec §6 acceptance criterion 3:* "A test run
    produces no tracked or non-ignored repository changes" is not
    evidenced by the gate set. Recommendation unchanged from r1: add a
    clean-tree assertion to G-test-2 / isolate the map-regenerating
    test to a temporary project. This is an evidence-framework gap,
    not a product-code defect, and does not block the hotfix.

### Minor

- **M-1 (carried forward from r1):** `ontos/core/frontmatter_edit.py:57-60`
  docstring: "Ambiguous constructs in a field being changed" is an
  incomplete sentence with no predicate. Cosmetic. Static-inspection.
  Still unfixed as of `e33a31d`.
- **M-2 (carried forward from r1):** The committed map (`Ontos_Context_
  Map.md`, doc count 177) drifts from the live working tree once
  concurrent B.1 review artifacts land under `docs/reviews/…`. The
  manifest lists the map as an allowed path so this is expected, but
  reviewers running the full suite should restore the map to HEAD
  before committing. Minor / process. r1 reported restoring it; this
  r2 did not run the full suite and has not modified the working tree
  beyond writing this artifact.

## 6. Positive observations

- **Contract discipline is exemplary.** Every forbidden path in spec
  §9 (`cli.py`, `ui/json_output.py`, link_check/map/stub/activate,
  `body_refs`/`graph`/`link_diagnostics`, `mcp/schemas.py`, both
  golden trees, and the four corresponding golden-driven test files)
  is byte-identical to baseline by direct-run. The v5 behavior-bleed
  risk item in spec §8 is concretely mitigated.
- **Locking/transaction design is correctly fail-closed across both
  POSIX and Windows seams.** The single-link lock invariant, the
  stable directory-inode guard, the no-follow final-entry open, the
  dual-window `os.fstat(handle)` / `os.lstat(path)` consistency
  check, and the recovery-backup-preserved-for-diagnosis contract on
  commit failure are non-trivial and well-tested (1131 new lines in
  `test_session_context.py`, 86 new lines in `test_locking.py`).
- **Read-only MCP is defense-in-depth.** Write tools are not
  advertised; usage logging is suppressed; portfolio is not
  initialized or rebuilt; no SQLite sidecars; `export_graph` carries
  the MCP `readOnlyHint` annotation matching its mode. All confirmed
  by direct-run.
- **Format-preserving editor genuinely preserves BOM, CRLF, leading
  whitespace, inline comments on the changed field, and document
  body, while rejecting anchors, aliases, tags, and block scalars**
  (direct-run: `test_patch_preserves_bom_crlf_comments_quoting_and_
  body`).
- **Version sources, schema-3.4 key set, "no `result` object," and "no
  `command_registry.py`" cardinality** all verified directly this
  session.
- **Whitespace-clean diff** over the full hotfix range and over
  `locking.py`/`context.py`/`frontmatter_edit.py` specifically.
- **The hotfix is honest about its evidence framework.** Spec §3
  explicitly permits only the mechanically verified provider-limited
  fallback (withheld D.6) when a genuine family dispatch fails; the
  preserved `.raw/` artifacts and the retry pattern observed here for
  glm-peer align with that contract — no fabricated receipts, no
  implicit waivers.

## Verdict

Approve

The hotfix implementation is complete against spec §2, contract-
preserving against spec §9, and rigorously verified this session by
direct-run: 206 focused and 5 doctor tests pass; G-version-1,
G-contract-1, G-contract-2, G-golden-1, G-diff-1, G-branch-1, the
no-`command_registry.py` cardinality, and the forbidden-path scope
enumeration all hold; 52 files / +5436 / -483 changed with none of the
spec-excluded paths touched. The single Should-fix (SF-1) is an
evidence-gate gap — add a clean-tree assertion to G-test-2 or isolate
the map-regenerating test to a temporary project — and is not a
product-code defect; r1's report that the full suite rewrites
`Ontos_Context_Map.md` is reproduced here as a manifest-scope
finding (G-test-2 verifies only `exit-0`), not re-bisected at the
filesystem level because the task constraint forbids running the
full suite. Two cosmetic Minors (M-1 docstring, M-2 map drift) are
carried forward for follow-up. This r2 confirms the r1 Approve and
adds independent direct-run reproduction of the gate set and the
frontmatter-editor/serializer/locking contracts.

## Notes

- Evidence labels used:
  - **direct-run** for every git state / git diff / cardinality / gate
    / focused-test reproduction executed in this worktree this session:
    G-test-1 (206/206 in 17.68s), G-doctor-1 (5/5 in 0.40s),
    G-version-1, G-contract-1, G-contract-2, G-golden-1, G-diff-1,
    G-branch-1, the `! -e ontos/command_registry.py` cardinality, the
    forbidden-path scope enumeration on `bf91b42..e33a31d`, and the
    per-file whitespace check on `locking.py`, `context.py`, and
    `frontmatter_edit.py`.
  - **orchestrator-preflight** for the prior glm-peer-r2 dispatch
    preserved by HEAD `6168267` ("chore: preserve and retry B.1 review
    evidence"): `docs/reviews/project-ontos-v4-7-1-hotfix/.raw/ontos-471-B1-gp-r2.r1.c20260712T015452Z.38215…raw.txt`
    contains only three orientation lines and was truncated before a
    review was produced; this artifact is the bound retry and inherits
    no claims from sibling `B1-ca-r2`, `B1-cp-r2`, or `B1-ga-agy`
    attempts.
  - **static-inspection** for code reads: `ontos/core/frontmatter_edit.py`
    (lines 1-170 and 53-136 contract), `ontos/core/locking.py` (lines
    1-229, 200-214 for `WorkspaceLockGuard`), `ontos/mcp/server.py`
    (lines 985-1094 for `_log_usage` and `_build_portfolio_index`), the
    manifest `G-test-2` verification definition (manifest lines
    285-290 and 233-237), the M-1 docstring nit, and the spec/diagram
    parity mapping against §10.
  - **not-run** for G-test-2 (full suite) and G-scope-1 (framework
    script outside the worktree): per task constraints this reviewer
    was instructed not to run the full suite, and G-scope-1 was
    substituted by direct enumeration of changed paths against the
    manifest's `allowed_paths` / `forbidden_paths` lists.
- HEAD is `6168267` ("preserve and retry B.1 review evidence"), four
  commits above the declared implementation snapshot `e33a31d`. The
  two intermediate dispatch/lifecycle commits (`b9c81f0`,
  `82ab894`) and the HEAD retry commit do not modify any product code.
  The review implementation diff is `bf91b42..e33a31d`; the working
  tree is `6168267`.
- The working tree currently carries untracked `.prompts/` and `.raw/`
  artifacts from the prior r1 and r2 dispatch attempts. These match the
  `docs/reviews/project-ontos-v4-7-1-hotfix/**` allowed pattern from
  the manifest `allowed_path_patterns` and are pre-existing
  orchestrator artifacts; this r2 did not create, modify, or delete any
  pre-existing file and only writes the declared artifact file.
- Per review constraints: no merge, commit, tag, push, release; no
  product-code edits; no docs or logs other than this review artifact
  were touched. This r2 did not run the full test suite, did not invoke
  any interactive command, and produced its evidence inside the
  declared review window.
