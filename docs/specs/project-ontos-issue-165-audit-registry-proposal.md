---
id: project_ontos_issue_165_audit_registry_proposal
type: spec
status: proposed
created: 2026-07-15
owner: Project Ontos Maintainers
depends_on:
  - project_ontos_v5_remediation_release_plan_proposal
  - project-ontos-fable-repo-audit-2026-07
  - project-ontos-codex-audit-revalidation-2026-07
  - project_ontos_v5_remediation_phase_0_live_issue_audit
concepts:
  - proposals
  - workflow
  - devops
---

# Project Ontos Issue #165 Audit Registry Proposal

## 1. Decision Requested

Return the exact Template 16 verdict **Proceed to Phase A** if this proposal is
an appropriately bounded basis for issue #165's machine-readable audit
registry and parity gate.

Approval would authorize a Phase A specification. It would not authorize
implementation, a workflow change, a generated-ledger replacement, a live
GitHub write, a release, a merge, or publication. This governance scaffold
contains no registry data and performs no issue mutation.

## 2. Parent Authority and Fixed Boundary

The merged `project_ontos_v5_remediation_release_plan_proposal` received the
terminal parent disposition **Split into multiple proposals**. Its approved
Phase 0 route authorizes this independent child to propose the #165 work in
parent §§9, 12, 21, and 23. The child remains **own Pre-A pending**: only its
own non-author proposal verdict may open Phase A.

The inherited release boundary is fixed:

> Project Ontos completes the approved feature and remediation program in v5;
> v6.0.0 removes only the exact eleven deprecated path-compatibility names.

The registry is required before v5.1 and therefore cannot be deferred to v6.
It cannot delete or rename a v5 public compatibility surface, treat historical
audit data as expendable cleanup, or broaden the v6 breaking change.

## 3. Evidence and Problem

### 3.1 The current ledger has evidence but no single machine authority

The Fable audit records 91 curated findings. The Codex Round-2 revalidation
records 9 additional findings and confirms that the intended machine-readable
registry and parity gate are absent from current `main`. Together they define
the approved invariant **91 + 9 = 100**.

The existing O4 audit remediation release-line ledger is useful historical
evidence, but it is a human-maintained projection. Editing both a registry and
that document by hand would create two mutable authorities and make drift
inevitable. Any older registry prototype found only on an off-main branch may
be inspected as seed evidence; it is not authoritative code, schema, or data
and must not be copied without reconciliation against current source records.

### 3.2 Issue #165 remains valid and unreconciled

The 2026-07-15 read-only live-issue audit confirmed that #165 is open with
`audit` and `P2-hygiene`, no milestone, and unresolved priority/release custody.
The board-hygiene child owns those public metadata corrections. This registry
child owns the technical data model and parity behavior; it must not race the
board child by treating today's issue metadata as the final baseline or by
writing back to GitHub.

### 3.3 Historical audit IDs and runtime finding IDs are different contracts

Issue #165 needs stable curated identifiers for the finite audit corpus.
Issue #174 separately proposes stable runtime `finding_key` identities for
future validation output and no-new-debt baselines. Similar words do not make
these keys interchangeable. **No mapping is inferred between the #165 and #174 namespaces.**

Any later bridge between those namespaces would need its own explicit schema,
cardinality, evidence, and migration decision. This child neither invents nor
requires one.

## 4. Goals

1. Define one versioned, schema-validated registry containing exactly 100
   unique curated audit-finding IDs.
2. Preserve the source, severity, disposition, release custody, lifecycle
   state, transfer history, and evidence needed to audit each finding.
3. Make the registry the sole mutable authority and render O4 deterministically
   from it.
4. Validate and render locally, deterministically, and without network access
   or credentials.
5. Add an explicitly authenticated, read-only parity tier for comparing the
   registry with live GitHub issue state.
6. Fail clearly on duplicates, missing evidence, invalid transitions, broken
   transfers, and nondeterministic projections.
7. Keep #165's curated-ID namespace independent from #174's runtime findings.

## 5. Non-Goals

This child does not:

- implement #174's runtime finding identity, diffing, or no-new-debt baseline;
- change issue labels, milestones, bodies, state, or comments;
- create or close a GitHub issue;
- remove a finding merely to satisfy a count or parity check;
- rewrite historical severities or audit conclusions without evidence;
- make a network call part of the default local validator or renderer;
- modify the Ontos product runtime, command behavior, MCP surface, public API,
  packaging, publish workflow, or existing CI/golden-master workflows;
- treat an off-main prototype as already shipped; or
- implement complete dynamic vocabularies or any v6 compatibility removal.

## 6. Owned, Composed, and Forbidden Scope

### 6.1 Owned implementation surface

After its own lifecycle authorization, this child may own:

- a versioned registry data file and JSON Schema;
- one registry validator and one deterministic ledger renderer;
- the generated `docs/reference/Audit_Remediation_Registry.md` projection;
- focused registry tests, including invalid fixtures created in the test
  module or an explicitly approved fixture extension;
- a dedicated read-only parity workflow;
- this child's proposal, specification, tracker, review evidence,
  retrospective, and manifest;
- the existing audit release-line tracker only for the explicit authority
  handoff; and
- orchestrator-generated Ontos map and agent-instruction updates.

The Phase A spec must freeze exact filenames and decide whether registry YAML
is ordered as a sequence or as an ID-keyed mapping. The manifest's current
paths are the maximum candidate write boundary, not permission to touch every
path.

### 6.2 Composed evidence

The child reads, but does not own:

- the merged parent proposal and its fixed release boundary;
- the 91-finding Fable audit and 9-finding Codex revalidation;
- the fresh Phase 0 live-issue snapshot;
- issue #165 and linked GitHub evidence;
- the board-hygiene child's verified post-transaction snapshot; and
- historical release/session evidence cited by registry records.

### 6.3 Forbidden scope

`ontos/`, internal archive state, package metadata, release artifacts,
publication, site sources, unrelated tests/scripts/docs, and the existing CI,
golden-master, and publish workflows are forbidden. The parity workflow may
read live issue state only; all GitHub mutation remains forbidden.

## 7. High-Level Data and Execution Contract

### 7.1 Registry record

Each curated record must have a stable `id` and the following reviewable
fields, with nullability and conditional requirements frozen by Phase A:

| Field | Required meaning |
|---|---|
| `id` | Immutable curated identifier in the #165 namespace |
| `source` | Origin audit and source locator |
| `severity` | Historical/approved severity under a closed vocabulary |
| `title` | Stable human-readable finding title |
| `owning_issue` | Current GitHub custody, if assigned |
| `state` | Finding resolution state, distinct from issue open/closed state |
| `disposition` | Approved treatment such as fix, accept, transfer, or supersede |
| `target_release` | Release custody or an explicit unassigned value |
| `evidence` | One or more source, implementation, verification, or release references |
| `lifecycle_state` | Registry lifecycle stage governed by legal transitions |
| `transferred_from` | Prior curated ID when a real transfer occurred |
| `updated_at` | Normalized timestamp for the latest evidence-bearing change |

The top-level document must also carry a registry schema/version identifier.
The specification must define legal values, required combinations, transition
rules, terminal-state evidence, supersession semantics, and transfer
semantics. Free-form status strings are insufficient.

### 7.2 Sole-authority flow

The intended one-way flow is:

```text
curated source evidence
        ↓
machine-readable registry (sole mutable authority)
        ↓ validate schema + semantic invariants
deterministic O4 renderer
        ↓
checked-in human-readable projection
        ↓ optional authenticated read-only comparison
live GitHub parity report
```

The checked-in projection must carry a generated warning and must never be
edited as a second source. A verification command renders to a temporary
location and byte-compares or checksum-compares the result with the committed
projection. Stable ordering, normalized line endings, and a fixed timestamp
policy are part of the contract.

### 7.3 Two parity tiers

**Tier 1 — deterministic local parity** validates schema, semantic rules,
record count, ID uniqueness, evidence links, transfers, projection freshness,
and checked-in fixtures. It is the default developer and pull-request path,
runs offline, and requires no GitHub token.

**Tier 2 — authenticated live parity** fetches current issue metadata and
compares only fields whose live correspondence is specified. It is read-only,
uses least-privilege credentials, records the repository and observation time,
and reports unavailable authentication distinctly from data drift. Missing
credentials must not fail Tier 1 or silently produce a passing Tier 2 result.

## 8. Identity, Custody, and Transition Rules

- The registry contains exactly 100 unique curated records at initial
  acceptance; the Phase A spec must list the expected source partitions.
- IDs are immutable after publication. A corrected record keeps its ID and
  adds evidence; it is not deleted and recreated.
- A transfer names both source and destination and preserves provenance.
- A superseded record remains present, names its successor, and carries
  evidence explaining the change.
- A terminal resolved/accepted/transferred state requires dated evidence and
  cannot be inferred from a closed GitHub issue alone.
- `owning_issue` describes custody; it does not collapse finding state into
  issue state.
- #174 runtime `finding_key` values are neither aliases nor successors for
  these IDs unless a future approved bridge says so.
- Renderer and parity failures must identify record IDs without mutating data.

## 9. Dependencies and Sequencing

1. The parent split verdict and this scaffold establish Phase 0 only.
2. A GLM non-author reviewer must return **Proceed to Phase A**.
3. Phase A reconciles the two source inventories, any off-main prototype, and
   every proposed field/transition before implementation.
4. The board-hygiene child completes before authenticated live parity freezes
   its issue-state baseline.
5. Product and technical review approve usability, policy, schema, and failure
   behavior before implementation.
6. Phase C implements registry, validator, renderer, tests, and the dedicated
   read-only parity workflow.
7. Three-family verification proves local determinism and authenticated parity
   before final approval.
8. Completion unblocks the v5.1 release gate.

This design may be prepared while independent v5.0.3 children proceed, but
that does not make them concurrent lifecycle siblings. This manifest therefore
declares an empty sibling list. Any future concurrent pair needs an explicit,
reciprocal handoff decision.

## 10. Safety, Failure Modes, and Rollback

- Validation and rendering default to no network and no write outside an
  explicitly selected output path.
- Live parity uses read-only API operations and no issue-write permission.
- Invalid or ambiguous input fails closed with record-level diagnostics.
- A renderer writes to a temporary file before atomic replacement; failure
  leaves the committed projection unchanged.
- Implementation must reject duplicate IDs, unknown fields when prohibited,
  illegal lifecycle transitions, dangling transfer/supersession links,
  terminal records without evidence, and source-partition count drift.
- Determinism tests run under varied locale/timezone or otherwise neutralize
  those inputs.
- Rollback reverts the registry/schema/tooling/projection commit together; it
  never selectively discards historical records to regain a green check.
- If source inventories disagree, stop and record an explicit blocker rather
  than choosing one silently.
- If live issue state drifts, report the difference to board custody; do not
  auto-rewrite the registry or GitHub.

## 11. Acceptance Outline

Before the child can claim completion:

- [ ] A non-author Template 16 verdict authorizes Phase A.
- [ ] The Phase A spec freezes schema versioning, field requirements, legal
      values, lifecycle transitions, terminal evidence, transfer, and
      supersession rules.
- [ ] The registry validates with exactly 100 unique curated IDs, partitioned
      into the approved 91-record and 9-record source inventories.
- [ ] Each record has required custody/evidence, and terminal records have
      sufficient dated evidence.
- [ ] Duplicate IDs, bad source counts, unknown/invalid values, illegal
      transitions, missing terminal evidence, and dangling or cyclic
      transfer/supersession links fail focused tests.
- [ ] Rendering the same registry repeatedly produces byte-identical O4
      output with stable ordering and no wall-clock drift.
- [ ] A freshness check detects any manual edit or stale checked-in projection.
- [ ] Tier 1 validation/rendering succeeds in a clean fork without credentials
      or network access.
- [ ] Tier 2 uses authenticated read-only access, distinguishes unavailable
      credentials from drift, and matches the post-hygiene live baseline.
- [ ] Tests prove that #165 IDs and #174 runtime finding keys are not silently
      merged, cross-counted, or rewritten.
- [ ] Maintainer documentation explains how to add evidence, make a legal
      transition, render O4, diagnose failures, and run both parity tiers.
- [ ] Review receipts, Product verdicts, final approval, and retrospective are
      present before the v5.1 gate is considered satisfied.

## 12. Unknowns and Escalation Classification

### Product-policy unknowns — resolve in Pre-A or Phase A

- Whether accepted-risk records are terminal and which evidence makes that
  disposition reviewable.
- Whether records without current issue custody use `null`, an explicit
  `unassigned` value, or a dedicated backlog owner.
- Which live issue fields are parity-authoritative versus informational.

### Technical-design unknowns — resolve in Phase A

- Sequence versus ID-keyed mapping for the source file.
- JSON Schema draft and the boundary between schema and semantic validation.
- Timestamp normalization and deterministic projection policy.
- Exact local/live commands and workflow trigger policy.
- Whether invalid fixtures remain embedded in focused tests or need a narrowly
  added fixture directory through an approved scope amendment.

### Evidence-reconciliation unknowns — blockers, not implementation guesses

- Any disagreement between the 91-source and 9-source inventories.
- Any off-main prototype ID that cannot be traced to current approved evidence.
- Any terminal disposition lacking an implementation, verification, release,
  acceptance, transfer, or supersession reference.

## 13. Questions for Reviewers

### Product

1. Are the proposed dispositions and terminal-evidence rule understandable to
   maintainers and auditors, or do they risk presenting custody as completion?
2. Should live parity compare issue priority/milestone, given that the board
   child owns those fields and may change them independently?
3. Does making O4 generated-only preserve enough human reviewability?
4. Is the distinction between curated historical IDs and runtime finding keys
   explicit enough for release notes and contributor documentation?

### Technical

1. Is the registry's proposed record surface minimal while still sufficient
   for validation, rendering, transfers, and evidence auditability?
2. Which invariants belong in JSON Schema, and which require deterministic
   semantic validation?
3. What is the least-privilege authentication and stable output contract for
   live parity?
4. Which checksum/byte-comparison strategy best proves the checked-in O4
   projection is fresh across supported platforms?
5. What test matrix most convincingly separates source-count correctness,
   lifecycle legality, determinism, and live drift?

## 14. Allowed Template 16 Verdicts

The non-author reviewer must choose exactly one:

- **Proceed to Phase A**
- **Revise and re-review**
- **Abandon direction**
- **Split into multiple proposals**

Any missing, malformed, or differently worded verdict leaves Phase A blocked.

## 15. Recommendation

**Proceed to Phase A.** The parent has already authorized the independent
#165 child, current evidence confirms the gap remains valid, and the proposed
boundary separates governance data, deterministic documentation, and read-only
live comparison without touching the Ontos runtime or the GitHub issue board.
