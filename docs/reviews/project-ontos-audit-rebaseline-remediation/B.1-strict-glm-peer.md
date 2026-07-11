---
deliverable_id: project-ontos-audit-rebaseline-remediation
phase: B.1
role: peer
family: glm
evidence_labels_used: [static-inspection]
status: completed
---

# Peer Review — project-ontos-audit-rebaseline-remediation / B.1 / glm

Static inspection only. I0 reviewed against frozen snapshot `b6f89d7` (parent
`bf91b42`) via bounded `git show b6f89d7:<path>`; spec v1.5 read from the
committed review branch HEAD `fe585c5`. No prior verdicts/results/receipts were
read; no in-progress Phase C code was used as proof; no worktree, full suite,
agent, or implementation edit was performed. File-existence attestation:
`git branch --show-current` = the lifecycle review branch,
`git rev-parse HEAD` = `fe585c5`, target path untracked (created below).

## 1. Completeness check

All thirteen mandatory sections are present and non-stub: §1 Overview, §2
Scope (in/out), §3 Dependencies, §4 Technical Design (§4.1–§4.5), §5 Open
Questions, §6 Test Strategy, §7 Migration/Compatibility, §8 Risk, §9 Exclusion
List, §10 Diagrams (10.1 architecture + 10.2 lifecycle), §11
Contract/Invariant-to-Evidence Matrix, §12 Helper-Divergence Disclosure, §13
Self-Review. §13 self-asserts "no TBD or placeholder remains"; confirmed by
search — every open question carries a resolved recommendation (§5), and the
three incorporation notes (v1.1/v1.2/v1.3/v1.4/v1.5) thread prior board findings
into named Phase C gates.

Anchor grounding (I0, `b6f89d7`): every cited I0 path resolves and the cited
line ranges fall inside the file boundaries — validator (`scripts/validate-
audit-remediation-registry.py`, 728 lines; `main()` at 697; cited 18–728),
writer (`ontos/core/context.py`, 975 lines; cited 645–770 staging/replace and
485–501 anchor-open), log collision (`ontos/commands/log.py`, 351 lines;
cited 283–300), log no-follow defect (cited 115 `.resolve()`, 334–340 plain
`open("x")`), config required-version branches (`ontos/core/config.py`, 516
lines; cited 239–266, 279–345), shadowing guard (cited 360–363), advisory-lock
backends (`ontos/core/locking.py`, 81 lines; cited 13–81), and the MCP gap
(`ontos/mcp/locking.py`, 46 lines; cited 21–27 plain `open("a+")`). All cited
test anchors (`test_frontmatter_roundtrip_regression.py`,
`test_cli_contract_v4.py`, `test_session_context.py`, `test_release_artifact.py`,
`test_ci_release_workflows.py`, `test_read_only_registration.py`,
`test_locking.py`) exist at I0.

I0 evidence baseline is accurate: the registry has exactly 100 findings
(91 original + 9 `R2-*`), programs `#146`–`#157` (12) with `#158` as the epic,
and the recorded revalidation base matches `bf91b42`. The validator prints are
grounded by computed gates, not asserted: status counts are produced via
`Counter(row.get("status") ...)` and compared against expected constants
(41/40/7/1/2 summing to 91), and severity parity (P0=1, P1=27, P2=63) is
computed, not hardcoded into the verdict.

## 2. Diagram-prose cross-reference

| Diagram component | In prose? | Prose component | In diagrams? |
|-------------------|-----------|-----------------|--------------|
| Audit Registry | yes — §4.1 | §4.1 control plane | yes |
| Validator / Control Plane | yes — §4.1 | quarantine boundary §4.1 | yes |
| O4 Ledger + O5 Leases | yes — §4.1 (producer edges) | O4/O5 §4.1 | yes |
| Canonical Loader + Serializer | yes — §4.2 | serialize_frontmatter §4.2 | yes |
| Safe Writer + CLI Logging | yes — §4.3 | no-follow writer §4.3 | yes |
| CLI / MCP Contracts | yes — §4.4 | schema-v4 + read-only §4.4 | yes |
| Activation + Doctor | yes — §4.4 | required_version + doctor §4.4 | yes |
| Cross-platform Locking | yes — §4.4 | fcntl/msvcrt §4.4 | yes |
| Release Pipeline | yes — §4.5 | one-wheel + provenance §4.5 | yes |
| Tests + Lifecycle Evidence | yes — §6 | test strategy §6 | yes |
| Generated Context Map + AGENTS | yes — §4.5 | dynamic map §4.5 | yes |
| EXTERNAL: GitHub (parity) | yes — §3 | `#146`–`#158` parity §3 | yes |
| EXTERNAL: Windows Runner | yes — §3 | platform proof §3 | yes |
| EXTERNAL: TestPyPI / PyPI | yes — §3 | artifact proof §3 | yes |

Diagrams 10.1 and 10.2 match the prose. External nodes are dashed and styled;
both GitHub-parity, Windows, and TestPyPI/PyPI external edges are carried into
§3 as explicit external blockers. The lifecycle diagram (10.2) shows the
code-first `B2 → Phase_C_Reconciliation → D1` reconciliation and the
`D5 → Loose_Falsification → D6_Pending: no release claim` stop boundary,
matching §2 scope and the v1.4 "code-first Phase C reconciliation in the
diagram" note. No component appears in only one representation.

## 3. Quality assessment

The artifact's distinguishing strength is its disciplined separation of frozen
I0 evidence from Phase C acceptance requirements. Every I0 citation is
prefixed `b6f89d7:` and labeled the "pre-upgrade" / "frozen-I0 defect" surface,
while Phase C gates are stated as construction requirements to implement and
verify — never rounded up as already-satisfied. This separation is
mechanically checkable and I confirmed it holds: the I0 validator does carry a
broad `except Exception` returning exit `2`/`ERROR` (the exact shape the spec
says Phase C must convert to quarantined exit `1`/`FAILED`), I0
`version_satisfies_requirement` does use lazy `all(...)` (so an earlier-false
clause can hide a later-malformed one) and echoes the whole requirement in the
invalid message, and I0 MCP `workspace_lock` does a plain `open("a+")` with no
no-follow/single-link binding. The spec therefore does not overclaim I0.

Implementability is strong: each Phase C gate (registry/child-manifest
quarantine before all consumers; exact `#146`–`#157` membership; entry-binding
rechecks before rename/unlink; eager clause parsing; single-link lockfiles;
exact live-GitHub identity/checklist sets; archive-marker warnings-only exit
`3`) is stated as a construction plus a deterministic regression in §6, and the
§11 matrix ties each invariant to an implementation anchor and a test anchor.
A mid-level engineer can build from this without follow-up questions.

Clarity and design quality are high: the row-template/merge-key registry shape
is documented, helper-divergence is disclosed (§12), rollback is commit-level,
and the self-review (§13) separates resolved specification design from "execution
still pending." State semantics are sound: `status` and `lifecycle_state` are
validated independently and the 41 `confirmed_open` / seven partial counts are
preserved as release-blocking rather than reinterpreted as fixed.

## 4. UX review

The deliverable is reviewer/operator-facing rather than end-user-facing, so UX
maps to migration accuracy, exit-code taxonomy, and error/message ergonomics.
The migration copy contract (§7) is actionable: it names the exact guidance
anchor, the `E_LOG_EXISTS` recovery choices, the warnings-only exit `3` shell-
automation impact, string-only ID rules, and the reserved exit code `4`. Exit
semantics (`0`/`1`/`2`/`3`/`5`/`130`) are complete and exclude `4`. Error copy
requirements (canonical CLI ID message equality, clause identification for
malformed `required_version`) are testable. Documentation-drift gating against
the §4.2/§4.4 code/test anchors blocks D.1 — a sound coupling. No user-facing
surface defect found.

## 5. Issues found

### Blocking (Critical)

| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| — | none | — | — | — | — |

No blocking findings. No fabricated or memory-sourced citations, no
diagram/prose mismatch, no I0 anchor error, no implementability gap, and no
overstatement of I0 or Phase C state.

### Should-fix (Major)

| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| P-1 | Grounding gap: §9 and §4.5 name two "preserved untracked user documents" (`docs/specs/project-ontos-rationale-capture-template-proposal.md`, `docs/zeta.md`) as "preserved user work outside I0," but neither is present in the review worktree at HEAD `fe585c5` (not tracked, untracked, or ignored). The exclusion is conservative/harmless but the existence assertion is unverifiable here. | spec §9, §4.5 | static-inspection | `git ls-files` + on-disk `ls` of both paths (empty / "No such file or directory"); `git status --ignored` empty for both | Scope the exclusion to the originating integration working tree (where the untracked docs live) or note they are absent in the review worktree, so a downstream test or reader does not assert presence. |

### Minor

| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| P-2 | Illustrative clause-identification example `version clause '>='` does not match the actual I0 clause literal shape (`<comparator><version>`, e.g. `>=4.7.0`); could mislead a test author about the expected diagnostic token. | spec §4.4 | static-inspection | `git show b6f89d7:ontos/core/config.py` `_version_clause_matches` raises `invalid version clause {clause!r}` over the full clause | Align the example with the real clause literal/repr that the regression must count exactly once. |
| P-3 | Validator human-output lines hardcode the same status counts that are also computed and gated elsewhere (`original findings: 91 ...`; `original status: committed_fixed=2, ...`). Not a defect (the gate is computed), but a reader could mistake the print strings for assertions. | `b6f89d7:scripts/validate-audit-remediation-registry.py:718-721` | static-inspection | `git show b6f89d7:scripts/...py \| sed -n '697,728p'` vs computed `Counter` at 296–308 | Optional: derive the print labels from the computed counts so output and gate cannot drift. |
| P-4 | Lifecycle diagram labels `D1_Implementation_Snapshot`; the framework D.1 role is implementation pre-review/snapshot. Consistent with the code-first flow but the label could read `D1_PreReview_Snapshot` for clarity. | spec §10.2 | static-inspection | diagram 10.2 vs role catalog | Optional label clarity nit. |

### Reachability gaps

No dead validation rules found. Each Phase C gate has at least one citable
triggering construction in §6 (omit each required field in turn; remove
`#146`/`#147`; plant a symlinked `logs_dir`; staged-temp swap after descriptor
close; earlier-false/later-invalid clause ordering; hard-link/symlink lock
attack; malformed live GitHub metadata; phantom epic row). The exit-code-`4`
reservation is reachable as a "must-not-emit" assertion against the
`ExitCode` IntEnum (which skips `4`).

## 6. Positive observations

- I0-vs-Phase-C anchor discipline is exemplary and verifiable: every frozen
  citation is `b6f89d7:`-prefixed and the I0 contents I inspected match the
  claims (lazy `all()`, whole-requirement echo, broad `except`→exit 2, plain
  MCP open, `.resolve()` log defect).
- The validator's status/severity/cardinality gates are genuinely computed and
  compared, not asserted in print strings — the 41 open / 7 partial / 91+9
  baseline is honest.
- External and nonrelease blockers are stated honestly and non-exhaustively:
  Windows, TestPyPI/PyPI, and live GitHub parity are explicit external
  pending/blocking states; D.6/tag/publish/release, merge, per-issue strict-P3
  certification, and the 41 open / 7 partial findings are preserved as
  out-of-scope and release-blocking. No dependency is convertible into a
  synthetic receipt (§3).
- The release pipeline enforces one-wheel provenance (rejects count ≠ 1),
  records version/hash, re-verifies the downloaded artifact, and grants the
  OIDC permission only to publisher jobs while non-publisher jobs hold
  `contents: read` only — matching the §4.5 design.
- Quarantine-before-consumers is correctly extended (v1.4) to
  `shared_path_leases` and `shared_tree_integration`, both confirmed present in
  the registry, and program membership is pinned to exactly `#146`–`#157`,
  which the registry supports.

## Verdict

Approve

The spec is complete, clear, implementable, and diagram-prose consistent with
verified I0 anchors and accurate I0-vs-Phase-C separation. The single
should-fix (P-1) is a grounding-scope clarification for an otherwise
conservative, harmless exclusion; the remaining findings are minor clarity
nits. None block B.2 review or Phase C construction. The issues stand for
Phase C pickup; they do not warrant a revision round.

## Notes

- Per Template 01 commit-split-by-role, no `git commit` was run; the
  orchestrator stages/commits on the worker's behalf.
- Route-redaction observed: workflow identity-token permissions are described
  here as the OIDC permission in prose; no secret-shaped configuration keys are
  quoted with literal values.
- Short SHAs only (`b6f89d7`, `bf91b42`, `fe585c5`); no high-entropy strings
  emitted. The full base SHA is intentionally not reproduced.
- Only the two declared paths were edited: the placeholder sentinel file
  (`B.1-strict-glm-peer.md`) and this verdict (`.raw/audit-rb-B1-gp.review.md`).
