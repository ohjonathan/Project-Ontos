# B.1 alignment recertification — closed, source-backed static packet

Do not call tools, inspect the workspace, start tasks, or narrate actions. This static-inspection packet contains the source material you may cite. The wrapper destination is `docs/reviews/project-ontos-audit-rebaseline-remediation/B.1-recert-gemini-alignment.md`; emit only its complete artifact bytes to stdout. The first output byte must be `-`, beginning `---`; do not wrap the artifact in a Markdown code fence.

You are the Gemini-family Alignment reviewer, executed through AGY, for `project-ontos-audit-rebaseline-remediation`, phase `B.1`, evidence cap `static-inspection`. Independently determine whether spec v1.2 matches its approved audit revalidation and release-line authorities. Deviations are issues. Do not merely restate the packet: cross-reference every constraint, diagram boundary, compatibility change, and §11 row; identify omissions or contradictions.

The alignment question is whether the **spec describes the required truth**, not whether the repository is release-ready. The authorities REQUIRE 41 open and seven partial findings, #146/#147 evidence-pending states, an unproven shared-tree integration blocker, external Windows/TestPyPI proof, and no D.6/release claim. If the spec preserves those pending states, that is alignment, not a deviation or issue. Do not request changes merely because required downstream Phase C, D.5, child, external, or release work remains. Raise an issue only for an actual contradiction or omission between spec v1.2 and an approved authority.

Evidence-cap discipline is mechanical: in your artifact, do not use the exact label `direct-run`, do not say any test or check was run, passed, executed, confirmed, or independently verified, and do not convert source-document evidence labels into claims about your own work. Describe them as `execution evidence declared by the spec` or `external pending`. Your only evidence label is `static-inspection`.

## Fixed output contract

Use this exact frontmatter shape and values:

---
id: project-ontos-audit-rebaseline-remediation-B.1-recert-gemini-alignment
deliverable_id: project-ontos-audit-rebaseline-remediation
phase: B.1
role: alignment
family: gemini
evidence_labels_used: [static-inspection]
reference_documents_consulted:
  - docs/specs/project-ontos-audit-rebaseline-remediation-spec.md
  - docs/reviews/2026-07-10-codex-audit-revalidation.md@b6f89d7
  - docs/trackers/project-ontos-audit-remediation-release-line.md@b6f89d7
  - manifests/project-ontos-audit-remediation-registry.yaml@b6f89d7
status: completed
---

Then emit one H1 and every exact unnumbered Template-04 section: `## 1. Architecture compliance`, `## 2. Diagram-architecture cross-reference`, `## 3. Roadmap alignment`, `## 4. Constraint verification` with the exact four columns `Constraint | Source (doc:lines) | Verified? | Evidence`, `## 5. Backward compatibility`, `## 6. Consistency check`, `## 7. Deviation report` with the exact four columns `Divergence | Authority cited? | Authority source | Severity`, `## 8. Issues found` with Blocking/Should-fix/Minor subsections, exact `## Verdict`, and `## 10. Notes`. In the constraint table, use `Aligned by packet` or `Pending as required`, never execution claims. Under `## Verdict`, put exactly one self-chosen bare token from `Approve`, `Request changes`, `Reject`, or `Concur`; put reasoning only in Notes. Empty issue classes must say `None.`

## Source packet

Packet identity: current spec v1.2 SHA-256 `2c4ffe943e70b766cd26a47df1900bd21fe48d942b04f63bc24302e52b92b3c9`; frozen authorities are read at I0 `b6f89d7`. These identifiers bind the packet but are not proof of execution.

Approved revalidation authority, `docs/reviews/2026-07-10-codex-audit-revalidation.md@b6f89d7:11-49,72-87`:

- Baseline is `bf91b42`; the Fable report is historical for `589d919`, not current status authority. The machine registry is canonical.
- Original register is exactly 91 unique findings at P0/P1/P2 = 1/27/63 and issues #146–#157 assign each once.
- Fable §5 covers only 68/91 and cites nonexistent `D6a-test-gaps-3`; it cannot be called complete.
- Doctor code is fixed at `03c36e6` but evidence pending; no old lifecycle prose certifies strict P3.
- Old O5 is refuted because it omitted shared-path collisions.
- At the I0-preparation checkpoint the original partition is 2 historical fixed, 1 serializer code-fixed/evidence-pending, 40 implemented, 7 partial, and 41 confirmed-open; all remain lifecycle pending. Nine named R2 findings cover hermeticity, temp symlinks, ID types, Windows import, lifecycle types, TestPyPI provenance, activation skew, read-only MCP writes, and control-plane parity.

Approved release-line authority, `docs/trackers/project-ontos-audit-remediation-release-line.md@b6f89d7:13-25,27-61,73-98`:

- Registry is sole machine authority; O4/O5 are validated human renderings.
- Status and lifecycle state are independent; only `strict_p3_review_complete` is certified, while emergency waiver is visibly non-certified.
- #146 remains `code_fixed_evidence_pending`; #147 remains evidence pending; seven partials remain; `shared_tree_integration.status` is `unproven_rebaseline_integration` and release-blocking.
- Scope proof must union committed, staged, unstaged, and untracked paths from immutable `base_sha`; bare `git diff` and branch-name equality are insufficient.
- O5 lease ordering applies prospectively and cannot be retroactively claimed for I0.

Spec v1.2 actual clauses, `docs/specs/project-ontos-audit-rebaseline-remediation-spec.md:16-59,63-132,134-211`:

- Scope reviews immutable `bf91b42...b6f89d7`; it explicitly excludes closing 41 open/seven partial, historical lease proof, child certification, D.6, release actions, and two preserved user docs.
- Registry validator requires field/cardinality/severity/scope/lease/parity checks; Phase C must collect every missing required field without KeyError and skip missing/None duplicate IDs.
- Serializer keeps its signature/order and guarantees semantic round trips; document IDs are string/pattern valid with exact ValueError/parse_error/E_USER_INPUT behavior.
- Safe writer is no-follow/workspace-contained/UTF-8/fsync/mode-preserving; log collision is `E_LOG_EXISTS`; Phase C must test a reachable intermediate default-path symlink with an unchanged outside sentinel before path resolution.
- Activation has exact `required_version` behavior and a singular invalid-clause diagnostic; doctor compares the PATH program; locking is cross-platform; read-only MCP performs no writes; type counts are exhaustive.
- Schema-v4 envelope keys and exit taxonomy are explicit; exit 4 is reserved. Windows and TestPyPI service proof remain external. Publishing builds/tests/promotes one exact wheel with hash/version identity and publisher-only OIDC.
- Map count is dynamic from a clean tracked snapshot, never a hard-coded 175/177; test commands and all tracked/staged/unstaged/untracked paths must be clean.
- Migration/manual must document required-version adoption, string/YAML IDs, error codes, schema 4.0, reserved 4, and upgrade-before-activation warning.
- Risks and exclusions retain P0 corruption, P1 path/publish/lifecycle risks and forbid synthesized evidence or release claims.

Architecture diagram actual edges, spec lines 217-238: Registry→Validator→O4/O5; Loader/Serializer→Safe Writer/Logging→CLI/MCP; Activation/Doctor→CLI/MCP; Locking→Writer; Release→Tests/Evidence; Serializer/Writer/CLI-MCP/Validator→Tests; Tests→Map/AGENTS. GitHub→Validator, Windows→Tests, and TestPyPI/PyPI→Release are dashed external boundaries.

Lifecycle diagram actual states, spec lines 242-259: I0→A→B.1→B.2→D.1→D.2→D.3; blocker→D.4→D.2; closed→D.5; D.5 FAIL→D.4; D.5 PASS→loose falsification; reproduced catch→D.4; no catch→D.6 pending→stop with no release claim.

Contract enumeration actual rows, spec lines 261-278:

1. semantic YAML round trip → `serialize_frontmatter` → frontmatter regression, execution evidence declared by spec;
2. string/pattern ID → `validate_document_id` → loading contract test, execution evidence declared by spec;
3. workspace-exclusive commit → `SessionContext.commit` → session-context tests, execution evidence declared by spec;
4. log collision → `log_command` → log tests, execution evidence declared by spec;
5. runtime version → config/activate/doctor exact anchors → three test anchors, execution evidence declared by spec;
6. schema-v4 JSON/exit → json_output anchors → CLI/link tests, execution evidence declared by spec;
7. reachable log-parent no-follow → log/config anchors → named Phase C test, Phase C execution required;
8. all-field malformed rows → validator sites → named Phase C test, Phase C execution required;
9. singular required-version clause → config sites → named Phase C test, Phase C execution required;
10. cross-platform lock → locking/tests/Windows CI → local evidence plus Windows external pending;
11. read-only MCP no writes → server/export/portfolio → registration test, execution evidence declared by spec;
12. exact wheel provenance → artifact checker → local tests plus external tag-run pending;
13. registry sole authority → validator → local/external parity modes, execution evidence declared by spec;
14. dynamic clean map → map generator → double-generation/clean-tree, execution evidence declared by spec.

Perform the alignment analysis now. Static evidence may support findings and verdict but must not be mislabeled direct-run.
