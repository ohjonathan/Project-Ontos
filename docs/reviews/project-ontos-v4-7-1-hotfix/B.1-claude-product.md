---
id: project-ontos-v4-7-1-hotfix-B.1-claude-product
deliverable_id: project-ontos-v4-7-1-hotfix
phase: B.1
role: product
family: claude
evidence_labels_used: [direct-run, static-inspection]
status: completed
---

# Product Review — project-ontos-v4-7-1-hotfix / B.1 / claude

Environment: worktree `/tmp/project-ontos-worktrees/project-ontos-v4.7.1-hotfix`, branch
`audit/v4.7.1-hotfix`, working tree at `82ab894` (dispatch commit). Product code and tests
are byte-identical between the review snapshot `e33a31d` and `82ab894`
(`git diff e33a31d..82ab894 -- ontos/ tests/` is empty), so direct runs against the working
tree are valid evidence for the snapshot. All CLI runs used a clean venv installed from the
worktree (`ontos 4.7.1`); the ambient `ontos` on PATH is a stale 4.6.0 and was not used.

## 1. User-value assessment

The release delivers its headline promise. The P0 that motivated it — hand-built YAML
frontmatter corrupting documents on write — is fixed at the serializer, and the two
data-destroying behaviors that could previously appear to succeed now refuse. I reproduced
both refusals directly.

The user-visible value, in order of how much it matters to a user:

1. **Logs are no longer silently destroyed.** At baseline `create_session_log` ended in an
   unconditional `output_path.write_text(content)` (static-inspection of the removed lines in
   `ontos/commands/log.py`), so a second `ontos log` with the same day and slug overwrote the
   first session's record with no warning. 4.7.1 refuses. Direct-run: the existing log's hash
   is byte-identical before and after the refused second write, and only one log file exists.
2. **Mutations can no longer rewrite a malformed document into replacement characters.**
   Direct-run against a document containing raw `0xff 0xfe` bytes: read paths still load it
   (`ontos map` exits 0, per the deliberate patch-compat decision), and `retrofit --apply`
   refuses with the file's bytes unchanged.
3. **Writes stay inside the workspace.** Direct-run with `docs/logs` replaced by a symlink to
   `/tmp/p3-outside`: the command fails closed and zero files are written outside the
   workspace.
4. **Configured `logs_dir` is finally honored.** This is a real, under-advertised fix — see §3.

The contract parity the spec sells this release on is real, not merely claimed. I verified
independently rather than taking the author's word: `ontos/ui/json_output.py` is byte-identical
to baseline, the error envelope is still schema `3.4` with the same eight top-level keys and no
schema-4 `result` object, tracked goldens are unchanged, and every file on the spec's exclusion
list (`cli.py`, `json_output.py`, `link_check.py`, `map.py`, `stub.py`, `graph.py`,
`mcp/schemas.py`, `command_registry.py`) is untouched in the diff. The full suite is
**1550 passed, 2 skipped** from the hotfix environment.

Where the release falls short is not integrity — it is the **legibility of its own refusals**.
Two of the three new "we protected you" behaviors are well-presented. The third (malformed
UTF-8) reaches the user as an internal crash that names no file and offers no remedy, which is
the blocking finding below.

## 2. Product-surface cross-reference

### 2.1 Spec-declared user-visible surfaces

The spec declares these as the user-observable behavior deltas (§2 Scope, §7
Migration/Compatibility, and the CHANGELOG "Compatibility notes"):

| # | Spec-declared surface | Source |
|---|---|---|
| S1 | A log filename collision returns an error instead of overwriting | §7 |
| S2 | A mutation targeting an unsafe/linked/duplicated/outside-workspace path fails before changing external data | §7 |
| S3 | Malformed UTF-8 still loads on read; a mutation refuses it | §7, CHANGELOG |
| S4 | Command envelope stays schema 3.4; no v4 `result` object, no new exit-code taxonomy | §4, AC-5 |
| S5 | CLI logs route through configured `logs_dir`, safe YAML, exclusive creation | §2, §4 |
| S6 | Archive-marker failure stays best-effort and preserves baseline success exit | §4 |
| S7 | Read-only MCP suppresses persistent graph export, usage logs, portfolio init, SQLite sidecars | §2, §4 |
| S8 | Both version sources report 4.7.1 | §2, AC-6 |
| S9 | Map timestamps, CLI flags, graph/link output, MCP `by_type`, stub type set unchanged | CHANGELOG |

### 2.2 Spec-vs-implementation cross-reference

| # | Verdict | Evidence |
|---|---|---|
| S1 | **Matches, well-executed** | direct-run: 2nd `ontos log --title "my session"` → exit 1, human `❌ Session log already exists: …`, JSON `{"schema_version":"3.4","status":"error","exit_code":1,"error":{"code":"E_LOG_EXISTS"},"data":{"path":"…"}}`; pre/post `shasum` of the existing log identical; log count stays 1 |
| S2 | **Matches** | direct-run: symlinked `docs/logs` → outside root → exit 1, `E_COMMAND_FAILED`, `find /tmp/p3-outside -type f` = 0 files |
| S3 | **Integrity matches; presentation does not** | direct-run: `map` exit 0 (tolerant read) ✓; `retrofit --obsidian --apply` refuses, bytes unchanged ✓ — but surfaces as **exit 5 / `E_INTERNAL` / "Internal error: 'utf-8' codec can't decode byte 0xff in position 53"**, naming no file. See B-1 |
| S4 | **Matches** | direct-run: `map --json` and `query --health --json` both return exactly `[command, data, error, exit_code, message, schema_version, status, warnings]`, `schema_version` `3.4`, no `result` key; `git diff` on `ontos/ui/json_output.py` empty |
| S5 | **Matches, but the `logs_dir` half is a behavior change not called out as one** | direct-run: `logs_dir = "custom/journal"` → log lands at `custom/journal/…`. At baseline the `from ontos_config import LOGS_DIR` import was dead (v2-era module, always `ImportError`) so `docs/logs` was forced. See SF-3 |
| S6 | **Matches** | direct-run: `.ontos/session_archived` written; marker path is via `SessionContext` in a `try/except … pass`; success exit stays 0 |
| S7 | **Matches** | direct-run: `tests/mcp/test_read_only_registration.py`, `test_write_tools.py`, `test_locking.py` → 40 passed |
| S8 | **Matches** | direct-run: `ontos --version` → `ontos 4.7.1`; `ontos.__version__` → `4.7.1`; `pyproject.toml` → `4.7.1` |
| S9 | **Matches** | static-inspection: exclusion-list files absent from `git diff --name-only bf91b42..e33a31d`; goldens unchanged |

## 3. UX-friction inventory

**F1 — The documented default agent workflow now hard-fails on the second session of a day.**
`CLAUDE.md` and the Manual both instruct: at session end, run `ontos log`. Bare `ontos log`
derives its slug from the last commit subject, not from anything session-unique. Direct-run in a
fresh repo: first `ontos log --auto` → `docs/logs/2026-07-11_init.md`, exit 0. Second
`ontos log --auto`, same day, same branch, no new commit → exit 1, collision refusal. There is no
`--force`, `--overwrite`, or auto-suffix (`ontos log --help` has no such flag). A human reads the
message and passes `--title`; an agent following `CLAUDE.md` literally gets a nonzero exit at the
end of every second session of the day.

The refusal itself is right — the old behavior destroyed the first log. The friction is that the
guidance prescribing the command was not updated to match, and there is no non-interactive
escape. This is SF-2.

**F2 — One bad byte anywhere aborts the entire mutation run.** `retrofit --apply` against a
workspace where a single document has invalid UTF-8 aborts the whole command with zero documents
processed and no indication of which file is at fault. Baseline replacement-decoded and continued
(corrupting that one file, which is why the change is right, but processing the rest). Users with
a large docs tree get an all-or-nothing failure they cannot triage from the output. Coupled with
B-1's missing path, this is the sharpest usability regression in the release.

**F3 — No remediation step on the unsafe-path error.** `Unable to prepare session log:
paths.logs_dir must resolve within repository root` correctly names the offending config key but
does not say what to do (point `logs_dir` inside the repo / remove the symlinked component).

## 4. Copy review

**Good.** The collision message is the strongest copy in the release: it states the condition,
names the exact file, and gives two concrete recovery paths, one of which (`--title`) is a real,
existing flag I verified. That is the standard the other messages should meet.

**Weak.**

- **`Internal error: 'utf-8' codec can't decode byte 0xff in position 53: invalid start byte`** —
  this is a Python exception string promoted to a user-facing message. It names a byte offset in
  a file it does not name. "Internal error" tells the user Ontos is broken when in fact Ontos is
  working exactly as designed and *their document* is the problem. In human mode it degrades
  further to a bare `Error: 'utf-8' codec can't decode byte 0xff…`. This is B-1.
- **"Choose a different `--title`, or intentionally move/remove the existing log before
  retrying."** — "intentionally" is doing no work and reads oddly; the point it is groping toward
  is that removing a log is a destructive act the user should not do casually. It also never
  explains *why* the name collided (logs are keyed `date_slug`, so the same title tomorrow is
  fine), which is the single fact that would let a user predict the behavior instead of being
  surprised by it. Suggested: `Session log already exists: <path>. Logs are named
  <date>_<slug>, so a second log on the same day needs a different --title. To replace the
  existing log, move or delete it first.`
- **`paths.logs_dir must resolve within repository root`** — accurate and correctly names the
  config key; add the fix ("set it to a path inside the repository, or remove the symlinked
  path component").

## 5. Accessibility surface

Ontos is a terminal CLI plus an MCP server; there is no GUI, color-only signal, or
keyboard-navigation surface in this diff. The relevant accessibility properties are
machine-readability and non-visual usability, and they hold:

- Every state I exercised is available as structured JSON (`--json`) with a stable schema, so
  screen-reader and programmatic consumers are not dependent on the decorated human output.
- The human output uses `✅`/`❌` emoji as a *redundant* cue — the text alone carries the meaning,
  and `--quiet`/`--json` suppress the decoration. No information is conveyed by glyph or color
  alone.
- One gap, inherited rather than introduced: the `E_INTERNAL` malformed-UTF-8 failure emits
  `"data": {}`, so a non-visual or programmatic consumer gets no path either — the JSON surface
  is exactly as unactionable as the human one. Fixing B-1 should populate `data.path`, as the
  collision error already does.

## 6. Failure-visibility

| Failure | Visible? | Correctly classified? | Actionable? |
|---|---|---|---|
| Log collision (S1) | Yes — human + JSON, `data.path` | Yes — exit 1, `E_LOG_EXISTS` | **Yes** — names file + two recovery paths |
| Unsafe/outside-root log path (S2) | Yes — human + JSON | Yes — exit 1, `E_COMMAND_FAILED` | Partly — names the config key, no fix step (F3) |
| Malformed UTF-8 on mutation (S3) | Yes, but as a crash | **No — exit 5, `E_INTERNAL`** | **No** — no path, no doc id, no remedy (B-1) |
| Archive-marker failure (S6) | No — silent by design | Yes — best-effort per spec | N/A — correctly non-fatal |

The pattern is that the two failures the authors *designed* an error for are excellent, and the
one they only designed a *refusal* for was never given an error to surface through. The strict
decode raises `UnicodeDecodeError`, nothing in the retrofit path catches it (`grep` for handlers
finds them only in `ontos/io/files.py:200,338` and `ontos/commands/scaffold.py:114,158`), and it
falls through `cli.main()`'s generic `except Exception` into the internal-error taxonomy.

## 7. Issues found

### Blocking

**B-1 — The release's headline safety refusal (malformed UTF-8) ships as an internal crash that
names no file and offers no recovery.** [direct-run]

Spec §7 promises "a mutation refuses it"; the CHANGELOG promises "Every mutation path decodes
strictly and refuses to rewrite malformed input." A refusal is a designed, user-facing product
behavior. What a user actually gets:

```
$ ontos retrofit --obsidian --apply --json     # one doc in the tree has raw 0xff bytes
{"schema_version": "3.4", "command": "retrofit", "status": "error", "exit_code": 5,
 "message": "Internal error: 'utf-8' codec can't decode byte 0xff in position 53: invalid start byte",
 "data": {}, "warnings": [], "error": {"code": "E_INTERNAL"}}

$ ontos retrofit --obsidian --apply            # human mode
Error: 'utf-8' codec can't decode byte 0xff in position 53: invalid start byte
```

Reproduced end-to-end: temp project, one document with invalid UTF-8 in its body, clean git
tree. The document's bytes are correctly left unchanged — **the integrity property holds and is
not in question.** The defect is the contract and the copy:

- **Misclassified.** `E_INTERNAL` / exit 5 is the "Ontos has a bug, file a report" taxonomy. This
  is not a bug; it is the deliberate safety behavior this release was built to add. Presenting it
  as a crash will generate bug reports instead of remediation, and it is precisely the
  anti-pattern the repo's own audit already logged as a defect (`docs/reviews/2026-07-02-fable-repo-audit.md`,
  D1c-envelope-4: environmental/user conditions returning exit 5 `E_INTERNAL` where peers return
  exit 1 `E_COMMAND_FAILED`). The hotfix adds a fresh instance of it.
- **Unactionable.** No file path, no document ID, `"data": {}`. A user with one bad byte among
  178 documents has a byte offset into a file the tool declines to name. There is no supported
  way to find it from Ontos's output.
- **Untested.** No test in the suite exercises malformed UTF-8 at all — `grep` across `tests/`
  for invalid-byte fixtures, `UnicodeDecodeError`, or equivalents returns nothing, while the
  spec's own risk table claims mitigation by "Strict mutation reads and **byte-unchanged failure
  tests**" and §6 lists the coverage. The safety property is real but rests on no regression
  test, and the envelope it fails through was evidently never looked at.

Fix is small and localized: catch `UnicodeDecodeError` at the mutation boundaries, map it to
exit 1 with `E_COMMAND_FAILED` (or a dedicated `E_INVALID_ENCODING`), populate `data.path`, and
word it as a refusal with a remedy ("`<path>` is not valid UTF-8 and was not modified; re-save it
as UTF-8, then retry"). Add the byte-unchanged regression test the spec already promises. None of
this touches the exclusion list or the envelope schema, so it fits inside the patch boundary.

### Should-fix

**SF-1 — Two different machine-readable codes for the same "already exists" condition.**
[static-inspection] CLI log collision emits `E_LOG_EXISTS` (`ontos/commands/log.py:317`); the MCP
write tools emit `E_FILE_EXISTS` for the same semantic condition
(`ontos/mcp/writes.py:456,529`). A consumer handling "the thing I tried to create is already
there" must special-case per surface. Pick one code. `E_FILE_EXISTS` already existed, so
`E_LOG_EXISTS` is the newly-introduced divergence.

**SF-2 — The guidance that prescribes `ontos log` was not updated for the new hard failure.**
[direct-run] Per F1, bare `ontos log` twice in one day now exits 1, and that command is exactly
what `CLAUDE.md` ("When ending a session: Run `ontos log`") and the Manual tell users and agents
to run. The `AGENTS.md` diff in this release is purely regenerated metadata (timestamps, doc
count, branch) and adds nothing about the collision; the Manual has no mention of log collision
(`grep -i "already exists|collision|overwrit"` finds only `init --force` and `rename`). The
CHANGELOG documents it, but the CHANGELOG is not what an agent reads at session end. Either
document the new failure and the `--title` remedy where the workflow is prescribed, or give the
command a non-interactive path through the collision (auto-suffix, or an explicit `--force`).

**SF-3 — `logs_dir` is now honored, which silently relocates new logs for any project that set
it — and §7 says "No migration is required."** [direct-run + static-inspection] Baseline's
`try: from ontos_config import LOGS_DIR / except ImportError: docs/logs` referenced a v2-era
module that no v4 project ships, so `paths.logs_dir` in `.ontos.toml` was dead config and every
log went to `docs/logs`. 4.7.1 reads it for real: with `logs_dir = "custom/journal"`, the log
lands at `custom/journal/2026-07-11_cfg-test.md` (verified). This is the correct fix, but it is a
**third** intentional behavior change, and spec §7 enumerates only two (collision, unsafe path)
before asserting no migration is needed. A user who set `logs_dir` and never noticed it was
ignored will find their log history split across two directories after upgrading. Add it to the
compatibility notes with a one-line "your existing logs stay in `docs/logs`; move them or reset
`logs_dir`."

**SF-4 — The patch's risk profile deserves a louder note than "Patch release."** See §10; the
scoping is defensible but the release comms undersell what changed underneath.

### Minor

- **M-1** — Unsafe-path copy has no remediation step (F3).
- **M-2** — Collision copy: drop "intentionally"; state the `date_slug` naming rule (§4).
- **M-3** — `OntosUserError` / `OntosInternalError` changed from `@dataclass(frozen=True)` to
  `@dataclass`. Verified: instances are now **unhashable** (`TypeError: unhashable type`) and
  mutable (`e.message = 'mutated'` succeeds). Neither is re-exported from `ontos/__init__`, so
  blast radius is internal, but this is an undocumented API/behavior change riding a patch with
  no rationale in the spec or CHANGELOG. Flagging for the adversarial lane to confirm nothing
  depends on hashing them.
- **M-4** — A `logs_dir` pointing outside `docs_dir` produces logs the context map does not index
  (verified: `custom/journal` log absent from `Ontos_Context_Map.md`). Latent config-coherence
  issue that SF-3 newly makes reachable; not introduced by this diff's logic.
- **M-5** — Generated logs now emit `created: '2026-07-11'` (quoted) where baseline emitted it
  bare. This is the anti-coercion fix working as intended and is harmless, but it is a visible
  format delta between old and new logs in the same directory.

## 8. Positive observations

- **The collision refusal is a model error.** Correct exit code, correct machine code, structured
  `data.path`, human message that names the file and gives two real recovery paths using a flag
  that actually exists. I verified the existing log is byte-identical after the refusal. If B-1
  were brought up to this standard the release would be clean.
- **Contract parity is real, not asserted.** I checked it independently: `json_output.py`
  byte-identical, envelope still 3.4 with the baseline key set and no `result` object, goldens
  unchanged, and every exclusion-list file untouched. For a release whose entire premise is
  "we changed the write path but nothing you depend on," this is the thing that had to be true,
  and it is.
- **Fail-closed actually fails closed.** The symlink-escape attempt wrote zero bytes outside the
  workspace.
- **The scope discipline is genuinely impressive.** §5's Open Questions table takes six tempting
  improvements (schema 4.0, strict loader, timestamp suppression, activation states, wheel-only
  publishing, hook rewiring) and defers every one with a stated reason. Splitting a P0 out of a
  breaking PR and holding the line on the boundary is the right call and was executed.
- **1550 tests pass** from the hotfix environment, and the test run leaves no tracked repository
  changes.

## 9. Verdict

Request changes

The data-integrity goal is met and I verified it directly: corruption stops, the two
previously-silent destructive operations now refuse, byte-level preservation holds, and the
compatibility boundary the release is sold on survives independent checking. The patch scoping is
defensible.

I am blocking on B-1 only. The release's third headline safety behavior — refusing to rewrite
malformed UTF-8 — reaches the user as `exit 5 / E_INTERNAL / "Internal error: 'utf-8' codec can't
decode byte 0xff in position 53"`, with no file path in either the human or the JSON surface, no
remedy, and no test coverage, while aborting the entire mutation run. A release whose purpose is
to make users trust Ontos with their files should not present its own designed safeguard as a
crash the user cannot act on. The fix is small, localized, and fits entirely inside the declared
patch boundary. SF-1 through SF-4 should ride with it.

## 10. Notes

**Is a patch release correctly scoped?** Yes, with a caveat worth stating plainly. The diff is
enormous for a patch — +5,436/−483, a new 596-line locking module, and a rewrite of the central
write transaction touching every mutation surface. Semver governs the *contract*, not the diff
size, and the contract parity holds under independent verification (envelope, exit codes,
goldens, exclusion list), so `4.7.1` is technically correct. The two intentional behavior changes
are refusals of operations that previously destroyed data, which is the right thing to do in a
patch. But users auto-upgrade into patch releases, and this one replaces the machinery that
writes every one of their documents. The CHANGELOG's "Patch release stopping active frontmatter
corruption and hardening local write paths" undersells that. I would add an explicit line to the
release notes — the write transaction, locking, and every serializer-backed mutation path were
replaced; verify in a scratch workspace before running mutations against a corpus you care about
— and make SF-3's relocation note prominent. That is release comms, not a code change (SF-4).

**Concurrent-worker artifact, not an implementation defect.** During this session
`Ontos_Context_Map.md` appeared as modified in `git status`. This was **not** produced by my runs
or by the test suite: a sibling B.1 reviewer (the gemini worker) ran `ontos map`, which absorbed
its own freshly-written `B.1-gemini-alignment.md` into the index (`documents_loaded` 177→178, new
`B.1-gemini-alignment.md` row, timestamps mid-session). I left it untouched per my write
restrictions. It has no bearing on the implementation, but it does illustrate why the spec's
decision to keep map timestamps unsuppressed (§5) makes a shared worktree easy to dirty. My own
full test run produced no tracked repository changes, satisfying acceptance criterion 3.

**Test-environment note.** An initial `pytest` run showed 3 failures in `tests/mcp/`
(`test_error_paths.py`, `test_parity.py`). These are **not** hotfix regressions: those tests shell
out to a hardcoded `python3` rather than `sys.executable`, and picked up a system interpreter
lacking `tomli_w`. With the venv first on `PATH` the suite is **1550 passed, 2 skipped**. Worth a
follow-up outside this deliverable — the tests should use `sys.executable` — but it is not in
scope here and I am not counting it against the release.

**Evidence labels.** direct-run for §1–§7 behavioral claims (collision, unsafe path, malformed
UTF-8, envelope/exit parity, versions, logs_dir, full suite, read-only MCP tests);
static-inspection for baseline-comparison claims (the removed `write_text` overwrite, the dead
`ontos_config` import, error-code sites, exclusion-list and golden parity via `git diff`).
