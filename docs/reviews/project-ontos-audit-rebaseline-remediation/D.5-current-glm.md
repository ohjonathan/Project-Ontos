---
id: audit-rb-D5-current-glv
deliverable_id: project-ontos-audit-rebaseline-remediation
role: verifier
family: glm
phase: D.5
evidence_mode: direct-run
canonical_verdict_consumed: docs/reviews/project-ontos-audit-rebaseline-remediation/D.3-verdict.md
fix_summary_consumed: docs/reviews/project-ontos-audit-rebaseline-remediation/D.4-fix-summary.md
clarification_artifacts: []
status: completed
verdict: Request Further Fixes
---

# Verification — project-ontos-audit-rebaseline-remediation / D.5 / glm

Routed through the attested Neuralwatt OpenCode GLM-5.2 profile (direct-run
evidence cap, attested-third-party trust tier). The immediately preceding GLM
capture executed every requested check at exact product head `388845c`; this
artifact records those findings as the verifier receipt. No test, EH-15-A
probe, lifecycle script, or broad inspection was re-run for this write; only
git state and diff scope were re-confirmed directly here.

The product code passes. Every historical D.4 should-fix row is independently
reproduced broken pre-fix and closed post-fix, and every current-head addendum
row passes at `388845c`. Two framework defects remain open, so the canonical
verdict is `Request changes`: the fail-open EH-15-A gate (D4-INFRA-1) and the
strict lifecycle `review_pending` state with receipt-inventory schema gaps
(D5-INFRA-2). Receipts were not waived or repaired manually.

## Environment and snapshots

- Exact product head: `388845c` (branch `codex/audit-rebaseline-remediation-lifecycle`).
- Pre-fix implementation: `aa41c39`. Post-fix functional snapshot I2: `311b60b`.
- I3 loose-falsification close: `859ecf7`. Scope base: `bf91b42`.
- Historical should-fix rows were verified with the canonical loader-swap
  pattern against two orchestrator-prepared, in-repo snapshots (no external git
  access): a post-fix snapshot and a pre-fix snapshot whose only divergence from
  post-fix is the five target implementation files restored from `aa41c39`
  (`ontos/commands/activate.py`, `ontos/core/config.py`,
  `ontos/commands/rename.py`, `ontos/mcp/rename_tool.py`,
  `scripts/validate-audit-remediation-registry.py`). Both snapshots share one
  interpreter (`../bin/python`, Python 3.14.6) and the SAME post-fix test files,
  so `ontos.__file__` resolves under whichever snapshot is under test — the
  five-file restore genuinely takes effect. Import-origin was confirmed before
  each run (post markers present / pre markers absent).

### pytest flag discipline

Every focused snapshot invocation used `-B` plus `--cache-clear` (never
combined with `-p no:cacheprovider`, which removes the owning plugin and
rejects `--cache-clear`). The current-head focused and full runs used
`-q -p no:cacheprovider` per the manifest smoke command.

## Target and tree confirmation (direct-run, this session)

| Precondition | Command | Result | Evidence |
|---|---|---|---|
| HEAD is the exact product target | `git rev-parse HEAD` | `388845c` (short) | direct-run |
| Product/test working tree clean | `git status --porcelain -- ontos tests scripts` | empty; exit 0 | direct-run |
| Whitespace clean since scope base | `git diff --check bf91b42..388845c` | exit 0 | direct-run |
| Committed scope path count | `git diff --name-only bf91b42..388845c \| wc -l` | 605 | direct-run |

The only working-tree modifications are `Ontos_Context_Map.md` and the
deliverable manifest (both within `scope.allowed_paths`), plus untracked
review/prompt/raw files under the `docs/reviews/project-ontos-audit-rebaseline-remediation/**`
glob. No product or test path has uncommitted changes.

## Per-blocker verification table — historical D.4 should-fix

The D.3 preserved-blocker list is empty (`preserved_blocker_ids: []`). The
empty blocker list does not waive the six canonical should-fix findings; each
was directly reproduced pre-fix and closed post-fix.

| Blocker ID | Original failure reproduced? | Fix addresses it? | Regression test fails pre-fix? | Regression test passes post-fix? | Evidence label |
|---|---|---|---|---|---|
| CAN-ACT-1 | Yes — human `not_usable` output rendered zero `Reason:` lines | Yes — one nonempty `Reason:` line now rendered | Yes — exit 1, 4 failed | Yes — exit 0, 4 passed | direct-run |
| CAN-ACT-2 | Yes — malformed-range reason began `Config error:` not the `Invalid [ontos].required_version:` prefix/anchor | Yes — typed category routed through one canonical formatter | Yes — exit 1, 4 failed | Yes — exit 0, 4 passed | direct-run |
| CAN-CP-1 | Yes — issue-158 root/scope mutations not detected; owner-parity fragments never emitted | Yes — synthetic owner + reserved pairing; root/scope checked through same owner path | Yes — exit 1, 8 failed | Yes — exit 0, 8 passed | direct-run |
| CAN-CP-2 | Yes — duplicate lease `programs`/`order` not rejected under synchronized O5 | Yes — duplicates rejected before set conversion / O5 comparison | Yes — exit 1, 8 failed | Yes — exit 0, 8 passed | direct-run |
| CAN-CP-3 | Yes — malformed registry + both child YAMLs returned exit 2/`ERROR` not exit 1/`FAILED` | Yes — YAML syntax/read/decode failures become typed control-plane failures, exit 1 | Yes — exit 1, 8 failed | Yes — exit 0, 8 passed | direct-run |
| CAN-ID-1 | Yes — incl. invalid same-ID false-green (exit 0/`nothing_to_do`); MCP preflight ran before validation | Yes — both operands validated with `validate_document_id` before no-op/preflight | Yes — exit 1, 24 failed | Yes — exit 0, 24 passed | direct-run |

Selection (file-level, by finding ID):

- Group 1 — CAN-ACT-1 / CAN-ACT-2: `tests/commands/test_agentic_activation_resilience.py`
  (post: 4 passed; pre: 4 failed).
- Group 2 — CAN-CP-1 / CAN-CP-2 / CAN-CP-3:
  `tests/test_audit_remediation_registry_validator.py` (post: 8 passed; pre: 8
  failed).
- Group 3 — CAN-ID-1: `tests/commands/test_rename.py` +
  `tests/mcp/test_rename_document.py` (post: 24 passed; pre: 24 failed).

```bash
# post-fix (expect pass) and pre-fix (expect nonzero), per group
cd <snapshot> && ../bin/python -B -m pytest <test-file> --cache-clear -v
```

Pre-fix behavioral evidence captured: CAN-ACT-1 zero `Reason:` lines
(`assert 0 == 1`); CAN-ACT-2 JSON reason `"Config error: ..."` missing the
mandated prefix/anchor; CAN-CP-1/2 expected owner/duplicate diagnostics absent
while mutations passed through; CAN-CP-3 `assert 2 == 1` on malformed registry
+ both child YAMLs; CAN-ID-1 invalid old ID returned `old_id_not_found` (not
`invalid_old_id`), invalid new ID used regex copy, invalid same-ID returned
exit 0/`nothing_to_do` (the false-green), and MCP preflight ran before ID
validation. Each pre-fix run exited nonzero; each post-fix run exited 0.

### Loose-falsification findings (LF-ID-1, LF-CP-1)

The D.4 fix summary also closes two post-D.5 loose-falsification findings at
I3 `859ecf7`: LF-ID-1 (unquoted rename replacements now use the canonical
PyYAML-backed serializer so YAML-like IDs reload as exact strings) and LF-CP-1
(program IDs and roots share one normalized ownership namespace including the
synthetic issue-158 owner before O4 consumers run). Both regression suites are
part of the full test collection and PASS at `388845c` within the 1740-passed
full run (file refs: `tests/commands/test_rename.py`,
`tests/test_audit_remediation_registry_validator.py`).

## Current-head addendum verification table — PR #161

Verified at exact head `388845c` (addendum advances the target from I3
`859ecf7`; the `cdf904f..388845c` PR-feedback series is green in CI run
`29155957357` per the addendum). The addendum does not resolve D4-INFRA-1 or
D5-INFRA-2.

| Addendum ID | Current-head behavior verified | Focused evidence file(s) | Result at 388845c | Evidence label |
|---|---|---|---|---|
| PR161-IDLESS | filename-derived IDs preserved; only explicit/newly added IDs validated | `tests/core/test_frontmatter_edit_pipeline.py` | PASS | direct-run |
| PR161-UMASK | new staged files use `0o666 & ~umask`; existing destination modes preserved | `tests/test_session_context.py` | PASS | direct-run |
| PR161-FENCE | splitter accepts only unindented `---` (+ trailing horizontal whitespace) | `tests/test_document_loading_contract_a1.py` | PASS | direct-run |
| PR161-COVERAGE | local coverage artifacts ignored; CI floors block; registry runs in CI; Codecov downloads stay outside checkout | `tests/test_ci_release_workflows.py`, `tests/test_test_isolation.py` | PASS | direct-run |
| PR161-UTF8 | direct decoding remains strict; batch loading reports invalid UTF-8 as `parse_error` | `tests/test_document_loading_contract_a1.py` | PASS | direct-run |
| PR161-PARITY | CLI help parity normalizes only interpreter-controlled rendering; map alias parity ignores only declared volatile timestamps | `tests/commands/test_query_parity.py`, `tests/commands/test_verify_parity.py`, `tests/commands/test_scaffold_parity.py`, `tests/mcp/test_context_map.py` | PASS | direct-run |

```bash
# focused current-head (6 addendum files)
.venv/bin/python -m pytest tests/core/test_frontmatter_edit_pipeline.py \
  tests/test_session_context.py tests/test_document_loading_contract_a1.py \
  tests/test_ci_release_workflows.py tests/test_test_isolation.py \
  tests/commands/test_query_parity.py tests/commands/test_verify_parity.py \
  tests/commands/test_scaffold_parity.py tests/mcp/test_context_map.py \
  -p no:cacheprovider -q
# → 104 passed, exit 0

# complete suite
.venv/bin/python -m pytest tests/ -q -p no:cacheprovider
# → 1740 passed, 1 deprecation warning, exit 0
```

## Regression check

| Smoke check | Result | Evidence |
|---|---|---|
| Focused current-head (6 addendum files) | PASS — 104 passed, exit 0 | direct-run |
| Post-fix full `tests/` suite at `388845c` | PASS — 1740 passed, 1 warning, exit 0 | direct-run |
| Historical CAN-* post snapshot, 3 focused groups | PASS — 4 + 8 + 24 = 36 passed | direct-run |
| Historical CAN-* pre snapshot, 3 focused groups | 36 failed, exit 1 (proves coverage of the bug) | direct-run |
| Snapshot full suite (post-fix) | PASS — 1720 passed, 1 warning, exit 0 | direct-run |

## Lifecycle and scope checks (direct-run)

| Check | Result | Evidence |
|---|---|---|
| Registry local validation (`scripts/validate-audit-remediation-registry.py`) | PASS — 91 original (P0=1, P1=27, P2=63) + 9 revalidation; exit 0 | direct-run |
| Registry external parity (`--require-external-parity`) | PASS — local+external; exit 0 | direct-run |
| Changed-path scope (`bf91b42..388845c`) | PASS — 605 committed paths, all within allowed set; exit 0 | direct-run |
| Manifest conformance (`scripts/llm-dev verify`) | PASS — 4/4 checks; exit 0 | direct-run |
| `git diff --check bf91b42..388845c` | PASS — exit 0 | direct-run |
| `git diff --check HEAD` | PASS — exit 0 | direct-run |

## Cardinality assertions

| Cardinality assertion | Result | Evidence |
|---|---|---|
| Audit registry contains exactly 100 findings | PASS — `100` | direct-run |
| I0 snapshot exists | PASS — exit 0 | direct-run |
| I1 snapshot exists | PASS — exit 0 | direct-run |
| I2 snapshot exists | PASS — exit 0 | direct-run |
| I3 snapshot exists (ancestor of HEAD) | PASS — exit 0 | direct-run |
| User-owned forbidden documents absent | PASS — exit 0 | direct-run |

## Scope-lock check

- Paths touched outside allowed set: **none.** The `859ecf7..388845c` diff
  touches `ontos/core/context.py`, `ontos/core/frontmatter_edit.py`,
  `ontos/io/files.py`, `ontos/io/yaml.py`, the six addendum test files, plus
  docs/CI/manifest/tracker paths — all within `scope.allowed_paths` or the
  `docs/reviews/project-ontos-audit-rebaseline-remediation/**` glob.
- Product/test working tree clean (no uncommitted `ontos/`, `tests/`, or
  `scripts/` changes).
- No spec deviation declared by the fix summary; the `ontos/commands/rename.py`
  scope correction at `737fe27` is documented as a Phase-0 omission recovery
  authorized by spec §4.2 and canonical D.3 CAN-ID-1.

## Framework findings (defects remain — preserved)

### D4-INFRA-1 — EH-15-A adopter regression registration (fail-open + unresolvable)

`verify-fix-summary-regressions.sh` hard-binds its bundle, registry, and
fixture resolution to `.llm-dev/framework`, not the adopter root. Both EH-15-A
probes were re-run directly:

- Probe 1 (manifest-mode, absolute manifest path): exit **0** with
  `OK (no D.4 fix-summary exists at ...)` — **fail-open**: the gate reports
  the fix summary does not exist at a path where a tracked file plainly exists.
- Probe 2 (direct absolute fix-summary path): exit **1**, `FAILED` — every
  adopter pytest fixture is reported as `does not exist` and
  `not registered ... in eh15a_regression_fixtures` because resolution runs
  under the framework bundle, not the adopter root.

The D.4 fix summary remains `status: halted` on D4-INFRA-1. Functional fixes
are verified, but the pinned framework gate cannot register or validate
adopter-owned runnable fixtures.

### D5-INFRA-2 — strict lifecycle `review_pending` + receipt-inventory schema

- `scripts/llm-dev verify-lifecycle` (strict-p3): **FAIL**, exit 1,
  `status=review_pending`, 5 issues: `dispatch-verify-failed` (claude
  verifier round 1 exit 1), `dispatch-verifier-output` (gemini and glm
  current result rows `status=failed`), `missing-receipt` (gemini verifier),
  `route-redaction` (historical glm receipt carries an unredacted
  high-entropy token), `dispatch-entry-not-found` (glm receipt entry status
  not in recognized strict completion set).
- Receipt inventory (`lifecycle-receipt-inventory-strict-final.yaml`):
  `schema_version` 1, historical D.5 receipts for claude + glm only (gemini
  missing). `verify-lifecycle` **does** apply the strict-p3 lifecycle schema
  (receipt status + dispatch completeness + hash-binding) and rejects the
  current inventory. The three current-head D.5 dispatches all failed
  promotion (gemini: exit 55, no output; glm: artifact hash `missing`; claude:
  artifact hash `missing`), so strict-P3 cannot certify at this head.
- The PR-161 disposition additionally recorded six v2.0.1 producer/schema
  mismatches in the receipt schema (three Product roles, three OpenCode
  promotion sources).

## If "Request changes"

| Finding | Evidence | Required further action |
|---|---|---|
| D4-INFRA-1 | EH-15-A probe 1 fail-open exit 0; probe 2 exit 1; D.4 `status: halted` | Upstream framework support for an explicit adopter root + adopter-owned runnable-fixture registry, then a pinned framework upgrade and fresh D.4/D.5. Do not waive the gate, cite an unrelated framework fixture, lower the manifest version, or manually repair receipts. |
| D5-INFRA-2 | `verify-lifecycle` strict-p3 exit 1, `review_pending`, 5 issues; receipt inventory v1 with gemini missing + glm route-redaction flag | Re-dispatch the three current-head D.5 verifiers so each produces a hash-bound, redaction-clean receipt; rebind the v3 receipt inventory; re-run `verify-lifecycle` until `status=strict_p3_review_complete`. Do not manually edit or fabricate receipts. |

## Verdict

Request changes

The product code passes: all six historical D.3 should-fix rows are reproduced
broken pre-fix and closed post-fix (36 focused pre/post swap tests), all six
PR-161 current-head addendum rows pass at `388845c` (104 focused), the complete
suite is green (1740 passed), and registry/scope/manifest/cardinality checks
all pass. But framework defects remain open — the fail-open EH-15-A gate
(D4-INFRA-1) and the strict lifecycle `review_pending` state with
receipt-inventory schema gaps (D5-INFRA-2). Per the Template 15 contract,
functional success is not lifecycle certification while these framework
defects are open; receipts were not waived or repaired manually. This verdict
does not certify D.6, strict-P3, merge, tag, or release.
