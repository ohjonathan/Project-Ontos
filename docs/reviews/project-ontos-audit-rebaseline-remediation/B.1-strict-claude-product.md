---
id: audit-rb-B1-cp
deliverable_id: project-ontos-audit-rebaseline-remediation
phase: B.1
role: product
family: claude
evidence_labels_used: [static-inspection, not-run]
status: completed
---

# Product Review — project-ontos-audit-rebaseline-remediation / B.1 / claude

Fresh Product session, separate from the engineering seats. Lens: is spec
v1.5 the right thing to ship for the Ontos **operator/adopter**, and will
that operator experience the failure and recovery paths the way the spec
intends? Current behavior is checked only against frozen I0
`b6f89d77e7fb684b8bd9a181a24c773d5777397a` via `git show`; no Phase C
worktree, no other verdict, and no live CLI/test execution were consulted.
All I0 source citations below are byte-reads of the committed snapshot
(`static-inspection`); nothing here carries `direct-run` evidence, so per
P5 no finding is graded Blocking.

## 1. User-value assessment

The user is the Ontos operator/adopter who runs `ontos` at the CLI (or
through the read-only MCP server) and who reads Ontos error/warning text
at exactly the moment something has gone wrong: a duplicate session log, an
incompatible runtime pin, a shadowed PATH binary, a symlinked write target,
a malformed `required_version` clause. The job-to-be-done is "recover
safely and keep my documentation tree trustworthy without corrupting a
file or being told a green result that isn't real."

The spec advances that job well. It treats user-visible surfaces —
`E_LOG_EXISTS`, `E_USER_INPUT`, `E_ACTIVATION_UNUSABLE`, the exhaustive
schema-v4 exit taxonomy, the new warnings-only exit `3`, the exhaustive
MCP lifecycle-type counts, and migration copy — as first-class contracts,
not incidental strings. Crucially for this operator, the spec is
relentlessly honest about what it does *not* certify: Windows behavior,
TestPyPI/PyPI availability, any child-issue lifecycle, D.6 approval, and
release readiness are all held as explicit external/pending blockers
(§3, §9, §11, and the lifecycle diagram's `D6_Pending` "stop boundary; no
release claim"). That honesty is itself a product feature: the operator is
never handed a synthetic receipt or a rounded-up "release ready." The
central test of this review — do the failure messages explain state and
recovery *without* overstating those five areas — passes.

Two refinements below (both should-fix) keep the operator from meeting a
soft dead-end on the unsafe-path/lock refusal copy and a potentially
dead in-doc guidance link. Neither undermines the deliverable's value.

## 2. Product-surface cross-reference

### 2.1 Spec-declared user-visible surfaces

| ID | Surface type | Spec reference | User action that reaches it |
|----|--------------|----------------|-----------------------------|
| S-1 | copy — invalid/non-string document ID error (`E_USER_INPUT`) | §4.2 | Operator passes a bad `--id` to a CLI mutation |
| S-2 | copy — log collision refusal `E_LOG_EXISTS` + recovery hint | §4.3 | `ontos log` when the target log already exists |
| S-3 | state+copy — archive-marker failure warning, human + JSON `warnings[]`, exit `3`, `result.status: warnings` | §4.3 | `ontos log` succeeds but `.ontos/session_archived` cannot be written |
| S-4 | copy — activation incompatibility: shell `1`, `E_ACTIVATION_UNUSABLE`, `data.status: not_usable`, prefix `Incompatible Ontos version` / `Invalid [ontos].required_version`, guidance anchor | §4.4 | `ontos activate` with an incompatible/malformed `required_version` |
| S-5 | copy — doctor PATH-skew warning/failure with `-m ontos` fallback hint | §4.4 | `ontos doctor` when PATH binary version ≠ running package |
| S-6 | state — schema-v4 JSON envelope + public exit taxonomy (`0/1/2/3/5/130`, `4` reserved) | §4.4 | Any `--json` invocation; shell automation reads exit code |
| S-7 | copy — required-version malformed-clause diagnostic (offending clause named, literal once) | §4.4 | `ontos activate` with a multi-clause bad range |
| S-8 | state — read-only MCP omits write tools / no persistent export / no usage logs | §4.4 | Operator starts MCP server in read-only mode |
| S-9 | state — exhaustive MCP lifecycle-type counts incl. zero-count types | §4.4 | Operator reads type counts via MCP/CLI |
| S-10 | copy — unsafe-path / workspace-lock refusal message | §4.3 | Operator's write target or `.ontos.lock` is a symlink/hard-link, or lock is contended/stale |
| S-11 | doc-copy — migration/manual guidance (`required_version` ranges, exit-`3` impact, ID quoting, anchor) | §7 | Operator reads `Migration_v3_to_v4.md` / `Ontos_Manual.md` before pinning `required_version` |

Copy completeness: S-1, S-4, S-5, S-6, S-8, S-9 are pinned to exact
prefixes/codes/behavior and are complete. S-2/S-3/S-7/S-11 are pinned as
Phase C construction gates and the spec is explicit that I0 does not yet
satisfy them — an honest separation, not a copy gap. **S-10 is the one
declared user-visible failure path whose human/JSON presentation and
recovery hint are NOT pinned** (finding PRD-1). The S-4 guidance anchor is
pinned as a string but not as a resolvable heading (finding PRD-2).

### 2.2 Spec-vs-implementation cross-reference (I0 current-behavior only)

Per the dispatch, this walk uses frozen I0 as the runnable snapshot for
*current behavior*; the Phase C successor is out of bounds, so "not at I0"
means "declared as a Phase C gate," which the spec states plainly and does
not misrepresent as already-green.

| Spec-declared surface | At I0? | I0 evidence | Honestly framed as Phase C gate where absent? |
|-----------------------|--------|-------------|-----------------------------------------------|
| S-1 invalid-ID copy | Yes | `b6f89d7:ontos/core/schema.py:83-97` — plain-language message | n/a (present) |
| S-2 collision refusal | Partial | `b6f89d7:ontos/commands/log.py:288-296` emits `Session log already exists:` + `E_LOG_EXISTS`, no recovery hint | Yes — recovery hint is Phase C (§4.3) |
| S-3 archive-marker warning | No | `b6f89d7:ontos/commands/log.py:344-351` swallows `OSError` silently (`pass`) | Yes — visibility+exit-`3` is Phase C (§4.3) |
| S-4 activation copy | Prefixes present | `b6f89d7:ontos/core/config.py:250-266` returns `Incompatible Ontos version:` / `Invalid [ontos].required_version` | Anchor pointer is Phase C; see PRD-2 |
| S-5 doctor PATH-skew | Yes | `b6f89d7:ontos/commands/doctor.py:640-687` — every branch carries a `-m ontos` fallback hint | n/a (present, strong) |
| S-6 exit taxonomy | Yes | `b6f89d7:ontos/ui/json_output.py:28-35` — `ExitCode` = `0/1/2/3/5/130`; no `4` | n/a (reserved-`4` honored) |
| S-7 malformed-clause copy | Partial | `b6f89d7:ontos/core/config.py:239-245,262-264` raises clause repr, wrapped by whole-requirement repr | Yes — single-count is Phase C (§4.4) |
| S-8 read-only MCP | Yes | `b6f89d7:ontos/mcp/server.py:197-204` — write tools registered only when `not read_only` | n/a (present) |
| S-9 exhaustive type counts | Yes | `b6f89d7:ontos/mcp/tools.py:63-99` — seeds every canonical type; raises if counts don't sum | n/a (present) |
| S-10 unsafe-path/lock copy | Partial | `b6f89d7:ontos/core/context.py:194-197,441-460` — descriptive `RuntimeError`/`ValueError`, no recovery hint, presentation unspecified | Not addressed as a copy gate — PRD-1 |
| S-11 migration copy | Partial | `b6f89d7:docs/reference/Migration_v3_to_v4.md:113` already documents exit taxonomy + pre-adoption-runtime warning; no `#audit-remediation-compatibility-contracts` heading | Yes — added copy + anchor is Phase C (§7); PRD-2 |

## 3. UX-friction inventory

| ID | Flow step | Friction | Severity | Evidence |
|----|-----------|----------|----------|----------|
| U-1 | Operator symlinks/hard-links a write target or `.ontos.lock`, or hits a stale lock, then retries | Refusal messages state *what* is wrong ("must not be a symlink", "Could not acquire write lock. Another Ontos process may be running.") but not *what to do next* (e.g., remove a stale `.ontos.lock` if no process is running); presentation (clean envelope vs. raw traceback) is unspecified | should-fix | static-inspection: `b6f89d7:ontos/core/context.py:194-197,441-460` |
| U-2 | Incompatible-version operator clicks the guidance pointer in the activation error | Pointer targets an in-doc anchor the spec does not require to resolve to a real heading; a broken jump is a soft recovery dead-end | should-fix | static-inspection: spec §4.4/§7; `b6f89d7:docs/reference/Migration_v3_to_v4.md` (no matching heading) |
| U-3 | Shell-automation operator upgrades and starts seeing exit `3` | New warnings-only code can be misread as a hard failure by scripts treating all non-zero as error | minor (well-mitigated) | static-inspection: spec §7 explicitly calls this out as migration copy |
| U-4 | Operator reads a multi-clause `required_version` error | Offending clause is echoed inside the whole-requirement repr *and* the clause repr at I0 (duplication) | minor | static-inspection: `b6f89d7:ontos/core/config.py:239-245,262-264`; spec §4.4 makes single-count a Phase C gate |

## 4. Copy review

| ID | Surface | Current copy (I0) | Issue | Suggested alternative |
|----|---------|-------------------|-------|-----------------------|
| C-1 | Log collision (S-2) | `Session log already exists: <path>` | States the fact, omits recovery; spec already schedules the fix in Phase C | Phase C copy: append "choose a different title/slug, or move/remove the existing log intentionally" — pin the literal so a copy-equality test can assert it |
| C-2 | Lock contention (S-10) | `Could not acquire write lock. Another Ontos process may be running.` | No recovery for the stale-lock case; "may be running" leaves the operator unsure whether removing `.ontos.lock` is safe | Add a bounded recovery hint (e.g., "If no other Ontos process is running, remove `<workspace>/.ontos.lock` and retry") and pin its presentation |
| C-3 | Unsafe path (S-10) | `<label> must not be a symlink: <path>` / `... must not contain a symlinked directory: <path>` | Clear state; no next-step and no guaranteed clean envelope | Give the writer refusal a stable user-facing code + one-line recovery, parallel to `E_LOG_EXISTS` |
| C-4 | Activation guidance (S-4) | `... Use a compatible Ontos installation.` | Correct at I0; Phase C replaces the tail with the anchor pointer — ensure the anchor it names actually exists | See PRD-2 |
| C-5 | Doctor PATH-skew (S-5) | `PATH ontos ... retry with '<py> -m ontos'` | None — this is a model of good failure copy (state + recovery in one line) | Keep; use as the template for C-2/C-3 |

## 5. Accessibility surface

| Concern | Evidence | Severity | Remediation category |
|---------|----------|----------|----------------------|
| CLI/MCP text-only interface; no color/contrast or focus surface | static-inspection: command handlers emit plain text + JSON | n/a | none — terminal/JSON surface, no graphical a11y obligation |
| Machine-readability for assistive/automation consumers | static-inspection: `b6f89d7:ontos/ui/json_output.py:16-49` structured envelope; `warnings[]` carries the S-3 message | positive | localization/structure — JSON envelope keeps failure text programmatically reachable |

No blocking accessibility concern: the product's "assistive tech" is the
JSON envelope, and the spec keeps every user-visible warning/error inside
it (§4.3/§4.4). Recommend PRD-1's refusal copy also land in the JSON
`error`/`warnings` channel, not only stderr, so automation is not blind to
the refusal reason.

## 6. Failure-visibility

| Failure path | User-visible signal | Recovery available? | Evidence |
|--------------|---------------------|---------------------|----------|
| Duplicate session log (S-2) | `E_LOG_EXISTS` + path, exit `1` | Yes at I0 (no overwrite); explicit recovery hint is Phase C | static-inspection: `b6f89d7:ontos/commands/log.py:288-300` |
| Archive-marker write fails (S-3) | **Silent at I0** (`OSError` → `pass`); Phase C makes it a visible warning + exit `3` | Improves in Phase C; honestly gated | static-inspection: `b6f89d7:ontos/commands/log.py:344-351` |
| Incompatible/malformed `required_version` (S-4) | `E_ACTIVATION_UNUSABLE`, `not_usable`, exact prefixes, shell `1` | Yes — message + (Phase C) guidance anchor | static-inspection: `b6f89d7:ontos/core/config.py:250-266`, `ontos/commands/activate.py:90-95` |
| PATH/package skew (S-5) | Warning/failure with `-m ontos` fallback | Yes — recovery in the same line | static-inspection: `b6f89d7:ontos/commands/doctor.py:640-687` |
| Unsafe-path / lock refusal (S-10) | Descriptive `ValueError`/`RuntimeError`; presentation + recovery unspecified | Partial — state yes, next-step no | static-inspection: `b6f89d7:ontos/core/context.py:194-197,441-460` — **PRD-1** |
| Windows / TestPyPI / release | Explicit external/pending blocker; never a synthetic pass | Correct — no dead-end, no false-green | static-inspection: spec §3, §9, §11 |

## 7. Issues found

### Blocking
None. No user-facing regression, inaccessible surface, misleading error-path
copy, or unrecoverable dead-end was reproduced. (Blocking Product findings
require `direct-run`; this session ran no CLI/tests per the dispatch, so
findings are `static-inspection` → should-fix per P5.)

### Should-fix (Major — degrades UX without blocking ship)
| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| PRD-1 | The unsafe-path / workspace-lock refusal is a declared user-visible failure path (S-10) but the spec pins its behavior only as a security invariant (external sentinel unchanged), not as user copy. At I0 it surfaces as bare `ValueError`/`RuntimeError` with descriptive-but-recovery-less text and an unspecified presentation (clean envelope vs. traceback). The stale-lock case ("Another Ontos process may be running.") gives the operator no safe next step. | spec §4.3 (lock/writer paras), §6, §11 rows; `b6f89d7:ontos/core/context.py:194-197,441-460` | static-inspection | Read §4.3/§6/§11: the writer/lock refusal is specified for *effect* (no-follow, sentinel unchanged) but no human/JSON message + recovery contract is pinned, unlike `E_LOG_EXISTS`/activation | Add a user-facing copy+code+recovery contract for writer/lock refusal (parallel to `E_LOG_EXISTS`), routed through the JSON envelope, and a copy-equality regression |
| PRD-2 | The activation/JSON incompatibility message must point to `docs/reference/Migration_v3_to_v4.md#audit-remediation-compatibility-contracts` (§4.4), and §7 requires adding the copy — but neither pins a check that the anchor resolves to a real heading. An incompatible-version operator following the pointer could hit a non-existent in-doc anchor (soft recovery dead-end). At I0 no such heading exists. | spec §4.4, §7, §11 "Migration warns about warnings exit 3" row; migration doc | static-inspection | Branch `codex/audit-rebaseline-remediation-lifecycle`, HEAD `fe585c5`, `git ls-files docs/reference/Migration_v3_to_v4.md` → tracked; `git show b6f89d7:...` heading scan → no `#audit-remediation-compatibility-contracts` heading | Add a Phase C gate: the pinned heading slug must exist and match the message pointer; test the anchor's existence, not just the message string |

### Minor
| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| PRD-3 | Log-collision recovery copy is described in prose ("choose a different title/slug, or move/remove...") but not pinned as a literal the way `E_LOG_EXISTS` shape is; §11 requires a "title/slug-or-move/remove message regression" but not exact-string equality. | spec §4.3, §11 collision row | static-inspection | Compare §4.2 ID-copy exactness vs. §4.3 collision-hint prose | Pin the recovery sentence as a literal for copy-equality assertion |

## 8. Positive observations

- **Doctor PATH-skew copy (S-5) is a model failure message**: every branch
  pairs the diagnosis with the exact `'<py> -m ontos'` recovery in one line
  (`b6f89d7:ontos/commands/doctor.py:640-687`). Use it as the template for
  PRD-1's refusal copy.
- **Reserved exit `4` is honored, not quietly reused**: the `ExitCode` enum
  omits `4` entirely (`b6f89d7:ontos/ui/json_output.py:28-35`), matching the
  spec's public promise and protecting shell-automation operators.
- **Exhaustive lifecycle-type counts including zero-count types**
  (`b6f89d7:ontos/mcp/tools.py:63-99`) mean the operator never has to guess
  whether a missing type is "zero" or "not reported."
- **The archive-marker improvement is genuinely operator-serving**: I0
  silently swallows the failure (`log.py:344-351`); the spec makes it a
  visible warning with exit `3` *and* flags the shell-automation migration
  consequence in §7 — closing an invisibility gap the right way.
- **Nonclaim discipline is exemplary and is the product's trust anchor**:
  Windows, TestPyPI/PyPI, child-issue lifecycle, D.6, and release readiness
  are held as explicit external/pending blockers across §3/§9/§11 and the
  lifecycle diagram, with an unconditional "no synthetic receipt" rule
  (§3). The operator is never shown a false green.

## Verdict
Approve

Spec v1.5 is the right thing to build for the Ontos operator/adopter. Every
declared user-facing surface except the writer/lock refusal (S-10) carries
complete, honest, actionable copy, and the deliverable's nonclaims on
Windows, TestPyPI, child lifecycle, D.6, and release are neither overstated
nor rounded up — the central test of this review. The two should-fix items
(PRD-1 unsafe-path/lock refusal copy+recovery; PRD-2 resolvable guidance
anchor) refine failure-visibility and recovery but do not block ship, and
both are `static-inspection`-only (no `direct-run`), so neither can gate
under P5. Recommend the Phase C author fold PRD-1/PRD-2 into the existing
copy gates.

## 10. Notes

- Scope discipline: this review stayed on the operator-experience lens.
  Scope-compliance, forbidden-path, and cardinality checks (mechanical
  gate) and spec-surface enumeration (Alignment) were deliberately not
  performed here per the v1.2 boundary tightening in Template 19.
- Cross-cutting (surface briefly; depth belongs to Peer/Alignment): PRD-1
  is a product-copy finding with an obvious technical consequence — the
  writer/lock refusal path already exists at I0 as raw exceptions, so
  giving it a user-facing code+envelope is a small, contained handler
  change, not a redesign.
- Evidence: all I0 citations are `git show b6f89d7:<file>` byte-reads
  (`static-inspection`); Windows, TestPyPI, the full suite, and any Phase C
  worktree were `not-run` by dispatch instruction. No other verdict was
  read.
- File-existence attestation for PRD-2: branch
  `codex/audit-rebaseline-remediation-lifecycle`, HEAD
  `fe585c56e94d9bb28533adb97e870c05d578d3d7`,
  `git ls-files docs/reference/Migration_v3_to_v4.md` → tracked; the
  `#audit-remediation-compatibility-contracts` heading is absent at I0.
