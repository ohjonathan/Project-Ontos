---
id: project-ontos-v4-7-1-hotfix-B.1-claude-product-r2
deliverable_id: project-ontos-v4-7-1-hotfix
phase: B.1
role: product
family: claude
evidence_labels_used:
  - direct-run
  - static-inspection
status: completed
---

# B.1 Product Review — Project Ontos v4.7.1 Hotfix (claude, r2)

Implementation `e33a31d` reviewed against baseline `bf91b42` and
`docs/specs/project-ontos-v4-7-1-hotfix-spec.md`.

## User value

The patch delivers what a user of a documentation tool most needs from a patch
release: their documents stop being silently corrupted. The frontmatter
serializer now routes every scalar through PyYAML-safe quoting with a semantic
round-trip assertion before commit, so date-like IDs, hash-leading values,
comma-bearing list items, and Unicode survive a write instead of changing type
or breaking the file. The two behavioral rejections the patch introduces — a log
collision refusing to overwrite, and a mutation refusing an unsafe path — both
trade a silent data loss for a visible error, which is the correct direction for
a tool whose entire value is that the docs on disk are trustworthy.

Crucially, the user's *visible contract* is untouched. `ontos/ui/json_output.py`
is byte-identical to baseline (static-inspection: `git diff bf91b42 e33a31d --
ontos/ui/json_output.py` is empty), so the schema-3.4 envelope, exit codes, and
key set that scripts and agents depend on all survive. Users get the fix without
paying a migration cost.

## Surface cross-reference

| Surface | Spec requirement | Implementation | Evidence |
|---|---|---|---|
| CLI `log` | Configured `logs_dir`, safe YAML, exclusive create, refuse collision | `ontos/commands/log.py:113-118, 286-336` | direct-run |
| Log frontmatter | Serializer, not hand-built strings | `_build_frontmatter` now dict → `serialize_frontmatter` | direct-run |
| Collision | Error, not overwrite | `E_LOG_EXISTS` + `data={"path": ...}` | direct-run |
| Unsafe path | Fail before touching external data | `SessionContext._safe_workspace_path`, `create_text_file_exclusively` (`O_EXCL|O_NOFOLLOW`) | direct-run |
| Invalid encoding | Mutation refuses; read stays lenient | strict decode on mutation readers; loader unchanged | static-inspection |
| Archive marker | Best-effort, preserves baseline success exit | `_create_archive_marker` still swallows `OSError/RuntimeError/ValueError` | direct-run |
| Envelope | Schema 3.4, no `result` object | `json_output.py` unmodified | static-inspection |
| Exclusion list | 9 named files untouched | `git diff --name-only` over the exclusion set returns nothing | static-inspection |

Tests: `tests/commands/test_log.py`, `tests/core/test_schema.py`,
`tests/test_session_context.py`, `tests/test_frontmatter_roundtrip_regression.py`
— **115 passed** (direct-run, worktree `.venv`). Per the timebox, the full suite
was **not-run**; acceptance criteria 2–4 are therefore unverified here.

## Friction

The one place a user meets new friction is a same-day slug collision. This is a
real workflow event, not an edge case: `ontos log -e "fix-parser"` twice in a
day now fails the second time where it previously overwrote. That is the right
call — the old behavior destroyed the earlier log — and the error copy tells the
user exactly how to proceed. Friction is proportionate and well-signposted.

## Copy

`E_LOG_EXISTS` is the standout. It names the conflicting path, and offers two
concrete recoveries ("Choose a different `--title`, or intentionally move/remove
the existing log before retrying"). The word "intentionally" is doing real work:
it tells the user the tool is refusing on purpose. This is the model the rest of
the patch should follow.

It does not. The `SessionContext` guard messages that a user can actually reach —
`operation path is outside the workspace: …`, `operation path must not be a
symlink: …`, `operation path must not contain a reparse point: …`
(`ontos/core/context.py:685-899`) — are internal invariant language surfaced
verbatim through log.py's generic wrapper as `Unable to create session log
<path>: <exc>`. A user who symlinks `docs/logs/` to a shared drive (a legitimate
setup) gets a message that reads like a crash, with no statement of what the tool
wants instead. See Issue 2.

## Accessibility

No regression. All new output is plain text through the existing `OutputHandler`
and JSON envelope; no color-only signaling, no new interactive prompts, no ASCII
diagrams. Errors carry a machine-readable `code` alongside the human `message`,
so both screen-reader and programmatic consumers are served.

## Failure visibility

Good, with one caveat. Every new failure mode is surfaced with a distinct exit
path and a JSON-mode equivalent — nothing fails silently *at the write*. The
caveat is at the *config* layer: because the resolved log directory is no longer
echoed and the legacy override is no longer read (Issue 1), a user whose logs
quietly relocate gets no signal at all. The write succeeds; it just succeeds
somewhere else. That is the one silent outcome in an otherwise loud patch.

The archive-marker path correctly stays best-effort — a marker failure still
exits 0 with the baseline envelope, preserving the contract, and
`test_archive_marker_symlink_preserves_legacy_success_contract` pins it.

## Issues

**Issue 1 — P2, compatibility: legacy `ontos_config.py` `LOGS_DIR` override is
silently dropped for `log`.** (static-inspection)

Baseline `log.py` resolved the log directory via `from ontos_config import
LOGS_DIR` with a `docs/logs` fallback, and explicitly honored an absolute value.
`e33a31d` replaces that entirely with
`load_project_config(repo_root=project_root).paths.logs_dir`, and
`ontos/io/config.py:27` reads only `.ontos.toml` — it does **not** bridge the
legacy module. Meanwhile `ontos/core/paths.py:82-103` still documents and
implements the legacy precedence chain (`ontos_config.py` → `ontos_config_defaults.py`
→ default) for other surfaces, and `Ontos_CHANGELOG.md:397` states legacy config
is "still supported with deprecation notice."

User impact: a user on legacy config with a non-default `LOGS_DIR` has their logs
silently written to `docs/logs` instead, with no warning and exit 0. Their prior
logs remain in the old directory, so `ontos log` appears to work while the
archive splits in two. This is a behavior change not listed in spec §7
(Migration / Compatibility), which claims "No migration is required," and the
CHANGELOG entry ("logs use the configured `logs_dir`") does not disclose it.

Recommendation: either read the legacy override through the same `paths.py`
precedence chain the rest of the package uses, or state the drop explicitly in
§7 and the CHANGELOG as a deliberate deprecation. Silently relocating a user's
archive is the one outcome this patch is otherwise built to prevent.

**Issue 2 — P2, recovery copy: an absolute or symlinked `logs_dir` hard-fails
with internal invariant language.** (static-inspection)

Baseline explicitly supported an absolute logs directory. Now
`project_root / config.paths.logs_dir` passes an absolute value straight through
to `_safe_workspace_path`, which raises `operation path is outside the
workspace: …` (`ontos/core/context.py:685`); log.py catches it as generic
`E_COMMAND_FAILED` with `Unable to create session log <path>: <exc>`. The
symlinked-`docs/logs` case behaves the same way and is pinned as intended
behavior by `test_default_logs_dir_symlink_is_rejected_before_resolution`.

The *rejection* is defensible and is arguably covered by spec §7's "a mutation
targeting an unsafe, linked, duplicated, or outside-workspace path fails." The
*copy* is not: a user with a deliberately-configured external log directory is
told an internal invariant was violated, not that their configuration is no
longer supported and not what to change. Recommendation: detect the
outside-workspace / symlinked `logs_dir` case at config resolution and emit a
dedicated code (e.g. `E_LOG_DIR_UNSAFE`) whose message names `logs_dir` and
states the workspace-containment requirement, in the register of `E_LOG_EXISTS`.

**Issue 3 — P3, patch scope: `errors.py` drops `frozen=True` with no spec or
CHANGELOG mention.** (static-inspection)

`ontos/core/errors.py` changes `@dataclass(frozen=True)` → `@dataclass` on both
`OntosUserError` and `OntosInternalError`. This loosens the immutability of two
public exception types. There is a plausible mechanical reason (frozen dataclass
exceptions conflict with `Exception.__init__` setting `args`), but it appears in
neither spec §4 nor the CHANGELOG, and it is not required by any in-scope bullet
in §2. In a release whose stated boundary is "observable contract parity with
`bf91b42`," an unexplained public-type mutation change should be justified in the
spec or reverted.

## Positives

- `E_LOG_EXISTS` copy is exemplary: names the path, offers two recoveries, signals
  intent. This is the bar.
- No envelope regression. `data` is a pre-existing `emit_command_error` kwarg
  (`ontos/ui/json_output.py:161`), so `data={"path": …}` adds no key and the 3.4
  key set is preserved — the new error code is purely additive within the
  existing contract.
- Exclusion list fully respected across all nine named files.
- Archive marker stays best-effort, preserving the baseline success exit — a
  hardening change that resisted the temptation to make a peripheral failure fatal.
- The CHANGELOG's compatibility framing ("without changing the command-envelope
  schema or exit-code taxonomy") is accurate as implemented, and the two
  intentional rejections are disclosed.
- Test coverage tracks the user-visible cases directly: configured logs dir,
  adversarial round-trip values, collision-without-overwrite, symlink rejection,
  legacy success contract.

## Verdict

Request changes

Issues 1 and 2 are the blocking pair, and they are the same defect viewed twice:
the log-directory resolution was rewritten without carrying the baseline's
configuration contract with it. Issue 1 is the more serious of the two because it
fails *silently* — a legacy-config user's archive relocates with no warning and a
success exit, which is precisely the class of quiet data outcome this hotfix
exists to eliminate. Issue 2 is loud but unhelpful, and is a copy fix. Neither is
deep: both live in the ~6 lines of `create_session_log` that resolve `logs_dir`,
plus a CHANGELOG/§7 disclosure. Issue 3 is a scope question for the author, not a
gate.

Everything else in this patch is sound product work, and the core value — the
corruption fix — is delivered without touching the user's visible contract. I
expect this to clear on a single revision.

## Notes

- Evidence labels used: **direct-run** (115 focused tests passed via worktree
  `.venv`: `tests/commands/test_log.py`, `tests/core/test_schema.py`,
  `tests/test_session_context.py`, `tests/test_frontmatter_roundtrip_regression.py`);
  **static-inspection** (spec, CHANGELOG, targeted diff, exclusion-list diff,
  config-resolution call chain).
- **not-run**: full suite, clean-tree verification, golden-baseline byte
  comparison, manual CLI/MCP exercises. Spec acceptance criteria 2, 3, 4, and 7
  are therefore **unverified by this review** and must be confirmed elsewhere.
  Criteria 1 (focused tests) and 5 (envelope parity) are supported by the
  evidence above.
- The 1,322-line `ontos/core/context.py` and 596-line `ontos/core/locking.py`
  additions were reviewed only at the product surface (error copy, failure
  visibility, containment behavior reachable from `log`). Their correctness under
  concurrency and crash recovery is an engineering-review concern and is out of
  scope for this role.
- Timebox honored; no code, docs, logs, or git state modified. This artifact is
  the only file written.
