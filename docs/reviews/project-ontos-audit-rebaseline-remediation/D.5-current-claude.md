---
id: audit-rb-D5-current-cv
deliverable_id: project-ontos-audit-rebaseline-remediation
role: verifier
family: claude
phase: D.5
evidence_mode: direct-run
canonical_verdict_consumed: docs/reviews/project-ontos-audit-rebaseline-remediation/D.3-verdict.md
fix_summary_consumed: docs/reviews/project-ontos-audit-rebaseline-remediation/D.4-fix-summary.md
addendum_consumed: docs/reviews/project-ontos-audit-rebaseline-remediation/D.4-current-head-addendum.md
target_commit: 388845c
clarification_artifacts: []
status: completed
verdict: Request Further Fixes
---

# Verification — project-ontos-audit-rebaseline-remediation / D.5 / claude

Target confirmed by `git rev-parse HEAD` = `388845cbd0cfc6ee8a9b2f61f7ebe5f14eff70a2`
(`direct-run`). Working-tree differences are lifecycle evidence only —
`Ontos_Context_Map.md`, `manifests/…yaml`, and
`docs/reviews/project-ontos-audit-rebaseline-remediation/**`. `git status
--porcelain -- ontos/ tests/ scripts/ .github/ pyproject.toml` returned `0`
lines before and after every probe (`direct-run`), so no product path was
dirtied by this verification.

All evidence below is my own in-session execution. No CI result and no prior
reviewer claim was converted into direct-run evidence; GitHub Actions run
`29155957357` is referenced by the addendum but is **not** relied on here.

## Per-finding verification — historical D.4 rows (D.3 canonical)

The D.3 preserved-blocker list is empty (`preserved_blocker_ids: []`). The six
canonical should-fix findings and the two loose-falsification findings are
verified at `388845c` against the tests named in `D.4-fix-summary.md`. Combined
run: `28 passed`, exit `0` (`direct-run`).

| Finding ID | Original failure reproduced? | Fix addresses it? | Regression test passes at `388845c`? | Evidence label |
|------------|------------------------------|-------------------|--------------------------------------|----------------|
| CAN-ACT-1 | Yes — reproduced in D.3 record | Yes | Yes — `test_activate_human_renders_incompatible_version_reason_once` | direct-run |
| CAN-ACT-2 | Yes — reproduced in D.3 record | Yes | Yes — `test_activate_json_renders_malformed_range_contract_once`, `test_eager_required_version_validation_preserves_typed_raw_detail` | direct-run |
| CAN-CP-1 | Yes — reproduced in D.3 record | Yes | Yes — `test_issue_158_control_plane_finding_is_checked_against_synthetic_owner`, `test_control_plane_finding_id_and_issue_158_are_reserved_as_a_pair` | direct-run |
| CAN-CP-2 | Yes — reproduced in D.3 record | Yes | Yes — `test_duplicate_lease_lists_fail_even_when_o5_is_synchronized` | direct-run |
| CAN-CP-3 | Yes — reproduced in D.3 record | Yes | Yes — `test_malformed_registry_yaml_returns_exit_one_never_two`, `test_malformed_child_manifest_yaml_returns_exit_one_never_two`, `test_unexpected_validator_runtime_error_remains_exit_two` | direct-run |
| CAN-ID-1 | Yes — reproduced in D.3 record | Yes | Yes — `test_rename_invalid_id_is_rejected_before_project_discovery`, `test_rename_document_rejects_invalid_id_before_preflight` | direct-run |
| LF-ID-1 | Yes — per D.4 summary | Yes | Yes — `test_rename_yaml_like_ids_remain_strings_in_all_frontmatter_shapes` | direct-run |
| LF-CP-1 | Yes — per D.4 summary | Yes | Yes — `test_program_identity_collision_fails_when_findings_and_o4_are_synchronized` | direct-run |

Command:

```bash
./.venv/bin/python -B -m pytest -q --cache-clear <13 named node ids>
# 28 passed — exit 0
```

## Per-finding verification — current-head addendum rows (`859ecf7..388845c`)

Each row was verified with the canonical loader-swap pattern: extract the
pre-fix module from `859ecf7`, run the regression with `-B` +
`--cache-clear` (bytecode-cache invariant), then `git checkout --` to restore
and re-run. Every swap was restored; the post-swap product dirty count is `0`.

| Row | Regression test fails pre-fix (`859ecf7`)? | Passes post-fix (`388845c`)? | Evidence label |
|-----|--------------------------------------------|------------------------------|----------------|
| PR161-IDLESS | Yes — exit `1`, `1 failed, 13 passed` with `ontos/core/frontmatter_edit.py` swapped | Yes | direct-run |
| PR161-UMASK | Yes — exit `1`, `2 failed, 51 passed` with `ontos/core/context.py` swapped | Yes | direct-run |
| PR161-FENCE | Yes — exit `1`, `1 failed, 3 passed` with `ontos/io/yaml.py` swapped, **against `tests/core/test_frontmatter_edit_pipeline.py`, not the file the addendum cites** (see FW-3) | Yes — `4 passed` | direct-run |
| PR161-COVERAGE | Yes — exit `1`, `3 failed, 7 passed` with `.github/workflows/ci.yml` + `.gitignore` swapped | Yes — `10 passed` | direct-run |
| PR161-UTF8 | **No — and correctly so.** The `859ecf7..388845c` change to `ontos/io/files.py` is comment-only; `errors='strict'` was already in force. The two new tests are characterization tests locking existing behavior, exactly as the row itself claims ("Direct decoding **remains** strict"). Pre-fix pass is expected, not a coverage gap. | Yes | direct-run |
| PR161-PARITY | Yes — reproduced cross-version. On a purpose-built **Python 3.12.13** venv the pre-fix tests fail exit `1` (`2 failed, 8 passed`: `test_query_help_parity`, `test_verify_help_parity`); at `388845c` the same interpreter returns `11 passed`. | Yes — `11 passed` on 3.12.13 and on 3.14.6 | direct-run |

The PR161-PARITY row is the only one whose failure mode is invisible on the
default interpreter (3.14.6), so I built an isolated 3.12 environment outside
the repository to reproduce it honestly rather than accept the addendum's
assertion. The `tests/mcp/test_context_map.py` timestamp race is timing-
dependent under slow coverage runs; I confirmed the test passes at head on both
interpreters but did **not** reproduce the original race, so that specific
sub-claim is `static-inspection`, not direct-run.

Addendum focused set, all rows together:

```bash
./.venv/bin/python -B -m pytest -q --cache-clear \
  tests/core/test_frontmatter_edit_pipeline.py tests/test_session_context.py \
  tests/test_document_loading_contract_a1.py tests/test_ci_release_workflows.py \
  tests/test_test_isolation.py tests/commands/test_query_parity.py \
  tests/commands/test_verify_parity.py tests/commands/test_scaffold_parity.py \
  tests/mcp/test_context_map.py
# 104 passed — exit 0
```

## Regression check

| Smoke check | Command | Result | Evidence |
|-------------|---------|--------|----------|
| Complete suite | `./.venv/bin/python -B -m pytest -q tests/` | PASS — `1740 passed, 1 warning`, exit `0` | direct-run |
| Addendum focused set | see above | PASS — `104 passed`, exit `0` | direct-run |
| D.4 named regressions | see above | PASS — `28 passed`, exit `0` | direct-run |
| Registry validation, local | `./.venv/bin/python scripts/validate-audit-remediation-registry.py` | PASS — exit `0`; 91 original (P0=1, P1=27, P2=63) + 9 revalidation | direct-run |
| Registry parity, live GitHub | `… --require-external-parity` | PASS — exit `0`; `mode: local+external`; 91 + 9 | direct-run |
| Changed-path scope | `verify-changed-path-scope.sh --base bf91b42…` | PASS — exit `0`, `OK (624 changed path(s) within scope)` | direct-run |
| Manifest conformance | `scripts/llm-dev verify manifests/…yaml` | PASS — exit `0`, `PASSED manifest-conformance (4/4)` | direct-run |
| Whitespace/conflict gate | `git diff --check bf91b42..388845c` | PASS — exit `0`, no output | direct-run |

The scope count is `624`, above the `605` the disposition recorded, because
that receipt bound an earlier snapshot and lifecycle evidence has landed since.
The gate itself passes; the delta is evidence-binding drift, not a scope breach.

## Scope-lock check

- Paths touched outside allowed set: **none**. `verify-changed-path-scope.sh`
  returned `OK` for all 624 changed paths from `bf91b42` (`direct-run`).
- The `859ecf7..388845c` diff touches `ontos/` (4 files), `.github/workflows/ci.yml`,
  `.gitignore`, `tests/`, and lifecycle documentation. No forbidden path, no
  undeclared spec deviation.
- Cardinality: registry remains 91 original + 9 revalidation findings
  (`direct-run`).

## Framework findings (both preserved — not waived)

Both defects declared by D.4 and the addendum are **independently reproduced at
`388845c`**. They are framework/lifecycle defects, not product defects.

| ID | Finding | Evidence (direct-run) | Required further action |
|----|---------|-----------------------|-------------------------|
| D4-INFRA-1 | EH-15-A cannot honestly register adopter-local regression fixtures, and its manifest path **fails open**. | Probe 1 — `verify-fix-summary-regressions.sh --manifest "$PWD/manifests/…yaml"` returns **exit `0`**: `OK (no D.4 fix-summary exists at docs/reviews/…/D.4-fix-summary.md)` — while that exact file **is git-tracked and present**. A false green. Probe 2 — the same script invoked on the summary path returns **exit `1`** with 16 diagnostics claiming every fixture `does not exist`; I confirmed all 8 cited fixtures are `git ls-files`-tracked in the adopter root. The script resolves fixtures and `scripts/verify-all.sh` only under `.llm-dev/framework`. | Upstream framework support for an explicit adopter root + adopter-owned runnable-fixture registry, then a pinned framework upgrade and a fresh D.4/D.5. Must not be closed by citing an unrelated framework fixture or editing the framework checkout. |
| D5-INFRA-2 | The pinned framework's **own receipt schema and its own lifecycle verifier disagree**, and no framework command applies the schema to this deliverable's inventory. | Applying `.llm-dev/framework/manifest/lifecycle-receipt-inventory.schema.yaml` to the manifest-declared inventory yields **exit `1`, exactly 6 errors**: three `role: 'product' is not one of ['peer','alignment','adversarial','verifier']` (receipts 2, 5, 10) and three `artifact_source: 'opencode_written_file_promoted' is not one of [...]` (receipts 3, 6, 9). Both rejected values are **framework-generated**: `templates/19-review-board-product.md:123` mandates `role: product`, and `scripts/verify-family-dispatch.sh:2815-2819` calls `opencode_written_file_promoted` "a legitimate wrapper" value. `verify-schema.sh` feeds the receipt schema only its own bundled fixtures (line 18 + 53-66), never `lifecycle_receipt_inventory_path`; `verify-lifecycle.sh` parses the inventory YAML directly and its own comment (lines 1304-1306) concedes it runs "without re-running check-jsonschema." | Reconcile the receipt-inventory schema with the roles and artifact sources the framework's own templates and dispatch tooling emit, and make `verify-lifecycle` actually apply the schema. Until then a user-facing deliverable running the framework-mandated Product board cannot produce a schema-valid receipt. |
| FW-3 (new, minor) | The D.4 current-head addendum **mis-cites the PR161-FENCE regression location**. | The addendum's PR161-FENCE row names `tests/test_document_loading_contract_a1.py`. That file contains no fence regression; swapping `ontos/io/yaml.py` to `859ecf7` leaves it at `14 passed`, exit `0`. The real regressions are `tests/core/test_frontmatter_edit_pipeline.py:44` (`test_frontmatter_fences_accept_trailing_horizontal_whitespace`) and `:70` (`test_frontmatter_fences_remain_line_delimited_and_unindented`), which **do** fail pre-fix. The fix is real and covered; only the citation is wrong. | Correct the PR161-FENCE row's focused-evidence citation. Documentation-only; no code change. |

### Lifecycle receipt state (side-check)

The manifest declares `lifecycle_receipt_inventory_path` at a `schema_version: 1`
inventory with no `orchestrator_artifacts[]`, so Template 15's v3 self-receipting
side-validation contract does not apply here (`direct-run`). For completeness:

```bash
scripts/llm-dev verify-lifecycle manifests/…yaml
# exit 1 — status=review_pending
#   missing-receipt: phase=D.5 role=verifier family=gemini
#   route-redaction / dispatch-entry-not-found: ('D.5','verifier','glm')
#   dispatch-verify-failed: ('D.5','verifier','claude')

scripts/llm-dev verify-lifecycle manifests/…yaml --mode provider-limited-fallback
# exit 1 — status=provider_limited_fallback_incomplete
#   fallback-mode-requires-exception: manifest declares no
#   provider_limited_review_exception / p3_exception
```

These failures bind the **prior** D.5 round's receipts, which the current round
supersedes. I record them as observed state; I do not treat them as resolved,
and this artifact is not itself a receipt.

## Verdict

Request changes

The product is sound at `388845c` and I say so plainly: every one of the six
canonical D.3 should-fix findings, both loose-falsification findings, and all
six current-head addendum rows are verified by my own direct execution. The
complete suite is `1740 passed`, registry parity passes locally **and** against
live GitHub, changed-path scope is `OK` at 624 paths, manifest conformance is
`4/4`, and the whitespace gate is clean. Every regression test that should fail
against pre-fix code does fail against pre-fix code — including the cross-version
help-parity drift, which I reproduced on a separate Python 3.12 interpreter
rather than take on trust.

I am nevertheless required to withhold approval, because both framework defects
survive at this exact target and I reproduced both myself. D4-INFRA-1 is worse
than "unavailable": its manifest path returns **exit 0 while the fix summary it
claims is absent is sitting in the tree**, which is a fail-open gate that would
silently manufacture closure. D5-INFRA-2 is a genuine self-contradiction in the
pinned framework — the schema rejects the very `role: product` and
`opencode_written_file_promoted` values the framework's own template and dispatch
tooling produce, and no framework command ever applies that schema to this
deliverable's inventory, so the disagreement is latent rather than caught. Neither
is an adopter error and neither can be closed by any action inside this
repository; both must be preserved as required further action. FW-3 is a minor
documentation correction to the addendum's own evidence citation.

Scope note: this verdict certifies neither D.6, strict-P3 closure, merge, tag,
nor release, and it makes no claim about any of them.

## If "Request changes"

| Finding | Evidence | Required further action |
|---------|----------|--------------------------|
| D4-INFRA-1 | direct-run — probe 1 exit `0` fail-open on a present, tracked fix summary; probe 2 exit `1`, 16 diagnostics against 8 tracked fixtures | Upstream adopter-root + adopter fixture-registry support; pinned framework upgrade; fresh D.4/D.5. Do not waive. |
| D5-INFRA-2 | direct-run — inventory vs. framework receipt schema: exit `1`, 6 errors, all on framework-emitted values; `verify-lifecycle` never applies the schema | Reconcile the receipt schema with framework-emitted roles/artifact sources and make the lifecycle verifier apply it. Do not waive. |
| FW-3 | direct-run — pre-fix swap of `ontos/io/yaml.py` leaves the cited file at `14 passed`; the real fence regressions live in `tests/core/test_frontmatter_edit_pipeline.py:44,70` | Correct the PR161-FENCE focused-evidence citation in the D.4 current-head addendum. |
