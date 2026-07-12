---
id: project-ontos-v4-7-1-hotfix-D.3-verdict
deliverable_id: project-ontos-v4-7-1-hotfix
phase: D.3
role: meta-consolidator
family: codex
families_consulted: [claude]
verdicts_consulted:
  - docs/reviews/project-ontos-v4-7-1-hotfix/D.1-claude-peer.md
  - docs/reviews/project-ontos-v4-7-1-hotfix/D.2-claude-product.md
consolidation_mode: provider_limited_fallback
provider_limited_fallback: true
strict_p3_gap: "The D.2 board is incomplete because Gemini, GLM, and wrapper promotion failed."
canonical_p3_evidence: false
fallback_authorization_ref: "Maintainer split directive in this task"
preserved_blocker_ids:
  - D1-FM-QUOTED-KEY-BOUNDARY
  - D1-PORTFOLIO-WAL-SNAPSHOT
status: completed
---

# Canonical Verdict — Project Ontos v4.7.1 Hotfix / D.3

> **⚠️ Provider-limited fallback artifact (warning-only, non-canonical P3 evidence).**
> Authored under `provider-limited-review-exception` per the maintainer split directive in this task.
> Strict-P3 gap: the D.2 board is incomplete because Gemini, GLM, and wrapper promotion failed.
> This artifact is NOT external-family review evidence and does NOT certify framework strict-P3 closure.

## Context header

- Baseline: `bf91b42f4eb5ba2ed6e0e3ea5e76d22ec6d7ec95`
- Implementation reviewed: `a71ac4a0d55ad86b8f9051f9c339bd1397ff4751`
- Post-fix implementation: `a0062ae8b6e8413f15e64259ec16d1c927d55328`
- Release boundary: behavior-preserving v4.7.1 hotfix; observable-contract changes remain in v5.0.0
- Authority: recommendation only; no merge, tag, publication, release, or issue closure

## Evidence inventory

| Phase | Family / role | Wrapper state | Evidence used |
|---|---|---|---|
| D.1 | Claude peer | completed and shape-valid | Direct full-suite run, exact quoted-key reproduction, exact SQLite/WAL reproduction |
| D.2 | Claude Product | substantive artifact, shape-invalid | Direct UX checks; findings are nonblocking and retained as advisory only |
| D.2 | Claude peer | no completed artifact | Timebox ended without a promotable artifact |
| D.2 | Gemini adversarial | provider failure | Empty artifact plus separate provider-policy stderr; not counted as review evidence |
| D.2 | GLM alignment | sandbox/permission failure | No artifact; not counted as review evidence |

The D.2 dispatch bundle does not pass `verify-family-dispatch.sh
--require-complete`. This verdict therefore adjudicates the valid D.1 artifact
and the clearly labeled advisory Product artifact under the maintainer-authorized
fallback. It is not strict-P3 canonical evidence.

## Preserved blockers

| Blocker ID | Finding | Evidence | Required closure |
|---|---|---|---|
| D1-FM-QUOTED-KEY-BOUNDARY | The format-preserving editor did not index quoted top-level keys. Updating a quoted target appended a duplicate; updating the preceding field could delete an untouched quoted key. | `direct-run`; `ontos/core/frontmatter_edit.py:25-31,301-340`; exact pre-fix reproductions in D.1 and orchestrator preflight | Recognize plain/single-quoted/double-quoted scalar keys, reject mixed duplicates, preserve quoted non-target boundaries, and compare the entire reparsed mapping with the expected mapping before returning. |
| D1-PORTFOLIO-WAL-SNAPSHOT | Per-workspace rebuild used a passive WAL checkpoint. A concurrent reader could leave committed rows only in WAL, while `immutable=1` readers indefinitely served the old main-db snapshot. | `direct-run`; `ontos/mcp/portfolio.py:463-478`; exact pre-fix WAL reproduction in D.1 and orchestrator preflight | Use a blocking truncating checkpoint for every rebuild, inspect the SQLITE_BUSY result, and prove an immutable reader observes the new snapshot after a transient concurrent reader. |

## Should-fix disposition

| Finding ID | Disposition | Rationale |
|---|---|---|
| D1-YAML-ANCHOR-OVERREFUSAL | deferred | The current behavior fails closed; narrowing anchor detection is not necessary to stop corruption and should use a parser-aware follow-up. |
| D1-IMMUTABLE-CONCURRENT-DB | deferred and tracked as residual risk | A truncating checkpoint closes the demonstrated persistent-WAL staleness gap. SQLite `immutable=1` still assumes the fixed-path database is not modified during a query; a fully sound solution needs versioned immutable snapshots or a different journal/locking design and exceeds this hotfix. |
| D2-LOG-DIR-RUNTIME-WARNING | deferred to v5/follow-up | Adding warning-envelope content changes observable command output; the split-history behavior is documented in the patch. |
| D2-UTF8-COPY-COMMAND | deferred | Existing recovery copy is actionable and the Product reviewer marked this nonblocking. |
| D2-LOG-HELP-COLLISION | deferred to v5/follow-up | Help text is observable CLI output; runtime refusal copy already explains the collision contract. |

## Contract and scope check

- Neither blocker requires schema 4.0, a new result object, an exit-code change,
  a CLI-flag reinterpretation, or a golden-baseline update.
- `ontos/ui/json_output.py`, the v5 command/graph paths, and tracked golden
  directories remain unchanged from `bf91b42`.
- `tests/mcp/test_portfolio.py` is added to the manifest scope because the
  preserved WAL blocker requires a runnable concurrency regression.

## Verdict

Needs Fixes

strict_p3_certified: false

Both preserved blockers are supported by direct reproductions and must be
closed in D.4. The evidence gap remains a lifecycle-certification blocker even
after the code fixes pass.
