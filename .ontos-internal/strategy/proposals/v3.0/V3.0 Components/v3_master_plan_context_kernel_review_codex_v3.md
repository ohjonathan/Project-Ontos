---
id: v3_master_plan_context_kernel_review_codex_v3
type: strategy
status: draft
depends_on: [master_plan_v4]
---

# Review: Strategic Master Plan & Context Kernel v4.0.0 (Final Consensus Edition)

Source reviewed: `.ontos-internal/strategy/proposals/v3.0/v3_master_plan_context_kernel.md` (2025-12-19, Status: APPROVED FOR IMPLEMENTATION).

## Findings
- **Missing frontmatter / placement mismatch:** Plan declares “APPROVED” and v4.0.0 but lives under `proposals/` with no YAML frontmatter. Source-of-truth path and graduation target remain ambiguous.
- **Schema/version compatibility gaps:** Schema versioning is mentioned (v2.9), but the plan doesn’t define min/max supported schema for V2 vs V3 runtimes, nor how V3 MCP reacts to mismatched repos (warn/block/migrate).
- **Immutable history not specified:** v2.7 “Immutable History” says regenerate ledger but lacks canonical ordering, merge policy, and CI assertion that ledger == logs. Parallel branches can still diverge.
- **Typed edges underdefined:** Allowed edge vocab, validation rules, cardinality, and dual-write period with `depends_on` are not specified. Migration/backfill path and query/context-selection semantics are missing.
- **Context Object / transactional model shallow:** SessionContext/transaction pattern is named, but required injected services (git, fs, clock/env), error model, rollback semantics, and test strategy for purity are not articulated.
- **Config cascade edge cases:** Precedence is listed, but protections against malicious parent configs, symlink/worktree traversal, and a “show effective config” capability are absent.
- **MCP security/perf:** Bind/auth/token are specified, but no ACLs, rate limits, redaction policy, pagination/chunking for `get_context`, or write-conflict handling beyond a single lock file.
- **Installer hygiene:** install.py watch-out notes checksums/idempotency but no requirements for pinned tag/commit, signature/verify step, uninstall path, or offline/manual install.
- **Curation Levels criteria:** Levels 0-2 are named; validation severity (warn vs fail), promotion workflow, and handling of `pending_curation` artifacts are unspecified.
- **Validation/metrics thin:** SWE-bench experiment lacks sample-size rationale, seed/control definition, measurement of elapsed time or token cost, and reproducibility criteria.

## Suggestions
- Add YAML frontmatter (id/type/status/depends_on) and declare the authoritative location (proposals → strategy?) with graduation criteria and supersedes/obsoletes note.
- Define schema compatibility contract: min/max schema per runtime, MCP behavior on mismatch (block/warn/auto-migrate), and a `migrate --dry-run` + backup flow.
- Codify immutable ledger rules: deterministic sort (timestamp + branch + slug), regeneration command, merge guidance, and CI check to assert ledger derives from logs.
- Specify typed edge schema: allowed types, validation errors, cardinality constraints, dual-write with `depends_on` during transition, query/context-selection semantics, and a migration/auto-suggest tool.
- Detail SessionContext contracts: required injected services (git API, fs API, clock/env), side-effect boundaries, transaction/rollback behavior, and test matrix (core unit + adapter integration).
- Harden config cascade: stop conditions for parent walk, symlink/worktree safeguards, CLI to show effective config, and env-var precedence clarity.
- Secure MCP operations: optional ACLs, rate limits, redaction/allowlist, pagination/chunking for `get_context`, caching strategy, and clear write-conflict/error responses.
- Installer requirements: pinned ref/tag, checksum/signature verification, idempotent rerun, uninstall/verify commands, and offline/manual install instructions.
- Formalize Curation Levels: acceptance criteria per level, which validations warn vs fail, and how/when to promote `pending_curation`.
- Strengthen validation plan: define control arm, seeds, sample size, metrics (FPY, turns, elapsed time, cost), and publication/replication criteria.

## Open Questions
- Where will the approved plan live (path/status), and does it supersede prior kernels?
- How long will typed edges and `depends_on` coexist before deprecation?
- Will MCP serve only validated context (post-lint), and what is the policy when validation fails?***
