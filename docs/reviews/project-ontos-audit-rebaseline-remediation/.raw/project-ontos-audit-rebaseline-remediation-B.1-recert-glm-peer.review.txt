---
deliverable_id: project-ontos-audit-rebaseline-remediation
phase: B.1
role: peer
family: glm
evidence_labels_used: [static-inspection]
status: completed
---

# Peer Review — project-ontos-audit-rebaseline-remediation / B.1 / glm

Recertification pass: independent review of spec v1.2 (`docs/specs/project-ontos-audit-rebaseline-remediation-spec.md`) against frozen implementation I0 `b6f89d7` (base `bf91b42`). Inspection was strictly bounded to `git show b6f89d7:<path>` / `git diff bf91b42...b6f89d7`; no worktree was created, the suite was not run, no nested agents were invoked, and no implementation file was modified. The in-progress Phase C in the current worktree was not treated as evidence that I0 satisfied any Phase C requirement. All evidence below is `static-inspection`; under that cap no finding is raised as blocking (per the contract, blocking Peer findings require `direct-run` or `orchestrator-preflight`).

## 1. Completeness check

The spec is structurally complete for a code-first integration deliverable: §§1–13 cover overview, scope, dependencies, technical design (5 subsections), open questions (all resolved), test strategy, migration/compatibility, risk assessment, exclusion list, two diagrams, an invariant→evidence matrix, a helper-divergence disclosure, and a self-review. No section is missing or placeholder; §13 confirms no TBD survives and all open questions carry resolved states (verified: spec §§5, 13). The B.1 (X-M1/X-M2 → Phase C) and B.2 (X-1/X-2, M-1/M-2) incorporation notes are explicit and restate the non-discharge clause for Phase C/D.5/child/release (spec §1, lines 24–26).

Requested scope confirmation (static-inspection):
- **Branch-level integration evidence vs per-issue / release certification is sharply distinguished.** Spec §1 calls this "a branch-level lifecycle review, not a release"; §2 out-of-scope blocks "#146/#147 per-issue certification" and "D.6 final approval, tagging, publishing, merging, or declaring a release ready"; §5 resolves the child-issue question to "No; require each child manifest's own strict receipts"; §9 forbids claiming "per-issue strict-P3 certification, D.6 approval, merge, tag, publication, or release readiness"; §10.2 ends at `D6_Pending --> [*]: stop boundary; no release claim"; §11 marks wheel/Windows rows "external pending." Consistent and unambiguous.
- **Windows / TestPyPI execution is kept external.** Spec §3 lists Windows ("local POSIX emulation is not release evidence") and TestPyPI/PyPI ("only a tag-run proves service behavior") as external blockers; §5 keeps both pending until external proof. Implementation confirms this boundary, not a local substitute: `ci.yml:139-170` runs `windows-base-cli` on `runs-on: windows-latest` (msvcrt backend assertion + lock/CLI smoke); `publish.yml` downloads exact `ontos==<tag>` from TestPyPI with `--no-deps` (anchors 249-320), compares the manifest, and scopes `id-token: write` to the publisher jobs only (publish-testpypi / publish-pypi), not to `verify-wheel`. The spec does not convert these into synthetic receipts.

## 2. Diagram-prose cross-reference

§10.1 architecture diagram — every node maps to a §4 subsection and vice versa; external boundaries are dashed and labeled.

| Diagram component | In prose? | Prose component | In diagrams? |
|-------------------|-----------|-----------------|--------------|
| Audit Registry / Validator / O4+O5 | yes (§4.1) | §4.1 registry & control plane | yes |
| Canonical Loader + Serializer | yes (§4.2) | §4.2 loader/serializer | yes |
| Safe Writer + CLI Logging | yes (§4.3) | §4.3 writer/logging | yes |
| CLI / MCP Contracts | yes (§4.4) | §4.4 CLI/MCP/activation/platform | yes |
| Activation + Doctor | yes (§4.4) | §4.4 required_version + doctor | yes |
| Cross-platform Locking | yes (§4.4) | §4.4 `locking.py` fcntl/msvcrt | yes (K→W only; MCP lock use folded into C — minor) |
| Release Pipeline / Tests / Map+AGENTS | yes (§4.5) | §4.5 pipeline/tests/generated metadata | yes |
| EXTERNAL GitHub / Windows / TestPyPI-PyPI | yes (§3, §5) | §3 dependency rows + §11 external-pending | yes (dashed, parity/platform/artifact proof) |

§10.2 lifecycle state machine: `I0_Frozen → Phase_A_Spec → B1_Design_Review → B2_CodeFirst_Review → D1_Implementation_Snapshot → D2_PostImpl_Review → D3_Verdict → {D4_Fix | D5_Verification}`, with `Loose_Falsification` after D.5 PASS and `D6_Pending → [*]: stop boundary; no release claim`. The `B2_CodeFirst_Review` label reconciles the §1 "code-first" framing (implementation reviewed at B.2), and the terminal stop boundary matches §9's release nonclaim. No diagram/prose mismatch found.

## 3. Quality assessment

Quality and clarity are high. The spec is anchor-dense and the anchors are real: spot-checked `scripts/validate-audit-remediation-registry.py:18-50,209-266,219-223,244-286,632,656-661` (X-M2 malformed-row sites — `ids=[row.get("id") ...]` then `Counter(ids)` can surface `[None]`, and dict comprehensions use bare `row["id"]`); `ontos/commands/log.py:115` (the `.resolve()` collapse site for X-M1) with `334-340` collision refusal (`open("x")`) and the `config.py:360-363` `_validate_path` shadowing guard; `ontos/core/config.py:223-266` returning the exact `Incompatible Ontos version` / `Invalid [ontos].required_version` copy quoted in §4.4; and the duplicate-copy branches `config.py:239-266,279-345` (both emit `invalid ... version clause` diagnostics). All Phase-C-directed test anchors are correctly absent at I0 (e.g. `test_audit_remediation_registry_validator.py`, the symlinked-`logs_dir` log test) and explicitly flagged "Phase C direct-run required" in §11 — a sound, non-overclaiming posture.

Implementability is strong: a mid-level engineer can act on every Phase C gate from the cited "current sites" plus the referenced `SessionContext` no-follow pattern (`context.py:645-770`). The test strategy (§6) is broad and concrete (serializer fixtures, writer edge cases, hermetic post-suite clean-tree, activation/version skew, lock smoke, B.1 regressions for symlinked `logs_dir`/malformed rows/one-copy invalid `required_version`, wheel hash/import). The §11 matrix is mostly precise, pairing each invariant with an implementation anchor and a test/verification anchor plus an evidence label, and honestly separates local direct-run from external-pending (lock backend, wheel provenance).

## 4. UX review

Not a user-facing UI deliverable, but the public API/CLI ergonomics are well-specified: the schema-v4 envelope top-level key set, the exit taxonomy (0 clean, 1 findings, 2 usage, 3 warnings, 5 internal, 130 interrupted), `required_version` activation messages, and `E_LOG_EXISTS`/`E_USER_INPUT`/`parse_error` failure contracts are all stated with exact copy. §7 binds Phase C documentation (`Migration_v3_to_v4.md`, `Ontos_Manual.md`) to the same code/test anchors and blocks D.1 on drift — a good DOC-code alignment mechanism.

## 5. Issues found

### Blocking (Critical)
None. Stated under the static-inspection evidence cap: no direct-run reproduction was available within the bounded inspection, so no finding is promoted to blocking per contract § evidence-discipline.

### Should-fix (Major)
| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| P-1 | Spec §4.4 makes a hard public contract — exit code 4 "is reserved and must not be emitted or reassigned without an explicit schema-version change" — but the §11 "Schema-v4 JSON and exit taxonomy" direct-run anchor (`tests/test_cli_contract_v4.py:78-155`; `tests/commands/test_link_check.py:315-325`) covers only the positive envelope and the emitted codes (0/1/2); there is no negative/characterization assertion that no code path emits 4, and the reserved-4 case is not flagged as a Phase C gate. Rule-reachability gap: a reader cannot cite a triggering case for the "must not be emitted" invariant. (Implementation currently respects it: `_exit_category` has no code-4 branch.) | spec §4.4 (code `4` reserved) + §11 matrix row; impl `ontos/ui/json_output.py:454-470` | static-inspection | `git show b6f89d7:ontos/ui/json_output.py` (no `== 4` branch); `git show b6f89d7:tests/test_cli_contract_v4.py` / `tests/commands/test_link_check.py:315-325` (no reserved-4 negative assertion) | Add a characterization test asserting no v4 code path emits exit code 4 (and that the reserved slot is not reassigned), or mark the reserved-4 negative case "Phase C direct-run required" in the §11 row. |

### Minor
| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| P-2 | The §11 "Registry is sole status authority" row's test/verification anchor is a mode description ("local and external-parity modes") rather than a concrete file:line, less precise than peer rows (which cite test paths). | spec §11 matrix row | static-inspection | `git show b6f89d7:scripts/validate-audit-remediation-registry.py:209` (`def validate(require_external_parity)`) | Cite the validator entrypoint file:line (and/or a registry-validator test anchor once added in Phase C) instead of the prose mode label. |
| P-3 | §10.1 draws only `Cross-platform Locking → Safe Writer + CLI Logging`; the MCP read-only locking surface (§4.4) is folded into the `CLI/MCP Contracts` node rather than shown. Not a contradiction, but the diagram under-represents a platform boundary it otherwise emphasizes. | spec §10.1 + §4.4 | static-inspection | — | Optional: add a `Cross-platform Locking → CLI/MCP Contracts` edge or a note. |

## 6. Positive observations

- Grounded, honest anchoring: every spot-checked direct-run citation resolved to real bytes at `b6f89d7` (validator sites, log `.resolve()`, config copy, workflow Windows/TestPyPI/OIDC, wheel-hash tests in `tests/test_release_artifact.py`). The §11 matrix explicitly marks not-yet-existing anchors as "Phase C direct-run required" rather than over-claiming I0 coverage.
- Clean separation of branch-level integration evidence from per-issue/release certification, repeated across §§1, 2, 5, 9, 11, 10.2 — directly satisfying the recert scope question.
- Windows and TestPyPI/PyPI execution kept genuinely external (real windows runner; exact-tag `--no-deps` TestPyPI download + manifest compare; OIDC scoped to publisher jobs only), with no synthetic-receipt substitution.
- B.1/B.2 incorporation is non-weakening: X-M1/X-M2 and the duplicate-`required_version`-copy dedup become explicit Phase C gates with current defect sites and reachable test anchors named, while the immutable SHA pair, 41-open/7-partial truth, and release nonclaims are preserved.
- One-wheel provenance chain is internally coherent (single wheel build → hash record → TestPyPI exact download → manifest compare → PyPI promotion).

## Verdict

Approve

Reasoning: spec v1.2 is complete, clear, implementable, and diagram/prose-consistent; all load-bearing anchors verified against I0 `b6f89d7` under bounded static inspection; the branch-level-vs-release and external-Windows/TestPyPI distinctions hold. Open items (P-1 should-fix, P-2/P-3 minor) are coverage/precision refinements, not correctness defects or internal contradictions — none block phase advance at the static-inspection evidence cap, and the harder contract enforcement is correctly deferred to Phase C / D.5.

## 8. Notes

- Evidence cap: `static-inspection` only. No direct-run/orchestrator-preflight reproduction performed (bounded inspection per dispatch; suite not run, worktree not created, no nested agents, no implementation edits). Findings above are calibrated to that cap (no blocking promoted).
- Short SHAs only (`b6f89d7`, `bf91b42`); no credentials, token-bearing URLs, or other high-entropy strings emitted.
- Worker writes, orchestrator commits (Template 01 commit-split-by-role); no `git commit` performed by this reviewer.
