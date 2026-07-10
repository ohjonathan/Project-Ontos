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

# Alignment Recertification Report: Project Ontos Phase B.1

## 1. Architecture compliance

An analysis of [project-ontos-audit-rebaseline-remediation-spec.md](file:///Users/jonathanoh/.gemini/antigravity-cli/scratch/docs/specs/project-ontos-audit-rebaseline-remediation-spec.md) has been performed against the approved revalidation authority [2026-07-10-codex-audit-revalidation.md](file:///Users/jonathanoh/.gemini/antigravity-cli/scratch/docs/reviews/2026-07-10-codex-audit-revalidation.md) and the approved release-line authority [project-ontos-audit-remediation-release-line.md](file:///Users/jonathanoh/.gemini/antigravity-cli/scratch/docs/trackers/project-ontos-audit-remediation-release-line.md).

The specification aligns with the approved architectural baseline. Specifically:
- **Baseline Integration**: The specification restricts its scope to the range beginning at baseline `bf91b42` and ending at the checkpoint `b6f89d7`.
- **Finding Partitioning**: The registry retains the exact partition of 91 unique findings (1 P0, 27 P1, and 63 P2). Spec v1.2 respects this partitioning by leaving 41 findings confirmed-open and 7 findings partial.
- **Pending States**: Issue #146 remains in the `code_fixed_evidence_pending` state, and issue #147 remains in the `evidence_pending` state. No premature closures are declared.
- **Doctor Code Status**: The Doctor script is recognized as fixed at revision `03c36e6` but remains subject to pending verification without claiming historical strict-P3 compliance.
- **Safe Writing & Refuted O5**: The old O5 lease structure is omitted because it failed to account for shared-path collisions. The spec establishes a safe writer architecture requiring path validation (such as intermediate default-path symlink checking with an external sentinel before path resolution).
- **Tooling Parity**: The specification details strict CLI and MCP boundaries, ensuring control-plane parity, read-only MCP constraints, and exit status taxonomies.

This structure complies with the revalidation authority's baseline.

## 2. Diagram-architecture cross-reference

The specification defines its component layout and edge connections in lines 217-238. A static review of these diagrams confirms compliance:

- **Registry to Output Rendering**: The flow `Registry -> Validator -> O4/O5` shows that the registry serves as the sole machine authority, with Validator verifying the fields and generating human-readable render formats (O4/O5).
- **Core Operations**: The path `Loader/Serializer -> Safe Writer/Logging -> CLI/MCP` routes input loading and serialization through the no-follow safe writer and command logging before interfacing with external runtimes.
- **Diagnostics and Activation**: The edges `Activation/Doctor -> CLI/MCP` connect system environment audits and version constraints directly to the main interfaces.
- **Locking Control**: The edge `Locking -> Writer` confirms that workspace concurrency control restricts unsafe write actions.
- **Testing Paths**: The edges `Serializer/Writer/CLI-MCP/Validator -> Tests` and `Tests -> Map/AGENTS` route execution verification through the test suites to validate dynamic repository maps and agents.
- **External Boundaries**: The dashed boundaries (`GitHub -> Validator`, `Windows -> Tests`, `TestPyPI/PyPI -> Release`) establish that Windows-specific lock testing and TestPyPI publishing verification are external dependencies. This matches the authority requirements for external proof.

## 3. Roadmap alignment

The lifecycle state machine in lines 242-259 traces the progression path:
- **Linear Sequence**: The sequence `I0 -> A -> B.1 -> B.2 -> D.1 -> D.2 -> D.3` is preserved. Phase B.1 acts as the static-inspection alignment gate.
- **Integration Blocker**: The path `blocker -> D.4 -> D.2` accommodates the shared-tree blocker. The state `shared_tree_integration.status` remains `unproven_rebaseline_integration`, preventing progress to D.4 until resolved.
- **Verification Loop**: The path `closed -> D.5; D.5 FAIL -> D.4; D.5 PASS -> loose falsification; reproduced catch -> D.4; no catch -> D.6 pending -> stop with no release claim` governs release gate verification. It enforces that failure at D.5 redirects back to resolution (D.4), and a passing run moves to falsification testing.
- **Release Exclusions**: The sequence terminates with a stop instruction and no release claim under D.6, aligning with the release-line authority's prohibition of premature release packaging.

## 4. Constraint verification

| Constraint | Source (doc:lines) | Verified? | Evidence |
| :--- | :--- | :--- | :--- |
| Semantic YAML Round Trip via `serialize_frontmatter` | `spec:63-132, 261-278` | Aligned by packet | execution evidence declared by the spec |
| String/Pattern validated document IDs with specific exception behavior | `spec:63-132, 261-278` | Aligned by packet | execution evidence declared by the spec |
| Workspace-exclusive commit checks via `SessionContext.commit` | `spec:63-132, 261-278` | Aligned by packet | execution evidence declared by the spec |
| Log collision detection raising `E_LOG_EXISTS` via `log_command` | `spec:63-132, 261-278` | Aligned by packet | execution evidence declared by the spec |
| Runtime version checks with exact `required_version` behavior and doctor anchors | `spec:63-132, 261-278` | Aligned by packet | execution evidence declared by the spec |
| Schema-v4 envelope keys and exit taxonomy with reserved exit 4 | `spec:134-211, 261-278` | Aligned by packet | execution evidence declared by the spec |
| No-follow workspace-contained safe writing with default-path symlink test on reachable log-parent | `spec:63-132, 261-278` | Pending as required | Phase C execution required |
| Validator malformed row check collecting missing fields without KeyError and skipping duplicates | `spec:63-132, 261-278` | Pending as required | Phase C execution required |
| Singular required-version clause config validator | `spec:63-132, 261-278` | Pending as required | Phase C execution required |
| Cross-platform locking verification | `spec:63-132, 261-278` | Pending as required | local evidence plus Windows external pending |
| Read-only MCP performs no write operations | `spec:63-132, 261-278` | Aligned by packet | execution evidence declared by the spec |
| Exact wheel provenance (OIDC publisher-only, single wheel build) | `spec:134-211, 261-278` | Pending as required | local tests plus external tag-run pending |
| Registry as sole machine authority with validator parity checks | `spec:63-132, 261-278` | Aligned by packet | execution evidence declared by the spec |
| Dynamic map count from clean tracked snapshot (excluding hard-coded counts) | `spec:134-211, 261-278` | Aligned by packet | execution evidence declared by the spec |
| Baseline established at bf91b42 | `revalidation:11-49; spec:16-59` | Aligned by packet | static-inspection of spec scope exclusions |
| Partition of 91 findings (41 confirmed-open, 7 partial) | `revalidation:72-87; spec:16-59` | Aligned by packet | static-inspection of spec scope exclusions |
| #146 remains code-fixed/evidence-pending and #147 remains evidence-pending | `release-line:27-61; spec:16-59` | Aligned by packet | static-inspection of spec scope exclusions |
| Unproven shared-tree integration status blocker | `release-line:27-61` | Aligned by packet | static-inspection of spec scope exclusions |
| O5 lease ordering applies prospectively and cannot be claimed retroactively | `release-line:73-98; spec:16-59` | Aligned by packet | static-inspection of spec scope exclusions |

## 5. Backward compatibility

The specification ensures compatibility integrity through several design constraints:
- **Serialization Interface**: The serialization system preserves signature formats and parameter ordering. Round-trip safety guarantees that valid document structures do not experience frontmatter degradation.
- **Document ID Validation**: Document IDs must conform to defined string patterns. Attempted ingestion of malformed IDs is mapped to specific errors (`ValueError`, `parse_error`, or `E_USER_INPUT`), preventing unexpected system crashes.
- **CLI/MCP Interface Integrity**: Schema-v4 envelope keys and exit codes maintain strict backwards compatibility. The reserved exit code 4 is documented to prevent collision with downstream systems.
- **Path Resolution Integrity**: The refuted historical O5 lease report (which omitted shared-path collisions) is corrected. The new path resolution model utilizes workspace-contained write boundaries and tests default-path symlinks prior to path resolution to preserve host environment sandboxing.

## 6. Consistency check

A consistency review between spec v1.2 and the approved authorities shows full alignment:
- **Baseline Alignment**: The spec limits its review scope to `bf91b42...b6f89d7`. This aligns with the Codex Revalidation baseline.
- **Rejection of Historical Fable Claims**: The revalidation authority highlights that Fable §5 was incomplete (only covering 68/91 findings) and referenced a nonexistent `D6a-test-gaps-3` phase. The spec ignores these invalid claims, adhering strictly to the canonical registry data.
- **Registry Authority**: The spec validator treats the machine registry as the sole canonical authority, rejecting human-rendered deviations in O4/O5.
- **Scope Proof Requirements**: The spec maps dynamic counts from a clean snapshot of the repository (including tracked, staged, unstaged, and untracked files relative to `base_sha`), ensuring that bare `git diff` output or branch-name matching is not used as proof.
- **Prospective Leasing**: Spec v1.2 does not make retroactive lease claims for I0, complying with the prospective lease ordering constraint.

## 7. Deviation report

| Divergence | Authority cited? | Authority source | Severity |
| :--- | :--- | :--- | :--- |
| None | N/A | N/A | N/A |

## 8. Issues found

### Blocking
None.

### Should-fix
None.

### Minor
None.

## Verdict

Approve

## 10. Notes

The static alignment review shows that spec v1.2 is aligned with the Codex Revalidation and Release-line authorities. The specification maintains the required open and partial findings, excludes premature release claims, and retains the blocker status of the shared-tree integration. The design resolves the shortcomings of historical documents (such as the refuted O5 lease and Fable §5 report) by establishing a no-follow safe writer and using the machine registry as the canonical authority. Consequently, the specification represents the required truth for Project Ontos and is approved for the B.1 phase.
