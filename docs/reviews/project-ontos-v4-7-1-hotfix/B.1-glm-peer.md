---
id: project-ontos-v4-7-1-hotfix-B.1-glm-peer
deliverable_id: project-ontos-v4-7-1-hotfix
phase: B.1
role: peer
family: glm
evidence_labels_used: [direct-run, static-inspection]
status: completed
---

# Peer Review — project-ontos-v4-7-1-hotfix / B.1 / glm

Reviewer: glm (peer). Branch inspected: `audit/v4.7.1-hotfix` at `82ab894`
(review-board dispatch), implementation snapshot `e33a31d` over baseline
`bf91b42`. All evidence below is reproduced directly unless labeled
`static-inspection`. No author claims were taken on trust.

## 1. Completeness check

Every in-scope spec item (spec §2) has corresponding, verified implementation:

- Safe serialization + round-trip: `ontos/io/yaml.py:45` (`safe_dump`,
  `sort_keys=False`, `allow_unicode`), `assert_frontmatter_roundtrip` at
  `yaml.py:111`. Delegation from `schema.py` confirmed
  (`serialize_frontmatter` at `schema.py`, delegated via
  `frontmatter_edit.py:140`).
- Line-delimited frontmatter parser + `---`-in-scalar handling:
  `split_frontmatter_text` at `yaml.py:53`, fence predicate `yaml.py:76`.
- Non-string/malformed ID rejection before write/load:
  `validate_document_id` at `schema.py:83`, called inside
  `frontmatter_edit.py:129` before any patch returns.
- Format-preserving mutation across promote/migrate/verify/retrofit/repair/
  rename/MCP: `patch_frontmatter_fields` at `frontmatter_edit.py:53`; BOM,
  CRLF, leading whitespace, inline comments preserved; anchors/aliases/tags/
  block scalars rejected (`frontmatter_edit.py:158`); reparse + round-trip
  assert before return (`frontmatter_edit.py:118,135`).
- Exclusive, unpredictable, contained, symlink-safe, mode-preserving,
  durable, atomic, recoverable transactions: `SessionContext.commit` at
  `context.py:286`; unique temp via `secrets.token_hex` (`context.py:1034`);
  no-follow `_safe_workspace_path` (`context.py:670`); `fsync` +
  `os.replace` (`context.py:1088,1162`); rollback `_rollback_records`
  (`context.py:1204`).
- Cross-platform single lock abstraction with outer-identity binding:
  `ontos/core/locking.py` (no unconditional `fcntl`: `locking.py:17-25`);
  `external_lock_guard` binding at `context.py:1363-1389`.
- CLI log via configured `logs_dir`, safe YAML, exclusive creation,
  collision refusal: `ontos/commands/log.py:118,376`, `FileExistsError` at
  `log.py:307`.
- Read-only MCP suppresses graph export / usage log / portfolio init / DB:
  `ontos/mcp/server.py:197` (gates `_register_write_tools`),
  `server.py:1003` (usage-log skip), `server.py:1061-1077` (no
  init/rebuild), `test_read_only_registration.py:69-146`.
- Version 4.7.1 in both sources + imported package: verified
  (`ontos.__version__`, `pyproject.toml`, `ontos/__init__.py`).
- Doctor RCE fix inherited from main: `tests/test_doctor_mcp_probe_regression.py`
  passes (5/5).

Manifest gates reproduced (direct-run): G-version-1 ✓, G-contract-2 (schema
3.4, no `result`) ✓, cardinality "no `command_registry.py`" ✓, G-contract-1
(byte-identical forbidden paths incl. `cli.py`, `ui/json_output.py`,
`mcp/schemas.py`, goldens) ✓, G-golden-1 ✓, G-diff-1 (whitespace) ✓, G-branch-1
(merge-base) ✓, G-test-1 (206 focused) ✓, G-test-2 (1550 passed, 2 skipped) ✓.

## 2. Diagram-prose cross-reference

Spec §10 architecture and sequence diagrams map cleanly to code:

- "Format-preserving editor" → `frontmatter_edit.py`; "Ordered safe
  serializer" → `io/yaml.py` + `schema.py`; "YAML parser + round-trip
  assertion" → `parse_frontmatter_content` + `assert_frontmatter_roundtrip`;
  "SessionContext transaction" → `context.py`; "Cross-platform workspace
  lock" → `locking.py`. Every diagram node has a real implementation.
- Sequence failure paths are honored: invalid UTF-8 → reject before buffered
  write (mutation reads are strict, `io/files.py:179,198`, vs replacement
  decode on general reads at `io/files.py:293,381`); unsafe/replaced
  workspace → reject (`_workspace_root` rebinding check `context.py:738-751`,
  `verify_workspace_binding` `locking.py:53`); commit failure → rollback of
  applied operations with recovery backups preserved
  (`context.py:615-621,1204`).
- Prose claim "MCP holds an outer workspace lock and passes a typed,
  runtime-bound guard into the inner transaction" is implemented exactly:
  `WorkspaceLockGuard` (`locking.py:200`) is verified by the inner
  `owns_lock=False` path (`context.py:1378-1389`), with mismatched workspace
  binding rejected.

No diagram-prose gaps found.

## 3. Quality assessment

The transactional core is unusually rigorous. Notable strengths:
two-phase stage-then-mutate with pinned no-follow directory anchors
(`context.py:322-583`); stable workspace-inode guard to survive lockfile
unlink/replace attacks (`locking.py:65-123`); single-link enforcement on the
lock file itself (`locking.py:163-197`); ambiguous backup-rename state is
reconciled rather than silently dropped (`context.py:452-504`); non-inheritable
handles (`locking.py:432`); best-effort directory `fsync` after replace
(`context.py:1322`). Windows and POSIX seams are both real (not stubbed):
`_open_windows_lock_file`, `_pin_windows_directory`, `LockFileEx`/`UnlockFileEx`.

Serializer/editor coupling is clean: the surgical editor delegates scalar
emission to the safe serializer (`frontmatter_edit.py:140`) and never
hand-builds YAML quoting, matching the spec exclusion list.

Quality nits (non-blocking):
- `frontmatter_edit.py:57-60` docstring has a dangling incomplete sentence
  ("Ambiguous constructs in a field being changed" lacks a predicate and
  runs into the next sentence). Cosmetic.
- `context.py:99-104` retains legacy v2.8 "SCOPE LIMITS" commentary that is
  now stale relative to the v4.7.1 transaction scope; harmless but noisy.

## 4. UX review

Not a UI deliverable; observable CLI/MCP contracts are the UX surface and
are preserved byte-for-byte (G-contract-1, direct-run). Read-only MCP gives
clear operator guidance: write tools are not advertised at all (not merely
runtime-refused), and the server instructions redirect users to the CLI
`ontos log -e "slug"` fallback (`server.py:973-979`). The CHANGELOG
compatibility notes explicitly call out the two intentional behavior changes
(log collision → error; unsafe/linked/outside-workspace mutation → fail),
which is the right user-facing framing for a patch release.

## 5. Issues found

### Blocking (Critical)

None.

### Should-fix (Major)

- **SF-1: Clean-tree acceptance criterion is ungated and not satisfied in
  this worktree.** Reproduced (direct-run): running the manifest's G-test-2
  full suite rewrites the tracked `Ontos_Context_Map.md` — a refreshed
  `generated_at` timestamp plus, in this worktree, absorption of the
  sibling `B.1-gemini-alignment.md` review artifact (doc count 177 → 178).
  This conflicts with spec §6 acceptance criterion 3 ("A test run produces no
  tracked or non-ignored repository changes"). The manifest's G-test-2 gate
  asserts exit-0 only and does not enforce a clean tree, so the acceptance
  criterion is unevidenced by the gate set. Bisect: the rewrite is a
  test-ordering effect within `tests/commands/` — no single module group
  triggers it, but the full commands directory does (496 passed → `M
  Ontos_Context_Map.md`). The hotfix's own added tests (`test_session_context`,
  `test_frontmatter_edit_pipeline`, `test_locking`,
  `test_read_only_registration`, `test_log`, `test_retrofit`,
  `test_doctor_mcp_probe_regression`) all use `tmp_path` and leave the tree
  clean in isolation, so I could not attribute the rewrite to a
  hotfix-introduced test; it appears to be pre-existing test debt within
  `tests/commands/` surfacing against a working tree that contains concurrent
  review artifacts. Recommendation: add a clean-tree assertion to G-test-2
  (e.g. `git diff --exit-code` over tracked files after the suite) or
  isolate the map-regenerating test to a temporary project. This is an
  evidence-framework gap, not a product-code defect.

### Minor

- **M-1:** `ontos/core/frontmatter_edit.py:57-60` docstring has an
  incomplete/dangling sentence ("Ambiguous constructs in a field being
  changed"). static-inspection. Cosmetic.
- **M-2:** The committed map (`Ontos_Context_Map.md`, doc count 177) drifts
  from the live working tree (178) once the concurrent B.1 review artifacts
  land under `docs/reviews/...`. The manifest lists the map as an allowed
  path, so this is expected, but reviewers running the suite should restore it
  before committing (I restored it to HEAD). Minor/process.

## 6. Positive observations

- Contract discipline is exemplary: every forbidden path
  (`cli.py`, `ui/json_output.py`, link_check/map/stub/activate,
  `body_refs`/`graph`/`link_diagnostics`, `mcp/schemas.py`, tracked goldens)
  is byte-identical to baseline, verified directly — the v5 behavior bleed
  risk called out in the spec §8 risk table is concretely mitigated.
- Locking/transaction design is correctly fail-closed across both POSIX and
  Windows seams; single-link enforcement, reparse-point rejection, and
  ambiguous-backup-rename reconciliation are non-trivial and well-tested
  (`test_session_context.py`, `test_context_contention.py`, 1131+72 lines).
- Read-only MCP is defense-in-depth: write tools are not advertised
  (`server.py:197`), usage logging suppressed (`server.py:1003`), portfolio
  not initialized/rebuilt (`server.py:1061-1077`), no SQLite sidecars
  (`test_read_only_registration.py:101-146`), graph export in-memory only
  (`test_read_only_registration.py:69-83`).
- Format-preserving editor genuinely preserves BOM/CRLF/whitespace/inline
  comments while rejecting anchors/aliases/tags/block-scalars, and
  reparse+round-trip-asserts before returning — exactly the spec §4 contract.
- Version sources, schema-3.4 envelope key set, "no `result` object," and
  "no `command_registry.py`" cardinality all verified directly.
- Whitespace-clean diff over the full hotfix range (`git diff --check`).
- Full suite green (1550 passed, 2 skipped; the 2 skips are pre-existing
  golden-master baselines awaiting recapture, unrelated to this hotfix).

## 7. Verdict

Approve

The implementation is complete, contract-preserving, and rigorously
verified: all cardinality, parity, golden, whitespace, and branch gates pass
by direct run; 206 focused and 1550 full-suite tests pass; the serializer,
format-preserving editor, transactional core, locking abstraction, CLI log,
and read-only MCP surfaces faithfully implement the spec with strong
test coverage. The single Should-fix (SF-1) is an evidence-gate gap
(add a clean-tree assertion to G-test-2 / isolate the map-regenerating test)
rather than a product-code defect, and the rewrite appears to be pre-existing
test-ordering debt amplified by sibling review artifacts in this worktree. It
does not block the hotfix. Two cosmetic Minors are noted for follow-up.

## 8. Notes

- Evidence labels used: `direct-run` for all git/cardinality/gate/test
  reproductions and the map-rewrite bisect; `static-inspection` for code
  reads (`locking.py`, `context.py`, `frontmatter_edit.py`, `yaml.py`,
  `server.py`, `writes.py`, `log.py`, `schema.py`, `io/files.py`) and the
  docstring nit.
- HEAD is `82ab894` (B.1 review-board dispatch), two commits above the
  declared implementation snapshot `e33a31d`; the two extra commits are
  lifecycle/dispatch bookkeeping (`b9c81f0`, `82ab894`) and do not touch
  product code. The review was performed against `e33a31d..bf91b42` for the
  implementation diff and `82ab894` for the working tree.
- I restored `Ontos_Context_Map.md` to HEAD after the test-run bisect so the
  only file changed by this review session is this artifact.
- Per review constraints, no merge/commit/tag/push and no product-code or
  doc/log edits were performed.
