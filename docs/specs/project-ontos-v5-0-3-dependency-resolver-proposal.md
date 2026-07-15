---
id: project_ontos_v5_0_3_dependency_resolver_proposal
type: spec
status: proposed
created: 2026-07-15
owner: Project Ontos Maintainers
depends_on:
  - project_ontos_v5_remediation_release_plan_proposal
  - project-ontos-codex-audit-revalidation-2026-07
  - ontos_manual
  - ontology_spec
concepts:
  - proposals
  - link-check
  - testing
  - mcp
---

# Project Ontos v5.0.3 Dependency Resolver Proposal

## 1. Decision Requested

Return the exact Template 16 verdict **Proceed to Phase A** for a narrowly
scoped v5.0.3 child that fixes issue #176. The child would make an existing
bare workspace-root file such as `pyproject.toml`, `Dockerfile`, `Makefile`,
or `LICENSE` resolvable without requiring a misleading `./` prefix, while
preserving document-ID precedence and all existing security boundaries.

This document is a Pre-A proposal only. It does not authorize a Phase A
specification, implementation, issue closure, release, or lifecycle
certification.

## 2. Parent Authority and Evidence

The terminal parent proposal
`project_ontos_v5_remediation_release_plan_proposal` assigns this child:

- the graph resolver and cross-surface parity tests for #176;
- composition from the current containment and external-file allowlist
  behavior; and
- an explicit prohibition on body-reference policy.

The parent places the fix in v5.0.3 as one independently reversible product
change. Current-main reproduction showed that a bare `pyproject.toml` is
classified as a broken dependency while `./pyproject.toml` reaches existing
filesystem and allowlist handling. The current `_looks_like_path()` heuristic
recognizes separators and `.md`, but not an otherwise valid root file.

Issue #176 and the parent remain the direction-level evidence. A future Phase A
spec must re-fetch `origin/main`, record an immutable base SHA, and rerun the
characterization matrix before proposing implementation details.

## 3. Problem Statement

Ontos currently lets spelling, rather than identity, decide whether a
`depends_on` value receives filesystem resolution. That creates three product
problems:

1. a valid repository-root file is reported as broken unless users add `./`;
2. naively widening path guessing could steal an exact document ID or expose an
   escaping filesystem target; and
3. activation, doctor, link-check, map, hooks, and MCP must not drift into
   different interpretations of the same dependency.

The desired correction is a bounded fallback for previously unrecognized bare
tokens, not a new general path language.

## 4. Goals

- Resolve existing bare regular files from the workspace root or declaring
  document directory after exact document-ID resolution.
- Preserve precedence for active and configured-external document IDs.
- Fail closed on duplicate IDs, path ambiguity, containment escape, physical
  aliases, and case collisions.
- Apply the existing external-file allowlist to the contained resolved
  repository-relative path.
- Preserve the current `broken_link` rule ID, severity, and human behavior when
  no safe target exists.
- Carry privacy-safe structured context without exposing absolute workspace or
  escaping target paths.
- Make every graph-consuming CLI and MCP surface share one resolver.

## 5. Non-Goals

- No Markdown/body-reference namespaces or body path policy.
- No new configuration fields or allowlist grammar.
- No log-path, consolidation, archive, or compatibility-wrapper work.
- No custom vocabulary, public document model, finding-ID, or baseline work.
- No change to explicit pre-v5.0.3 path behavior beyond characterization.
- No inference that every dotted or extensionless token is a path.
- No new validation rule ID or severity.
- No package release, issue closure, or board mutation in this child proposal.

## 6. Owned, Composed, and Forbidden Scope

### 6.1 Owned

- The shared `depends_on` graph resolver for previously unrecognized bare
  tokens.
- Collision-aware target indexing needed by that resolver.
- Structured dependency-resolution context.
- Focused graph, link-diagnostic, CLI, and MCP parity fixtures for #176.
- Necessary user documentation and v5.0.3 release documentation after
  implementation is independently approved.

### 6.2 Composed

- Existing active-document and configured-external-document loading.
- Existing containment, symlink/reparse-point, physical-identity, and case
  collision behavior.
- Existing `validation.allowed_external_dependency_paths` semantics.
- Existing `ValidationError`, graph, and JSON/MCP serialization boundaries.

### 6.3 Forbidden

- Body-reference scanning or Markdown link policy.
- Config schema or vocabulary changes.
- Resolved log paths, log writers, consolidation, or any #149 wrapper.
- Archive migration/deletion and v6 API removal.
- Sibling child proposal, manifest, tracker, specification, or implementation
  scope.

## 7. High-Level Contract

Before graph traversal, build one collision-aware exact-ID target index from
active documents and configured external documents. For each `depends_on`
value:

1. An exact unique document ID wins over every filesystem interpretation.
2. A duplicated active/external ID emits the existing fail-closed ambiguity
   diagnostic and never falls through to a path.
3. An already explicit path spelling uses the characterized current resolver.
4. Only a previously unrecognized bare token receives workspace-root and
   declaring-document-relative candidate probes.
5. Candidate resolution reuses containment and filesystem identity checks and
   discloses no escaping absolute target.
6. The new bare probe accepts only existing regular files.
7. Candidates resolving to the same physical entry are deduplicated.
8. Different root-relative and source-relative targets are ambiguous; neither
   wins by iteration order.
9. The external-file allowlist matches the contained resolved
   repository-relative path.
10. One safe allowlisted target becomes `external_file_dependency`.
11. No target preserves the current `broken_link` contract.

Structured context should include the raw dependency, declaring document ID
and relative path, candidate-base roles, contained resolved path when safe,
matched allowlist rule, ambiguity targets when safe, stable reason code, and
final classification. Exact field names and private object placement belong in
Phase A.

## 8. Issue Custody and Dependencies

- **Product issue:** #176.
- **Board custody:** the board-hygiene child owns title, labels, milestone, and
  closure actions.
- **Closure rule:** #176 stays open until the released artifact—not merely the
  source tree—passes the reproduction.
- **Safety predecessor:** board cleanup records correct v5.0.3 custody before
  implementation begins.
- **Sibling relationship:** registry work and the other v5.0.3 product
  children may proceed independently, but shared files require explicit
  composition and post-merge revalidation.
- **Future branch:** `codex/project-ontos-v5-0-3-dependency-resolver`, created
  from a then-current immutable `origin/main` commit only after Pre-A approval.

## 9. Safety and Rollback

- Reject containment and symlink/reparse-point escapes without disclosing the
  external target.
- Never choose among ambiguous IDs, candidate bases, physical identities, or
  case variants.
- Preserve existing explicit-path behavior and unresolved-dependency
  compatibility.
- Dry-run/check paths write no files, locks, Git state, or generated artifacts.
- Keep the change independently revertible. If the resolver regresses, revert
  only this child and ship a new patch; never replace an immutable release tag.

## 10. Acceptance Outline

The Phase A specification must turn every row below into an unskippable test
through the shared resolver and appropriate CLI/MCP surfaces.

| ID | Fixture | Expected result |
|---|---|---|
| R1 | Existing `pyproject.toml`, allowlisted | External file dependency |
| R2 | Existing `./pyproject.toml`, allowlisted | Same classification and resolved path as R1 |
| R3 | Existing extensionless `LICENSE`, allowlisted | External file dependency |
| R4 | Exact active document ID named `pyproject.toml` | Document edge wins |
| R5 | Exact configured-external document ID named `pyproject.toml` plus same-named file | External document edge wins |
| R6 | Active and configured-external records share one exact ID | Existing duplicate/ambiguous-document finding; no path fallback |
| R7 | Missing dotted value | Existing broken-link contract |
| R8 | Existing bare directory | No new file classification; existing broken-link contract |
| R9 | Existing explicit `./directory` | Characterized pre-patch result unchanged |
| R10 | Symlink/reparse point to outside workspace | Contained-security result; no edge and no external target disclosure |
| R11 | Root-relative and source-relative candidates are one physical entry | One external target |
| R12 | Root-relative and source-relative candidates are different files | Structured ambiguity error |
| R13 | Case collision on a case-insensitive filesystem | Existing fail-closed behavior |

Additional acceptance:

- activation, doctor, link-check, map, hooks, and MCP agree;
- human and structured diagnostics retain compatible rule/severity behavior;
- supported Python, golden-master, coverage, wheel/sdist, and isolated
  TestPyPI gates pass at release time; and
- the exact published wheel reproduces the fixed bare-file behavior.

## 11. Unknowns

### 11.1 Must resolve before Pre-A

No known direction-level unknown remains. A reviewer finding a contradiction
with document-ID precedence, privacy, or compatibility should select **Revise
and re-review** rather than allowing Phase A.

### 11.2 Resolve during Phase A

- Exact private index/helper ownership and reason-code spellings.
- Exact structured-context schema while retaining current public envelopes.
- Characterized directory and case-filesystem results on supported platforms.
- A measured performance budget for index construction and graph traversal.
- The narrowest implementation file set after current-main revalidation.

### 11.3 Defer

- Body-reference namespaces and path policy.
- New rule IDs, severities, or general path inference.
- Any v5.1 vocabulary or v5.2 findings behavior.

## 12. Review Questions

### 12.1 Product lens

1. Does the bounded bare-file fallback solve #176 without surprising users who
   intentionally chose a document ID?
2. Are ambiguity and missing-target messages actionable without exposing host
   paths?
3. Is preserving explicit-path behavior preferable to tightening unrelated
   directory handling in this patch?
4. Are the release and rollback expectations proportionate to a correctness
   patch?

### 12.2 Technical lens

1. Can active and configured-external IDs share one complete index before
   traversal without changing external-scope semantics?
2. Does the resolution order preserve containment, physical identity, case,
   allowlist, rule-ID, and severity contracts?
3. Can all CLI and MCP consumers reuse the shared graph result rather than
   reconstructing resolution?
4. Does the thirteen-row matrix cover every unsafe ordering or ambiguity case?

## 13. Template 16 Verdict Set

The non-author GLM proposal reviewer must return exactly one:

- **Proceed to Phase A**
- **Revise and re-review**
- **Split into multiple proposals**
- **Abandon direction**

Only **Proceed to Phase A** authorizes creation of the Phase A specification.
No abbreviated verdict is lifecycle evidence.

## 14. Recommendation

Return **Proceed to Phase A**. The proposal is one issue, one shared resolver
boundary, one fixed compatibility contract, and one independently revertible
v5.0.3 change. Phase A should specify implementation details only after
recording a fresh immutable base and reproducing the matrix on current main.
