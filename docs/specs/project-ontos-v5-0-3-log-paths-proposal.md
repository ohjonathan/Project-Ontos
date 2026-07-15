---
id: project_ontos_v5_0_3_log_paths_proposal
type: spec
status: proposed
created: 2026-07-15
owner: Project Ontos Maintainers
depends_on:
  - project_ontos_v5_remediation_release_plan_proposal
  - project-ontos-codex-audit-revalidation-2026-07
  - ontos_manual
  - ontos_agent_instructions
  - ontology_spec
concepts:
  - proposals
  - config
  - mcp
  - release
---

# Project Ontos v5.0.3 Log Paths Proposal

## 1. Decision Requested

Return the exact Template 16 verdict **Proceed to Phase A** for a narrowly
scoped v5.0.3 child that introduces one shared resolved-log-path authority,
moves log writers and readers to it, and converts exactly seven deprecated
#149 helpers into compatibility delegates.

The change fixes the current split in which the configured active writer can
use `docs/logs` while contributor-mode counting and consolidation consult
`.ontos-internal/logs`. It preserves the contributor-internal archive and
decision-history authority and does not migrate, merge, delete, or reactivate
any log stream.

This document is a Pre-A proposal only. It does not authorize a Phase A
specification, implementation, archive cutover, issue closure, release, or
lifecycle certification.

## 2. Parent Authority and Evidence

The terminal parent proposal
`project_ontos_v5_remediation_release_plan_proposal` assigns this child:

- the v5.0.3 `ResolvedLogPaths`-equivalent authority and its production
  consumers;
- active-log query behavior shared by readers and counters;
- the mandatory isolation of exactly seven log-related #149 compatibility
  helpers; and
- an explicit prohibition on archive deletion or migration.

The parent establishes the defect from current-main evidence: the active log
writer honors effective `paths.logs_dir`, but contributor-mode consolidation
uses internal hard-coded active, archive, and history paths. In Project Ontos,
that lets the writer use `docs/logs` while a reader or consolidator looks at
`.ontos-internal/logs`. The result can be incorrect counts, stale-session
selection, and consolidation of the wrong stream.

The parent also fixes the release boundary. v5.0.3 aligns path authority and
isolates the seven wrappers; a later independently reviewed archive child owns
inventory, extraction, migration, cutover, and deletion. A future Phase A spec
must re-fetch `origin/main`, record an immutable base SHA, characterize every
consumer, and recompute the current history/archive inventory before proposing
implementation details.

## 3. Problem Statement

Ontos has path helpers and consumers that answer related questions from
different sources. Configuration can correctly select an active log stream,
while contributor-mode branches independently select where to count,
consolidate, archive, or find decision history. That creates four risks:

1. writers and readers may operate on different streams;
2. deprecated helpers can continue to encode shadow path policy even after a
   new resolver is added;
3. an eager repair could silently merge or move historical material; and
4. contributor and non-contributor workspaces require different established
   history authorities without permitting each consumer to invent one.

The desired correction is one immutable resolution result plus one active-log
query boundary. It is not a storage migration.

## 4. Goals

- Resolve active, archive, archived-log, and decision-history paths once from
  effective configuration and repository mode.
- Preserve all existing 5.x configuration precedence for `logs_dir`.
- Make the effective configured directory the active read/write stream and the
  only consolidation input.
- Preserve Project Ontos contributor history at
  `.ontos-internal/reference/decision_history.md` and archived logs at
  `.ontos-internal/archive/logs` until an independently approved cutover.
- Preserve existing non-contributor archive/history behavior rather than
  imposing Project Ontos' internal layout on adopters.
- Route CLI, MCP, consolidation, maintenance, health, instruction, and
  retention/archive-planning consumers through the same resolved value.
- Provide a shared active-log query service for counts, age selection, and
  last-session discovery.
- Convert exactly seven #149 helpers into thin delegates while preserving their
  v5 public compatibility contracts.
- Report inactive legacy streams without moving, merging, or reactivating
  them.
- Expose effective source, destinations, history authority, and cutover state
  in dry-run and structured output.

## 5. Non-Goals

- No archive inventory execution, extraction, copy, rewrite, migration,
  cutover, deletion, or Git-history rewrite.
- No `docs/strategy/decision_history.md` or `docs/archive/logs` shadow
  authority.
- No removal or signature change for any deprecated public helper.
- No isolation of non-log #149 names and no v6 deletion work.
- No new configuration field, schema, precedence rule, or vocabulary.
- No dependency graph, body-reference, document-model, or finding-ID work.
- No automatic activation of `.ontos-internal/logs` or any other detected old
  stream.
- No invented number for the residual log-alignment issue.
- No package release, board mutation, or issue closure in this child proposal.

## 6. Owned, Composed, and Forbidden Scope

### 6.1 Owned

- One immutable `ResolvedLogPaths`-equivalent value and its resolution logic.
- One active-log query boundary used for counts, age queries, and default
  last-session lookup.
- Delegation by exactly the seven wrappers enumerated in §8.
- Migration of production log consumers from independent path derivation to
  the shared resolver/query boundary.
- Dry-run and structured diagnostics for effective paths, authority, inactive
  streams, and cutover state.
- Focused CLI, MCP, contributor, non-contributor, consolidation, health,
  instruction-generation, and compatibility tests.
- Necessary user and v5.0.3 release documentation after implementation is
  independently approved.

### 6.2 Composed

- Effective configuration and the current 5.x `logs_dir` precedence contract.
- Existing workspace-root, contributor-mode, normalization, containment, and
  symlink/reparse-point safeguards.
- Existing log writer and `SessionContext` write behavior.
- Existing transactional consolidation behavior; this child changes path
  authority, not migration transaction semantics.
- Existing public signatures, return types, warnings, import paths, and
  re-export locations for the seven deprecated helpers.
- The parent's current archive and canonical-history inventory as evidence to
  be recomputed, never as a hard-coded constant.

### 6.3 Forbidden

- Configuration-schema or loader changes.
- Archive source or destination content changes.
- Creation of an alternate history/archive tree under `docs/`.
- Dependency resolver, graph, body-reference, ontology, vocabulary, or MCP
  schema work.
- Any non-log #149 compatibility helper or v6 API deletion.
- Sibling child proposal, manifest, tracker, specification, or implementation
  scope.

## 7. High-Level Contract

### 7.1 Resolved value

Build one immutable value from effective configuration and repository mode. It
must expose at least:

```text
active_logs_dir
archive_root_dir
archive_logs_dir
decision_history_path
inactive_legacy_streams[]
resolution_source
history_authority
cutover_state
```

`resolution_source` records why the effective paths were selected rather than
forcing callers to infer precedence. `history_authority` identifies the one
canonical decision-history owner. `cutover_state` is exactly one of
`not_planned`, `planned`, or `approved`; this child expects `not_planned` for
Project Ontos and does not approve a transition.

### 7.2 Resolution rules

1. Preserve the effective configured `logs_dir`, including current 5.x legacy
   precedence.
2. Treat that directory as the active log write stream, active read/query
   stream, and consolidation input.
3. In Project Ontos/contributor mode, retain exactly one history authority at
   `.ontos-internal/reference/decision_history.md` and consolidation output at
   `.ontos-internal/archive/logs`.
4. Never derive or create `docs/strategy/decision_history.md` or
   `docs/archive/logs` merely because the active stream is `docs/logs`.
5. For non-contributor adopters without an established internal authority,
   preserve current configured/docs-derived archive and history behavior.
6. Resolve, normalize, and contain every path before a write.
7. Detect old streams and report their contained paths and counts, but never
   merge, move, reactivate, or write to them implicitly.
8. Show effective sources, destinations, canonical authority, inactive streams,
   and cutover state in dry-run and structured output.

For Project Ontos, the expected resolved result is:

```text
active_logs_dir       = docs/logs
archive_root_dir      = .ontos-internal/archive
archive_logs_dir      = .ontos-internal/archive/logs
decision_history_path = .ontos-internal/reference/decision_history.md
history_authority     = contributor_internal
cutover_state         = not_planned
```

The old `.ontos-internal/logs` stream is inactive after alignment. The internal
archive and history destinations remain canonical and may still receive
explicit consolidation writes; "inactive" does not mean frozen, migrated, or
eligible for deletion.

### 7.3 Required consumers

The same resolved value must be consumed by:

- CLI `log`;
- MCP `log_session` and `session_end`;
- `consolidate`;
- `maintain` log counts and consolidation dispatch;
- activation and doctor log health;
- instruction generation; and
- any retention or archive planner.

Production consumers move to the non-deprecated resolver/query services in the
same implementation patch that delegates the wrappers. No consumer may retain
an independent path-policy branch.

## 8. Exactly Seven #149 Compatibility Wrappers

The Phase A specification must preserve this complete matrix and may not add a
non-log helper to the child.

| ID | Compatibility name | Required delegation |
|---|---|---|
| W1 | `get_logs_dir` | Return `active_logs_dir` |
| W2 | `get_log_count` | Use the shared active-log query service |
| W3 | `get_logs_older_than` | Use the shared active-log query service |
| W4 | `find_last_session_date` when no directory is supplied | Use the shared active-log query service |
| W5 | `get_archive_dir` | Return the resolver's established archive authority |
| W6 | `get_archive_logs_dir` | Return `archive_logs_dir` |
| W7 | `get_decision_history_path` | Return `decision_history_path` |

All seven remain public throughout v5. Their signatures, path string return
types, deprecation warnings, import locations, and re-export locations stay
pinned; byte-for-byte behavior is preserved where the existing contract makes
that meaningful. They become delegates, not alternate authorities.

## 9. Issue Custody and Dependencies

- **Primary inherited issue:** #149 supplies the seven deprecated log helpers,
  but remains open until the v6 deletion artifact verifies the entire frozen
  compatibility inventory.
- **Residual correctness issue:**
  `[Bug] Align contributor log writes and consolidation with configured logs_dir`.
  Its number remains pending creation by the board-hygiene child; this proposal
  must not guess or reserve one.
- **Board custody:** the board-hygiene child owns issue creation, number,
  labels, milestone, cross-links, and closure actions.
- **Residual closure rule:** keep the residual issue open until Project Ontos
  and at least one internal-log fixture prove writer, reader, counter, and
  consolidator parity from a released artifact.
- **Archive successor:** the separately reviewed archive child may compose the
  resolver later, but this child grants no migration or deletion authority.
- **Sibling relationship:** the other v5.0.3 children may proceed independently;
  any shared-file overlap requires serialization and post-merge revalidation.
- **Future branch:** `codex/project-ontos-v5-0-3-log-paths`, created from a
  then-current immutable `origin/main` commit only after Pre-A approval.

## 10. Safety and Rollback

- Normalize and contain every resolved path before any write; fail closed on a
  workspace escape or unsafe symlink/reparse point.
- Read, count, and consolidate only the configured active stream. Detection of
  another stream is diagnostic and never authorizes a write.
- Preserve exactly one canonical history authority and one established archive
  destination for each mode.
- Dry-run/check behavior writes no files, lockfiles, Git objects, generated
  artifacts, shadow history, or shadow archive.
- Consolidation remains transactional and never performs an implicit
  migration. Failure-injection expectations belong in the Phase A spec after
  current behavior is characterized.
- Change the resolver, active queries, production consumers, and all seven
  delegates atomically. A partial rollout that leaves two authorities is not a
  valid intermediate release state.
- Keep the child independently revertible. If parity regresses, revert the
  resolver and wrapper delegation together and ship a new patch; never move
  user logs as rollback and never replace an immutable release tag.

## 11. Acceptance Outline

Phase A must turn the following into unskippable normative tests rather than
merely checking prose in the parent.

### 11.1 Resolution and parity

- Project Ontos resolves the exact values in §7.2.
- An internal-log contributor fixture preserves its established contributor
  behavior.
- A non-contributor fixture preserves its current configured/docs-derived
  archive and history behavior and never receives a contributor-internal path.
- CLI `log`, MCP `log_session`, MCP `session_end`, maintenance counts,
  consolidation input, activation, doctor, and generated instructions all
  agree on the active stream.
- Active-log count, age, and default last-session queries operate on the same
  normalized active directory.
- Old streams are reported as inactive with contained path/count evidence and
  receive no automatic read-as-active, merge, move, reactivation, or write.
- Dry-run and structured output identify resolution source, all effective
  destinations, history authority, inactive streams, and cutover state.

### 11.2 Authority and history integrity

- Project Ontos retains one canonical internal decision history and one
  internal archived-log destination.
- No `docs/strategy/decision_history.md` or `docs/archive/logs` shadow is
  created.
- Every inventoried archived-log reference in canonical history resolves
  before and after consolidation. The current baseline is approximately 77;
  the gate recomputes the inventory and must never hard-code that count.
- Consolidation consumes the configured active stream, writes only to the
  established archive/history authority, and performs no implicit migration.

### 11.3 Compatibility and release

- Every W1–W7 row delegates to the shared resolver/query service.
- Public signatures, string path returns, warnings, imports, and re-exports
  remain pinned for v5.
- No eighth/non-log wrapper changes in the child.
- Supported Python, coverage, golden-master, wheel/sdist, isolated install, and
  TestPyPI gates pass at release time.
- The exact published wheel proves Project Ontos plus one internal-log fixture
  writer/reader/counter/consolidator parity before the residual issue closes.

## 12. Unknowns

### 12.1 Must resolve before Pre-A

No known direction-level unknown remains. A reviewer finding that this child
requires a configuration schema change, shadow authority, archive movement, or
wrapper deletion should select **Revise and re-review**, not broaden Phase A.

### 12.2 Resolve during Phase A

- Exact private module and immutable-value type placement.
- Exact active-log query interface and dependency-injection boundary.
- Exact structured/JSON field names while preserving current public envelopes.
- Complete consumer call graph, including any retention/archive planner that
  currently derives paths indirectly.
- Exact inactive-stream detection rules and stable ordering without unbounded
  workspace scanning.
- Consolidation transaction integration and failure-injection matrix.
- Recomputed canonical-history/archive inventory and a performance budget for
  repeated log queries.
- The narrowest implementation file set after current-main revalidation.

### 12.3 Defer

- Archive destination selection, extraction, copy/rewrite, cutover, and source
  deletion.
- Any decision-history authority move.
- Non-log #149 isolation and all v6 API deletion.
- Configuration vocabulary, body-reference, and finding-model work.

## 13. Review Questions

### 13.1 Product lens

1. Does one visible active stream eliminate the confusing mismatch among log
   creation, counts, health, and consolidation?
2. Are inactive-stream diagnostics useful without implying that Ontos will
   merge or recover those streams automatically?
3. Is retaining the internal history/archive authority while using `docs/logs`
   as active input understandable in dry-run and structured output?
4. Do users receive enough compatibility protection from preserving all seven
   helper signatures, returns, warnings, imports, and re-exports through v5?
5. Is requiring Project Ontos plus a second internal-log fixture before issue
   closure an adequate adopter-facing release gate?

### 13.2 Technical lens

1. Can every listed consumer receive one immutable resolution result without
   introducing a second configuration parser or hidden global authority?
2. Does the active-log query boundary cover count, age, and last-session needs
   without preserving path policy in the seven delegates?
3. Do contributor and non-contributor rules preserve current authority while
   preventing `docs/` shadow destinations?
4. Are normalization, containment, inactive-stream reporting, transactions,
   and rollback sufficient to ensure this patch cannot become an implicit
   migration?
5. Does the seven-row matrix completely freeze the log-related #149 slice and
   mechanically exclude every non-log compatibility name?

## 14. Template 16 Verdict Set

The non-author GLM proposal reviewer must return exactly one:

- **Proceed to Phase A**
- **Revise and re-review**
- **Split into multiple proposals**
- **Abandon direction**

Only **Proceed to Phase A** authorizes creation of the Phase A specification.
No abbreviated verdict is lifecycle evidence.

## 15. Recommendation

Return **Proceed to Phase A**. The proposal contains one shared path/query
authority, one complete seven-wrapper compatibility matrix, one fixed no-
migration boundary, and one independently revertible v5.0.3 change. Phase A
should specify implementation details only after recording a fresh immutable
base, reproducing the writer/reader split on current main, and recomputing the
history/archive inventory.
