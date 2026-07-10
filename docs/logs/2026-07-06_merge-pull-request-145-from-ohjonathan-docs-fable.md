---
id: log_20260706_merge-pull-request-145-from-ohjonathan-docs-fable
type: log
status: active
event_type: update-llm-dev-framework-v2-0-0
source: cli
branch: main
created: 2026-07-06
concepts: [devops, workflow, testing, docs]
---

# Update llm-dev-framework to v2.0.0

## Goal

Pull the latest `llm-dev-framework` from GitHub and update Project-Ontos so the
repo-local wrapper can use the v2.0.0 command surface.

## Key Decisions

- Upgraded `.llm-dev/framework` from `v1.10.2` to `v2.0.0` using
  `scripts/llm-dev update --to latest`.
- Kept `.llm-dev/config.yaml` repo-relative and changed only
  `framework_ref: v2.0.0`.
- Refreshed `scripts/llm-dev` from the framework copy so commands such as
  `goal-card`, `capability assess`, `review-seats`, `gate-preflight`,
  `lint-artifact`, and the newer verification helpers are available.
- Added `.llm-dev/routes.yaml` via the v2 first-run route-profile setup for the
  existing `claude`, `codex`, and `gemini` families, with conservative
  read-only, provider-egress, no-shell execution risk defaults.

## Alternatives Considered

- Leaving route-profile setup for later would still leave the v2 wrapper usable,
  but adding the validated conservative profile now exercises the v2 adopter
  path and gives future route-planner work a repo-owned policy file.
- Running the installer from the in-repo framework checkout was rejected after it
  clobbered the source path; the framework checkout was restored from GitHub and
  subsequent setup used a temporary external clone.

## Impacts

- Existing v1 manifests remain schema-compatible under v2.0.0.
- The strict-P3 trust model is unchanged: route profile, capability, run-state,
  and goal-card metadata are operator aids, not lifecycle evidence.
- The repo now has a v2 route profile that can be edited by operators for pins,
  connector routes, or role/phase preferences.

## Testing

- `python3 -m ontos activate` returned `usable_with_warnings`; task-critical
  context was read directly.
- `scripts/llm-dev doctor` passed after the upgrade.
- `scripts/llm-dev update --to latest` now exits cleanly on the v2 wrapper.
- `bash .llm-dev/framework/scripts/verify-route-profile.sh .llm-dev/routes.yaml`
  passed schema and semantic validation.
- `scripts/llm-dev capability assess --mode fixture --max-models 2` passed as a
  smoke test; transient generated reports/raw data were removed afterward.
- `scripts/llm-dev goal-card verify --manifest
  manifests/project-ontos-v44-agentic-activation-resilience.yaml --surface plain`
  passed as a smoke test; the transient generated card was removed afterward.
- Manifest conformance passed for
  `project-ontos-audit-doctor-rce`,
  `project-ontos-github-issues-115-117`,
  `project-ontos-issue-119-cli-activate-json-warning-metadata`, and
  `project-ontos-v44-agentic-activation-resilience`.
- Manifest conformance failed for
  `project-ontos-audit-serializer-corruption` because the manifest has a codex
  Phase C / D.3 self-review overlap without `self_review_caveats[]`, and
  `anchor_parity_strict=true` while the spec lacks `## § 11` and `## § 18`
  headings.
