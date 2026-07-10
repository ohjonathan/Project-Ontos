---
deliverable_id: project-ontos-audit-rebaseline-remediation
phase: B.1
role: peer
family: glm
evidence_labels_used: [static-inspection]
status: completed
---

# Peer Review — project-ontos-audit-rebaseline-remediation / B.1 / glm

Inspection method: I0 was inspected exclusively via `git show b6f89d7:<path>`
and `git show --stat b6f89d7`. No prior verdicts, results, or receipts were
read. No in-progress Phase C working-tree changes were used as proof. No
worktree was created, no test suite was run, no agents were invoked, and no
implementation files were modified. File-existence attestation:
branch `codex/audit-rebaseline-remediation-lifecycle`, HEAD `43dd7dc`,
spec tracked at `docs/specs/project-ontos-audit-rebaseline-remediation-spec.md`.

## 1. Completeness check

All 13 mandatory sections are present (§1 Overview through §13 Self-Review).
No TBD or placeholder remains (§13 self-review claims this; confirmed by
static-inspection of the full spec). All three open questions in §5 carry
"Resolved" status with concrete recommendations.

CREATE/MODIFY/DELETE targets are specified for every §4 subsection:
§4.1 (registry + validator + control plane), §4.2 (loader + serializer),
§4.3 (safe writer + CLI logging), §4.4 (CLI/MCP/activation/platform),
§4.5 (release pipeline + tests + generated metadata). The
contract/invariant-to-evidence matrix (§11) maps 17 invariants to
implementation and test anchors. The helper-divergence disclosure (§12)
covers four existing helpers with explicit dispositions.

Every test file and script referenced in §6 and §11 was verified to exist at
I0: `tests/test_session_context.py`, `tests/test_cli_contract_v4.py`,
`tests/test_frontmatter_roundtrip_regression.py`, `tests/mcp/test_locking.py`,
`scripts/check_release_artifact.py`, `tests/test_release_artifact.py`,
`tests/test_ci_release_workflows.py`, `tests/mcp/test_read_only_registration.py`.

The exclusion list (§9) preserves two user documents, forbids hand-edited
framework/receipts, and blocks synthesis of fix commits, lease history,
provider receipts, GitHub state, Windows results, and TestPyPI results.

## 2. Diagram-prose cross-reference

| Diagram component | In prose? | Prose component | In diagrams? |
|-------------------|-----------|-----------------|--------------|
| Audit Registry (A) | §4.1 | Validator/control plane contracts | Yes (A→V) |
| Validator / Control Plane (V) | §4.1 | O4 Ledger + O5 Leases | Yes (V→L) |
| O4 Ledger + O5 Leases (L) | §4.1 | Canonical Loader + Serializer | Yes (S→W) |
| Canonical Loader + Serializer (S) | §4.2 | Safe Writer + CLI Logging | Yes (S→W) |
| Safe Writer + CLI Logging (W) | §4.3 | CLI / MCP Contracts | Yes (W→C) |
| CLI / MCP Contracts (C) | §4.4 | Activation + Doctor | Yes (X→C) |
| Activation + Doctor (X) | §4.4 | Cross-platform Locking | Yes (K→W, K→C) |
| Cross-platform Locking (K) | §4.4 | Release Pipeline | Yes (P→T) |
| Release Pipeline (P) | §4.5 | Tests + Lifecycle Evidence | Yes (S/W/C/V→T) |
| Generated Context Map + AGENTS (M) | §4.5 | External: GitHub | Yes (G-.→V) |
| External: GitHub (G) | §3 Dependencies | External: Windows Runner | Yes (R-.→T) |
| External: Windows Runner (R) | §3 Dependencies | External: TestPyPI/PyPI | Yes (Y-.→P) |
| External: TestPyPI/PyPI (Y) | §3 Dependencies | Registry serializer contracts | Yes (A→S) |

All diagram components map to prose and vice versa. External nodes are
dashed (`.->`) and styled with `classDef external`. No mismatches found.

Lifecycle diagram (§10.2): `I0_Frozen → Phase_A_Spec → B1_Design_Review →
B2_CodeFirst_Review → Phase_C_Reconciliation → D1_Implementation_Snapshot →
D2 → D3 → D4/D5 → Loose_Falsification → D6_Pending`. The code-first sequencing
(I0 exists before spec, Phase C reconciles implementation with spec) is
consistent with §1's "code-first integration deliverable" and B.2
incorporation note's "code-first Phase C reconciliation." `D6_Pending` with
"stop boundary; no release claim" matches §2's out-of-scope nonrelease
claims. D4 and D5 retry/fix-back paths are shown. No mismatches.

## 3. Quality assessment

The spec is implementation-ready. Each §4 subsection provides concrete file
paths, I0 line anchors, and an explicit boundary between frozen-I0 evidence
and Phase C requirements. The architectural decisions are sound:

**Registry quarantine (§4.1).** At I0, the validator consumes collections
via `Counter(ids)`, `set(lease.get("programs", []))`, and
`program_by_issue[issue]` before structural type-validation of individual
rows. I confirmed exception paths that produce exit 2 (via `main()`'s
`except Exception` → `return 2`): a finding dict missing `"id"` raises
`KeyError` in the `original` dict comprehension; a program dict missing
`"issue"` raises `KeyError` in `program_by_issue`; a non-mapping lease row
raises `AttributeError` on `lease.get()`. The spec correctly converts this
from finite call-site enumeration to construction-level quarantine before all
downstream consumers, covering `findings`, `programs`, `shared_path_leases`,
`shared_tree_integration`, GitHub snapshot count maps, `external_drift`,
and collection-valued fields inside those records. This is a sound
architectural upgrade.

**Writer/log/lock no-follow (§4.3).** I confirmed three I0 defect
locations: `log.py:115` uses `.resolve()` (follows symlinks before any
no-follow check); `_create_archive_marker` uses `marker_path.write_text()`
(plain write, no no-follow pipeline); `mcp/locking.py:25` and
`context.py:925` both use `lock_path.open("a+")` (plain open, no
`O_NOFOLLOW`, no symlink/reparse check). The spec correctly requires Phase C
to centralize the no-follow opener for both SessionContext and MCP callers
and to reject symlinked `logs_dir` components before `.resolve()` collapses
them. The regression shape (external sentinel inode unchanged) is
well-specified.

**Multi-clause version copy (§4.4).** I confirmed `required_version_incompatibility`
returns `f"Invalid [ontos].required_version {required!r}: {exc}"`, where
`{required!r}` echoes the full requirement and `{exc}` repeats the offending
clause. For a multi-clause malformed range, the clause literal appears in
both the full-requirement echo and the sub-error. The spec's Phase C
requirement — identify the offending clause while emitting its literal/repr
exactly once — is correct and actionable.

**Public compatibility (§4.2/§4.4).** At I0, `ExitCode(IntEnum)` in
`json_output.py` defines CLEAN=0, FINDINGS=1, USAGE=2, WARNINGS=3,
INTERNAL=5, INTERRUPTED=130. Code 4 is absent from the enum (reserved). Schema
version `4.0`. The CLI stub (`stub.py:183-192`) maintains a divergent regex
and error message (`"Invalid --id. Expected ^[A-Za-z0-9]..."`) rather than
calling the canonical `validate_document_id` (which says `"Document id must
start and end with an alphanumeric character..."`). The spec correctly requires
Phase C to route every CLI-supplied ID through the canonical validator.

The spec honestly labels the frozen advisory-lock backend (`b6f89d7:ontos/core/locking.py:13-81`)
as separate from the Phase C no-follow opener, and explicitly states the
backend anchor "is not evidence that the opener already existed."

## 4. UX review

Migration copy requirements (§7) document every public-contract change:
warnings-exit-3 shell automation impact (automation treating non-zero as hard
error must distinguish warnings from findings), string-only ID rules
(quoting date-like, numeric, and null YAML scalars), log-collision
`E_LOG_EXISTS` with title/slug-or-move/remove recovery hint, `required_version`
guidance pointer, and the public exit taxonomy including reserved code 4.

The log collision message at I0 (`"Session log already exists: {path}"`)
is user-visible but lacks the actionable recovery hint the spec requires.
The CLI invalid-ID message at I0 exposes a raw regex pattern to users rather
than plain-language copy. Both are correctly scoped as Phase C fixes.

## 5. Issues found

### Blocking (Critical)
| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| — | None identified | — | static-inspection | — | — |

### Should-fix (Major)
| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| — | None identified | — | static-inspection | — | — |

### Minor
| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| M-1 | Validator anchor `b6f89d7:scripts/validate-audit-remediation-registry.py:18-715` cites a range ending at line 715 but the file is 728 lines. The tail (716–728) contains the `main()` PASS output and `if __name__` guard. The exit-code logic (try/except→return 2, if errors→return 1) falls within 18–715, so the anchor is functionally adequate, but extending to 728 would fully cover `main()`. | spec §4.1 | static-inspection | `git show b6f89d7:scripts/validate-audit-remediation-registry.py \| wc -l` → 728 | Extend anchor end to 728 or note the exclusion explicitly. |
| M-2 | §11 matrix row "Workspace lock open is no-follow for CLI and MCP" uses a generic implementation anchor ("`SessionContext` lock acquisition") rather than the specific I0 defect line `b6f89d7:ontos/core/context.py:916` where `_acquire_lock` uses plain `open("a+")`. Other Phase C-required rows use generic anchors too, but the prose in §4.3/§4.4 provides specific I0 line references that the matrix omits. | spec §11 matrix row 10 | static-inspection | `git show b6f89d7:ontos/core/context.py` line 925: `handle = lock_path.open("a+", ...)` | Consider adding the I0 defect line to the matrix for parity with I0-anchored rows. |

## 6. Positive observations

- **Honest I0-vs-Phase-C boundary.** The spec consistently uses `b6f89d7:`
  prefixed anchors for frozen-I0 evidence and non-prefixed anchors for current
  defects/Phase C targets. Every `b6f89d7:` anchor I independently verified
  is accurate: `ontos/core/locking.py:13-81` (fcntl/msvcrt backend),
  `ontos/mcp/locking.py:21-27` (plain open gap), `ontos/core/context.py:485-501`
  (O_NOFOLLOW directory anchor), `scripts/validate-audit-remediation-registry.py:18-715`
  (pre-upgrade consumer surface). The spec never claims a Phase C requirement
  is already satisfied at I0.

- **Registry cardinality is verified.** The validator checks
  `len(findings) != 100`, original severity totals `{P0:1, P1:27, P2:63}`
  (91 originals), and `EXPECTED_R2_IDS` (9 R2 findings). I confirmed the
  registry YAML has exactly 12 programs for issues #146–#157, with #158 as
  the epic issue, matching the spec's "normalized program issue set must
  equal exactly #146 through #157."

- **Exception-to-exit-code gap correctly diagnosed.** The spec identifies
  that `main()`'s `except Exception → return 2` with `ERROR` print must
  become exit `1`/`FAILED` for every malformed construction. I confirmed
  multiple `KeyError`/`AttributeError`/`TypeError` paths in `validate()` that
  would hit this wrapper.

- **v1.4 closure of prior GLM peer findings is genuine.** The spec claims
  v1.4 closes prior GLM peer P-1/P-2/P-3 by (a) separating advisory-lock
  backend from no-follow opener, (b) labeling I0 validator anchors as
  pre-upgrade consumer surface, and (c) showing Phase C reconciliation in
  the lifecycle diagram. I verified all three: (a) §4.4 distinguishes the
  backend anchor `b6f89d7:ontos/core/locking.py:13-81` from the Phase C
  no-follow opener requirement; (b) §4.1 explicitly states the typed/quarantine
  boundary "is a Phase C upgrade and is not represented as already satisfied
  by I0"; (c) §10.2 lifecycle diagram includes `Phase_C_Reconciliation`
  between `B2_CodeFirst_Review` and `D1_Implementation_Snapshot`.

- **External blockers are honestly stated.** Windows CI (requires real
  runners), TestPyPI/PyPI (requires tag-run), GitHub parity (requires live
  queries), D.6/tag/publish/merge/release, and the 41 open + 7 partial
  findings are all explicitly blocking. No synthetic receipts are permitted
  (§3: "An unavailable provider or external service yields an explicit
  pending/blocking state, not certification").

- **Test strategy is construction-level.** §6 specifies table-driven registry
  validation (omit every required field in turn, remove #146/#147,
  non-mapping roots/rows, wrong/unhashable types, `None` elements,
  malformed GitHub metadata, `main()` exit 1/FAILED), non-vacuous symlinked
  `logs_dir` regression (default-path provenance + post-config plant +
  external sentinel), and multi-clause clause-literal counting. These are
  implementable without follow-up questions.

## Verdict
Approve

The committed spec v1.4 is complete, clear, internally consistent, and
implementation-ready. All I0 anchors I independently verified are accurate.
The I0-versus-Phase-C boundary is honestly and consistently drawn. The
registry quarantine, exact program membership, writer/log/lock no-follow
boundaries, multi-clause version copy, public compatibility, state
semantics, and external/nonrelease blockers are all correctly identified
with accurate I0 defect descriptions and well-scoped Phase C requirements.
No blocking or should-fix findings. Two minor anchor-precision observations
(M-1, M-2) do not affect implementability.

## Notes

- Evidence cap: `static-inspection` only. I0 was inspected via bounded
  `git show b6f89d7:<path>` per the dispatch constraints. No `direct-run`
  evidence was produced (test suite was not executed).
- Prior verdicts, results, and receipts were not read. In-progress Phase C
  working-tree changes were not used as proof.
- The spec's §13 self-review claim "Concrete paths and anchors were read
  from I0 before citation" is consistent with my independent verification of
  the `b6f89d7:` prefixed anchors.
- Short SHAs used: `b6f89d7` (frozen I0), `bf91b42` (base). The spec's §1 full
  SHA pair was not reproduced here per the no-high-entropy-strings constraint.
