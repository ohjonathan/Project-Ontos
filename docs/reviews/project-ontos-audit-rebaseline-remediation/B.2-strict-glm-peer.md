---
deliverable_id: project-ontos-audit-rebaseline-remediation
phase: B.2
role: peer
family: glm
evidence_labels_used: [static-inspection]
status: completed
---

# Peer Review — project-ontos-audit-rebaseline-remediation / B.2 / glm

## 1. Completeness check

Spec v1.5 (`docs/specs/project-ontos-audit-rebaseline-remediation-spec.md`) carries
every mandatory section: Overview, Scope, Dependencies, Technical Design (§§4.1–4.5),
Open Questions, Test Strategy, Migration/Compatibility, Risk, Exclusion List, Diagrams
(§§10.1–10.2), Contract/Invariant-to-Evidence Matrix (§11), Helper-Divergence
Disclosure (§12), and Self-Review (§13). No TBD or placeholder remains; the three open
questions all carry resolved states (static-inspection: spec §5).

All eight v1.5 corrections named in the dispatch charter are present and construction-level:

- Eager clause parsing — §4.4 (spec:134) and §11 row "Required-version clause copy is
  singular, eagerly parsed, and actionable." Verified against the I0 defect
  `b6f89d7:ontos/core/config.py` `version_satisfies_requirement`, which reduces clauses
  via `all(_version_clause_matches(...))` — a short-circuiting generator so an
  earlier-false comparison hides a malformed later clause. The spec correctly frames
  eager parsing as a Phase C gate, not an I0 property (static-inspection).
- Binding checks around every name-based writer mutation — §4.3 (spec:95); §11 row
  "Staged, backup, move, and delete bindings survive no entry swap." The I0 writer
  (`b6f89d7:ontos/core/context.py` anchored `_DirectoryAnchor`/`_stage_text`/
  `_replace_entry`) already has anchor binding plus `O_NOFOLLOW`/`O_EXCL` staging; the
  spec honestly extends the recheck to "immediately before every name-based rename/unlink"
  for move/delete sources and recovery backups (static-inspection).
- Multi-link lock refusal — §4.3 (spec:103); single-link regular-file assertion with
  POSIX `st_nlink` / Windows `nNumberOfLinks` before any backend sentinel. §11 row
  "Workspace lock open is no-follow and single-link for CLI and MCP" (static-inspection).
- Control-plane root/child/enum/owner/path quarantine — §4.1 (spec:77–83); §11 row
  "Every consumed control-plane root/collection is typed and quarantined." Boundary
  names registry root, `findings`, `programs`, `shared_path_leases`,
  `shared_tree_integration`, GitHub snapshot count maps, `external_drift`, collection
  fields, and #146/#147 child-manifest roots (static-inspection).
- Exact GitHub identity/checklists — §4.1 (spec:83); §11 row "Local/external GitHub
  metadata fails closed and preserves identity." The reproduction (issue payload
  `number` mismatch and phantom epic checklist IDs) maps to the §6 test anchors
  (static-inspection).
- Archive warning/exit-3 JSON semantics — §4.3 (spec:101); §11 row "Every log write,
  including archive marker, is no-follow and visible on ancillary failure." The
  human prefix, `warnings[]`, exit `3`, `result.status: warnings`, and retained log
  path in `data` are all pinned. Verified the I0 gap: `b6f89d7:ontos/commands/log.py`
  `_create_archive_marker` currently swallows `OSError` silently with `pass`
  (static-inspection).
- Exact guidance anchor — §4.4 (spec:134) + §7 (spec:224); the anchor
  `docs/reference/Migration_v3_to_v4.md#audit-remediation-compatibility-contracts` is
  pinned consistently across both. The anchor is not present at I0; the spec correctly
  treats its addition as a Phase C documentation requirement (static-inspection:
  `b6f89d7:docs/reference/Migration_v3_to_v4.md` contains no
  `audit-remediation-compatibility-contracts` heading).
- Final B.1 clarity fixes — v1.5 incorporation note (spec:32) and self-review
  (spec:379–388), including archive-marker visibility, exacting the guidance pointer,
  separating I0 collision evidence from the Phase C recovery-copy gate, and the O4/O5
  producer edge (static-inspection).

The C-phase falsification reproduction statements (C-FZ-1 through C-FZ-10) are each
traceable to a v1.5 construction gate; no reproduced gap is left without a matching
spec requirement. Honest-state, external, and nonrelease boundaries (§§2, 3, 9,
§11 "external pending" rows, and the repeated v1.5 nonclaim that these are Phase C
requirements "not claims that final verification has already occurred") are precise and
not over-claimed (static-inspection).

No missing sections. One completeness nit (ResultStatus vocabulary) is recorded under
Issues found.

## 2. Diagram-prose cross-reference

| Diagram component | In prose? | Prose component | In diagrams? |
|-------------------|-----------|-----------------|--------------|
| A "Audit Registry" | yes (§4.1) | §4.1 registry/control plane | yes (A → V) |
| V "Validator / Control Plane" | yes (§4.1) | §4.1 validator parity gate | yes (V → L, T) |
| L "O4 Ledger + O5 Leases" | yes (§4.1 spec:75) | §4.1 O4/O5 renderings | yes (V → L) |
| S "Canonical Loader + Serializer" | yes (§4.2) | §4.2 serializer/ID contract | yes (S → W, T) |
| W "Safe Writer + CLI Logging" | yes (§4.3) | §4.3 safe writer/log boundary | yes (W → C, T) |
| C "CLI / MCP Contracts" | yes (§4.4) | §4.4 command registry/locking/activation | yes (W → C) |
| X "Activation + Doctor" | yes (§4.4) | §4.4 required_version/doctor probes | yes (X → C) |
| K "Cross-platform Locking" | yes (§4.4) | §4.4 advisory-lock backend | yes (K → W, C) |
| P "Release Pipeline" | yes (§4.5) | §4.5 wheel/TestPyPI graph | yes (P → T) |
| T "Tests + Lifecycle Evidence" | yes (§6) | §6 test strategy + clean-tree | yes (S/W/C/V → T → M) |
| M "Generated Context Map + AGENTS" | yes (§4.5 spec:151) | §4.5 context-map generation | yes (T → M) |
| G "EXTERNAL: GitHub" | yes (§3 spec:61, §4.1) | §3/§4.1 external parity | yes (dashed) |
| R "EXTERNAL: Windows Runner" | yes (§3 spec:62, §4.5) | §3/§4.5 Windows CI | yes (dashed) |
| Y "EXTERNAL: TestPyPI / PyPI" | yes (§3 spec:63, §4.5) | §3/§4.5 TestPyPI proof | yes (dashed) |

External boundaries are correctly dashed and styled (`classDef external`). The
lifecycle state machine (§10.2) matches the code-first sequencing prose: B.2 precedes
Phase-C reconciliation, D.1 snapshots the implementation, and D.5 → Loose Falsification
→ D.6-stop matches §2 and §6 (static-inspection).

One diagram-prose mismatch is recorded under Issues found (under-specified edge labels).

## 3. Quality assessment

The design quality is high. The central architectural move — converting every reproduced
Phase-C gap into a construction-level gate (quarantine-before-consumers, eager
parse-before-reduce, bind-before-mutate, single-link-before-sentinel) rather than a
finite call-site enumeration — is the right shape for a security-sensitive filesystem
and control-plane remediation. The spec repeatedly and honestly distinguishes the
frozen-I0 pre-upgrade consumer surface from the Phase-C upgrade that must satisfy each
gate, never rounding a requirement up into a claim of already-green behavior. This
discipline is the strongest signal that v1.5 will not false-green Phase C.

Clarity is strong but not perfect. The spec mixes `b6f89d7:`-prefixed anchors for the
frozen-I0 surface with unprefixed anchors (e.g., `ontos/core/schema.py:315-343`,
`ontos/commands/stub.py:183-192`) that also resolve to I0 code but are not marked as
such. I verified the unprefixed anchors match b6f89d7 content, so the references are
accurate; the inconsistency is a readability nit, not a correctness defect. A few
vocabulary/edge-label gaps (Issues found) would let a Phase-C implementer proceed
without a follow-up question, which matters given the high risk rating.

Implementability is good: each Phase-C gate has a corresponding test-strategy anchor in
§6 and a contract-matrix row in §11, and the table-driven acceptance proof in §4.1
(omit every required field, remove #146/#147, exercise every malformed root/type/enum/
path/owner) is concrete enough to build directly. The migration/warnings-exit-3 shell
impact is surfaced for adopters (§7), which prevents a silent operator regression. OIDC
permission is described in prose as granted only to publisher jobs (§4.5), consistent
with the external release-proof boundary; no secret-shaped configuration is relied upon
here.

## 4. UX review

The public CLI/JSON contract is precise and operator-friendly: exit taxonomy
(0/1/2/3/5/130, 4 reserved), stable error prefixes (`E_ACTIVATION_UNUSABLE`,
`E_USER_INPUT`, `E_LOG_EXISTS`, `E_COMMAND_FAILED`), and actionable recovery copy
(choose a different title/slug or move/remove the existing log). The warnings-only
exit-3 channel for non-destructive ancillary failure (archive marker) is a deliberate
ergonomic improvement over a silent `pass`, and §7 calls out that shell automation must
distinguish warnings from findings/usage/internal errors. Documentation accuracy is
gated to Phase C with a `Documentation drift from the code/test anchors in §§4.2/4.4
blocks D.1` clause, which ties doc quality to lifecycle advance. The exact guidance
anchor keeps migration diagnostics navigable for adopters on older runtimes (static-inspection).

## 5. Issues found

### Blocking (Critical)
None. (Evidence cap is `static-inspection`; no direct-run reproduction available, so no
blocking finding is raised.)

### Should-fix (Major)
None at major severity. The v1.5 corrections are internally consistent, accurately
anchored to the frozen-I0 surface, and each carries a test-strategy trigger and a §11
contract row.

### Minor

| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| P-1 | Anchor prefixing is inconsistent: frozen-I0 anchors use the `b6f89d7:` prefix (e.g., §4.3 `b6f89d7:ontos/core/context.py:645-770`) while other I0-resident anchors are unprefixed (§4.2 `ontos/core/schema.py:315-343`, §4.4 `ontos/commands/stub.py:183-192`). I confirmed the unprefixed anchors resolve to b6f89d7 content, but a Phase-C reader cannot distinguish an I0 anchor from a post-I0 one by syntax alone. | spec §4.2:89, §4.4:91, §4.4:134 vs §4.3:95 | static-inspection | `git show b6f89d7:ontos/core/schema.py` line ~315 is `serialize_frontmatter`; `git show b6f89d7:ontos/commands/stub.py` ~183 is `_validate_stub_params` — both match the cited content and are I0-resident | Prefix all I0 anchors with `b6f89d7:` or add a one-line note that unprefixed anchors are also frozen-I0 |
| P-2 | The distinction between the 12 child programs (#146–#157, the `programs:` collection) and the epic #158 (`github_snapshot.epic_issue` plus an R2 finding row) is not stated explicitly. §4.1 (spec:81) says "the normalized program issue set must equal exactly `#146` through `#157`" while §3 (spec:61) references "Issues #146–#158"; a reader could briefly wonder whether #158 belongs in the quarantined program set. | spec §4.1:77,81; §3:61 | static-inspection | `git show b6f89d7:manifests/project-ontos-audit-remediation-registry.yaml`: `programs:` at line 93 holds #146–#157; `epic_issue: 158` is under `github_snapshot`; #158 appears as an R2 finding, not a program | Add one sentence: "#158 is the epic (`github_snapshot.epic_issue`); the programs collection is exactly #146–#157" |
| P-3 | The `ResultStatus` domain vocabulary is not enumerated, although §4.3 uses `result.status: warnings`. §4.4 describes `result` as separating "domain status, result kind, exit category" without listing the allowed domain-status values. Any Phase-C author preserving exit-3 behavior must know the canonical set. | spec §4.3:101, §4.4:132 | static-inspection | `git show b6f89d7:ontos/ui/json_output.py`: `ResultStatus` = {clean, findings, warnings, incomplete, error}; `WARNINGS=3` matches §4.4's exit taxonomy | State the ResultStatus enum in §4.4 so the `warnings` value is contract-pinned |
| P-4 | Two architecture-diagram edge labels are not grounded in §4 prose: `A -->|"serializer finding contracts"| S` and `A -->|"CLI/MCP finding contracts"| C`. The registry owns finding/program/lease metadata; the serializer (§4.2) and CLI/MCP (§4.4) sections do not describe a "finding contracts" feed from the registry, so the cross-reference is under-specified. | spec §10.1:267-268 vs §§4.1–4.4 | static-inspection | No prose sentence states the registry feeds serializer/CLI-MCP "finding contracts" | Rename the edges (e.g., "finding/program metadata") or add a sentence linking the registry's finding metadata to the serializer and CLI/MCP consumers |
| P-5 | The required-version diagnostic is singular ("identify which clause failed", "that offending clause") but the "each non-empty malformed clause's literal/repr appears exactly once" wording in §4.4 raises whether a requirement with multiple malformed clauses yields one diagnostic or all. | spec §4.4:134; §6:196 | static-inspection | No test-strategy anchor states the multi-malformed-clause cardinality (first vs all) | Add half a sentence: eager parsing reports the offending clause(s); for multiple malformed clauses, state first-only or all |

### Reachability gaps
None. Each v1.5 validation rule has a citable triggering case in §6: eager parsing
("earlier-false/later-invalid" orderings); binding rechecks (staged-temp swap, source
swap, backup-reservation swap); multi-link lock (hard-link/symlink/reparse attacks with
external sentinel); quarantine (omit every required field, remove #146/#147, malformed
roots/types/enums/paths); GitHub identity (identity/title errors, phantom epic rows);
archive marker (no-follow creation + warning/exit-3); guidance anchor (exact Migration
anchor test). No rule is present-but-unreachable (static-inspection).

## 6. Positive observations

- The honest separation of frozen-I0 pre-upgrade surface from Phase-C gates is applied
  uniformly across §§4.1–4.5 and the §11 matrix; nothing is rounded up from the prior
  green suite into a release claim.
- Converting finite-subscript enumeration into quarantine-before-all-consumers is the
  correct structural response to the C-FZ-3/C-FZ-4 reproductions and avoids the
  brittle "finite line-number list" boundary the v1.3/v1.4 notes correctly retired.
- The exit-3 warnings-only channel with retained primary log path in `data` is a
  well-designed non-destructive-failure surface; pairing it with the §7 shell-impact
  migration note pre-empts a real operator regression.
- The §11 contract-to-evidence matrix rows mark every v1.5 gate as "Phase C direct-run
  required" and external items as "external pending," keeping the lifecycle honest.
- The external boundaries (Windows, TestPyPI/PyPI, GitHub live parity) are
  consistently rendered as pending blockers in §3, the §10.1 diagram (dashed), and the
  §11 rows — no synthetic receipt is admitted.

## Verdict
Approve

The spec is complete, internally consistent, accurately anchored to frozen-I0 `b6f89d7`,
and implementable without blocking follow-up. All v1.5 corrections are present as
construction-level gates with matching §6 triggers and §11 rows, and every reproduced
Phase-C gap (C-FZ-1 through C-FZ-10) maps to a gate. The five findings are minor clarity
nits (anchor prefixing, program/epic distinction, ResultStatus vocabulary, two diagram
edge labels, multi-malformed-clause cardinality); none blocks Phase C. The nonrelease,
external-proof, and honest-state boundaries are intact. Findings may be folded into a
specrevision pass without gating phase advance.

## Notes

- Bounded I0 inspection only: all `git show b6f89d7:<path>` reads were line-range scoped.
  No worktree created, no full suite run, no agents invoked, no implementation edited,
  no commit made (per charter).
- Evidence label for every finding is `static-inspection`; blocking findings would have
  required `direct-run`, which the charter does not permit, so none is raised.
- Route-redaction note: publish-workflow identity-token permission is described in prose
  as OIDC permission granted only to publisher jobs; no secret-shaped configuration keys
  or literal values are quoted.
- Short SHAs only; no high-entropy strings emitted.
