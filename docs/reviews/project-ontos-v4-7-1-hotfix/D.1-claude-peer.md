---
id: project-ontos-v4-7-1-hotfix-D.1-claude-peer
deliverable_id: project-ontos-v4-7-1-hotfix
phase: D.1
role: peer
family: claude
evidence_labels_used: [direct-run, static-inspection]
status: completed
---

# D.1 Claude Peer Implementation Review — Project Ontos v4.7.1 Hotfix

## Attestation

I reviewed commit `a71ac4a` against baseline `bf91b42` in the worktree at
`/tmp/project-ontos-worktrees/project-ontos-v4.7.1-hotfix`, using the spec at
`docs/specs/project-ontos-v4-7-1-hotfix-spec.md` as the acceptance contract.

Evidence is `direct-run` (the full suite, plus two standalone reproductions run
against the worktree's own `.venv` interpreter and library code) and
`static-inspection` (read-only `git diff`/`grep`/file reads of the serializer,
mutation editor, transaction, locking, log, and MCP surfaces).

I did not run Ontos activation, `map`, or `log`. I did not modify code, commit,
push, merge, tag, or release. Both reproductions below executed entirely in
process memory or in a `tempfile.mkdtemp()` scratch directory; neither wrote to
the repository. `git status --porcelain` over tracked source and test paths was
empty after the suite run, satisfying acceptance criterion 3.

I have no authorship stake in this implementation.

## Findings

### 1. Read-only MCP portfolio can serve indefinitely stale rows (Medium)

`ontos/mcp/portfolio.py:472` opens read-only connections with
`?mode=ro&immutable=1`. SQLite treats `immutable=1` as a promise that the file
cannot change, so it ignores the `-wal` sidecar entirely. That promise does not
hold here: a writable `ontos serve` or portfolio CLI in another process can
rebuild the same database underneath the read-only server.

The hotfix upgraded `rebuild_all` to `PRAGMA wal_checkpoint(TRUNCATE)`
(`ontos/mcp/portfolio.py:126`) precisely so the main database file is a
self-contained snapshot — the inline comment says so. But the per-workspace path
`_rebuild_workspace`, which is the one every MCP write tool and
`rebuild_workspace()` call actually takes, still ends at
`PRAGMA wal_checkpoint(PASSIVE)` (`ontos/mcp/portfolio.py:469`). A passive
checkpoint is a no-op whenever any reader holds the WAL, so committed rows stay
WAL-resident, and the `immutable=1` reader never observes them.

Reproduction (`direct-run`, scratch tempdir, mirroring the module's own
`journal_mode=WAL` + `wal_autocheckpoint=0` settings):

```
PASSIVE result: (0, 1, 0)            # ok, 1 frame in WAL, 0 frames checkpointed
read-only(immutable=1) sees: ['before']
read-only(mode=ro only)  sees: ['before', 'after-rebuild-workspace']
```

The row committed by the simulated `rebuild_workspace` is invisible to the
`immutable=1` reader and visible to a plain `mode=ro` reader. This is a
correctness gap in the read-only snapshot the spec asks for ("opens an existing
portfolio snapshot without initialization, rebuild, journal, or sidecar
writes"): it opens without sidecar writes, but it also reads a snapshot that can
silently lag the filesystem. Dropping `immutable=1` and keeping `mode=ro` gives
the same no-write guarantee (`query_only=ON` is already set at
`ontos/mcp/portfolio.py:477`) while reading the WAL correctly; alternatively,
make `_rebuild_workspace` checkpoint with `TRUNCATE` to match `rebuild_all`.
Note that `mode=ro` alone still lets SQLite create `-shm`/`-wal` sidecars on a
WAL database, so if strict zero-sidecar behavior is the binding requirement, the
`TRUNCATE` fix is the one that preserves both properties.

### 2. Duplicate-field rejection misses quoted keys, writing a duplicate key (Medium)

The spec states the format-preserving editor "rejects duplicates". It does so
for plain keys, but `_TOP_LEVEL_FIELD_RE` in `ontos/core/frontmatter_edit.py:26`
is `^([A-Za-z_][A-Za-z0-9_-]*)\s*:(.*)$`, which does not match a quoted key such
as `'id':`. `_index_top_level_fields` therefore never indexes that line, the
duplicate guard in `patch_frontmatter_fields` sees zero occurrences, and the
update takes the append branch — emitting a *second* `id:` line while the quoted
original stays in place.

Reproduction (`direct-run`, in-process against the worktree's
`ontos.core.frontmatter_edit`):

```
[quoted-key duplicate]     ACCEPTED -> frontmatter="\n'id': old-doc\ntype: atom\nid: new-doc\n"
                           reparsed id='new-doc'   (duplicate key written to disk)
[plain duplicate (control)] rejected: ValueError: Field 'id' appears more than once at top level
```

The post-write guards do not catch it: PyYAML's `safe_load` is last-wins, so
`reparsed["id"]` equals the new value, the per-key semantic check passes, and
`assert_frontmatter_roundtrip` compares the new text against a dict parsed from
that same text, which is self-consistent. The document written to disk has two
top-level `id` keys. Under PyYAML the value still resolves correctly, so this is
not silent value corruption — but it violates the stated duplicate-rejection
contract, leaves a stale contradictory line in a user's document, and produces a
file that strict YAML consumers (and `yaml.safe_load` with duplicate-key
checking enabled) will reject. Widening the regex to recognize quoted keys, or
cross-checking the indexed top-level key count against the parsed mapping's key
count before patching, closes it in the fail-closed direction the rest of the
module already takes.

### 3. Ambiguity rejection is broader than necessary (Low)

`_reject_ambiguous_field_block` (`ontos/core/frontmatter_edit.py:160`) rejects a
field update whenever `&` or `*` appears anywhere in the existing block,
including inside a quoted scalar — so patching a document whose `status` or
`title` legitimately contains `*` or `&` refuses instead of proceeding. This is
fail-closed and therefore not a data-integrity risk, and I would not hold the
release for it, but it will read as a spurious refusal to users with ordinary
prose in their frontmatter. Anchor/alias detection could reuse the existing
`_split_comment_unquoted` quote-tracking to test only the unquoted region.

## Positives

The parts of this hotfix that carry the most risk are the parts that are done
best.

The serializer replacement is genuinely safe rather than cosmetically safer.
`serialize_frontmatter` (`ontos/core/schema.py:323`) preserves its public
signature and field order, delegates every scalar to `yaml.safe_dump`, and then
refuses to return unless `assert_frontmatter_roundtrip` reloads the text to a
value equal to the input. That is the correct shape for a fix to the P0
corruption: the round-trip assertion is the contract, not the quoting rules.
`validate_document_id` is applied at both the serializer and the editor
boundaries, and the editor deliberately preserves the ID-less filename-fallback
case the spec calls for rather than over-rejecting it.

`split_frontmatter_text` handles the `---`-inside-a-scalar case by requiring an
unindented fence line, which is the parser foundation the spec asks for, and the
editor's BOM / leading-whitespace / dominant-line-ending handling means CRLF and
BOM documents survive a field patch byte-for-byte outside the edited field.

The transaction envelope in `ontos/core/context.py` matches the design: staging
uses `O_WRONLY|O_CREAT|O_EXCL` with unpredictable names rather than a
predictable `<target>.tmp`, parents are pinned via directory anchors with
binding verification, `lstat` is used throughout so links are not followed,
existing file modes are preserved via `fchmod` while new files respect umask,
content and directories are `fsync`ed before an `os.replace`, and
`_rollback_records` restores already-applied operations on a failed
multi-operation commit. The `log` collision path returns a distinct
`E_FILE_EXISTS` code with the offending path in `data` instead of overwriting
(`ontos/commands/log.py:375`), which is exactly the intended behavior change,
and the archive marker stays best-effort so the baseline success exit is
preserved.

On the MCP side, `_preflight` in `ontos/mcp/writes.py` captures the workspace
binding, re-verifies it after slug resolution, and passes a typed
`WorkspaceLockGuard` into a `SessionContext` constructed with `owns_lock=False`,
so the outer and inner locks cannot diverge. `read_only` is enforced before any
mutation, and `_build_portfolio_index` skips `ensure_portfolio_config()` on
read-only servers so no config is created.

v5 exclusion parity holds. `git diff bf91b42 a71ac4a` over `ontos/cli.py`,
`ontos/ui/json_output.py`, `ontos/commands/link_check.py`, `commands/map.py`,
`commands/stub.py`, `core/body_refs.py`, `core/graph.py`,
`core/link_diagnostics.py`, and `mcp/schemas.py` is empty; `ontos/command_registry.py`
does not exist; no golden path is touched. Both version sources report `4.7.1`.
The full suite is green: **1563 passed, 2 skipped** in 61s, leaving no tracked
repository changes.

## Notes

The two Medium findings are independent of each other and neither reopens the P0
frontmatter-corruption class that this hotfix exists to close — the serializer
and transaction core, which are the release's actual risk surface, hold up under
inspection. Finding 1 is a read-path staleness bug confined to the read-only
portfolio MCP server and does not corrupt data. Finding 2 writes a
well-formed-under-PyYAML but duplicate-keyed document and contradicts an explicit
spec sentence; it is reachable from `retrofit`, `rename`, and MCP
`promote_document` on any document whose frontmatter quotes a top-level key.

Both are small, local fixes, and both are testable with the patterns already
present in `tests/core/test_frontmatter_edit_pipeline.py` and
`tests/mcp/test_read_only_registration.py`. I am withholding approval only
because Finding 2 is a direct, reproducible contradiction of a stated scope item
("rejects duplicates") on the very surface this release hardens; a peer reviewer
should not wave that through on a data-integrity hotfix. The remediation is
narrow enough that I would expect a fast turnaround and a straightforward
re-review.

Timebox: five minutes, observed.

## Verdict

Request changes
