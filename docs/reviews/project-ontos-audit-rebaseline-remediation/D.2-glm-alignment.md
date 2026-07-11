---
id: audit-rb-D2-glm-alignment-r2
deliverable_id: project-ontos-audit-rebaseline-remediation
phase: D.2
role: alignment
family: glm
evidence_labels_used:
  - direct-run
  - static-inspection
  - orchestrator-preflight
reference_documents_consulted:
  - docs/specs/project-ontos-audit-rebaseline-remediation-spec.md
  - .llm-dev/framework/templates/01-worker-session-contract.md
  - .llm-dev/framework/templates/02-phase-dispatch-handoff.md
  - .llm-dev/framework/templates/04-review-board-alignment.md
  - docs/reviews/project-ontos-audit-rebaseline-remediation/D.2-dispatch-intent.yaml
status: completed
---

# Alignment Review — project-ontos-audit-rebaseline-remediation / D.2 / glm

## 1. Architecture compliance

The spec v1.5 at `docs/specs/project-ontos-audit-rebaseline-remediation-spec.md`
defines a layered architecture: Audit Registry → Validator/Control Plane → O4
Ledger/O5 Leases → CLI/MCP Contracts → Tests/Generated Metadata. The Phase C
implementation at I1 (`05b090d`) implements each layer with the import
boundaries the spec prescribes.

**Registry validator** (`scripts/validate-audit-remediation-registry.py`):
The quarantine-before-consumers boundary is implemented structurally. The
`validate()` function (line 867) calls `normalize_shared_path_leases()`,
`normalize_shared_tree_integration()`, `normalize_snapshot_counts()`, and
`normalize_external_drift()` before any aggregation, release-counting,
collision-check, or parity logic. Finding rows (line 920–1039) and program rows
(line 1048+) are validated field-by-field with `.get()` accessors; structurally
invalid rows set `row_invalid = True` and `continue` past all downstream
consumers, preventing `KeyError`/`TypeError` in counters or lookups. Child
manifests are processed through `normalize_child_manifest()` (line 641) with
quarantine before scope/parity lookups. GitHub metadata is validated through
`normalize_live_issue_payload()` (line 515) before issue-number/identity
comparison. `REQUIRED_PROGRAM_ISSUES = set(range(146, 158))` (line 73) enforces
the exact `#146`–`#157` membership. `main()` (line 1881) returns exit `1` with
`FAILED` for validation errors; the exit-2 `ERROR` path (line 1893) is a
defense-in-depth catch for truly unexpected runtime failures, not the path for
malformed collection rows. (direct-run: `python3 scripts/validate-audit-remediation-registry.py`
→ `audit-registry: PASS`, 91 originals, 41 confirmed_open, 7 partial, 9 R2 findings;
static-inspection: lines 867–1039)

**Serializer** (`ontos/core/schema.py`): `validate_document_id` (line 83–97)
raises `ValueError` beginning `Document id must be a string` for non-strings,
`Document id must not be empty` for empty/whitespace, and the plain-language
pattern message for mismatches. `DOCUMENT_ID_PATTERN` (line 78) matches
`^[A-Za-z0-9](?:[A-Za-z0-9_.-]*[A-Za-z0-9])?$` exactly as specified.
`serialize_frontmatter(mapping) -> str` preserves field order and round-trips
to a semantically equal mapping (direct-run: YAML parse equality confirmed).
(static-inspection + direct-run: `ontos/core/schema.py:78-97`)

**Safe writer** (`ontos/core/context.py`): `create_text_file_exclusively`
(line 229) uses `O_NOFOLLOW` (line 244), captures the created binding via
`os.fstat`, re-verifies the anchor binding after the write (line 258), and
verifies the visible entry binding after creation (line 259–266). `commit()`
(line 287) calls `_verify_entry_binding()` at 15 distinct call sites (lines
401, 433, 439, 508, 515, 524, 540, 550, 565, 597, 1140, 1147, 1153, 1183, 1252)
covering staged files, temporaries, move/delete sources, backup reservations,
and final replacement — all before mutation. `_verify_entry_absent()` (line 1010)
blocks duplicate-pending destinations. (static-inspection)

**Cross-platform locking** (`ontos/core/locking.py`): `open_lock_file` (line 134)
resolves trusted ancestors, keeps the workspace-root entry lexical, opens via
`O_NOFOLLOW` (line 244 in POSIX path, equivalent in Windows path at line 283+),
and rejects `st_nlink != 1` (lines 168, 189, 267). `verify_lock_file_binding`
(line 163) rechecks both the open handle and the visible path including reparse
flag checks. MCP `workspace_lock` (`ontos/mcp/locking.py:28`) uses
`open_lock_file` + `verify_lock_file_binding` from `ontos.core.locking`,
closing the frozen-I0 plain-open gap at `b6f89d7:ontos/mcp/locking.py:21-27`.
(static-inspection)

**Log command** (`ontos/commands/log.py`): `logs_dir` is kept lexical (line 116–118,
explicit comment against collapsing through `.resolve()`), routed through
`SessionContext.create_text_file_exclusively` which applies the no-follow writer
pipeline. Collision refusal surfaces `E_LOG_EXISTS` with the recovery hint
"Choose a different --title, or intentionally move/remove the existing log"
(lines 310–314). Archive marker failure returns warnings-only exit `3` with
message beginning `Session log created, but archive marker was not updated:`
(lines 383–385, 342). (static-inspection + direct-run via import verification)

**Config/activation** (`ontos/core/config.py`): `version_satisfies_requirement`
(line 223) evaluates every clause eagerly via list comprehension before reducing
with `all()` (lines 252–254), preventing a false earlier clause from hiding a
malformed later one (direct-run confirmed: `>=5.0.0, !invalid` raises
`ConfigError` naming the clause). `required_version_incompatibility` (line 258)
returns messages beginning `Incompatible Ontos version:` and `Invalid
[ontos].required_version:` respectively, both pointing to `#audit-remediation-
compatpatibility-contracts` (direct-run confirmed). (direct-run)

**JSON output** (`ontos/ui/json_output.py`): `ExitCode` IntEnum (line 29–37)
contains exactly `[0, 1, 2, 3, 5, 130]` — code `4` is absent and reserved
(direct-run: `[int(c) for c in ExitCode]` → `[0, 1, 2, 3, 5, 130]`).
`COMMAND_ENVELOPE_SCHEMA_VERSION = "4.0"` (line 16).
(static-inspection + direct-run)

**MCP read-only** (`ontos/mcp/server.py` + `tools.py`): `build_server`
conditionally registers write tools only when `not read_only` (line 197).
`export_graph` refuses persistent file export when `read_only` (tools.py:397).
Type counts seed from `TYPE_DEFINITIONS` for every canonical type including
zero-count types (tools.py:68–72). Usage logs suppressed in read-only
(server.py:1003). (static-inspection)

No layer violations found. Import boundaries match the spec'sCREATE/MODIFY
matrix in §4.

## 2. Diagram-architecture cross-reference

**§10.1 Architecture diagram**: The Mermaid flowchart shows Audit Registry →
Validator → O4/O5 → (Serializer, Writer, CLI/MCP, Locking, Activation) →
Tests → Generated Map. External entities (GitHub, Windows, TestPyPI) are
dashed. This matches the code layout: registry/validator in `scripts/`,
serializer in `ontos/core/schema.py` + `ontos/io/`, writer in
`ontos/core/context.py`, locking in `ontos/core/locking.py`, CLI/MCP in
`ontos/cli.py` + `ontos/mcp/`, release pipeline in `.github/workflows/`.
(static-inspection)

**§10.2 Lifecycle diagram**: The state machine shows I0_Frozen → Phase A →
B.1 → B.2 → Phase C → D.1 → D.2 → D.3 → D.4/D.5 → Loose Falsification →
D.6 stop boundary. This matches the actual lifecycle progression observed in
`git log --oneline` (B.1 → B.2 → Phase C `05b090d` → D.1 `43583df` → D.2
`9dbe5e1`). The diagram shows failure/retry paths (D.3→D.4 on blocking,
D.5→D.4 on FAIL, Loose Falsification→D.4 on reproducible catch). (static-inspection)

No mismatches between diagrams and architecture.

## 3. Roadmap alignment

The spec §1 states target releases are v4.7.1, v4.8.0, and v4.9.0. The
registry validator's `EXPECTED_DEFAULT_RELEASES` (line 170–183) maps
issues #146–#157 to these exact releases. The release-line ledger at
`docs/trackers/project-ontos-audit-remediation-release-line.md` and the
publishing graph in `.github/workflows/publish.yml` implement one-wheel
provenance (build → verify → TestPyPI → PyPI) as planned. The spec §6 test
strategy's "Required commands at the stable snapshot" list (full pytest,
registry validator, llm-dev verify, lifecycle receipts, base-SHA scope
verification, git diff --check) is consistent with the CI workflow
structure. (static-inspection)

The code-first sequencing mode is visible: the spec is v1.5, Phase C
has already incorporated B.1/B.2 findings by construction, and the
lifecycle diagram shows Phase C reconciliation between B.2 and D.1.
(static-inspection)

## 4. Constraint verification

| Constraint | Source (doc:lines) | Verified? | Evidence |
|---|---|---|---|
| Quarantine-before-consumers for registry roots | spec §4.1:77–83 | Yes | static-inspection: `validate-audit-remediation-registry.py:867–1039` |
| Why and program membership exactly #146–#157 | spec §4.1:81 | Yes | direct-run: `python3 scripts/validate-audit-remediation-registry.py` PASS |
| String-only ID pattern + canonical CLI copy | spec §4.2:91 | Yes | direct-run: `validate_document_id` error messages match |
| serialize_frontmatter preserves order, round-trips | spec §4.2:89 | Yes | direct-run: YAML parse equality confirmed |
| Entry-binding rechecks before rename/unlink/replace | spec §4.3:95 | Yes | static-inspection: `context.py:994-1008` + 15 call sites |
| Log: no-follow logs_dir before .resolve() | spec §4.3:99 | Yes | static-inspection: `log.py:116-118` lexical path comment |
| Log collision E_LOG_EXISTS + recovery hint | spec §4.3:97 | Yes | static-inspection: `log.py:310-314` |
| Archive marker warnings-only exit 3, visible | spec §4.3:101 | Yes | static-inspection: `log.py:341-342,375-387` |
| Both .ontos.lock entry points no-follow + single-link | spec §4.3:103 | Yes | static-inspection: `locking.py:163-197,267-273`; `mcp/locking.py:28-106` |
| advisory-backend selection separate from no-follow opener | spec §4.4:119-122 | Yes | static-inspection: `locking.py` backend (`_open_posix_lock_file`/`_open_windows_lock_file`) distinct from `open_lock_file` opener |
| required_version eager clause parsing | spec §4.4:134 | Yes | direct-run: `>=5.0.0, !invalid` raises before false-clause short-circuit |
| Clause identification in multi-clause diagnostic | spec §4.4:134 | Yes | direct-run: error names `version clause '!invalid'` |
| Exact guidance anchor exists | spec §4.4:134 | Yes | static-inspection: `Migration_v3_to_v4.md:120` heading present |
| Exit code 4 reserved | spec §4.4:132 | Yes | direct-run: `[0,1,2,3,5,130]` confirmed |
| Schema-v4 envelope top-level keys | spec §4.4:132 | Yes | static-inspection: `json_output.py` envelope construction |
| Exhaustive lifecycle type counts (zero-count included) | spec §4.4:130 | Yes | static-inspection: `tools.py:68-72` seeds from TYPE_DEFINITIONS |
| OIDC permission only on publisher jobs | spec §4.5:149 | Yes | static-inspection: `publish.yml` `id-token: write` only on `publish-testpypi` + `publish-pypi` |
| One-wheel provenance chain | spec §4.5:148 | Yes | static-inspection: `publish.yml` builds one wheel, verifies hash, rejects multiple |
| TestPyPI download with --no-deps + manifest compare | spec §4.5:148 | Yes | static-inspection: `publish.yml:260-287` |
| Context map derived, not frozen | spec §4.5:153 | Yes | static-inspection: AGENTS.md records 207, spec says "not frozen to 175, 177" |
| Registry 91 originals + 9 R2 findings, 41 open, 7 partial | spec §1:22 | Yes | direct-run: validator output confirms exact counts |
| Exclusion list: user docs not touched | spec §9:247-249 | Yes | static-inspection: diff stat base→I1 contains neither file |
| No per-issue/D.6/merge/tag/release nonclaim | spec §2:50-51, §9:253-255 | Yes | static-inspection: spec explicitly states these are out of scope; no code claims release readiness |
| Windows/TestPyPI external blockers maintained | spec §3:62-63, §5:161-162 | Yes | static-inspection: spec marks both as "external blocker"; CI has real Windows jobs (`ci.yml:139-141`) |

## 5. Backward compatibility

The implementation intentionally changes public CLI/MCP/json contracts per
spec §7:

- **YAML serialization**: semantic round-trip is guaranteed; existing valid
  mappings remain compatible. The `serialize_frontmatter` signature is
  `(fm: Dict[str, Any]) -> str` — unchanged. (direct-run)
- **ID validation**: non-string/empty/pattern-invalid IDs now raise
  `ValueError` with canonical messages. This is a deliberate breaking change
  documented in the migration copy. (direct-run)
- **Log collisions**: now fail with `E_LOG_EXISTS` instead of overwriting.
  Documented in `Migration_v3_to_v4.md:162` and `Ontos_Manual.md:152`.
  (static-inspection)
- **Exit taxonomy**: code `4` is reserved and absent from the `ExitCode` enum.
  Shell automation must distinguish exit `3` (warnings) from `1` (findings).
  Documented in `Migration_v3_to_v4.md:173-177` and `Ontos_Manual.md:162-177`.
  (static-inspection + direct-run)
- **MCP read-only**: omits write tools, refuses graph export, suppresses usage
  logs. Existing writable MCP behavior unchanged when `read_only=False`.
  (static-inspection)
- **required_version**: activation now reports incompatibility with exact
  guidance pointer. Pre-adoption runtimes may reject the key — documented in
  migration copy. (static-inspection)

No undocumented breaking changes found. The migration documentation
(`docs/reference/Migration_v3_to_v4.md` and `docs/reference/Ontos_Manual.md`)
covers `required_version`, `E_LOG_EXISTS`, archive-marker warnings exit `3`,
string-only IDs, schema `4.0`, reserved exit `4`, and the public exit
taxonomy. (static-inspection)

## 6. Consistency check

- No conflict between the spec's frozen SHA pair (base `bf91b42`, I0
  `b6f89d7`) and the validator's `REVALIDATION_COMMIT` / `INTEGRATION_COMMIT`
  constants (lines 31–32). The `CONTROL_PLANE_FIX_COMMIT` (line 33) correctly
  traces to I1 `05b090d...`. (static-inspection)
- The registry validator's `EXPECTED_RELEASE_COUNTS` (lines 184–206) is
  consistent with the registry YAML structure. (direct-run: validator PASS)
- The publish workflow's `check_release_artifact.py` (CREATE, 144 lines)
  implements the version/hash recording and verification the spec requires.
  (static-inspection)
- The frozen-I0 anchors cited in the spec (e.g., `b6f89d7:ontos/core/context.py:
  645-770`, `b6f89d7:ontos/commands/log.py:283-300`) serve as pre-upgrade
  evidence; Phase C has moved or extended those code regions, which is the
  expected reconciliation outcome. (static-inspection)
- The spec's §11 Contract/Invariant-to-Evidence Matrix rows each map to
  identifiable implementation anchors. The "Phase C direct-run required" rows
  are construction-level requirements, not claims of prior verification — the
  spec is explicit about this distinction in each incorporation note.

## 7. Deviation report

| Divergence | Authority cited? | Authority source | Severity |
|---|---|---|---|
| None found | N/A | N/A | N/A |

No deviations from the approved spec were found. Every constraint re-derived
from spec v1.5 has a matching implementation anchor in the Phase C diff at
I1 `05b090d`.

## 8. Issues found

### Blocking

No blocking findings. Every spec constraint carries a direct implementation
anchor, and the bounded focused checks (registry validator PASS, ID validator
messages, version-clause eager parsing, exit-code enum, serializer round-trip)
confirmed the spec's claims by direct-run.

### Should-fix

None.

### Minor

None.

## 9. Notes

**Evidence methodology.** This review re-derived every architecture,
compatibility, release-sequencing, registry/lease, lifecycle, external-proof,
public-copy, and nonclaim constraint from spec v1.5 and traced each to the
actual diff/code at I1 `05b090d` and the current committed evidence
checkpoint (`9dbe5e1`). It did not read B/D verdicts, sibling reviews, results,
or receipts. Bounded focused checks were run: (1) registry validator
(`python3 scripts/validate-audit-remediation-registry.py` → PASS, exact
91/41/7/9 counts), (2) `validate_document_id` error messages (direct-run,
exact prefix strings confirmed), (3) `version_satisfies_requirement` eager
clause parsing (direct-run, multi-clause error before false short-circuit),
(4) `required_version_incompatibility` guidance pointer (direct-run,
`#audit-remediation-compatibility-contracts` present), (5) `ExitCode` enum
(direct-run, code 4 absent), (6) `serialize_frontmatter` round-trip
(direct-run, YAML parse equality confirmed).

**External-proof distinction.** Windows platform proof and TestPyPI artifact
proof are correctly marked as external blockers in the spec (§3:62–63,
§5:161–162). The CI workflow declares real Windows jobs (`ci.yml:139-141`)
but local inspection cannot certify Windows behavior — this is an explicit
nonclaim, not a gap. TestPyPI proof requires a tagged run; workflow inspection
is local evidence only. These are should-fix-as-external-pending items, not
D.2 alignment blockers.

**Nonclaim boundaries.** The 41 `confirmed_open` and 7 partial findings are
preserved as release-blocking per spec §2:49. No per-issue strict-P3
certification, D.6 approval, merge, tag, publication, or release readiness is
claimed (spec §9:253–255). The umbrella review does not certify child issue
lifecycles (spec §2:50). The context map count (207) is derived from the
current clean snapshot, not frozen to an earlier number (spec §4.5:153).

**Route provenance.** This review was authored through the attested
Neuralwatt/OpenCode GLM-5.2 route. The dispatch intent at
`D.2-dispatch-intent.yaml:60-83` declares `family: glm`, `expected_cli:
opencode`, `serving_provider: neuralwatt`, `evidence_trust_tier:
attested-third-party`, and `route_attestation_profile_id:
neuralwatt-opencode-glm-5-2-v1`. OIDC permission scoping for the publishing
pipeline is described as "OIDC permission granted only to publisher jobs"
per the route-redaction constraint; no secret-shaped values are reproduced.
The worktree was preserved; no full suite was run.

## Verdict

Approve

The Phase C implementation at I1 `05b090d` matches spec v1.5 on every
re-derived constraint. Architecture layer boundaries are intact; the
quarantine-before-consumers registry pattern is structurally complete;
version-clause parsing is eager; the no-follow writer and both workspace-lock
entry points implement entry-binding rechecks before and after mutation;
exit code 4 is reserved; OIDC permission is scoped to publisher jobs; the
migration copy documents the correct anchors; and every nonclaim
(41 open/7 partial, external Windows/TestPyPI proof, no release/tag/merge)
is preserved. No blocking or should-fix deviations were found.

## Final report — project-ontos-audit-rebaseline-remediation / D.2 / alignment / glm

- Status: completed
- Artifacts written: `docs/reviews/project-ontos-audit-rebaseline-remediation/.raw/glm-D2-r2.review.md`
- Smoke checks: registry validator = pass (evidence: direct-run); ID validator messages = pass (evidence: direct-run); version-clause eager parsing = pass (evidence: direct-run); exit-code enum = pass (evidence: direct-run); serializer round-trip = pass (evidence: direct-run)
- Cardinality checks: exit codes [0,1,2,3,5,130] code 4 absent = pass (evidence: direct-run); registry 91+9 findings, 41 open, 7 partial = pass (evidence: direct-run)
- Commit: `9dbe5e1` on `codex/audit-rebaseline-remediation-lifecycle`
- Notes: Reviewer did not read sibling reviews, B/D verdicts, or receipts. External Windows/TestPyPI proof correctly remains pending (nonclaim). Worktree preserved. No full suite run.
