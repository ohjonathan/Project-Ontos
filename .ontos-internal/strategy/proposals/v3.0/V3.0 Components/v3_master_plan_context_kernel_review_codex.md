---
id: v3_master_plan_context_kernel_review_codex
type: strategy
status: draft
depends_on: [master_plan_v4]
---

# Review: Strategic Master Plan & Context Kernel (v3.0 path, labeled v2.2.0)

## Scope
Architectural review of `.ontos-internal/strategy/proposals/v3.0/v3_master_plan_context_kernel.md` (Gemini-generated). Focus: correctness, risks, and readiness to graduate as the master plan.

## Findings
- **Identity/version drift:** File claims v3 master plan but version says 2.2.0 and lives under proposals. Save-path instructions conflict (`docs/strategy/…`). Source-of-truth ambiguous; graduation path undefined.
- **V2/V3 compatibility gap:** V3 package + MCP server assume stable data schema; no compatibility matrix, migration tooling, or pinning strategy. High risk of agents mixing old repo data with new package logic.
- **V2.8 refactor underspecified:** Splitting “logic” vs “ui” ignores shared mutable state (git status, fs writes, temp paths, config resolution). Without pure core boundaries and explicit I/O adapters, MCP/server reuse will stay brittle.
- **Librarian’s Wager lacks guardrails:** Manual tagging burden may spike on large repos or frequent commits; no mitigation (batch assists, heuristics, thresholds). Adoption risk before V3 relief.
- **Install.sh risks:** curl|bash bootstrap has no checksum/signature, ref pin, or idempotency story. Divergence from future PyPI flow likely; supply-chain risk unaddressed.
- **Typed edges undefined:** Edge vocab, validation, and back-compat with `depends_on` are unspecified. Free-form use would erode determinism and automated reasoning.
- **Immutable ledger hand-wavy:** “Regenerate, don’t append” is right, but determinism, ordering, and merge policy are not defined; parallel branches may still collide.

## Improvements Suggested
- **Clarify identity and lifecycle:** Pick a single version, state status (draft/proposal), and define graduation target path + status change. Note supersedes/replaces if it obsoletes earlier kernels.
- **Define V3 compatibility contract:** Publish schema versioning, min/max supported package versions, and a migration command (`ontos migrate --to X.Y --dry-run`). Have MCP advertise supported schema and refuse mismatches.
- **V2.8 architecture target:** Pure core consuming an injected context (config, git ops, fs ops), stateless log-construction functions, and I/O boundaries for UI/CLI. Add tests around the pure core to guarantee MCP-safe behavior.
- **Friction mitigation:** In V2.9 scaffolding, add semi-automated suggestions (depends_on from tree/concepts), batch tagging, and a “triage” mode requiring minimal metadata for small diffs.
- **Secure/install hygiene:** Provide checksum/signature and tag pin for install.sh; document idempotent re-run/uninstall; add verify step that asserts copied files match the published tag. Keep an offline/manual path.
- **Typed edge rollout plan:** Enumerate allowed types + cardinality, validation errors, and mapping to queries/context selection. Supply a migration/auto-suggest tool while retaining `depends_on` as fallback.
- **Deterministic ledger rules:** Define canonical sort (timestamp + branch + filename), stable render format, and merge guidance (regenerate from logs, no hand edits). Add CI check to assert ledger == logs.

## Additional Considerations
- **Security/privacy:** MCP server defaults should be local-only with auth/ACL options and redaction rules before serving sensitive docs to agents.
- **Performance:** Plan for rate limits and caching; support per-ID fetch to avoid dumping the full graph to agents.
- **Observability:** Track curation load (tags per file, stale counts, log lag) to validate the Librarian’s Wager ROI and trigger “maintain” nudges.
- **Backward compatibility:** Alias old scripts to `ontos.py` with deprecation notices during V2.8 rollout to avoid breaking existing users.
