---
id: project-ontos-github-issues-115-117-triage-verdict
type: review
deliverable_id: project-ontos-github-issues-115-117
phase: "-A.triage"
role: triage-verdict
family: codex
triage_report: docs/reviews/project-ontos-github-issues-115-117/pre-a-triage-report.md
status: complete
---

# Triage Verdict — project-ontos-github-issues-115-117

## Exit verdict

**Proceed to Phase A with approved scope.**

## Scope lock

| # | Issue | Disposition | Phase A scope-lock fragment |
|---|---|---|---|
| 115 | MCP `get_context_bundle` returns schema-invalid `_ontos_warning` before activate | In-Scope | MCP schema-safe pre-activate warning channel |
| 116 | Document MCP host reload requirement after pipx upgrade | In-Scope | MCP host reload documentation |
| 117 | Activation `usable_with_warnings`: false-positive `depends_on`, anonymous orphan warnings, 11k spurious body refs, overly narrow type/status schema | In-Scope | Activation diagnostic + link-check signal hardening + doctor severity alignment |

## Phase A author

`codex` per `manifests/project-ontos-github-issues-115-117.yaml`
`model_assignments[-A.triage]` continuing into `model_assignments[A]`.

## Next gate

`scripts/llm-dev verify manifests/project-ontos-github-issues-115-117.yaml` and
`bash .llm-dev/framework/scripts/verify-pre-a.sh manifests/project-ontos-github-issues-115-117.yaml`
both PASS as of this verdict (re-run before Phase A dispatch is acceptable;
no manifest mutation expected between triage and Phase A).

## Halt conditions still active

- If a new open issue appears against `ohjonathan/Project-Ontos` before Phase A spec land, the operator triages it against this manifest (expand scope) or opens a parallel deliverable.
- If, during Phase A or Phase C, direct-run evidence shows that an issue is invalid or already fixed in the current `ontos/` source tree, demote the affected finding to `Rejected` and re-emit this verdict.

No such conditions apply at exit of Pre-A.
