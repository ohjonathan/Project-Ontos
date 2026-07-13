---
phase: B.1
role: adversarial
family: claude
deliverable_id: project-ontos-v5-0-0
status: completed
reviewed_commit: 5678e910ce11ed7a3546822cf3e34d50c5741681
base_commit: 454b102b033310517dd4623b7eaa3a42b271f32d
---

# Ontos 5.0.0 — B.1 Claude adversarial review

## Scope and method

Reviewed product commit `5678e910ce11ed7a3546822cf3e34d50c5741681` against base
`454b102b033310517dd4623b7eaa3a42b271f32d` (shipped 4.7.1),
`docs/specs/project-ontos-v5-0-0-spec.md`, `manifests/project-ontos-v5-0-0.yaml`,
and `docs/releases/v5.0.0.md`.

All findings below were reproduced by execution, not inferred from reading alone.
Reproductions ran in a Python 3.12 virtualenv outside the checkout
(`pip install -e '.[dev,mcp]'`); scratch fixtures were written under `/tmp`. No
product file was modified. The checkout remains on
`lifecycle-evidence/project-ontos-v5-0-0` at `1a68ded` with only the three
pre-existing untracked prompt/raw artifacts.

Note on environment: the repository ships no virtualenv, and the machine default
`python3` (3.14) lacks both `pytest` and the runtime dependencies. A naive
`pytest | tail` pipeline reports success from the pipe, not from the suite. Any
verifier must capture the real pytest exit status.

## Evidence — gates that genuinely pass

Every product gate and runnable acceptance check in the manifest passes. These
were re-run independently rather than taken from the tracker.

| Check | Command | Result |
|---|---|---|
| Complete suite (G-test-1) | `pytest -q` | **1536 passed** |
| Focused contract/safety suite (C smoke) | `pytest -q tests/test_cli_contract_v4.py tests/core/test_body_refs.py tests/core/test_link_diagnostics.py tests/core/test_graph.py tests/core/test_rename_transaction.py tests/mcp/test_server_integration.py tests/mcp/test_rename_document.py` | **228 passed** |
| Golden comparison (G-test-2) | `python tests/golden/compare_golden_master.py --fixture all` | exit 0, all PASS |
| Cardinality (G-cardinality-1) | version + envelope schema | `5.0.0` / `4.0` |
| Scope (G-scope-1) | `.ontos/scripts` absent, CI invocation removed | exit 0 |
| Golden metadata identifies 5.0.0 | `tests/golden/baselines/small/map_metadata.json:4` | `"ontos_version": "5.0.0"` |
| Package build | `python -m build` | `ontos-5.0.0-py3-none-any.whl` |
| Non-editable install smoke | wheel into clean venv, `ontos init`, `ontos map --json` | exit 0, schema-4 envelope |

Substantive things verified **correct**, which the findings below should not
obscure:

- **No v4.7.1 safety fix was reverted.** The manifest's `watch_item` holds.
  `ontos/io/yaml.py`, `ontos/core/locking.py`, `ontos/core/context.py`, and
  `ontos/mcp/locking.py` have empty diffs against base, and every v5 caller still
  routes through them. `ontos/core/frontmatter.py` in fact *deleted* its lossy
  60-line `_fallback_yaml_parse` and now delegates to the canonical parser — a
  strengthening. The 13 deleted `tests/test_*.py` files all imported the legacy
  fork via `sys.path` and died with it; each has a surviving package equivalent.
- **Rename safety core is sound.** In both CLI (`ontos/commands/rename.py:171`)
  and MCP (`ontos/mcp/rename_tool.py:316`) the workspace lock is taken *before*
  recovery, the cleanliness check, and plan construction — no TOCTOU window. The
  journal stores exact original bytes via `read_bytes()` + base64
  (`ontos/core/rename_transaction.py:91`), is fsynced before the first mutation,
  and is removed only after a successful commit. **No unscoped git rollback
  survives anywhere**; the old `git checkout -- .` was replaced by the scoped
  journal, which is strictly safer than base.
- **Wikilink alias/heading display text is preserved** during rename:
  `[[old|Alias]]` → `[[new|Alias]]`, `[[old#H]]` → `[[new#H]]`, and an id
  appearing only as display text is correctly left alone
  (`ontos/core/body_refs.py:824-844`, `:479-486`).
- **`ontos/io/yaml.py` is genuinely the sole parser.** No rival YAML
  parser/serializer survives; `patch_frontmatter_fields` preserves BOM, CRLF,
  comments, quoting, and key order across all of LF/CRLF/BOM+LF/BOM+CRLF.
- **Graph traversal is genuinely iterative.** A 5000-node chain and 5000-node
  cycle both complete without `RecursionError`.
- **Exit code 4 is never produced**, and undocumented caller-supplied categories
  are sanitized (`ontos/ui/json_output.py:322-329`).
- **Legacy fork removal is complete** in CI and `.pre-commit-config.yaml`, which
  are rewired to `python -m ontos link-check` / `python -m ontos hook pre-commit`.

The passing suite is therefore real. The findings below are defects the suite
does not cover — in two cases, defects the suite actively enshrines.

## Findings

### BLOCKER 1 — `result.exit_category` contradicts the process exit code

`ontos/ui/json_output.py:464-469` derives `exit_category` from `result_status`,
never from `exit_code`. `incomplete` is a fifth result status with no
corresponding exit code, so it falls through to `findings`. `incomplete` is
triggered by any nonzero `load_warnings` / `load_issues` /
`parse_failed_candidates` (`ontos/ui/json_output.py:69-71`, `:444-448`),
independent of the exit code.

Reproduced on **Ontos's own documentation**, no fixture required:

```
$ ontos link-check --json ; echo $?
{"schema_version":"4.0","command":"link-check","exit_code":0,
 "message":"clean (exit 0)",
 "result":{"status":"incomplete","exit_category":"findings",
           "diagnostics":{"complete":true,
             "counts":{"load_warnings":1,"broken_references":0,"orphans":0}}}}
0
```

`exit_code` is 0 and the message says `clean`, but `exit_category` is `findings`.
The same defect mislabels the **exit 3** warning path: an orphan-only run emits
`exit_code: 3` with `exit_category: "findings"`.

`docs/releases/v5.0.0.md` instructs consumers to branch on `result.exit_category`
"when mapping process exits", and its table binds `findings` to exit 1. A CI
consumer following the published contract concludes that a clean repository has
findings, and that a warning-only run has findings. This is the central normative
promise of the release, and it misfires on the project's own docs.

### BLOCKER 2 — Graph path identity contradicts the spec's case-sensitivity clause

Spec: "path identity respects the filesystem's case sensitivity."
`ontos/core/graph.py:45-55` (`_casefold_path`) does the opposite — it
unconditionally casefolds every path and never probes the filesystem. Its own
docstring states the contradiction outright: *"gives the same lookup semantics on
Linux, macOS, and Windows."*

Confirmed on a genuinely case-sensitive APFS volume: with only `docs/Kernel.md`
on disk, a `depends_on: docs/KERNEL.md` — a file that **does not exist** —
resolves to a valid graph edge with **zero errors**.

The consequence is a false negative in broken-link detection, which is the
product's core function, on the case-sensitive Linux filesystem that CI and most
deployments run. `tests/core/test_graph.py:214`, named
`test_case_only_path_resolves_identically_on_every_filesystem`, asserts
`errors == []` — enshrining the negation of the spec bullet. Spec and
implementation cannot both stand; one must change deliberately.

### MAJOR 3 — Explicit caller `result_status` is silently overridden

`ontos/ui/json_output.py:441-450`: the `incomplete` heuristic is evaluated
*before* `if selected is not None`, so only an explicit `findings` short-circuits
it. A caller that explicitly declares `result_status="clean"` is silently
rewritten to `incomplete` when any load warning exists. This contradicts the
spec's "complete/**explicit** diagnostic counts".

`tests/test_cli_contract_v4.py:271-282` constructs this exact state (explicit
`result_status: "clean"` + `load_warnings: 1` + `exit_code=0`), asserts the
status becomes `incomplete`, and then stops — it never asserts `exit_category`,
which is the single assertion that would have caught BLOCKER 1. The contract test
locks in the bug instead of proving the contract.

### MAJOR 4 — `migration-report --json` discards its entire domain payload

`ontos/cli.py:1719-1727` populates `data` only when `args.format == "json"`, but
the parser default is `--format md` (`ontos/cli.py:933`). The report is generated
into `message`, `message` is then overwritten with `"Report output to stdout"`,
and human stdout is suppressed in JSON mode.

`$ ontos migration-report --json` → `"data": {}`, with the report irrecoverably
gone. Violates the spec's "retains domain values under `data`".

### MAJOR 5 — The registry is not authoritative for `result.kind`

Spec: "The declarative command registry is authoritative for … result kinds."
`rename` and `retrofit` are declared `ResultKind.OPERATION`
(`ontos/command_registry.py:58-59`) but emit their envelopes directly without
passing `result_kind`, so `ontos/ui/json_output.py:319-321` infers the kind from
payload shape. Because their payloads carry a `summary` mapping, they emit
`diagnostic`:

```
$ ontos rename p1 p1x --json    -> result.kind = "diagnostic"   (registry: operation)
$ ontos rename nope nope2 --json -> result.kind = "operation"   (same command)
```

The kind flips per invocation based on whether `data` happens to contain a
`summary`. Handlers routed through `_emit_handler_result_json` (`ontos/cli.py:77-80`)
do honour the registry, which is why only the self-emitting commands diverge.

### MAJOR 6 — `diagnostics.complete: true` on demonstrably partial scans

`ontos/ui/json_output.py:376-399` defaults `complete` to `True` for any
`data.summary` mapping, and `link-check` never overrides it:

```
$ ontos link-check --frontmatter-only --json  -> complete=true, broken_body=0   (real body findings exist)
$ ontos link-check --no-orphans --json        -> complete=true, orphans=0       (3 real orphans)
```

These flags' own help text warns they are "not recommended for CI gates" —
precisely the consumer that trusts `complete`. Partial counts labelled complete
is the opposite of the spec's "complete/explicit diagnostic counts".

### MAJOR 7 — `ontos rename` reports every body-reference line off by +1

`ontos/commands/rename.py:1217-1220` (`_count_pre_body_lines`) counts the closing
`---` fence line, but `_split_frontmatter` (`ontos/core/frontmatter_edit.py:286`)
already makes the tail of that fence line body line 1. The fence is counted twice,
so `body_base_line` (`ontos/commands/rename.py:783`) is one too high. Every
`BodyEdit.line` and the `{path}:{line}` conflict message
(`ontos/commands/rename.py:493`) is wrong.

A reference on physical line 10 is reported as `line 11`. Universal, independent
of line endings. The rewrite itself is byte-correct (it uses absolute offsets),
so this is a reported-location defect — but "link locations are physical
one-based file lines" is a normative clause.

### MAJOR 8 — Link locations drift in CRLF documents

`ontos/core/link_diagnostics.py:764` re-reads the file with
`read_text(encoding="utf-8")`, which applies universal-newline translation
(`\r\n` → `\n`), while the canonical loader preserves `\r\n` in `doc.content`
(`ontos/io/files.py:374-381`). The equality guards at
`ontos/core/link_diagnostics.py:782-786` therefore always fail for CRLF files,
falling into the fallback at `:790` that omits `stripped_prefix`.

The error equals the number of blank lines after the frontmatter fence — it is
unbounded, not a fixed off-by-one:

| blank lines after fence | LF reported | CRLF reported | true |
|---|---|---|---|
| 1 | 9 | **8** | 9 |
| 3 | 11 | **8** | 11 |

`tests/core/test_link_diagnostics.py:198,216,230` assert physical lines for LF,
leading-blank-line, and no-frontmatter documents. No CRLF case exists.

### MAJOR 9 — `ontos retrofit` is permanently blocked by any BOM'd document

`ontos/commands/retrofit.py:525-532` reattaches `decoded.leading_prefix` (the BOM)
*before* reparsing for verification, so `split_frontmatter_text` sees
`"﻿---"` at line 0, fails the fence check, returns `None`, and every field
"fails semantic round trip". (`patch_frontmatter_fields` gets this right at
`ontos/core/frontmatter_edit.py:127` by reparsing *without* the prefix — the bug
is retrofit's own reparse.)

One BOM'd file aborts the whole workspace run with exit 2
(`unsupported_target_format`), leaving all clean files unmodified. It fails
closed, so there is no corruption — but the feature is unreachable for exactly
the "encoding markers" class the spec calls out.

### MAJOR 10 — A rename crash leaves staging artifacts that block all future renames

`ontos/core/rename_transaction.py:115-158` restores journaled *content*
correctly, but the crashed commit's `docs/.<name>.<hex>.tmp` / `.bak` siblings
(`ontos/core/context.py:1049-1110`) are left behind. `is_workspace_clean`
(`ontos/core/git.py:65-71`) ignores only `.ontos.lock` and
`.ontos/transactions/`, so those untracked files fail the cleanliness gate.

After a hard crash, the next `ontos rename --apply` recovers content correctly
and then immediately refuses: `Error [dirty_git_state]`, exit 2 (MCP:
`E_DIRTY_WORKSPACE`). Renames stay dead until the user manually finds and deletes
dot-prefixed hidden files, which the error message does not mention. The `.bak`
files also leave full copies of user documents in `docs/`.

### MAJOR 11 — The evidence-ref verifier's only test does not test what it claims

`tests/test_lifecycle_evidence_ref.py:14`
(`test_evidence_ref_verifier_checks_hashes_and_orphans`) exercises neither orphan
class implemented at `scripts/verify_lifecycle_evidence_ref.py:67-75`. Deleting
the entire orphan block still leaves the test passing. This is the sole test for
the script gating the release in CI (`.github/workflows/ci.yml:90`), and the
untested case — an evidence artifact added but never indexed — is exactly the
tamper scenario the gate exists to catch.

### Minor

- `ontos/core/rename_transaction.py:41-52` hardcodes mode `0o600` on restore,
  while the normal write path preserves the original mode via `os.fchmod`
  (`ontos/core/context.py:1082-1083`). Every document touched by a rollback or
  crash recovery silently loses group/other read access. Bytes are correct;
  `tests/core/test_rename_transaction.py:12` asserts bytes and stops.
- `ontos/commands/rename.py:341-353`: a **fully rolled-back** rename emits
  `applied_files: 2` and lists the restored files in `applied_paths`, with
  `partial_commit.detected: false`. A consumer keying on `data.applied_paths`
  believes the rename landed when nothing was applied.
- `ontos/cli.py:2120,2130-2140`: nested-command *usage errors* emit the parent
  path (`"command": "mcp"`) instead of the canonical nested path
  (`"mcp install"`) promised by the migration table. Success envelopes are correct.
- `ontos/cli.py:1618,1546`: `ontos export --json` reports `"command": "export claude"`,
  a command the user did not run.
- `ontos/cli.py:1549`: `export claude --json` emits `"output_path": null`; the
  real path exists only inside the human message string.
- `ontos/cli.py:2089-2093`: `hook --json` "counts" are mutually exclusive boolean
  indicators derived from one status string, yet labelled `complete: true`.
- `ontos/core/git.py:65-69`: the internal-path exclusion uses `startswith`, so a
  real untracked `.ontos.lockfile` would not mark the tree dirty. Contrived, but
  this is a fail-closed guard for destructive multi-file edits and should be an
  exact-set match.
- `ontos/core/git.py:19-21`: docstring still asserts that `rename_tool` "runs
  `git checkout -- .` over the whole workspace" — the exact behavior the spec
  forbids. The code is correct; the docstring is false and misleading.
- `ontos/commands/rename.py:213-277` is dead, unreachable, un-journaled, unlocked
  legacy apply code behind the unconditional return at `:167-186`. A footgun if
  the early return is ever touched.
- `pyproject.toml:61` still ships `ontos/_hooks/pre-commit` and `pre-push` in the
  5.0.0 wheel (confirmed present in the built artifact). Both hand off to
  `ontos._scripts.ontos_pre_commit_check`, a module deleted in this release.
  Nothing installs them — `ontos init` writes its own correct shim delegating to
  `ontos hook` — so they are fail-open dead weight, but they contradict the
  "legacy fork removed" cleanliness goal.
- `docs/reference/Ontos_Manual.md:514` still documents
  `python3 .ontos/scripts/ontos_remove_frontmatter.py --yes` as step 1 of
  uninstall. That script is now deleted, so the procedure fails and step 3
  (`rm -rf .ontos/`) removes Ontos while leaving all frontmatter behind. The file
  predates v5 and is outside the manifest's `allowed_paths`, but v5 is what makes
  the reference dangling.
- `ontos maintain --json` leaks a `FutureWarning` to stderr
  (`ontos/commands/maintain.py:540`), contrary to the guide's claim that JSON mode
  suppresses human stderr. stdout remains a single clean envelope.

## Assessment

The engineering underneath this release is strong, and the parts most likely to
destroy user data — the rename lock ordering, the byte-exact journal, the removal
of unscoped `git checkout -- .` — are correct and are a genuine improvement on
4.7.1. No 4.7.1 safety fix was reverted. I want to be clear that the 1536 passing
tests are not hollow.

But this is a release whose entire purpose is a *contract*, and the contract does
not hold. `result.exit_category` — the field the migration guide explicitly tells
consumers to use for exit mapping — disagrees with the actual exit code on Ontos's
own documentation, and again on every warning-only run. `result.kind` flips per
invocation despite a registry the spec calls authoritative. `data` is silently
empty for `migration-report`. `complete: true` is asserted over admittedly partial
scans. "Physical one-based file lines" is off by one everywhere in rename, and
drifts without bound in CRLF documents. Each of these is a promise made in
`docs/releases/v5.0.0.md` or the spec's normative section, and each is falsified
by running the shipped code.

Two of these defects are actively enshrined by the tests meant to prove them:
`tests/test_cli_contract_v4.py:271` builds the exact state that breaks
`exit_category` and declines to assert on it, and
`tests/core/test_graph.py:214` asserts the negation of the spec's
case-sensitivity clause in its very name. A green suite is therefore not evidence
that the contract is met, and D.2/D.5 verifiers should not treat it as such.

The graph case-sensitivity clause additionally needs a *decision*, not just a
patch: the implementation and the spec state opposite things, and the docstring
shows the divergence was deliberate at authoring time. Someone must choose which
one is wrong.

None of this argues for abandoning the release — the defects are localized and
the fixes are mostly small (honour `exit_code` in `_exit_category`; move the
explicit-status check ahead of the `incomplete` heuristic; stop double-counting
the fence line; read bytes rather than `read_text` in `_body_line_offset`). But
they must be fixed and the contract tests must be tightened to actually assert
the envelope invariants before this ships as 5.0.0.

Consistent with `docs/reviews/project-ontos-v5-0-0/final-approval.md`, no merge,
tag, release, or publication is authorized by this review.

## Verdict

Request changes
