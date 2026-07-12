---
id: project-ontos-v4-7-1-hotfix-B.3-verdict
deliverable_id: project-ontos-v4-7-1-hotfix
phase: B.3
role: meta-consolidator
family: codex
families_consulted: [claude, glm]
verdicts_consulted:
  - docs/reviews/project-ontos-v4-7-1-hotfix/B.1-claude-adversarial-r2.md
  - docs/reviews/project-ontos-v4-7-1-hotfix/B.1-glm-peer-r2.md
  - docs/reviews/project-ontos-v4-7-1-hotfix/B.1-claude-product-r2.md
consolidation_mode: external
preserved_blocker_ids: []
status: completed
---

# Canonical Verdict — Project Ontos v4.7.1 Hotfix / B.3

## Context header

- Baseline: `bf91b42f4eb5ba2ed6e0e3ea5e76d22ec6d7ec95`
- Initial implementation reviewed: `e33a31d0c0040de9afa1f8efe22246c798534edd`
- Release boundary: observable-contract patch split, not audit-program tags
- Authority: recommendation only; no merge, tag, publication, or release

## Family verdict table

| Round | Family | Role | Verdict | Disposition |
|---|---|---|---|---|
| B.1 | Claude | adversarial | Request changes | All confirmed claims incorporated into the revised spec and Phase C worktree |
| B.1 | GLM | peer | Approve | Clean-tree observation retained as a mechanical gate |
| B.1 | Claude | Product | Request changes | Legacy log configuration, recovery copy, and workflow guidance incorporated |
| B.1 | Gemini | alignment | no artifact | Direct and AGY retries failed; provider-policy evidence preserved |
| B.2 | Claude | alignment/Product | no artifact | Wrapper recorded substantive stdout but did not promote an artifact |
| B.2 | GLM | adversarial | timed out | Terminated at the declared six-minute bound; failed capture preserved |
| B.2 | Gemini | peer | no artifact | Direct retry reproduced the retired-client provider-policy failure |

## Preserved blockers

None against proceeding to Phase C reconciliation. The B.1 implementation
findings are concrete and have accepted remedies. The missing B.2/Gemini
evidence is a lifecycle-certification blocker, not an unresolved product-design
choice; it remains preserved for the provider-limited terminal status.

## Accepted B.1 findings

1. Validate only explicit `id:` values. Preserve filename-derived fallback IDs
   verbatim so spaces, leading underscores, and Unicode do not disappear.
2. Preserve the public `dump_yaml` sorted-key default; callers that require
   insertion order opt out explicitly.
3. Preserve exception field immutability and hashing while permitting Python
   3.14 `BaseException` traceback metadata.
4. Preserve project-local legacy `LOGS_DIR` precedence and add modern
   `[paths].logs_dir` only when no legacy override exists.
5. Surface malformed UTF-8 mutation refusals as exit 1 / existing
   `E_COMMAND_FAILED`, with path, recovery step, and byte-unchanged tests.
6. Reuse `E_FILE_EXISTS` for log collisions and give unsafe log-directory
   failures actionable configuration copy.
7. Replace bare or mis-specified session-log guidance with a unique
   `--title`; do not add overwrite, force, or auto-suffix behavior.
8. Keep general read loading lenient, schema-3.4 envelopes and goldens at the
   baseline, and all contract-changing work in v5.0.0.

## Contradictions

The original spec simultaneously required strict ID validation and promised no
visible-document change. The resolution is explicit-ID validation plus the
historical filename fallback. The Product concern about outside-workspace logs
does not override the maintainer-authorized safety rejection; only its recovery
copy changes.

## Required Phase C evidence

- Focused serializer, filename fallback, mutation UTF-8, log compatibility,
  transaction, locking, MCP read-only, and inherited doctor tests.
- Full suite from a clean committed snapshot with identical pre/post porcelain.
- Exact source parity for the schema-3.4 envelope, v5-only commands/graph/MCP
  schemas, and tracked golden baselines.
- Manifest scope from the baseline SHA, whitespace checks, and honest lifecycle
  verification output.

## Verdict

Approve

Proceed to Phase C reconciliation with the eight accepted actions above. This
is not strict-P3 certification and does not authorize D.6 or release actions.
