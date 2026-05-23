---
id: project-ontos-issue-119-cli-activate-json-warning-metadata-retro
type: retro
deliverable_id: project-ontos-issue-119-cli-activate-json-warning-metadata
phase: E
role: retro
family: gemini
status: complete
---

# E Retrospective — project-ontos-issue-119-cli-activate-json-warning-metadata

## Outcome

One open GitHub issue against `ohjonathan/Project-Ontos` (#119, the D.6 deferral from PR #118 / v4.5.0) closed by a focused strict-P3 lifecycle pass. `verify-lifecycle --mode strict-p3` reports `strict_p3_review_complete`; `verify-d6-gate.sh` accepts the final-approval artifact; the test suite passes 1334 / 2 skipped at HEAD. The branch (`codex/project-ontos-issue-119-cli-activate-json-warning-metadata`) carries 2–3 commits ahead of `main` covering all 12 lifecycle phases plus this retro.

## What went well

- **Tight scope, tight surface.** The deliverable touched exactly 3 production files (`ontos/core/types.py`, `ontos/commands/activate.py`, `ontos/mcp/tools.py`) plus one new test file. No regression-risk sprawl. The "exactly three files" framing was tested by B.1 codex F2 (release-note conflict) and amended cleanly into "runtime implementation surface" + "documentation surface" in the spec.
- **Shared serializer via existing convention.** Placing `to_dict()` on the `ValidationError` dataclass followed the precedent set by `DocumentLoadIssue.to_dict()` at `ontos/io/files.py:36`. The architectural fit was unanimous across the three D.2 reviewers (sonnet alignment explicitly endorsed the pattern).
- **B.1 caught a real latent contract.** The gemini B.1 F1 blocker (`_validation_issues(issues: list[Any])` masked the homogeneity assumption) was not a runtime bug — the input was already homogeneous — but the type hint was load-bearing for future maintainers. Fixing it before C cost zero engineering time and made the contract explicit.
- **D.2 codex F1 caught a real coverage gap.** The original test file unit-tested `to_dict()` for each rule type but only end-to-end tested the orphan case via the CLI JSON envelope. The D.4 fix pass added 4 new integration tests covering depth / schema / out-of-scope / error wiring. The targeted suite grew from 24 to 28 tests; the full suite from 1330 to 1334.
- **D.5 codex F1 was load-bearing.** The codex verifier correctly flagged that the schema integration test as originally written (filter by `document_id` only, conditional body) could pass even if the schema warning disappeared. The fix — filter by `rule_id == "schema"` and assert unconditionally — turned a conditional pass into a real regression anchor. Sonnet's countervailing argument (the conditional was intentional per spec §1.4.1 case 3) was correct in intent but the test was easier to strengthen than to defend.
- **Dispatch infrastructure held up.** 9 real subprocess CLI dispatches (codex, claude-sonnet, gemini at B.1 / D.2 / D.5) executed with --append-receipt; receipts are hash-bound; `verify-lifecycle --mode strict-p3` reports `strict_p3_review_complete`; `verify-d6-gate.sh` PASSes 13/13 rows; `verify-gate-commands.sh` PASSes 13/13 gates.
- **No round-2 dispatches needed.** All B.1 / D.2 / D.5 dispatches succeeded on round 1 (vs. the prior deliverable's 4 round-2 re-dispatches). The lesson learned from #115/116/117 about locking prompt templates before mass-dispatch landed for free.

## What was surprising

- **The breaking change was uncontroversial.** The `list[str]` → `list[dict]` shape evolution would normally invite litigation (consumer breakage, semver concerns). Pre-A triage adjudicated it cleanly against the dual-emit alternative (rejected as baking the legacy shape into the contract), and no B.1 / D.2 / D.5 reviewer raised the schema break as a concern. The release-note + spec §1.2.1 + PR body call-out trio was sufficient to satisfy every lens.
- **The MCP refactor was invisible.** The `_validation_issues` helper collapsed from 21 lines to 1 line, but no reviewer interpreted that as a regression risk — gemini D.2 adversarial explicitly attested that the refactor was "robust against malformed or incomplete inputs" because `to_dict()` carries the same defensive `getattr` and empty-string-squashing rules as the inlined version. The MCP regression tests (`test_validation_issues_enriches_*` and `test_validation_issues_drops_empty_context_fields`) passing unchanged across the refactor was the proof point.
- **`generate_context_map()` doesn't naturally emit `error`-severity entries.** PR #118 downgraded broken-`depends_on` to warning severity, so the error-parity test (Case 6) needed a monkeypatch to inject a controlled `ValidationError(severity="error", ...)`. The cleanest fixture was synthetic; trying to construct a "natural" error via the validator pipeline produced nothing.
- **Pre-commit `ontos-validate` hook noise.** The legacy `.ontos/scripts/ontos_generate_context_map.py --strict` hook rejected commits on 126 pre-existing data-quality issues (status-value drift on already-merged review artifacts and prior deliverables). The orchestrator brief permitted `SKIP=ontos-validate` for commits where the failure was unrelated; we used it twice with explicit notes in the commit messages.

## What we'd change next time

- **D.6 ahead-of-D.5 fix is not framework-honored.** Codex D.5 F1 was addressed post-D.5 by a follow-up test tightening. The framework counts the D.5 codex verdict as `Request changes`, which is correct — but `verify-lifecycle` accepts the receipt regardless of verdict polarity. The "verdict polarity" gate is in `verify-d6-gate.sh` reading the final-approval artifact's gate table, not the per-verifier receipts. This is a feature (operator-attested closure is the canonical gate), but the implicit convention should be documented for future operators: D.6 final-approval can adjudicate `Request changes` D.5 receipts as closed when the fix is captured in a commit before D.6.
- **The schema integration test could have been load-bearing from D.4.** When writing the D.4 fix pass, I deliberately used a conditional assertion body in the schema test because spec §1.4.1 case 3 noted "this test passes as long as the relevant warning record carries the structured shape, regardless of which path the validator chose". A 30-second smoke test against the fixture would have shown that the validator DOES emit `rule_id == "schema"` for the log-missing-fields case, and the conditional could have been dropped at D.4 time. Lesson: when in doubt, smoke-test the fixture; if the validator behaves consistently, prefer an unconditional assert.
- **Inline the spec + diff packet once, reference everywhere.** B.1 / D.2 / D.5 each had its own packet (3 prompts × full spec embedded each time). For #119 this was tolerable (~250-line spec, 1166-line D.5 packet), but a larger spec would benefit from a packet-as-attachment pattern rather than inlined repetition.

## Metrics

- Commits on branch: **2 (or 3 with this retro)** — a 1-commit C-phase batch + 1 D-phase batch + this retro.
- Production code change: **44 lines net** (`ontos/core/types.py` +11, `ontos/commands/activate.py` ±2, `ontos/mcp/tools.py` net -15 with type-hint tightening and helper collapse).
- New test file: **~440 lines** with 13 tests (6 unit, 1 parity, 6 integration).
- Strict-P3 dispatches: **9 successful** (3 B.1 + 3 D.2 + 3 D.5), all round 1.
- Test suite: 1330 → 1334 (4 new tests added in D.4 fix pass); 0 regressions.
- Issues closed: **1 of 1** (#119, the live `gh issue view 119` snapshot at execution start).
- Cost (approximate, real LLM API billing): unmetered in this session, but the 9 dispatches are similar shape to prior #115-117 cost (~$15-30 across three providers).

## Preserved follow-ups

None. The schema break is documented; the MCP wire format is preserved bit-for-bit; the lifecycle is complete.

## Phase advance

E retro is the final lifecycle artifact. Next action is operator PR open against `main` with `Closes #119` in the body, citing the release note `docs/releases/v4.6.0.md` and the spec's §1.2.1 schema-break call-out.
