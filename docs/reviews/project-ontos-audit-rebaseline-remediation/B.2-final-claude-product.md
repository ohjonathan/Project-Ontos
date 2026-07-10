---
id: project-ontos-audit-rebaseline-remediation-B.2-final-claude-product
deliverable_id: project-ontos-audit-rebaseline-remediation
phase: B.2
role: product
family: claude
evidence_labels_used: [static-inspection]
status: completed
---

# Product Review — project-ontos-audit-rebaseline-remediation / B.2 / claude

Reviewed committed spec v1.5 (`docs/specs/project-ontos-audit-rebaseline-remediation-spec.md`)
on branch `codex/audit-rebaseline-remediation-lifecycle` at HEAD
`d12f85147e9c3ebb7dc1bdcc4976b6126eb4d860`. Frozen I0 `b6f89d7` was read only to
distinguish pre-upgrade behavior from the Phase C gates the spec proposes. No reviewer
verdict and no in-progress Phase C worktree state was consulted as certification. Evidence
is `static-inspection`: this is a spec review, so no live product run backs any finding, and
per P5 no finding is raised at Blocking severity.

## 1. User-value assessment

The user is the Ontos **operator/adopter** — an engineer who runs `ontos` on their own
repository and increasingly wires it into shell automation, CI, and an MCP client. Their
job is to keep documentation trustworthy without the tool silently corrupting files,
lying about outcomes, or escaping the workspace. The spec's problem statement (§1, §7)
is squarely about *that* operator's experience of a large public-contract change: semantic
YAML round-trips, string-only IDs, collision-refusing logs, no-follow writes, exhaustive
MCP type counts, honest activation errors, and a documented JSON/exit taxonomy.

Measured against that job, the spec brings real user value. The dominant operator risks it
targets — silent corruption (§8 P0), symlink/path escape (§8 P1), and a false-green
lifecycle (§8 P1) — are exactly the failures an operator cannot see until damage is done,
so moving them behind fail-closed behavior is high-leverage. Just as important for the
*day-to-day* operator, v1.5 converts three previously invisible or engineer-facing states
into honest, actionable surfaces: an archive-marker failure that I0 swallows silently
becomes a visible warning with exit `3` (§4.3); a raw-regex `--id` rejection becomes the
canonical plain-language message (§4.2); and a malformed `required_version` clause that I0
can hide behind an earlier incompatibility becomes an eagerly-parsed, clause-identified,
non-duplicated error pointing at a stable migration anchor (§4.4). These are the moments an
operator forms an opinion of the tool, and the spec improves each.

The spec is also honestly scoped: it repeatedly refuses to convert unavailable external
proof (Windows, TestPyPI, GitHub, per-issue lifecycle, D.6, release) into certification
(§2, §3, §11, §10.2). For a control-plane deliverable that could easily overclaim, that
restraint is itself user-protective — an adopter reading this will not mistake a branch
review for a shipped release.

## 2. Product-surface cross-reference

### 2.1 Spec-declared user-visible surfaces (always required)

Every surface below is declared in prose with enough copy/state detail for Phase C to
implement against. Nothing named in prose is missing an inventory entry.

| ID | Surface type | Spec reference | User action that reaches it |
|----|--------------|----------------|-----------------------------|
| S-1 | copy/state — log-collision error (human + JSON `E_LOG_EXISTS`, path + no-overwrite + recovery hint) | §4.3, §6 matrix, §11 | `ontos log` when the target log already exists |
| S-2 | copy/state — archive-marker warning (human warn line + JSON `warnings[]`, exit `3`, `result.status: warnings`, created-log path in `data`) | §4.3, §11 | `ontos log` succeeds but the `.ontos/session_archived` write fails |
| S-3 | copy — invalid document-ID error via canonical validator (`E_USER_INPUT`, plain-language, no divergent regex string) | §4.2, §11 | any CLI command supplied a malformed `--id` |
| S-4 | copy/state — activation `required_version` errors (`E_ACTIVATION_UNUSABLE`, `data.status: not_usable`, `Incompatible Ontos version…` / `Invalid [ontos].required_version…`, migration anchor) | §4.4, §7, §11 | `ontos activate` under an incompatible or malformed pin |
| S-5 | state — schema-v4 JSON envelope + public exit taxonomy (`0/1/2/3/5/130`, code `4` reserved, `result` separates domain status / kind / exit category) | §4.4, §7 | any command run with `--json` or read by shell automation |
| S-6 | state — read-only MCP (no write tools, no persistent export, no usage logs, immutable snapshot only) and exhaustive lifecycle type counts incl. zero-count types | §4.4 | an MCP client in read-only mode / a portfolio type-count query |
| S-7 | copy — migration + reference documentation (`Migration_v3_to_v4.md`, `Ontos_Manual.md`) covering ranges, exit/code/message contract, ID rules, `E_LOG_EXISTS` recovery, exit-`3` behavior, exit taxonomy | §7, §11 | an adopter reading docs before adding `required_version` |

Copy completeness at spec time: the collision recovery hint (choose a different title/slug,
or move/remove the existing log intentionally), the fixed activation prefixes, and the
archive-marker warning prefix are all pinned as literal, so Phase C has a concrete copy
contract to match. One copy gap and one anchor-consistency risk are recorded in §4 and §7
below; neither is a missing surface.

### 2.2 Spec-vs-implementation cross-reference (Phase D.2 only)

n/a (Phase B — no implementation to cross-reference). The manifest does not declare
`implementation_sequencing.mode: code-first-user-gated` in this dispatch, and I read frozen
I0 only to characterize pre-upgrade behavior, not to certify the spec's Phase C gates as
already built. §2.2 is skipped per Template 19.

## 3. UX-friction inventory

Golden path (an operator adds `required_version` and runs commands under CI) plus one
representative edge path (an operator whose `logs_dir` sits under a symlinked or full
volume, so the archive marker fails).

| ID | Flow step | Friction | Severity | Evidence |
|----|-----------|----------|----------|----------|
| U-1 | `ontos log` succeeds, archive marker fails, human console | Operator must know the log path to use the log they just created; §4.3 pins the created-log path only into JSON `data`, not explicitly into the human warning line (see PRD-1). | should-fix | static-inspection (§4.3; I0 success line `b6f89d7:ontos/commands/log.py:329`) |
| U-2 | Shell automation upgrades to schema v4 and starts seeing exit `3` | Any pipeline that treated non-zero as hard failure will now fail on a warnings-only success until it is taught to distinguish `3`. The spec surfaces this as required migration copy (§7), which is the right mitigation, but it is intrinsic friction of the change. | should-fix (mitigated by §7 doc requirement) | static-inspection (§7; taxonomy `b6f89d7:ontos/ui/json_output.py:29-40`) |
| U-3 | Operator hits a malformed multi-clause `required_version` | Without eager parsing (I0 behavior) the tool reports "Incompatible" and hides the real typo; v1.5 requires eager parse + clause identification, removing the misdiagnosis. | resolved by spec | static-inspection (§4.4; I0 `all(...)` short-circuit `b6f89d7:ontos/core/config.py:246`) |
| U-4 | Operator adds `required_version` on a repo whose PATH/hook/CI runtimes are older | Older runtimes may reject the key or fail activation; §7 requires the docs to warn adopters to verify runtimes first. Good pre-flight guidance. | resolved by spec | static-inspection (§7) |

## 4. Copy review

| ID | Surface | Current copy | Issue | Suggested alternative |
|----|---------|--------------|-------|-----------------------|
| C-1 | Invalid `--id` (I0 CLI) | `Invalid --id. Expected ^[A-Za-z0-9](?:[A-Za-z0-9_.-]*[A-Za-z0-9])?$` (`b6f89d7:ontos/commands/stub.py:189`) | Pre-upgrade copy dumps a raw regex at the operator — the archetypal engineer-for-engineer error. | **Already addressed by spec §4.2**: route CLI IDs through `validate_document_id`, whose message is plain-language ("Document id must start and end with an alphanumeric character…", `b6f89d7:ontos/core/schema.py:93-95`). Positive; verify the canonical message reaches `E_USER_INPUT` in Phase C. |
| C-2 | Archive-marker warning | `Session log created, but archive marker was not updated:` (§4.3, prefix pinned) | Honest and non-alarming — tells the operator the primary action *succeeded* before naming the secondary failure. Good tone. The continuation should name the marker error and (see PRD-1) the created log path. | Keep the prefix; ensure the continuation is actionable, not a bare exception repr. |
| C-3 | Log collision | I0: `Session log already exists: {path}` (`b6f89d7:ontos/commands/log.py:289`) | Pre-upgrade copy states the fact but gives no next step. | **Addressed by spec §4.3**: retain path/no-overwrite fact and add the recovery hint (different title/slug, or move/remove intentionally). Actionable. |

Overall the spec's copy contract is honest and operator-legible: fixed prefixes, plain
language sourced from one canonical validator, and recovery hints where the user is stuck.

## 5. Accessibility surface

| Concern | Evidence | Severity | Remediation category |
|---------|----------|----------|----------------------|
| Outcome is conveyed by text + numeric exit code + `result.status`, not by color alone | §4.4 envelope keys; taxonomy `b6f89d7:ontos/ui/json_output.py:19-48` | none (positive) | — |
| Warnings vs findings vs failure are distinguishable by an assistive reader without visual cues | §4.3 (`warnings[]`, `result.status: warnings`), §7 | none (positive) | — |
| Error/warning strings are hardcoded English with no localization hook | §4.2/§4.3/§4.4 literal prefixes | minor | localization |

For a CLI/MCP/docs deliverable the accessibility surface is terminal text and machine JSON.
The spec's separation of a machine-readable envelope (exit code + `result` + `warnings[]`)
from human console text is a genuine accessibility strength: assistive tooling and
screen-reader users get structured, non-color-dependent signals. Lack of localization hooks
is consistent with the rest of the codebase and is a minor, non-blocking note.

## 6. Failure-visibility

| Failure path | User-visible signal | Recovery available? | Evidence |
|--------------|---------------------|---------------------|----------|
| Log target already exists | `E_LOG_EXISTS` + path + no-overwrite + recovery hint (human & JSON) | Yes — pick new title/slug or move/remove existing | static-inspection §4.3, §11 |
| Log created, archive marker write fails | JSON: `warnings[]` + `result.status: warnings` + exit `3` + created-log path in `data`. Human: warning line beginning `Session log created, but archive marker was not updated:` | Yes, non-destructive — log is created and kept; marker is best-effort. **Human-mode caveat: created-log path not explicitly pinned to human output (PRD-1).** | static-inspection §4.3 |
| Incompatible `required_version` | `E_ACTIVATION_UNUSABLE`, `data.status: not_usable`, `Incompatible Ontos version…` + migration anchor | Yes — install compatible Ontos; anchor explains contract | static-inspection §4.4 |
| Malformed `required_version` (incl. late clause) | `Invalid [ontos].required_version…`, offending clause named once, migration anchor | Yes — fix the identified clause | static-inspection §4.4 |
| Read-only MCP write attempt | Write tools absent; no persistent export/usage log | Yes — surface is simply not offered | static-inspection §4.4 |

The exit-`3` design is the standout: at I0 a marker failure is swallowed
(`except OSError: pass`, `b6f89d7:ontos/commands/log.py:397-399`) and the command reports
plain success, so the operator never learns the pre-push marker is stale. v1.5 makes that
state visible without turning a successful log into a failure — `result.status` is a
*domain* outcome independent of execution success (`b6f89d7:ontos/ui/json_output.py:19-27`),
so exit `3` reads as "done, with a caveat," never as "the log failed." That is correct and
honest failure-visibility. The one gap is human-mode path visibility (PRD-1).

## 7. Issues found

### Blocking (Critical — user-facing regression, inaccessible surface, failure dead-end, misleading copy in error path)

None. No live user-facing failure path could be reproduced at spec time; per P5 a
spec-review Product finding cannot gate at Blocking on `static-inspection` alone.

### Should-fix (Major — degrades UX without blocking ship)

| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| PRD-1 | For the created-log + failed-marker case, §4.3 pins the created-log path into JSON `data` but only pins a warning *prefix* for human output. A human operator whose marker write fails may see `Session log created, but archive marker was not updated: <err>` without the log's location, unlike the success path which prints `Session log created: {path}`. Recovery (finding the created log) is then harder in human mode than in JSON mode. | spec §4.3; I0 success line `b6f89d7:ontos/commands/log.py:329` | static-inspection | Read §4.3: the "retaining the created log path in `data`" clause scopes path visibility to JSON; human clause pins only the prefix. | Have §4.3 explicitly require human output to also surface the created log path (e.g. keep the `Session log created: {path}` line and append the warning), so both modes are equally recoverable. |

### Minor

| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| PRD-2 | The spec pins the anchor *slug* `#audit-remediation-compatibility-contracts` in both the error copy (§4.4) and the doc requirement (§7), but does not pin the exact heading text that must generate that slug. The committed migration doc has no such heading yet (expected — it is a Phase C gate; `git show HEAD:docs/reference/Migration_v3_to_v4.md` → 0 matches). If Phase C authors a heading whose auto-slug differs, the operator's error pointer would dangle. | spec §4.4, §7 | static-inspection | Grep committed doc for the slug: absent. | Name the exact heading text (or require an explicit named/`<a id=>` anchor) so the pinned pointer and the doc heading cannot drift. |
| PRD-3 | User-facing error/warning strings are hardcoded English with no localization hook. | spec §4.2/§4.3/§4.4 | static-inspection | — | Note only; consistent with the codebase, no action required for this deliverable. |

## 8. Positive observations

- **Honest, non-alarming failure copy.** The archive-marker warning leads with the success
  ("Session log created…") before naming the secondary failure, and exit `3` maps to a
  *domain* warning independent of execution success — the operator is never told a
  successful log "failed" (§4.3; `b6f89d7:ontos/ui/json_output.py:19-27`).
- **One canonical source for ID copy.** §4.2 eliminates the I0 regex-dump `--id` error in
  favor of the plain-language validator message, so every ID surface reads the same, human
  way (`b6f89d7:ontos/core/schema.py:93-95` vs `b6f89d7:ontos/commands/stub.py:189`).
- **Actionable recovery hints.** Log collisions tell the operator exactly what to do next;
  malformed version clauses name the offending clause and point at a stable migration
  anchor (§4.3, §4.4).
- **Accessible signalling.** Outcomes ride on text + numeric exit code + `result.status`,
  never color alone; JSON gives assistive tooling a structured, non-visual channel (§4.4).
- **Scrupulous non-overclaim.** Windows, TestPyPI, per-issue/child lifecycle, D.6, and
  release readiness stay explicitly pending across §2, §3, §11, and the §10.2 `D6_Pending`
  stop boundary — an adopter cannot mistake this branch review for a shipped release.

## Verdict

Approve

The spec is the right thing to ship for the Ontos operator/adopter: it converts the
operator-facing failure states that matter (silent corruption, path escape, invisible
marker failure, regex-dump ID errors, hidden malformed version clauses, exit-code
ambiguity) into visible, honest, recoverable surfaces with pinned copy, and it refuses to
overclaim any external/pending proof. The two should-fix/minor items (PRD-1 human-mode log
path, PRD-2 anchor-heading pinning) improve recoverability and discoverability but do not
block ship, and no Blocking user-facing failure was reproducible at spec time.

## 10. Notes

- Cross-cutting (product decision with technical consequence, surfaced briefly for
  Peer/Alignment depth): PRD-1's remedy is a one-line human-output change but touches the
  §11 matrix row "Log collision refusal and actionable recovery" / "archive marker … visible
  on ancillary failure"; the Phase C regression for that row should assert the created-log
  path is present in **both** human and JSON output, not just `data`.
- Scope-boundary note (belongs to Alignment, recorded per Template 19 boundary tightening):
  I did not perform forbidden-path, cardinality, or spec-surface-enumeration checks; those
  are the mechanical gate's and Alignment's lens, not Product's.
- Evidence discipline: all findings are `static-inspection`; frozen I0 `b6f89d7` was used
  solely to characterize pre-upgrade behavior, and no Phase C worktree state or sibling
  review verdict was treated as certification. Attestation: branch
  `codex/audit-rebaseline-remediation-lifecycle`, HEAD `d12f851`, spec tracked at
  `docs/specs/project-ontos-audit-rebaseline-remediation-spec.md`.
