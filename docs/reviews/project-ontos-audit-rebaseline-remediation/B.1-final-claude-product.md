---
id: project-ontos-audit-rebaseline-remediation-B.1-final-claude-product
deliverable_id: project-ontos-audit-rebaseline-remediation
phase: B.1
role: product
family: claude
evidence_labels_used: [static-inspection]
status: completed
---

# Product Review — project-ontos-audit-rebaseline-remediation / B.1 / claude

## 1. User-value assessment

The user is the **Ontos operator/adopter**: the person who runs `ontos log`,
`ontos activate`, and `ontos stub`, pins `[ontos].required_version` in a
project, consumes CLI/JSON exit codes from shell automation, reads the
migration guide when upgrading, and runs the MCP server in read-only mode.
Their job is to keep a documentation corpus synchronized with code without
having the tool silently corrupt a file, overwrite a log, escape the
workspace, or lie about what it verified.

The spec's core user-value claim is honesty at the failure boundary: when
something goes wrong, the user should get a message that (a) names the state
they are in and (b) tells them how to recover — and when something is *not*
proven (Windows, TestPyPI, per-issue certification, D.6, release), the
product should say so rather than paint green. Measured against that claim,
the spec is unusually disciplined. It targets the two worst copy surfaces in
the frozen implementation head-on: the raw-regex CLI error
(`git show b6f89d7:ontos/commands/stub.py:187-192` dumps
`"Invalid --id. Expected ^[A-Za-z0-9](?:[A-Za-z0-9_.-]*[A-Za-z0-9])?$"` at the
user) and the bare log-collision message (`b6f89d7:ontos/commands/log.py:291`
says only `Session log already exists: {path}` with no recovery hint). §4.2
routes CLI IDs through the canonical plain-language validator; §4.3 adds an
actionable recovery hint. Both are real UX wins, not cosmetics.

The job is genuinely advanced: the deliverable converts a family of silent or
engineer-facing failure modes into user-actionable ones and keeps every
unproven external claim as an explicit pending/blocking state (§3 dependency
table, §2 out-of-scope, §9 exclusions). That "no synthetic receipt" stance
(§3 close) is the strongest product signal here — an operator can trust that a
PASS means what it says. I did not run the suite or the CLI; all evidence is
`static-inspection` of the committed spec and the frozen-I0 sources it cites.

## 2. Product-surface cross-reference

### 2.1 Spec-declared user-visible surfaces

| ID | Surface type | Spec reference | User action that reaches it |
|----|--------------|----------------|-----------------------------|
| S-1 | copy — invalid/non-string ID errors (`must be a string` / `must not be empty` / pattern message) | §4.2; anchor `ontos/core/schema.py:83-97` | Loads/edits a doc with a bad `id`; runs `ontos stub --id …` |
| S-2 | copy + state — log collision `E_LOG_EXISTS`, no-overwrite + recovery hint | §4.3; `ontos/commands/log.py:283-300` | Runs `ontos log` when a log of that title/slug already exists |
| S-3 | state — unsafe path/symlink write refusal (writer + `.ontos.lock` CLI & MCP) | §4.3 | Runs `ontos log` / commits a session / MCP `workspace_lock` under a symlinked path |
| S-4 | state — archive marker `.ontos/session_archived` (best-effort, non-fatal) | §4.3 | Runs `ontos log`; later `git push` (pre-push hook reads the marker) |
| S-5 | copy + code + state — activation `required_version` mismatch (shell `1`, `E_ACTIVATION_UNUSABLE`, `data.status: not_usable`, `Incompatible…`/`Invalid…` + Migration/Manual pointer) | §4.4; `ontos/core/config.py:223-266` | Pins `required_version`; activates on an incompatible/mispinned CLI |
| S-6 | code — CLI/JSON exit taxonomy (`0/1/2/3/5/130`, `4` reserved), schema `4.0` envelope | §4.4; `ontos/ui/json_output.py:16-49` | Shell automation branches on exit code / parses JSON |
| S-7 | state — read-only MCP (no write tools, no persistent export, no usage logs) | §4.4 | Runs MCP in read-only mode |
| S-8 | copy/state — MCP lifecycle type counts incl. zero-count types | §4.4; `ontos/mcp/tools.py:67-99` | Reads a portfolio/type-count view |
| S-9 | copy — migration guide (`required_version` ranges, exit contract, ID rules, `E_LOG_EXISTS`, warnings-exit-`3` automation warning) | §7 | Reads `Migration_v3_to_v4.md` / `Ontos_Manual.md` before upgrading |
| S-10 | state — one-wheel publishing provenance (external-pending) | §4.5 | Consumes a tagged release / downloaded wheel |

Copy completeness: S-1, S-5, S-6 declare exact leading strings/prefixes/codes;
S-2 and S-5's guidance pointer are declared semantically (not verbatim) — see
U-2/PRD-1 below. No prose-named surface is left un-inventoried.

### 2.2 Spec-vs-implementation cross-reference (code-first, `implementation_ref: b6f89d7`)

The manifest declares `implementation_sequencing.mode: code-first-user-gated`,
so per Template 19 §2.2 I cross-referenced §2.1 against frozen I0. The spec is
explicit that the copy/recovery upgrades are **Phase C gates**, not I0 state;
the deltas below are therefore expected, not spec defects — the check confirms
the spec accurately describes the I0 baseline it promises to change.

| Spec-declared surface (§2.1) | In I0? | I0 observation | Matches spec framing? |
|------------------------------|--------|----------------|-----------------------|
| S-1 canonical ID copy | Partial | `schema.py` message is plain-language ✓; but `stub.py:187-192` keeps a divergent raw-regex string | ✓ §4.2 names this exact anchor as a Phase C gate |
| S-2 collision recovery hint | No | I0 message is `Session log already exists: {path}` — path/no-overwrite only, **no** recovery hint | ✓ §4.3 marks the hint "Phase C direct-run required" |
| S-4 archive marker | Yes | `write_text` on `.ontos/session_archived`; `except OSError: pass` (silent non-fatal) | ✓ no-follow is a Phase C gate; **but** see PRD-1 on visibility |
| S-5 activation pointer | Partial | `Incompatible Ontos version: … Use a compatible Ontos installation.` — no Migration/Manual pointer yet | ✓ §4.4 requires the pointer in Phase C |
| S-6 exit taxonomy `4` reserved | Yes | `ExitCode` enum = `0/1/2/3/5/130`; no `4` | ✓ implemented, matches §4.4 |
| S-8 zero-count types | Yes | `tools.py:68` seeds every canonical type "so zero-count types remain visible" | ✓ implemented, matches §4.4 |
| S-9 migration copy | Partial | I0 doc documents the exit taxonomy + config-key upgrade warning; `required_version`/`E_LOG_EXISTS`/`E_ACTIVATION` copy absent | ✓ §7 requires the additions in Phase C |

No implementation surface was found that §2.1 fails to name. Rendered strings
that already exist in I0 (S-6 exit codes, the `Incompatible Ontos version:`
prefix) match the spec's declared strings.

## 3. UX-friction inventory

| ID | Flow step | Friction | Severity | Evidence |
|----|-----------|----------|----------|----------|
| U-1 | `ontos log` hits an existing log | I0 message names the collision but gives the user no next step; §4.3 fixes this | should-fix (spec already remediates) | static-inspection `b6f89d7:log.py:291` |
| U-2 | Recovery hint "choose a different title/slug" | Actionable — `ontos log` exposes `--title`/`--topic`, so the advice maps to real controls; slug-derivation is not surfaced but the move/remove alternative covers it | minor | static-inspection §4.3 |
| U-3 | `ontos stub --id <bad>` | I0 dumps a regex; §4.2 routes to the plain-language validator message. Clear win. | should-fix (spec already remediates) | static-inspection `b6f89d7:stub.py:187-192` |
| U-4 | Activation on mispinned `required_version` | Multi-clause diagnostic currently echoes the whole requirement *and* the clause; §4.4 requires naming the offending clause while printing its literal once — reduces "which part is wrong?" hunting | should-fix (spec already remediates) | static-inspection `b6f89d7:config.py:239-266` |

## 4. Copy review

| ID | Surface | Current copy (I0) | Issue | Suggested alternative |
|----|---------|-------------------|-------|-----------------------|
| C-1 | CLI invalid `--id` | `Invalid --id. Expected ^[A-Za-z0-9](?:[A-Za-z0-9_.-]*[A-Za-z0-9])?$` | Regex-as-error is engineer-copy; opaque to an adopter | Canonical validator message (spec §4.2 already mandates this) |
| C-2 | Log collision | `Session log already exists: {path}` | State stated, recovery omitted | Add "choose a different title/slug, or move/remove the existing log" (spec §4.3 already mandates) |
| C-3 | Activation incompatible | `…Use a compatible Ontos installation.` | Generic; no pointer to where the version contract is documented | Add Migration/Manual `required_version` pointer (spec §4.4 mandates the pointer but not its exact anchor text — see PRD-2) |

The spec's own declared copy is honest and non-hedging. §7's warnings-exit-`3`
automation warning ("shell automation that previously treated every non-zero
result as a hard error must distinguish warnings from findings/usage/internal")
is exactly the upgrade-time caveat an operator needs and is well-phrased.

## 5. Accessibility surface

| Concern | Evidence | Severity | Remediation category |
|---------|----------|----------|----------------------|
| CLI/JSON only; no GUI/contrast/focus surface | static-inspection | n/a | — |
| Localization hooks | static-inspection §4 | minor | Messages are English literals with no i18n layer; consistent with the existing CLI and out of scope for this deliverable — noted, not a finding. |

No accessibility blocker: the product surface is a terminal CLI + JSON
envelope. JSON structuring (stable `error.code`, `data.status`) is the
machine-accessibility analogue and is well-specified (§4.4).

## 6. Failure-visibility

| Failure path | User-visible signal | Recovery available? | Evidence |
|--------------|--------------------|---------------------|----------|
| Log collision | `E_LOG_EXISTS` (human + JSON), exit `1`, path retained | Yes once §4.3 hint lands; today path-only | static-inspection `b6f89d7:log.py:283-300` |
| Unsafe/symlinked write or lock | Fail-closed refusal; external sentinel unchanged | Yes — user re-points the path | static-inspection §4.3 |
| Version skew | shell `1` + `E_ACTIVATION_UNUSABLE` + `data.status: not_usable` + message | Yes once pointer lands (§4.4) | static-inspection `b6f89d7:config.py:249-266` |
| Invalid `required_version` range | `Invalid [ontos].required_version …` | Yes — clause-identifying diagnostic (§4.4) | static-inspection `b6f89d7:config.py:239-245` |
| **Archive marker write skipped** | **None** — `except OSError: pass`; policy stays "documented non-fatal" | **No connecting signal** — see PRD-1 | static-inspection `b6f89d7:log.py:345-351` |
| External proof pending (Windows/TestPyPI/child/D.6/release) | Explicit pending/blocking state, never certified | N/A — correctly withheld | static-inspection §3, §9 |

## 7. Issues found

### Blocking

None. No user-facing regression, inaccessible surface, failure dead-end, or
misleading error-path copy rises to Blocking, and Product blocking findings
require `direct-run` evidence of a reachable user dead-end (P5) — I ran no
program. The spec already remediates U-1/U-3/U-4/C-1/C-2 as Phase C gates.

### Should-fix

| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| PRD-1 | The best-effort `.ontos/session_archived` marker keeps a "documented non-fatal, silent" failure policy (§4.3 preserves it; `b6f89d7:log.py:349` swallows `OSError`). The marker is consumed by the pre-push check (`.ontos/scripts/ontos_pre_push_check.py:20`). A user whose marker write is skipped (no-follow refusal or `OSError`) while the primary log succeeds gets **no signal now and none required by the spec** — and can later be blocked or warned at `git push` with a "no archived session" message that has no thread back to the earlier silent skip. Happy-path invisibility is fine; a silently-missing marker that surfaces as a downstream push failure is a failure-visibility gap. | spec §4.3; `b6f89d7:ontos/commands/log.py:345-351`; consumer `.ontos/scripts/ontos_pre_push_check.py:20` | static-inspection | `ontos log` where the ancillary marker write refuses/`OSError`s but the primary log lands; later `git push` reads a missing marker | Keep the non-fatal policy, but require the retained recovery evidence to carry a user-visible or `warnings[]` note that the archive marker was skipped, so the state is discoverable rather than silent. |

### Minor

| ID | Description | Location | Evidence | Suggested action |
|----|-------------|----------|----------|------------------|
| PRD-2 | §4.4 requires both activation-failure forms to "point users to the Migration/Manual `required_version` guidance" but does not pin the exact pointer text or section anchor. Risk: Phase C ships a vague "see the manual" with no section, weakening the recovery path. | spec §4.4; §7 | static-inspection | Name the target section/anchor (or a stable phrase) so the pointer is copy-as-contract, matched by the §7 doc-drift gate. |

## 8. Positive observations

- **Honesty at the boundary is the headline win.** Windows, TestPyPI, child
  issue lifecycle, D.6, and release readiness are held as explicit
  external-pending/nonclaim states in §2, §3, §8, §9, §11, and every
  incorporation note. I found no place where the spec overstates proof to the
  user. "No dependency may be converted into a synthetic receipt" (§3) is the
  right operator-trust posture.
- **The two worst copy surfaces are targeted precisely.** Routing CLI IDs
  through the canonical validator (§4.2) kills the raw-regex error; the
  collision recovery hint (§4.3) turns a dead-stop into a next step.
- **Exit-taxonomy discipline protects automation.** `4` reserved, warnings as
  a distinct exit `3`, and the §7 warning that pre-4.6 CLIs reject the new
  config key are exactly the upgrade-time caveats an adopter needs.
- **Zero-count type enumeration** (§4.4, already in I0) means a portfolio view
  never silently hides an empty lifecycle type — the count a user reads is the
  count that exists.

## Verdict
Approve

The spec delivers the operator-facing value it promises — explicit failure
states, actionable recovery copy, and scrupulous non-overstatement of unproven
external work — and its code-first cross-reference against I0 holds. PRD-1
(silent archive-marker failure visibility) and PRD-2 (unpinned guidance
pointer) are should-fix/minor and do not gate spec approval; both are cleanly
addressable in Phase C alongside the already-declared gates. Approval reviews
the spec's user-facing contract only; it does not certify Phase C
implementation, D.5, any child lifecycle, D.6, or a release.

## 10. Notes

- Cross-cutting (surfaced briefly; depth belongs to Peer/Adversarial): PRD-1's
  fix has an obvious technical shape — the `warnings[]` slot already exists in
  the schema-v4 envelope (§4.4), so a "marker skipped" note is a low-cost add
  on the JSON path; the human path can mirror it. Not a Product mandate on the
  mechanism, only on discoverability.
- Evidence discipline: all findings are `static-inspection` of the committed
  spec and frozen-I0 sources via `git show b6f89d7:…`; I ran no suite, created
  no worktree, used no nested agents, and edited no implementation. Per P5 that
  caps my findings at should-fix, which is why PRD-1 is not raised as Blocking
  despite the real downstream push interaction.
- §2.2 was executed (not marked n/a) because the manifest declares
  `implementation_sequencing.mode: code-first-user-gated` with
  `implementation_ref: b6f89d7`.
