---
id: project-ontos-v4-7-1-hotfix-D.2-claude-product
deliverable_id: project-ontos-v4-7-1-hotfix
phase: D.2
role: product
family: claude
evidence_labels_used: [direct-run]
status: completed
---

# D.2 Product Review — project-ontos-v4-7-1-hotfix (`a71ac4a`)

Reviewed at commit `a71ac4a` in `/tmp/project-ontos-worktrees/project-ontos-v4.7.1-hotfix`.
All claims below are from direct read-only runs against the repo `.venv` in a
throwaway project (`/tmp/ontos_prodcheck`); no Ontos activation, map, or log
was run against the project itself, and no code was modified.

## User value

The hotfix delivers on its headline promise: the destructive paths a user was
most likely to hit silently now stop, say what happened, and leave bytes alone.

Two behaviors carry most of that value, and both hold up when actually exercised:

**Mutations refuse malformed input without touching it.** Running
`ontos verify docs/bad.md` against a file with invalid UTF-8 bytes prints
`❌ docs/bad.md is not valid UTF-8 and was not modified. Re-save the file as
UTF-8, then retry.`, exits 1, and the file's checksum is unchanged afterward.
The message names the offending path, states the file was not modified, and
gives a recovery step — the three things a user needs to unblock themselves.
The `apply_promotion` / `update_describes_verified` handlers re-raise
`InvalidDocumentEncodingError` past the broad `except Exception` that would
otherwise have downgraded it to a per-file "failed" line and let the batch
continue, so a bad file aborts the run instead of being buried in a scroll of
successes. That is the correct product call for a mutation.

**Log collision is non-destructive and self-explaining.** Running
`ontos log --title "history-split-check"` twice creates the log the first time
and the second time prints `❌ Session log already exists: <path>. Choose a
different --title, or intentionally move/remove the existing log before
retrying.` with exit 1. The earlier log survives. The copy names the path, gives
two concrete outs, and the word "intentionally" does real work — it signals that
clobbering is a deliberate act, not a shrug. This is a direct fix for the
data-loss footgun and it reads well.

## Friction, copy, and failure visibility

**The logs-directory split is documented but invisible in the product.** This is
the one place where a user can be silently surprised. With `[paths].logs_dir`
newly taking effect, `ontos log` wrote to `docs/logs_new/` while the pre-existing
log stayed in `docs/logs_old/`, and the command printed only
`✅ Session log created: /…/docs/logs_new/2026-07-11_history-split-check.md`.
No warning, no mention that history now lives in two places. Grepping
`ontos/commands/log.py` for any warning on the split or on the directory falling
outside scan scope returns nothing — the only signals are the CHANGELOG and the
new Manual paragraph. The Manual is candid that "Ontos does not move history
automatically" and that the directory must stay in scan scope "if those logs
should appear in maps and queries," which means the failure mode is logs quietly
dropping out of maps and queries. Documentation is the right *explanation*, but
it is a weak *notification*: the user most exposed here is the one upgrading who
never re-reads the Manual. See issue 1.

**The UTF-8 recovery step tells you what, not how.** "Re-save the file as UTF-8"
is correct and actionable for a human with an editor, but it stops one step short
of a command a user can paste. Minor, and arguably right to keep terse in a patch.
See issue 2.

**`ontos log --help` does not mention exclusivity.** `--title` is documented only
as "Log entry title (overrides positional topic)"; nothing in `--help` hints that
a same-day slug collision is refused. The runtime copy is good enough that this
is discoverable at the moment of failure rather than before it. See issue 3.

## Issues

1. **(Medium — failure visibility) The logs-directory split is announced only in
   docs, never by the product.** On the first `ontos log` after `[paths].logs_dir`
   takes effect, the command reports success against the new directory and says
   nothing about the old one. A user's log history is now split across two
   directories, and if the configured directory sits outside scan scope those logs
   disappear from maps and queries — with no in-product signal at any point.
   Suggest a one-line warning on the first write to a `logs_dir` that differs from
   the directory holding existing logs (e.g. "N earlier logs remain in docs/logs;
   Ontos does not move history automatically"), and a warning when `logs_dir`
   resolves outside scan scope. The `warnings: []` envelope field already exists
   to carry exactly this, so it costs nothing on the automation contract.

2. **(Low — copy) UTF-8 refusal gives no concrete recovery command.** "Re-save the
   file as UTF-8, then retry" leaves the mechanics to the user. A parenthetical
   such as `iconv -f <encoding> -t utf-8` would close the loop. Acceptable as-is
   for a patch release.

3. **(Low — copy) `ontos log --help` omits the collision contract.** The
   exclusivity rule is in the Manual but not in `--help`, where a user forming the
   command would see it. One clause on `--title` would cover it.

None of the three are release blockers. Issue 1 is the only one I would want
tracked, because it is a silent-visibility change rather than a wording gap.

## Positives

- **Refusals are fail-closed and verifiably non-destructive.** The invalid-UTF-8
  file's checksum was unchanged after a refused `verify`; the pre-existing log
  survived a refused `log`. The hotfix's central claim holds under direct test.
- **Error copy is consistently structured**: what happened, which path, what was
  *not* done, what to do next. Both the UTF-8 and collision messages follow it.
- **Schema-3.4 automation contracts are intact.** `--json` returns
  `{"schema_version": "3.4", …}` on both failures, with `E_COMMAND_FAILED` for the
  UTF-8 refusal and `E_FILE_EXISTS` for the collision, `exit_code: 1` matching the
  real process exit (1) in both cases. The log collision usefully carries the
  conflicting path in `data.path` rather than only in prose, so automation can act
  on it without parsing the message.
- **Stdout/stderr separation is clean.** The human-readable `❌` line goes to
  stderr and the envelope to stdout; `ontos --json verify … 2>/dev/null | jq -r
  '.error.code'` returns `E_COMMAND_FAILED` cleanly. Decorated output does not
  corrupt the JSON contract.
- **The Manual correction is the sleeper win.** The old text claimed "One log per
  branch per day—subsequent pushes append to the same log," which the exclusivity
  fix makes false. `a71ac4a` replaces it with an accurate description of hook
  refusal. Catching a doc claim that the fix silently invalidated is exactly the
  kind of thing that usually ships broken.
- **CHANGELOG is honest about scope**, explicitly stating that schema stays at 3.4,
  that lenient read-only decoding is retained for patch compatibility while
  mutations decode strictly, and that cross-command unification is deferred to
  v5.0.0. It does not oversell the patch.

## Verdict

The user-facing behavior matches what the CHANGELOG and Manual promise. Recovery
is real, refusals are non-destructive and legible, and the schema-3.4 automation
surface is unchanged. The one gap worth tracking is that the logs-directory split
is explained only in documentation and never surfaced by the product, which turns
an upgrade-time change into a silent one. That is a follow-up, not a blocker.

approve-with-comments

## Notes

- Timeboxed to five minutes; checks were focused and read-only.
- Verified by direct run: invalid-UTF-8 refusal on `verify` (message, exit code,
  JSON envelope, checksum-unchanged), log slug collision (message, exit code,
  envelope, `error.code`, `data.path`, earlier log preserved), logs-directory
  split behavior, stdout/stderr separation under `--json`, and `ontos log --help`.
- Read but not executed: the `promote` and `migrate` refusal paths in `a71ac4a`.
  I inspected their diffs — both re-raise `InvalidDocumentEncodingError` and return
  `1` with the message, and `migrate --apply` pre-scans all files before planning
  any write, which is the stronger fail-closed ordering — but I did not exercise
  them end-to-end within the timebox. A reviewer with more budget should confirm
  the batch-`promote` abort leaves already-buffered promotions in the intended
  state, since that path aborts mid-batch on encountering a malformed file.
- The scan-scope consequence in issue 1 is drawn from the Manual's own caveat and
  from the absence of any warning in `ontos/commands/log.py`; I did not run
  `ontos map`/`query` to observe logs dropping out, per the no-activation constraint.
