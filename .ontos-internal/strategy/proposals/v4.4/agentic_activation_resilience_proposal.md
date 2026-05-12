---
id: proposal_v44_agentic_activation_resilience
type: strategy
status: complete
depends_on:
  - ontos_agent_instructions
  - ontos_manual
---

# v4.4 Agentic Activation Resilience Proposal

## Problem

Agents increasingly enter Ontos projects through MCP rather than a human prompt that says "Ontos". GitHub issues #103, #111, and #112 describe the same failure class from three angles: activation can be skipped, large lifecycle repositories can flood agents with non-blocking warnings, and frontmatter enum failures are too imprecise to repair confidently. Issue #109 is import-path test debt that should close once local and CI full-suite evidence agree.

## Proposal

Ship v4.4 as an additive resilience release:

- Add `ontos activate` with best-effort status output: `usable`, `usable_with_warnings`, or `not_usable`.
- Add MCP `activate`, session activation state, and skipped-activation warnings on read-tool responses.
- Add MCP `session_end` as a typed wrapper over session logging.
- Add structured frontmatter diagnostics and conservative enum repair.
- Align `map`, `doctor`, `verify --all`, and repair scan exclusions.
- Reduce warning floods by grouping default map diagnostics and preserving full detail behind `--verbose`.
- Fix git worktree detection in `doctor`.

## Issue Mapping

| Issue | Treatment |
|-------|-----------|
| #103 | MCP `activate`, server instructions, skipped-read warning, CLI activation fallback |
| #111 | best-effort activation, grouped warning output, scan-scope consistency |
| #112 | structured diagnostics, `doctor --frontmatter`, enum repair |
| #109 | closure verification through local and CI full-suite evidence |

## Acceptance

The release is acceptable when targeted CLI/MCP tests pass, the full suite passes locally, the llm-dev manifest validates, and the final review evidence records any residual CI-only risk.
