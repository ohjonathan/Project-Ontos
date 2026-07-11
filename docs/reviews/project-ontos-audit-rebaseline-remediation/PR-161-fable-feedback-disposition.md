---
id: project-ontos-audit-rebaseline-remediation-pr-161-fable-feedback-disposition
type: review
status: completed
depends_on:
  - project-ontos-audit-rebaseline-remediation-D.5-orchestrator-status
---

# PR #161 Fable feedback disposition

This record pressure-tests Claude Fable 5 comment
[`4942697776`](https://github.com/ohjonathan/Project-Ontos/pull/161#issuecomment-4942697776)
against PR head `601591bfded32aae28c061dff5aacff791a95328` and base
`bf91b42f4eb5ba2ed6e0e3ea5e76d22ec6d7ec95`. It is a review disposition,
not a lifecycle receipt. The follow-up implementation and verification are
recorded below without reinterpreting prior lifecycle evidence.

The classifications below mean: **confirmed** (reproduced at the reviewed
head), **partially valid** (a narrower claim is proven), **obsolete** (already
superseded at that head), **unsupported** (the available evidence does not
establish it), and **out of scope** (not authorized for this PR follow-up).

## Claim-by-claim disposition

| Fable claim | Classification | Pressure-test result and disposition |
|---|---|---|
| A 19-agent workflow reproduced every candidate and independently re-verified it | unsupported | The comment does not attach the underlying agent transcripts or a mechanically checkable candidate register. Its concrete claims were re-derived independently below; the methodology claim itself is not release evidence. |
| “Strongest of the three audit PRs” | unsupported | This is a subjective comparison, not a reproducible repository property. The accompanying comparison with PR #160 was not used as a gate. |
| Zero blockers and zero majors | partially valid | No new major product defect was established by the comment, but PR #161 still has the declared `D4-INFRA-1` and `D5-INFRA-2` lifecycle/framework blockers. “Zero blockers” is valid only if narrowly limited to Fable's newly reported product findings. |
| The serializer P0 is genuinely fixed | confirmed | The named quoted, comma-bearing list, mapping-like, and hash-leading values survive semantic YAML round trips through the real dumper. This proves value preservation, not byte-for-byte preservation of the original frontmatter formatting. |
| Frontmatter parsing is consolidated in `ontos/io/yaml.py` | partially valid | The principal readers use the shared splitter and the old substring splits are gone. Pressure testing found that the reviewed head rejected whitespace-suffixed fences accepted by the base and required by audit `D3a-parsers-3`; focused positive and boundary-negative regressions now restore that contract. |
| The lifecycle is strict and complete through D.5 | partially valid | Fresh, hash-bound B.1, B.2, and D.2 boards verify `4/4` each. D.5 contains real attempts, but Gemini has no valid receipt, the active GLM promotion failed, the I3 fixes postdate the I2 verifier runs, and strict lifecycle verification fails. D.5 remains `review_pending`, not certified. |
| The PR body is honest | confirmed | The PR is a draft and explicitly says D.5 is pending, D.6 was not run, strict-P3 certification is not claimed, and the framework/provider gaps remain open. The summary phrase “through D.5” should be read as attempted through D.5, not completed. |
| 1. `patch_frontmatter_fields()` breaks id-less documents | confirmed | The failure is broader than the cited fail-soft commands: any caller patching a valid document whose ID is derived from its filename can reach unconditional ID validation. The reviewed default scope contained 166 id-less paths, including 10 with nonempty lifecycle frontmatter, so the claim that no real repository document omits `id` is false. Focused regressions now preserve filename-derived IDs while validating explicit or newly added IDs. |
| 2. New staged files ignore a restrictive umask | confirmed | `_stage_text` hard-codes `0o644` for a new file; under umask `0o077` that widens the result compared with normal creation semantics. A focused regression was reproduced and the new-file mode calculation was fixed while preserving existing-file modes. |
| 3. `link-check --json` changed line numbering and envelope shape | confirmed | The physical-file line numbers, top-level `result`, and schema `4.0` are intentional, version-signaled public contract changes. They require consumer migration awareness but are not a silent defect to revert in this follow-up. |
| 4. The hermeticity gate rejects local coverage artifacts | confirmed | A local coverage run can leave `.coverage` or `coverage.xml`, which the clean-tree gate treats as repository mutation. Those conventional local artifacts should be ignored; CI already redirects its artifacts to runner temporary storage. |
| 5. UTF-8 reads changed from replacement to strict decoding | partially valid | The strict-decoding behavior change is real and is being retained deliberately so corrupt documents fail visibly. The alleged stale adjacent comment was not reproduced as stated; the BOM comment does not promise replacement decoding. Contract tests/documentation, not a return to `errors='replace'`, are the justified response. |
| 6. The registry validator is 1,996 lines | confirmed | `wc -l` reports `1996`; local and live parity pass and its focused suite has 207 tests. Its size is a reasonable maintainability note, not evidence that the validator is theater or currently incorrect. Decomposition is deferred rather than mixed into this repair. |
| Symlink safety does not cover every repository writer | partially valid | The hardened no-follow/atomic substrate covers the scoped context and MCP mutation paths. Other legacy writers still use direct writes, so the global phrase “all writes are symlink-safe” would be too broad. Expanding every writer belongs to the remaining remediation programs, not this bounded feedback fix. |
| The PR's 602-path scope result lacks matching committed evidence | confirmed | The exact head count and scope pass were reproduced below. Earlier lifecycle artifacts record 559/578/594/598 because they bind earlier snapshots. This is a committed-evidence gap, not a scope failure; this section records the result plainly without inventing a receipt. |
| Existing CI hardening is sound | partially valid | The clean-tree gate, retirement of legacy injected tests, Windows boundary job, and non-editable smoke are sound. The reviewed workflow placed `runner.temp` in job-level `env`, where that context is unavailable; pushes failed before creating any job. The coverage-file environment is now step-scoped and regression-locked. |
| Coverage is still advisory | confirmed | The reviewed coverage step used `continue-on-error: true`. Direct measurements were 82.73% for the full/MCP suite and 70.33% without MCP; CI now gates at conservative floors of 82 and 70 respectively. |
| Coverage artifacts should be ignored | confirmed | Added `.coverage` and `coverage.xml` to the repository ignore contract and covered it with workflow/hermeticity regression tests. |
| The audit registry validator should run in CI | confirmed | The validator is the local registry/ledger/lease parity gate but was not invoked by `ci.yml`. A local, non-networked validation step is justified. Live GitHub parity remains a separately credentialed check. |
| The registry validator would itself prevent PR-body/scope-receipt drift | unsupported | It validates registry structure, evidence paths, leases, child-manifest parity, rendered ledger state, and optional GitHub issue parity. It does not validate the PR body, the current changed-path count, or this deliverable's receipt inventory. Those need their own evidence/gates. |
| Land all six findings as code changes | partially valid | Items 1, 2, and 4 justify fixes. Item 3 is an intentional versioned contract, item 5 retains strict decoding with clarified tests, and item 6 is a follow-up maintainability note. |
| Finish D.6 before dropping draft status | out of scope | D.6 is explicitly forbidden by the user for this run and cannot begin while D.5 and framework blockers remain. The PR must remain draft. |
| Split the PR into release slices now | out of scope | The branch intentionally reviews one integrated, snapshot-bound re-baseline spanning the v4.7.1/v4.8.0/v4.9.0 registry. Re-splitting now would invalidate review/evidence bindings and requires a separate maintainer decision. |

## Initial head scope proof

The following plain direct-run proof was captured before follow-up edits:

```text
base: bf91b42f4eb5ba2ed6e0e3ea5e76d22ec6d7ec95
head: 601591bfded32aae28c061dff5aacff791a95328
command: bash .llm-dev/framework/scripts/verify-changed-path-scope.sh --manifest manifests/project-ontos-audit-rebaseline-remediation.yaml --base bf91b42f4eb5ba2ed6e0e3ea5e76d22ec6d7ec95
result: verify-changed-path-scope: OK (602 changed path(s) within scope)
```

This proof is deliberately not represented as a strict-P3 receipt.

## Follow-up implementation

- Preserve filename-derived IDs when surgically editing id-less frontmatter;
  continue validating every explicit or newly added ID.
- Restore the shared parser's unindented `---` plus trailing horizontal
  whitespace fence contract without accepting embedded or indented markers.
- Keep invalid UTF-8 fail-closed, clarify the detection-versus-decoding policy,
  and cover both batch `parse_error` and direct-loader failure behavior.
- Let the operating-system umask determine new staged-file modes while
  preserving existing destination modes.
- Ignore conventional local coverage artifacts, gate measured coverage at 70%
  for the Python 3.9 non-MCP job and 82% for MCP-capable jobs, and run local
  audit-registry validation once in CI from a full-history checkout so its
  historical commit-provenance checks are meaningful. Keep `runner.temp`
  references step-scoped so workflow validation can resolve them.
- Document physical-file body-reference line numbers as a schema-v4 migration
  behavior. No broad legacy-writer symlink refactor was attempted.

## Final verification

| Check | Result |
|---|---|
| Focused frontmatter/loading/writer/CI/serializer/link diagnostics | PASS — `123 passed` |
| Cross-version help-parity regressions, Python 3.14 and 3.12 | PASS — `11 passed` on each interpreter; normalization is limited to stdlib-controlled usage wrapping, the Python 3.9 section label, and repeated alias metavars |
| Complete suite with coverage gate | PASS — `1739 passed, 1 warning`; `82.76%` coverage; required `82%` reached |
| Python 3.9 non-MCP coverage-floor calibration | PASS — `1442 passed`; `70.33%` measured at reviewed head; CI floor `70%` |
| Audit registry, local | PASS — 91 original + 9 revalidation findings |
| Audit registry, live GitHub parity | PASS — 91 original + 9 revalidation findings |
| llm-dev manifest conformance | PASS — `4/4` |
| Changed-path scope after follow-up | PASS — `605` paths from `bf91b42`, including exact `.gitignore` and session-log lease additions |
| `git diff --check bf91b42..HEAD` | PASS |
| First executable GitHub Actions matrix, run `29154665641` | DISCOVERY FAILURE — Python 3.10 completed with `1737 passed, 2 failed`; Python 3.9 also recorded the same presentation-only help-golden drift in `scaffold` before fail-fast cancellation. Windows 3.9/3.14 and non-editable smoke passed. The cross-version golden canonicalizer above is the focused follow-up; its head rerun is pending at this commit. |
| Strict lifecycle | EXPECTED BLOCK — exit `1`, `status=review_pending`; Gemini receipt missing and GLM/dispatch evidence invalid |
| Strict receipt-inventory schema | EXPECTED BLOCK — exit `1`, six v2.0.1 producer/schema mismatches (three Product roles, three OpenCode promotion sources) |

## Certification boundary

Follow-up code verification passes locally. The first executable remote matrix
exposed and reproduced cross-version `argparse` presentation drift in three
exact help snapshots; the narrow test-contract fix is included and its head
rerun is pending. `D4-INFRA-1` and `D5-INFRA-2` remain open, D.5 remains
`review_pending`, strict-P3 certification is not claimed, and D.6 has not been
run. No receipt or prior D.5 artifact is modified or reinterpreted by this
disposition.
