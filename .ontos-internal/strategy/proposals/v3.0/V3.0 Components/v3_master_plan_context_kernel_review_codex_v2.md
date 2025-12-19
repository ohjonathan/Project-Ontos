---
id: v3_master_plan_context_kernel_review_codex_v2
type: strategy
status: draft
depends_on: [master_plan_v4]
---

# Review: Strategic Master Plan & Context Kernel v3.0.0 (Synthesized Architect Edition)

Source reviewed: `.ontos-internal/strategy/proposals/v3.0/v3_master_plan_context_kernel.md` (dated 2025-12-19).

## Findings
- **Path/status ambiguity:** Lives under proposals with no frontmatter/status and yet claims “Strategic Master Plan.” Destination path and graduation criteria are unstated, leaving source-of-truth unclear.
- **Master Tracker truncation:** v2.8 “Unified CLI (ontos.py)” row is cut mid-line (“`python3 ontos.py [init | log |`”), so intended commands are undefined.
- **Immutable history underspecified:** “Regenerate” directive lacks canonical sort/merge policy and CI assertion; parallel branches can still drift.
- **Typed edges vague:** Allowed vocab, validation rules, migration/fallback with `depends_on`, and query/context-selection semantics are not defined, risking free-form edge sprawl.
- **Schema versioning shallow:** `ontos_schema: 3.0` and `ontos.py migrate` are named without concrete mappings, idempotency, downgrade/backfill rules, or failure handling.
- **Functional-core boundary abstract:** SessionContext pattern is described, but injected services (fs/git/time/env), error model, and test strategy for MCP-safe purity are not spelled out.
- **Config cascade gaps:** Precedence, stop conditions on parent traversal, worktree/symlink handling, env-var overrides, and “print effective config” are missing; potential security footguns.
- **MCP protocol safety/perf:** No defaults for bind/auth/ACL, redaction rules, rate limits, pagination/chunking for `get_context`, or conflict policy for `log_session`.
- **Install bootstrap risk:** install.py is preferred over .sh, but checksum/pin/signature, idempotent rerun/uninstall, and offline/manual flow are not documented.
- **Curation Levels undefined:** Level 0/1/2 named, but acceptance criteria, validation severity (warn vs error), and upgrade path for `pending_curation` are unspecified.
- **Validation metrics thin:** SWE-bench plan lacks control definition, sample-size rationale, metrics beyond FPY/turns, and reproducibility details; risk of inconclusive claims.

## Suggestions
- Add frontmatter (id/type/status/depends_on) and declare destination path + graduation criteria; state if it supersedes earlier kernels.
- Fix the v2.8 CLI row and enumerate supported subcommands explicitly.
- Define deterministic ledger rules: canonical sort (timestamp + branch + filename), regenerate-only guidance, merge policy, and CI check asserting ledger == logs.
- Specify typed edge schema: allowed types + cardinality, validation errors, dual-write period with `depends_on`, query/context selection semantics, and a migration/auto-suggest tool.
- Flesh out `ontos.py migrate`: exact field transforms, dry-run, backups, idempotency, downgrade strategy, and behavior on partial failures.
- Lock down SessionContext contracts: required injected services (git API, fs API, clock, env), side-effect boundaries, error model, and test matrix (core unit + adapter integration).
- Harden config cascade: precedence (CLI > env > repo > user > defaults), parent traversal stop rules, worktree handling, symlink safeguards, and a “show-effective-config” command.
- Secure MCP defaults: loopback bind, optional auth/token, redaction allowlist, request size limits/pagination, cache strategy, and conflict policy for writes.
- Document install.py hygiene: pinned tag/commit, checksum/signature, idempotent rerun, uninstall/verify steps, and offline/manual installation path.
- Formalize Curation Levels: criteria per level, which validations warn vs fail, and the process to upgrade `pending_curation` items.
- Strengthen experiment design: define control arm, dataset/seed strategy, metrics (FPY, turns, elapsed time), sample size, and publication/replication plan.

## Open Questions
- Which schema version ships with the first PyPI release, and how will MCP handle mismatches (warn vs block)?
- Will typed edges fully replace `depends_on`, or run dual-write with deprecation timing?
- Does MCP serve only validated context (post-lint) or raw files on demand? What’s the policy when validation fails?
