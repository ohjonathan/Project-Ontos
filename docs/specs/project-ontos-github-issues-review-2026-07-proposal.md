---
id: project-ontos-github-issues-review-2026-07-proposal
type: spec
status: proposed
created: 2026-07-16
owner: Project Ontos Maintainers
depends_on:
  - project_ontos_v5_remediation_release_plan_proposal
  - ontos_manual
concepts:
  - proposals
  - activation
  - link-check
  - config
  - schema
---

# GitHub Issues Review and Remediation Proposal — 2026-07-16

## 1. Executive Summary

This proposal reviews all ten open GitHub issues (#149, #158, #165, #173,
#174, #175, #176, #177, #178, #181) against the v5.0.2 codebase. Every issue
was investigated by an independent code-grounded review and each verdict was
adversarially re-verified, including end-to-end reproductions for every bug
claim. Verdicts:

| Issue | Kind | Verdict | Disposition |
|---|---|---|---|
| #176 | Bug | **Confirmed, reproduced twice** | **Fixed in this change** |
| #181 | Feature | Partially valid; review found a **new bug** (nested archive is scanned) | **Scan bug fixed in this change**; manifest/verify designed below; backends rejected |
| #178 | Feature | Partially valid; alias pain reproduced | **Alias MVP implemented in this change**; vocabulary extension deferred |
| #173 | Feature | Partially valid; **data-loss trap reproduced** | **Ownership guard + content-based staleness implemented**; digests next; receipt-v1 contract deferred |
| #175 | Feature | Partially valid | `map --check` + `merge-check` designed below; common-dir lock and CAS leases rejected |
| #177 | Feature | Valid | Namespace + annotation-glob design below; full 4-mode policy matrix rejected |
| #174 | Feature | Valid | Designed below; sequenced after #177/#178 per the merged v5 plan |
| #165 | Governance | Valid | Registry + validator plan below; needs its own session |
| #158 | Tracker | Status reconciled | Exact board edits enumerated below (not executed) |
| #149 | Tracker | 20 of 21 findings landed | Remaining: v6-only removal + two tails to split out |

The review was steered by the maintainer's stated priority: heavy agentic
coding across many git worktrees, repositories, and devices concurrently,
where capturing and curating context is the core value. Features were judged
against that use case, not against their own ambition.

**Implemented on this branch** (each independently revertible):

1. **#176 fix** — bare workspace-root files (`pyproject.toml`, `Makefile`,
   `LICENSE`) resolve as dependencies without a `./` prefix, per the
   resolution order in the merged v5 remediation plan §11.2.
2. **#181 slice-0 fix** — `scanning.skip_patterns` directory patterns such as
   the default `archive/*` now exclude nested layouts
   (`docs/archive/logs/…`), which `ontos consolidate` itself writes. Before
   this fix the archived payload was scanned straight back into the live
   graph — the opposite of the issue's premise.
3. **#178 alias MVP** — `[frontmatter.aliases.type]` /
   `[frontmatter.aliases.status]` in `.ontos.toml` with fail-closed
   validation, plus the built-in `in-progress -> in_progress` repair
   (also required by plan §11.4), threaded through both `ontos maintain
   --fix-frontmatter-enums` and `ontos doctor`'s frontmatter check.
4. **#173 slice-A** — instruction-file ownership classification
   (`ontos_owned` / `managed_block` / `user_managed`); `ontos maintain` and
   map-driven sync never implicitly overwrite a user-managed `AGENTS.md`;
   AGENTS.md staleness is decided by content comparison, not mtime.

## 2. Method

Nine investigation agents (one per issue; #158/#149 combined) each fetched
the full issue, read the cited v5.0.2 code, and built scratch-workspace
reproductions where the issue claimed a defect. Nine adversarial verifiers
then attempted to refute each verdict with independent reproductions and
citation spot-checks. A final synthesis pass mapped file-level interactions,
cross-cutting contract constraints, and landing order. Baseline: 1568 tests
green at `bd04620`.

Reproduction highlights:

- **#176**: `depends_on: [pyproject.toml]` with the file present and
  allowlisted → `broken_link` at error severity, activation
  `usable_with_warnings`, exit 1. Identical target spelled
  `./pyproject.toml` → `external_file_dependency` at info severity, clean
  activation, exit 0. Confirmed across `activate`, `doctor`, and
  `link-check` (all funnel through `build_graph`).
- **#173**: in a fresh `git clone` of a repo whose source tree reported
  "AGENTS.md up to date", checkout write-order alone flipped the verdict to
  "may be stale", and a plain `ontos maintain` then **replaced a fully
  hand-authored AGENTS.md with generated content** (only a `.bak`
  survived). `instruction_artifacts.py` even touches AGENTS.md on unchanged
  content (`touch_on_unchanged=True`) purely to game the mtime signal.
- **#181 (new bug)**: `ontos/io/files.py` matches skip patterns with
  `fnmatch(str(md_file), pattern) or md_file.match(pattern)`. `Path.match`
  is right-anchored, so `archive/*` matches `docs/archive/foo.md` but NOT
  `docs/archive/logs/foo.md` — the nested layout consolidate prefers. The
  same hole affects `node_modules/*` (every package README one level down).
- **#175**: two individually-clean branches merged into a graph with a
  duplicate ID and a cycle that no existing command can catch pre-merge;
  `ontos map` (and `ontos activate`'s map write) writes the context map with
  a bare `write_text`, without the workspace lock.
- **#178**: a fixture with the issue's exact values yields 6 diagnostics /
  0 repairable, and one unmapped value blocks the whole apply
  (`E_UNRESOLVED_ENUMS` refuses partial apply), so a single unknown status
  bricks the repair feature.

## 3. Per-Issue Findings and Dispositions

### 3.1 #176 — Bare workspace-root dependency resolution (bug; fixed here)

**Root cause** (`ontos/core/graph.py:39`): `_looks_like_path()` requires a
path separator or `.md` suffix; `_resolve_depends_on_path()` returns early
for bare tokens before any filesystem probe.

**Fix shape** (single file; every consumer — activation, doctor, map,
link-check, hooks, MCP — routes through `build_graph`):

- Active document IDs keep deterministic precedence (`dep_id in
  existing_ids` is checked before any path logic; unchanged).
- Explicit-path spellings keep their existing behavior byte-for-byte,
  including the characterized handling of directories.
- A previously unrecognized bare token now gets a **stricter** probe:
  workspace-root-relative and declaring-doc-relative candidates, regular
  files only (`is_file()`; a bare token matching a directory such as `docs`
  stays a broken link), the existing symlink-containment check, the
  existing `_LoadedPathIndex` lookup (so a bare name matching a loaded
  doc's file resolves as a graph edge and inode collisions stay
  fail-closed), and fail-closed ambiguity when the two candidate bases
  resolve to different files.
- The allowlist (`validation.allowed_external_dependency_paths`) applies to
  the resolved workspace-relative path, so `pyproject.toml` and
  `./pyproject.toml` classify identically.
- Missing values remain `broken_link` with the existing rule ID, severity,
  and message contract.

Regression tests mirror the plan §11.2 acceptance matrix (bare == `./`
equivalence, extensionless root files, doc-ID collision precedence, bare
directory stays broken, symlink escape stays broken, dual-candidate
ambiguity fail-closed, missing dotted value stays broken).

Note: plan §11.2's "combined active + external document-ID index" refers to
an external-documents concept that does not exist in v5.0.2; those rows
activate when that feature lands.

### 3.2 #181 — External archive backends (feature; slice-0 fixed here, rest designed/deferred)

**Verdict.** The need behind the issue is real — it is the maintainer's own
planned extraction of `.ontos-internal/archive` (460 files, 5.4 MB) — but
the proposed mechanism (provider-neutral backend registry, hydration,
two-phase commit with CAS on both repositories, writer-freeze, clone-proof
automation) is enterprise-grade machinery for a 5.4 MB markdown problem, and
the repository's own governance (merged plan §18.3 Phase C) forbids archive
extraction before a separately reviewed migration proposal. Front-running
that gate would be wrong.

**Slice-0 (implemented here).** The issue's premise "normal scanning
excludes the archive" was found to be false for the nested layout: skip
patterns now match segment-suffixes of the path, so `archive/*` (and
`node_modules/*`, `.git/*`) exclude entire subtrees. This is the cheapest
change that delivers the issue's core "archive out of the live graph"
motivation. Release note required: adopter repositories with nested
archive layouts will see document counts drop (correctly).

**Phase-A design (next session).** Read-only integrity tooling, no data
movement:

- `ontos/core/archive_manifest.py`: deterministic manifest — schema
  version, source commit, per-file `{posix_path, size, mode, full sha256,
  doc id/type/status when frontmatter parses}`, sorted by path, hashing raw
  bytes. Do **not** reuse the 16-hex truncated `compute_content_hash` for
  integrity claims.
- `ontos archive manifest [--output …]` and `ontos archive verify
  [--manifest …]` reporting added/removed/changed with non-zero exit on
  drift (new command → budget for the CLI v4 contract suite).
- Workflow doc: externalization stays manual-with-verification — the
  operator moves the archive tree wherever they choose; `MANIFEST.json`
  stays in the parent as the pinned catalog stub; `verify` proves inventory
  equality on either side.

**Rejected/deferred**: `[archives.*]` config schema, git/object-storage
backends, `externalize`/`hydrate` commands, two-phase commit, CAS,
writer-freeze, submodule mounts, clone-proof automation — design-only,
gated on the §18.3 Phase C review. Do not add the config surface early;
it would constrain the eventual design.

### 3.3 #178 — Workspace vocabularies and alias repair (feature; alias MVP here, extension deferred)

**Verdict.** The alias pain is real and reproduced; worse than filed, since
one unresolved value blocks the entire apply. But most "governed repair"
acceptance criteria already exist (plan-first deterministic JSON, relative
paths, `original_*` preservation, formatting/BOM/CRLF guarantees,
fail-closed apply). The genuinely missing piece is small: config-declared
alias tables and one built-in alias.

**Implemented here:**

- `FrontmatterConfig` section in config: `[frontmatter.aliases.type]` and
  `[frontmatter.aliases.status]`, string→string tables. Fail-closed
  validation: only `type`/`status` sub-tables; targets must be canonical
  enum members and never `unknown`; alias keys must not themselves be
  canonical values. Because targets must be canonical, chains and cycles
  are impossible by construction.
- Built-in `in-progress -> in_progress` in `STATUS_REPAIRS` (plan §11.4).
- Config aliases merge over built-ins (config wins; documented). Each edit
  carries `source: "built-in" | "config"` in dry-run/apply JSON.
- Threaded through **both** consumers of `build_enum_repair_plan`:
  `maintain --fix-frontmatter-enums` and `doctor`'s frontmatter check.
- Manual documents the new keys and the forward-compatibility caveat: older
  Ontos installs hard-reject unknown config sections, so repositories
  adopting `[frontmatter]` should pin `ontos.required_version` (e.g.
  `>=5.1`) so lagging devices fail with the version message instead of a
  confusing config error.

**Deferred** (retain on issue): custom types extending canonical types and
custom statuses with lifecycle classes. That is a cross-cutting refactor of
the str-Enum normalization boundary with ~98 type/status value comparisons
across 22 files (map, query, export, MCP, curation); `original_*`
preservation already retains domain semantics. Note on the issue that MVP
aliases are repair-time mappings, not load-time acceptance: files converge
to canonical values on `--apply` and canonical values then travel via git.
True frozen-path mode (diagnosed but never edited) remains open:
`scanning.skip_patterns` removes paths from diagnosis entirely, which is
not the same contract (correction from the PR #182 review).
Receipt/baseline invalidation depends on #173/#174.

### 3.4 #173 — Content-addressed activation receipts (feature; slice-A here, digests next, receipt contract deferred)

**Verdict.** Both premises confirmed: AGENTS.md freshness in doctor and
maintain is a pure mtime comparison that misfires on clones, worktrees, and
touch-only changes, and the maintain pipeline acts on the false signal by
force-overwriting even a fully hand-authored AGENTS.md. For a multi-device,
multi-worktree workflow this is the most urgent defect after #176: two
checkouts of the same tree report opposite freshness, and one of them will
destroy user content on a routine `ontos maintain`.

**Implemented here (slice-A):**

- `classify_instruction_ownership(path)` → `ontos_owned` (generated-by
  header) / `managed_block` (USER CUSTOM markers) / `user_managed`
  (neither). Maintain's sync task and map-driven agents sync skip
  `user_managed` files with an explicit message (`ontos agents --force` to
  adopt); doctor reports ownership instead of a false "stale".
- AGENTS.md staleness for `ontos_owned`/`managed_block` files is computed
  by rendering the current expected content and comparing through the
  existing timestamp-normalizing semantic comparator — content, not mtime.
  The `touch_on_unchanged` mtime hack is retired with the signal it gamed.
- Existing mtime-pinned tests rewritten to pin the content-based contract.

**Next slice (with #175's `map --check`; designed, not implemented):** the
shared digest core — `ontos/core/digest.py` (full-length sha256;
`graph_digest` over sorted (workspace-relative posix path, sha256(bytes))
pairs; `config_digest` over `.ontos.toml` bytes) and promotion of
`get_head_sha`/`is_dirty` from the private MCP closure into `ontos/io/git.py`
— then surface `graph_digest`, `config_digest`, `head_sha`, `dirty` in
`activate --json`, MCP health, and map frontmatter, batched with
`mcp/schemas.py` and parity-test updates in one commit. Mark the fields
experimental (pre-contract).

**Deferred/rejected:** the versioned `ontos-activation-receipt-v1` file
format, receipt export/diff commands, dirty-tree digests, merge-base
binding, session labels, and a general managed-block sync engine — zero
consumers today; freezing a v1 contract now is premature API commitment.
Portability caveat to document: digests hash raw bytes, so cross-OS
identity under `core.autocrlf` rewriting is out of scope by design.

### 3.5 #175 — Multi-worktree coordination and merge-result validation (feature; designed)

**Verdict.** The diagnosis is right (worktree-scoped `.ontos.lock`; nothing
queries the git common dir; the reproduced two-clean-branches → broken
merged graph failure mode is exactly the maintainer's daily risk). The
remedy is over-scoped:

- **Rejected: common-dir coordination lock.** Two worktrees write to
  disjoint checkouts; Ontos keeps no shared mutable state under the common
  dir today, so the lock would protect nothing. Revisit only if shared
  state appears.
- **Rejected: CAS writer-intent leases.** Cross-device coordination is
  already mediated by git push/pull for a single maintainer; a lease
  protocol adds failure modes without adding safety.
- **Already true: no silent merge drivers.** No merge driver exists in the
  codebase; capability 5 needs only a documentation sentence.

**Design to implement next (in order):**

1. `ontos map --check` (S effort): render the map in memory, compare
   against the committed file through the existing
   timestamp-normalizing comparator, exit `FINDINGS=1` on drift with a
   structured payload. **Constraint:** the exit-code taxonomy is closed
   (0/1/2/3/5/130; 4 reserved) — drift is `FINDINGS=1` + `error_code`,
   never a new numeric code. Must land after the digest fields stamp map
   frontmatter, or every `--check` goes red the day #173's digest lands.
   Fold in lock acquisition for `map`/`activate` map writes (today both
   write the context map without the workspace lock, non-atomically).
2. `ontos merge-check --base <ref> --head <ref>` per merged plan §17.5
   normative semantics: two parents plus computed merge base, three-tree
   comparison, and **new-vs-base findings are required output**, not
   polish. Materialize trees via `git worktree add --detach` (git-archive
   fallback); reuse `run_activation(root=…, write_map=False)`.
   Implementation note from reproduction: `git merge-tree --write-tree`
   exits 1 whenever any path conflicts, and the committed generated map
   will essentially always conflict — a conflicted merge-tree exit is
   data (report it, continue validating the mergeable paths), not a
   command failure. New command → CLI v4 contract suite applies.
3. Ownership/lease machinery for generated artifacts: **not needed** — a
   `--check` gate in CI/agent preflight achieves the guardrail without a
   leasing protocol.

### 3.6 #177 — Wikilink namespaces and body-reference policy (feature; designed)

**Verdict.** Fully confirmed: every `[[…]]` target is treated as a document
reference, so entity annotations in imported material become
`body.bare_id_token` errors driving exit 1 — which trains agents and hooks
to ignore diagnostics, the worst outcome for a trust-based tool. Because
`:` is provably outside the document-ID alphabet (`DOCUMENT_ID_PATTERN`),
`[[entity:…]]` is guaranteed-false-positive territory today and namespaces
are collision-free by construction.

**Design to implement (one slice, atomically with rename support):**

- Reserved namespaces `doc:` / `entity:` / `source:` in wikilink parsing:
  `doc:` always validated as a document reference (even inside
  entity-glob paths); `entity:`/`source:` classified as annotations, never
  validated as documents, **never rewritten by rename**; unknown prefixes
  stay broken (fail-closed). Unnamespaced `[[id]]` keeps current behavior.
- One config key `validation.body_entity_annotation_paths` (workspace-
  relative globs, same segment semantics as the existing allowlists):
  within matching files, unresolved unnamespaced wikilinks downgrade to
  entity annotations instead of broken references.
- Structured `body_annotations` section in link-check/map/MCP JSON — kind,
  path, location, matched rule — so nothing disappears silently. Keep the
  record fields stable so #174 can key finding identities off them.
- `rename` must learn `doc:`-namespace rewriting in the same change —
  verified today it skips `[[doc:old-id]]`, so shipping parsing without
  rename support creates a silent rename blind spot.
- Existing pinned candidate-extraction tests
  (`tests/core/test_body_refs.py`) flip; budget the rewrite.

**Rejected:** the full four-mode per-glob policy table
(`document`/`entity`/`source_provenance`/`off` with winning-rule
precedence) — one glob list plus three namespaces covers the demonstrated
cases (24 of 35 findings directly; provenance links in imported registers
already land in a non-fatal bucket when files exist). `source:` logical-
root mapping for relative Markdown links is the hardest, rarest case;
defer until demonstrated need. Honest caveat: `--frontmatter-only` and
prose rewriting are workarounds available today; this is a fidelity
feature, not a blocker.

### 3.7 #174 — Stable finding IDs and no-new-debt diffing (feature; designed, sequenced after #177/#178)

**Verdict.** Real and feasible: findings today are anonymous dicts with a
13-value `rule_id` taxonomy, machine-specific absolute `file_path`, no
identity, no diff, no baseline; non-strict surfaces exit 0 regardless of
warnings while `map --strict` exits 3 on any warning. Output determinism is
already verified (sorted scans, canonical cycles), and a working base-vs-
head diff was prototyped via `git worktree` + `run_activation(write_map=
False)` with correct introduced/resolved/unchanged classification.

**Sequencing:** the merged plan schedules this after #177/#178 semantics
stabilize (v5.2.0). Shipping the ID contract first would force an immediate
contract-version bump when #177 changes reference-rule semantics. Respect
that order.

**Design:**

- `finding_id` = truncated sha256 over a versioned tuple
  (FINDINGS_CONTRACT_VERSION, rule_id, document_id, workspace-relative
  posix file_path fallback, field/edge, normalized target, occurrence
  ordinal for duplicates). Exclude severity (reclassification ≠ new
  finding), absolute paths, line numbers, wording, discovery order.
- One serializer (`to_record(workspace_root)`) adds `finding_id` +
  repo-relative `file_path` **additively** across CLI and MCP.
  Parity-frozen surfaces to update in the same commit: the pinned
  `to_dict` shape (`ontos/core/types.py`), exact-payload activate tests,
  and `mcp/schemas.py` Literal-typed schemas.
- `ontos findings diff --base <ref>`: materialize base ref, re-scan
  read-only, report `introduced` / `resolved` / `unchanged` /
  `reclassified`, exit `FINDINGS=1` when `introduced` is non-empty. The
  git base ref **is** the baseline — this alone delivers the no-new-debt
  property for branch/worktree/PR workflows, and the two-clean-branches
  case falls out by diffing the merge result against either parent.
- `config_digest` (from the #173 digest core) distinguishes base/head
  config skew from real finding churn.

**Deferred:** the committed baseline/ratchet file with
owner/reason/expiry dispositions, staleness/migration gates, rule-contract
negotiation, CI annotation formats. Revisit only if a permanently-dirty
main branch needs green CI. This is a phase split of the issue's
acceptance criteria, not a silent re-scope — say so on the issue.

### 3.8 #165 — Machine-readable audit registry (governance; planned, own session)

**Verdict.** Well-founded; the named registry/validator never landed on
main, and the July program demonstrably drifted exactly as predicted
(mislabeled severity, closures without receipts, a phantom finding ID —
caught only by expensive manual revalidation). All inputs are mechanically
extractable: the 91 Fable IDs parse from the audit report's `###` headings
(1/27/63 severity split, verified by script), the 9 R2 IDs from the
revalidation table.

**Plan (needs a dedicated session — ~4 judgment-heavy non-terminal rows):**

- `manifests/project-ontos-audit-remediation-registry.yaml`: 100 rows
  (stable ID, owning issue, state, evidence ref); schema-validated;
  duplicate/missing/unassigned IDs rejected.
- `scripts/validate_audit_registry.py` (offline): report-derived ID +
  severity parity, O4 ledger custody cross-check (keep the human-authored
  ledger; cross-check rather than rewrite), terminal-state-requires-
  evidence rule.
- CI: observational step first, flipped to blocking after one green cycle
  (§12.5). Live GitHub checklist parity stays a manual, read-only,
  release-time script — per-PR live parity and issue-write automation are
  forbidden by §12.4/§12.6. Checklist parser must tolerate irregular rows
  (verified: #149 has rows without severity annotations).

### 3.9 #158 / #149 — Trackers (board maintenance; enumerated, not executed)

Reconciled against reality (PR #170 merged as `62348da`; v5.0.1 tag
`8976fa1`; v5.0.2 merge `61fd4bc`):

- **#149 is 20-of-21 landed.** Stale text to fix: header still says "18 of
  21 … draft PR #170 … pending"; D4a-config-3, D4a-config-5, and the
  maintain-exit-5 self-heal rows still say "merge/verification pending".
  Genuinely open: `D5b-dead-code-3` (v6.0.0-only breaking removal of the
  11 legacy path names), plus two inherited tails the merged plan says to
  split into named residual issues ("Align contributor log writes and
  consolidation with configured logs_dir"; "Classify and extract eligible
  internal archive material").
- **#158**: tick the `#148` and `R2-testpypi-provenance-1 → #148` boxes;
  append v5.0.1/v5.0.2 reconciliation entries; record successor custody
  (#149 v6 tail, #165, the two residual issues); then close #158 — the
  merged plan pre-authorizes this as board maintenance.
- **This change contributes:** the #176 fix, the #178 alias slice (plan
  §11.4 — record the checkbox on #178; do not close it), and this
  proposal. #176 closes per plan §11.8 only after a released artifact
  passes the reproduction, not at merge time.

These are GitHub mutations; they are listed here for maintainer approval
rather than executed by the implementing session.

## 4. Cross-Cutting Constraints (binding on all future slices)

1. **Exit-code taxonomy is closed** (`ontos/ui/json_output.py`): 0/1/2/3/5/
   130, 4 permanently reserved, category derived only from code. New
   conditions (map drift, introduced findings) map to `FINDINGS=1` plus a
   payload `error_code` — never a new numeric exit code.
2. **CLI v4 contract suite** (`tests/test_cli_contract_v4.py`)
   automatically covers any new registry command (`findings`,
   `merge-check`, `archive`): registry completeness, parser/handler
   presence, v4 JSON envelopes for argparse errors, alias contracts.
   `validate` is a hidden alias of `verify` — a findings command must be
   named `findings`.
3. **Config forward-compatibility skew**: `dict_to_config` hard-rejects
   unknown sections and keys, so any new config surface bricks activation
   on lagging devices sharing the repo. Every config addition ships with
   `ontos.required_version` pinning guidance in the manual and release
   notes.
4. **Two parity-frozen output surfaces**: the pinned `to_dict` record shape
   (`ontos/core/types.py`) with exact-payload tests, and `mcp/schemas.py`
   Literal-typed schema versions. Additive payload changes batch with
   schema + parity-test updates in one commit; never interleave two
   issues' payload edits.
5. **Dogfood regeneration**: `Ontos_Context_Map.md`, `AGENTS.md`, and
   `CLAUDE.md` are generated — regenerate via `ontos map` / `ontos export
   claude --force` in the same PR as any change to scan semantics, map
   format, or instruction content; end sessions with `ontos log`.
6. **Root `CHANGELOG.md` is the live changelog** (`Ontos_CHANGELOG.md` is a
   stale kernel doc). Behavior flips (bare-dep downgrade, archive-scan
   fix, staleness/overwrite-guard semantics) get entries there.
7. **Digest/manifest hashing**: full-length sha256 over raw bytes with
   posix-normalized sorted paths; never the 16-hex display truncation.
   Cross-OS identity under `core.autocrlf` is documented as out of scope.
8. **Recommended landing order** for the remaining designed work:
   digest core (`io/git.py` helpers + `core/digest.py`) → #173 digest
   fields in payloads → #175 `map --check` → #177 namespaces → #174
   finding IDs + `findings diff` → #175 `merge-check` → #181 Phase-A
   manifest/verify → #165 registry (anytime, disjoint).

## 5. Review Addendum — PR #182 Adversarial Review (2026-07-17)

The maintainer's adversarial review of PR #182
([comment](https://github.com/ohjonathan/Project-Ontos/pull/182#issuecomment-4998275065))
reproduced six findings against the first implementation round. All were
verified as real. Dispositions:

**Fixed on the branch (each reproduced, fixed, and pinned by regression
tests):**

1. **Scan matcher over-reach (P1).** The first segment-suffix matcher
   walked absolute-path suffixes, so a checkout under an ancestor directory
   named `archive`/`node_modules` scanned zero documents, and `fnmatch`'s
   separator-crossing `*` silently made custom patterns recursive. Rewritten
   to match contiguous runs of workspace-relative (or scan-root-relative)
   segments with segment-local `*` and explicit `/**` subtree syntax.
   Ancestors outside the repository never participate.
2. **Ownership sentinel too loose (P1).** "Generated by Ontos v" anywhere
   in the file conferred ownership, so a hand-authored file quoting the
   phrase was eligible for implicit replacement. Ownership now requires the
   byte-exact versioned header line in its structural template position
   (within the file head, preceded only by known template head lines);
   everything else fails closed to `user_managed`.
3. **Branch-dependent staleness + CWD leak (P1).** The Branch stats row is
   checkout-local state and is now normalized out of the semantic
   comparison (two worktrees at the same HEAD agree on freshness), and
   `generate_agents_content`/`is_agents_semantically_stale` take an
   explicit `repo_root` so freshness is never computed against whatever
   repository the process happens to run in.
4. **Alias safety (P2).** (a) `original_*` extraction is quote-aware: `#`
   inside a quoted scalar is content (`"qa#blocked"` round-trips), unquoted
   `#` opens a comment only after whitespace, malformed quoting falls back
   to the parsed value. (b) `config_to_dict` omits an empty `[frontmatter]`
   section, so defaults stay readable by ≤5.0.2. (c) A configured alias
   redefining a built-in mapping to a different target is now a
   fail-closed config error, per the issue's acceptance language; the
   manual's compatibility wording was corrected — old clients reject the
   unknown section before `required_version` is evaluated, so the real
   guidance is "upgrade every device first".
5. **#176 ambiguity diagnostics (P2).** Bare-token resolution now returns a
   typed result; both candidate bases are evaluated before deciding (a
   loaded-doc match no longer shadows a different file at the other base),
   and ambiguity produces an explicit diagnostic naming the
   workspace-relative candidates with reason code
   `ambiguous_bare_candidates` — never a false "does not exist".

**Acknowledged, tracked, not in this PR:**

6. **MCP cache freshness (P2).** `file-mtime-fingerprint` remains the MCP
   cache's authority and a same-size/same-mtime rewrite serves stale
   content. This is the #173 remainder: the digest core must land together
   with the MCP freshness-mode change and its pinned contract
   (`freshness_mode`, `mcp/schemas.py`, parity tests) in one batched
   change, per §4 constraint 4.

**Accepted corrections to this proposal's designs:**

- **#174**: keep a stable `finding_key` (identity) separate from a
  classification `finding_id`, carry multiplicity explicitly rather than
  discovery-order ordinals, and treat baseline/ratchet support as part of
  the deliverable rather than indefinitely deferred — the motivating
  repository carries hundreds of standing warnings.
- **#175**: source conflicts must stop merge-safety validation
  (`merge_safe=false`); partial analysis is advisory only.
- **#177**: body-reference resolution is source-relative first and
  workspace-root-relative second; and downgrading only *unresolved*
  unnamespaced wikilinks means adding a same-named document can silently
  change a reference's semantics and rename eligibility — the design must
  address that hazard explicitly.
- **#181**: a manifest is an inventory, not yet a catalog (no inbound
  links, writers, active/frozen classification, access policy, revision
  binding, recovery, or hydration), and moving files in a new commit does
  not reduce historical clone size — the honest benefit is checkout size
  and graph noise.
- **#158**: the live issue's own custody rule says it stays open until
  #149 closes; any closure under the merged plan's board-maintenance
  authorization must explicitly amend that rule.
- **§3.3**: the frozen-paths claim was corrected in place —
  `skip_patterns` removes paths from diagnosis, which is not
  diagnose-but-never-edit.

The review's recommended three-PR split (v5.0.3 correctness patch / v5.1
semantic foundation / architecture proposal) and the `WorkspaceAnalysis`
snapshot architecture are maintainer release decisions; this branch keeps
each concern in separate commits so it can be split or cherry-picked
either way.

## 6. Value Frame: Multi-Worktree / Multi-Device Agentic Work

For the maintainer's actual workflow the highest-leverage line is:

1. **Trust the diagnostics** (#176, #181 slice-0, #178 aliases — done
   here): false broken-links, phantom archive docs, and unrepairable enum
   noise train agents to ignore Ontos output.
2. **Never lose user context** (#173 slice-A — done here): a tool whose
   maintenance command can destroy a hand-authored instruction file cannot
   be given to autonomous agents.
3. **Make state portable and comparable** (#173 digests, #175 `map
   --check`): agents on different devices/worktrees can prove they
   activated the same graph and detect stale generated artifacts cheaply.
4. **Gate the merge, not the worktree** (#175 `merge-check`, #174
   `findings diff --base`): the real coordination surface for parallel
   agents is the merge result; per-worktree locks and leases are the wrong
   abstraction.
5. **Curate imported knowledge without noise** (#177): entity annotations
   and provenance links are how captured context refers to the world;
   they must not be graph errors.
