---
id: project-ontos-v4-7-1-hotfix-B.1-claude-adversarial-r2
deliverable_id: project-ontos-v4-7-1-hotfix
phase: B.1
role: adversarial
family: claude
evidence_labels_used:
  - direct-run
  - static-inspection
  - not-run
status: completed
---

# B.1 Adversarial Review — Project Ontos v4.7.1 Hotfix (claude, r2)

## Input attestation

| Input | Value | Evidence |
|---|---|---|
| Worktree | `/tmp/project-ontos-worktrees/project-ontos-v4.7.1-hotfix` | direct-run |
| Branch | `audit/v4.7.1-hotfix` | direct-run |
| Worktree HEAD | `6168267b336800ec7622c0bc1e4e746811f452e2` | direct-run |
| Implementation under review | `e33a31d0c0040de9afa1f8efe22246c798534edd` | direct-run |
| Baseline | `bf91b42f4eb5ba2ed6e0e3ea5e76d22ec6d7ec95` | direct-run |
| Spec | `docs/specs/project-ontos-v4-7-1-hotfix-spec.md` (300 lines, read in full) | direct-run |
| Manifest | `manifests/project-ontos-v4-7-1-hotfix.yaml` (present, 377 lines added) | static-inspection |
| Diff scale | 52 files, +5436 / −483 | direct-run |

Working tree carried only untracked `.prompts/` and `.raw/` review-dispatch
evidence; no tracked file was dirty at review start. I did not edit code,
commit, push, merge, tag, release, or write to `docs/logs`. The only file I
wrote is this artifact.

Coverage is timeboxed and therefore **partial**. I read the full diff of
`ontos/io/{yaml,files,toml,git}.py`, `ontos/core/{git,errors,schema}.py`,
`ontos/commands/log.py`, and the first ~120 lines of the new
`ontos/core/locking.py`. I did **not** read the 1322-line `ontos/core/context.py`
transaction diff or the MCP surfaces in depth. Findings below are scoped to
what I actually exercised; the unexercised surface is listed under Notes.

## Invariants checked

| # | Invariant (from spec §2/§4/§7) | Status | Evidence |
|---|---|---|---|
| I1 | Safe, ordered YAML emission replaces hand-built quoting | Holds | direct-run |
| I2 | Serializer round-trip is semantically asserted, fails closed | Holds | direct-run |
| I3 | `---` inside a YAML scalar is not a frontmatter delimiter | Holds | static-inspection |
| I4 | Non-string / malformed IDs rejected before write and at loader | Holds, but over-broad — see Issue 1 | direct-run |
| I5 | "No patch-release change to the visible document set" (§7) | **Violated** — see Issue 1 | direct-run |
| I6 | `rollback_path` never deletes user data on checkout failure | Holds | direct-run |
| I7 | CLI log creation is exclusive; collision errors, never overwrites | Holds | direct-run |
| I8 | Workspace lock binds `(st_dev, st_ino, S_IFMT)` and refuses symlinks | Holds (POSIX path only) | static-inspection |
| I9 | Package version reports 4.7.1 from both sources | Holds | direct-run |
| I10 | Exclusion list (`cli.py`, `json_output.py`, goldens, graph) untouched | Holds — none appear in the diff | direct-run |
| I11 | Cross-platform lock backend (Windows `msvcrt`) is correct | **Unverified** | not-run |
| I12 | Transaction staging: unpredictable, contained, symlink-safe, rollback | **Unverified in depth** | not-run |

## Assumption analysis

The change rests on three assumptions I consider load-bearing and only two of
which survive scrutiny:

1. *"A document ID and a filename stem obey the same grammar."* This is the
   assumption that fails. The implementation applies one strict ASCII grammar
   (`DOCUMENT_ID_PATTERN`) to both explicit `id:` values and filename-derived
   fallback IDs. Filenames are user-controlled, pre-existing, and frequently
   contain spaces or non-ASCII characters. See Issue 1.
2. *"PyYAML `safe_dump` with `sort_keys=False`, dumped one field at a time,
   preserves the declared field order."* This holds — `_dump_frontmatter_field`
   dumps a single-key mapping per field, so ordering is driven by
   `field_order`, not by PyYAML.
3. *"Advisory `flock` on the lockfile alone is insufficient because the
   lockfile inode can be swapped."* This is correct and the directory-inode
   guard in `open_workspace_guard` is the right mitigation.

## Failure analysis

- **Fail-closed paths are genuinely closed.** `assert_frontmatter_roundtrip`
  raises rather than writing on any semantic mismatch; `capture_workspace_binding`
  raises on a symlinked or reparse-point root; `verify_workspace_guard` raises
  when the held directory fd changes identity. No silent-success path found in
  the surfaces I read.
- **One fail-*open* path exists by construction:** a document whose fallback ID
  fails validation is not surfaced as an error to the user — it is dropped from
  the canonical set and recorded as a `parse_error` issue (Issue 1). The
  document disappears from the map, graph, and queries. Absence is the most
  expensive failure mode in a documentation graph, because nothing downstream
  can distinguish "not present" from "never existed".
- **Archive-marker failure remains best-effort**, matching the spec's stated
  intent to preserve the baseline success exit and schema-3.4 envelope.

## Security analysis

Attack surfaces I was asked to probe, and what I found:

- **Safe YAML.** `yaml.dump` → `yaml.safe_dump`. Arbitrary-tag / object
  construction on emission is closed. Parse side already used `safe_load`.
  Hand-built scalar quoting in `log.py::_build_frontmatter` — the original P0
  corruption vector — is gone, replaced by `serialize_frontmatter`. **No
  finding.**
- **UTF-8 failure visibility.** General reads keep `errors='replace'` per the
  spec's resolved open question; mutation readers are strict. Consistent with
  §7. **No finding.**
- **Containment / symlink & path races.** `capture_workspace_binding` uses
  `os.lstat` and rejects symlinks and Windows reparse points;
  `open_workspace_guard` opens with `O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC`,
  re-`fstat`s to confirm identity *after* open (TOCTOU-correct ordering), and
  clears the inheritable flag. `log.py` deliberately keeps the configured logs
  path **lexical** so the no-follow writer can reject symlinked components
  rather than resolving through them — this is the right call and is commented
  as such. **No finding in the code I read.** The staging/commit half of this
  claim lives in `context.py` and is `not-run`.
- **Rollback.** `core/git.py::rollback_path` is a real security fix: the
  baseline ran `git checkout --` and, on *any* nonzero exit, unlinked the path —
  so a transient checkout failure on a **tracked** file destroyed user data. The
  new code proves trackedness with `git ls-files --error-unmatch` first, never
  reinterprets a checkout failure as permission to delete, and refuses to unlink
  a directory. **Strong positive.**
- **Cross-platform locks.** POSIX path reviewed and sound. The `msvcrt` backend
  is `not-run` — no Windows execution available in this timebox.
- **v5 contract bleed.** I diffed the changed-file list against spec §9. None of
  `ontos/cli.py`, `ontos/ui/json_output.py`, `ontos/command_registry.py`,
  `link_check.py`, `map.py`, `stub.py`, `body_refs.py`, `graph.py`,
  `link_diagnostics.py`, or `mcp/schemas.py` appear in the diff, and no golden
  baseline is touched. **No bleed detected** at file granularity.

## Issues by severity

### Issue 1 — High — Loader ID validation silently drops previously-visible documents, contradicting the spec's own compatibility claim

**Where:** `ontos/io/files.py:451` (`doc_id = validate_document_id(fm.get('id', path.stem))`), grammar at `ontos/core/schema.py:78`.

**What:** `validate_document_id` is applied to the **filename-derived fallback
ID**, not just to explicit `id:` values. The grammar is
`^[A-Za-z0-9](?:[A-Za-z0-9_.-]*[A-Za-z0-9])?$` — ASCII-only, must start and end
alphanumeric. Any document without an explicit `id:` whose filename stem
contains a space, a leading underscore, or a non-ASCII character now raises
`ValueError` inside `load_document_from_content`. That exception is caught by the
`except (ValueError, UnicodeDecodeError)` handler in `load_documents`, which
**skips the document** and records a `parse_error` issue.

**Why it matters:** Spec §7 states the change avoids "a patch-release change to
the visible document set." This breaks that invariant. The document does not
error loudly — it vanishes from the canonical set, and therefore from `ontos map`,
the graph, and every query. The issue code is also wrong: nothing failed to
parse. Any `depends_on` edge pointing at the dropped document degrades into a
dangling-reference diagnostic with a cause that points at the wrong file.
Non-ASCII filenames are the sharpest edge, and spec §6 explicitly lists
"Unicode" in the test strategy.

**Reproduction** (direct-run, temporary directory, no repo data touched):

```python
from pathlib import Path; import tempfile
from ontos.io.files import load_documents
from ontos.io.yaml import parse_frontmatter_content

d = Path(tempfile.mkdtemp())
for name in ["My Notes.md", "_draft.md", "café-doc.md", "good-doc.md"]:
    (d / name).write_text("---\ntype: atom\nstatus: active\n---\n\n# hi\n", encoding="utf-8")

r = load_documents(sorted(d.glob("*.md")), parse_frontmatter_content)
print(sorted(r.documents.keys()))
for i in r.issues:
    print(i.code, i.path.name, i.message[:70])
```

Observed on `e33a31d`:

```
LOADED IDS: ['good-doc']
ISSUE code=parse_error path=My Notes.md  msg=Error parsing My Notes.md: Document id must start and end with an alphanum…
ISSUE code=parse_error path=_draft.md    msg=Error parsing _draft.md: …
ISSUE code=parse_error path=café-doc.md  msg=Error parsing café-doc.md: …
```

On baseline `bf91b42` all four load, with IDs derived verbatim from the stems.

**Mitigating fact (calibration):** I scanned this repository's own `docs/**/*.md`
and found **0** documents that would be newly dropped — the hotfix does not break
Ontos's own workspace. This is a latent break for downstream user workspaces, not
a self-inflicted one, which is why I rate it High and not Critical.

**Suggested resolution (one of):** (a) restrict `validate_document_id` at the
loader to *explicit* `id:` values and keep the permissive fallback for
filename-derived IDs, deferring stem validation to v5 with migration guidance;
or (b) if the strict grammar must apply to stems, sanitize rather than drop, and
at minimum emit a distinct, accurate issue code (`invalid_id`, not `parse_error`)
so the loss is visible. Either way, spec §7's "visible document set" claim needs
to be reconciled with spec §2's ID-rejection scope item — as written the two
contradict each other.

### Issue 2 — Low — `errors.py` silently drops `frozen=True` with no spec basis

**Where:** `ontos/core/errors.py:9,21`.

**What:** `OntosUserError` and `OntosInternalError` change from
`@dataclass(frozen=True)` to `@dataclass`. Exception instances become mutable.

**Why it matters:** Nothing in the spec's scope list asks for this. It is
plausibly an incidental fix (frozen dataclass exceptions interact awkwardly with
`Exception.__init__`/pickling), but an unexplained relaxation of an immutability
invariant inside a security hotfix is exactly the kind of quiet scope creep the
release boundary is supposed to exclude. **Reproduction:** static-inspection of
the diff; no test in the added suite covers exception mutability either way.

**Suggested resolution:** justify it in the changelog or manifest, or revert it
if it is not load-bearing.

### Issue 3 — Low / Informational — `dump_yaml` is an exported symbol whose output ordering changed

**Where:** `ontos/io/yaml.py:32-48`, exported via `ontos/io/__init__.py:8,44`.

**What:** `yaml.dump(...)` (PyYAML default `sort_keys=True`) becomes
`yaml.safe_dump(..., sort_keys=False)`.

**Why it matters:** For the two in-tree callers this is correct and required
(`schema.py` dumps one key at a time; `retrofit.py:610` wants declared order).
But `dump_yaml` is a public export, so any out-of-tree consumer sees multi-key
dumps switch from alphabetical to insertion order. That is a behavior change
shipped in a patch release. I found no in-tree breakage (**direct-run:** 82
focused tests pass), so this is informational rather than blocking.

## Positive observations

- **The P0 is genuinely fixed at the root, not patched at the call site.**
  `log.py::_build_frontmatter` no longer f-strings YAML together; it builds a
  dict and hands it to `serialize_frontmatter`, which validates the ID and
  asserts a semantic round-trip before returning. The corruption vector is
  closed at the serializer, so every consumer inherits the fix.
- **`rollback_path` is a real, previously-unreported data-destruction fix.** The
  baseline deleted tracked files whenever `git checkout --` failed for any
  reason. Proving trackedness first, and refusing to unlink directories, is
  strictly safer than what shipped.
- **The lock design anticipates the right attack.** Guarding the stable
  *directory* inode alongside the lockfile defeats the unlink-and-recreate race
  that plain `flock` on a lockfile cannot survive on POSIX. The `O_NOFOLLOW`
  open followed by an `fstat` identity re-check is the correct TOCTOU-free
  ordering, and clearing the inheritable flag prevents handle leaks into
  subprocesses.
- **Keeping the logs path lexical** so the writer can *reject* symlinked
  components, rather than `resolve()`-ing through them, is a subtle and correct
  choice that most implementations get wrong.
- **Exit-code and envelope discipline held.** The new `E_LOG_EXISTS` error rides
  the existing schema-3.4 `emit_command_error` envelope rather than inventing a
  result object — no v5 bleed.
- `tests/`: 82 focused tests across serialization, log, git-safety, TOML
  round-trip, and the frontmatter-edit pipeline all pass (**direct-run**,
  0.77s).

## Verdict

Request changes

Issue 1 is the blocker. The hotfix's own spec (§7) promises no patch-release
change to the visible document set, and the implementation breaks that promise:
documents with spaces, leading underscores, or non-ASCII filename stems are
silently dropped from the canonical loader and mislabeled `parse_error`. Ontos's
own repository is unaffected, so this is not a self-inflicted outage — but it is
a real, reproducible compatibility break for downstream workspaces, shipped in a
release whose entire boundary is defined by observable contract parity with
`bf91b42`. The fix is small: scope `validate_document_id` to explicit IDs at the
loader, or make the loss loud and accurately coded. Issues 2 and 3 are
non-blocking and can ride a follow-up.

Everything else I exercised is solid, and the core P0 remediation, the
`rollback_path` data-destruction fix, and the lock-identity design are all
better than the baseline. My confidence is bounded by coverage, not by doubt
about what I did review.

## Notes

**Evidence labels used:** direct-run, static-inspection, not-run.

- **direct-run:** git state and diff inspection; full spec read; the four-case
  loader reproduction in Issue 1; the repo-wide stem scan that bounded its blast
  radius to zero in-repo documents; `pytest` over
  `tests/io/test_toml_roundtrip.py`, `tests/core/test_schema.py`,
  `tests/test_frontmatter_roundtrip_regression.py`, `tests/commands/test_log.py`,
  `tests/core/test_git_safety.py`, `tests/core/test_frontmatter_edit_pipeline.py`
  → 82 passed.
- **static-inspection:** full diffs of `ontos/io/{yaml,files,toml,git}.py`,
  `ontos/core/{git,errors,schema}.py`, `ontos/commands/log.py`; first ~120 lines
  of `ontos/core/locking.py`; changed-file list checked against spec §9.
- **not-run, and therefore explicitly *not* attested by this review:**
  - the **full test suite** (out of scope per my instructions — acceptance
    criterion §6.2 remains unverified by me);
  - `ontos/core/context.py` (**1322 changed lines**) — the transaction staging,
    containment, mode/umask preservation, fsync, atomic-replace, and rollback
    logic. This is the single largest and highest-risk file in the diff and it is
    the one I could not cover in the timebox. **Another reviewer must own it.**
  - the MCP surfaces (`mcp/{locking,portfolio,rename_tool,server,writes}.py`),
    including outer-lock/inner-guard identity binding and read-only enforcement;
  - the **Windows `msvcrt` lock backend** — no Windows execution available;
  - acceptance criteria §6.3 (clean tree after a test run) and §6.4 (golden
    baselines byte-identical). I verified §6.4 only at file granularity — no
    golden file appears in the diff — not by content hash.
  - I did not run `ontos map` or `ontos log`, since both mutate tracked
    generated artifacts and my instructions forbid touching docs/logs.

**Timebox:** review completed within the four-minute budget. Coverage was traded
for depth on the serialization, ID, git-rollback, and lock-identity surfaces; the
transaction core and MCP paths are the known gaps.
