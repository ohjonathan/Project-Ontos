# Phase D Consolidation: Codex — PR #85

**PR:** ohjonathan/Project-Ontos#85  
**Branch:** `v4.1-track-a-portfolio` -> `main`  
**Scope:** Ontos v4.1 Track A (portfolio index, read tools, `verify --portfolio`, flock lock substrate)  
**Platform:** Codex (3 independent reviewer agents)  
**Date:** 2026-04-11

---

## 1. Verdict Summary

| Reviewer | Role | Verdict | Blocking Issues |
|---|---|---|---:|
| Reviewer 1 | Peer (Code) | **Request Changes** | 3 |
| Reviewer 2 | Alignment (Code) | **Request Changes** | 2 |
| Reviewer 3 | Adversarial (Code) | **Block** | 3 |

**Platform verdict: Needs Fixes**

The Track A substrate is mostly sound, but the two organic additions introduced late in Phase C are where the blocking issues landed: `verify --portfolio` diverges from the scanner/index contract, and mixed-version config compatibility silently weakens config validation.

---

## 2. Blocking Issues

| ID | Description | Flagged By | File:Line | Action Required |
|---|---|---|---|---|
| **B-1** | `verify --portfolio` does not parse the same registry shapes that portfolio indexing already supports. The verifier only accepts a top-level `projects` list, while the scanner accepts `projects`, `workspaces`, `entries`, `items`, and dict-shaped registries. This produces false discrepancy reports on otherwise valid Track A data. | R2, R3 | `ontos/commands/verify.py:396`, `ontos/mcp/scanner.py:202` | Factor registry parsing into shared code and make the verifier reuse it. Add coverage for alternate registry shapes. |
| **B-2** | `verify --portfolio` cannot validate collision-safe slugs produced by Track A itself. The verifier keys registry rows by basename slug, but the scanner allocates `-2`, `-3` suffixes for collisions. A clean multi-root portfolio can therefore verify as dirty. | R1, R2, R3 | `ontos/commands/verify.py:406`, `ontos/commands/verify.py:450`, `ontos/mcp/scanner.py:268` | Compare by normalized path or reuse the scanner's collision allocation rules instead of raw basename slugging. Add a collision regression test. |
| **B-3** | Mixed-version config compatibility silently disables config validation semantics across the whole app. `_section_kwargs()` drops unknown keys in every section, so typos and older unmapped keys fall back to defaults instead of surfacing as errors. | R1, R2, R3 | `ontos/core/config.py:143`, `ontos/core/config.py:160`, `ontos/core/config.py:180`, `ontos/core/config.py:202`, `tests/core/test_config_phase3.py:149` | Keep the explicit `validation.strict -> hooks.strict` mapping, but replace the blanket silent-drop behavior with an explicit allowlist and warnings, or revert to strict unknown-key validation. |

### Evidence highlights

- Reviewer 3 reproduced a false failure with registry JSON shaped as `{"workspaces": [...]}`: the verifier returned `missing_in_json` for a DB row that the scanner would accept.
- Reviewer 1 reproduced a false discrepancy with two `sample-app` directories: the DB contained `sample-app` and `sample-app-2`, but the verifier collapsed both registry rows into one slug and reported bogus drift.
- Reviewer 3 reproduced typo masking directly with `dict_to_config({'hooks': {'pre_pus': False}})`, which loaded successfully and silently fell back to `pre_push=True`.

---

## 3. Should-Fix Issues

| ID | Description | Flagged By | File:Line | Recommendation |
|---|---|---|---|---|
| **S-1** | `portfolio.toml` exposes bundle settings that are currently dead config. `bundle_token_budget`, `bundle_max_logs`, and `bundle_log_window_days` are parsed but never wired into runtime bundle construction. | R1, R3 | `ontos/mcp/portfolio_config.py:46`, `ontos/mcp/server.py:708`, `ontos/mcp/tools.py:410`, `ontos/mcp/bundler.py:31` | Either thread these settings into `get_context_bundle()` / `build_context_bundle()`, or remove/defer them until live. |
| **S-2** | Recent-log tiebreaking in the bundle implementation is not fully aligned with the deterministic ordering intent. `reverse=True` on `(date, id)` means equal-date log IDs sort in reverse alphabetical order. | R2 | `ontos/mcp/bundler.py:167` | Make the equal-date tie break deterministic in the same direction the spec describes. |
| **S-3** | Scanner collision handling does not emit the stderr warning called for by spec §4.3. | R2 | `ontos/mcp/scanner.py:86`, `ontos/mcp/scanner.py:268` | Emit a warning when suffix allocation occurs, or update the spec if silent suffixing is now intentional. |

---

## 4. Minor Issues

| ID | Description | Flagged By | File:Line |
|---|---|---|---|
| **M-1** | `SessionContext` docstring still says it provides "atomic writes via two-phase commit," which no longer matches the approved write-safety wording. | R1 | `ontos/core/context.py:1` |
| **M-2** | `TOOL_SUCCESS_MODELS` only maps Track A names even though Track B response models were added to the schema module. | R2 | `ontos/mcp/schemas.py:283` |

---

## 5. Out-of-Spec Changes Verdict

Two organic additions bypassed earlier spec review and require explicit disposition.

### 5.1 Mixed-Version Config Compat (`ontos/core/config.py`)

**Verdict: Reject as implemented.**

The targeted legacy mapping (`validation.strict -> hooks.strict`) is reasonable and should stay. The broader `_section_kwargs()` behavior is not a narrow compatibility fix; it changes config validation semantics repo-wide by silently discarding arbitrary unknown keys in all sections. That can mask:

- current-version typos,
- future-version incompatibilities,
- older legacy keys that were never explicitly mapped.

**Acceptable path:** keep explicit, reviewed legacy mappings only; if unknown keys must be tolerated, do it through a short allowlist plus warnings rather than silent fallback.

### 5.2 `has_ontos` Fallback in `verify.py`

**Verdict: Accept with conditions.**

The basic idea is justified because real registry data may omit `has_ontos`, and the verifier still needs a way to compare DB state against portfolio inputs. But the current implementation is too loose:

- it sits inside a verifier parser that already diverges from scanner behavior,
- `bool(record.get("has_ontos"))` will treat string values like `"false"` as truthy,
- the filesystem fallback should be tightened to file semantics rather than generic existence.

**Acceptable path:** keep the fallback only after the verifier reuses shared registry parsing and tightens boolean / file handling.

---

## 6. Regression Status

**Regression found.**

The reviewer team did **not** find a regression in the flock migration or the Track A tool matrix:

- existing CLI write paths still funnel through `SessionContext.commit()`,
- lock contention behavior appears correct under current CLI usage,
- the single-workspace `get_context_bundle()` crash path from UB-7 is fixed,
- portfolio mode registers the expected 11-tool Track A surface.

The regressions found are:

1. **Config validation regression**: typos and unmapped legacy keys are silently accepted where they previously surfaced.
2. **Verifier false positives**: `verify --portfolio` can report valid portfolio state as drift.

Reviewer reruns that passed while checking regression surface:

- `pytest -q tests/test_session_context.py tests/commands/test_rename.py tests/commands/test_promote_parity.py tests/commands/test_scaffold_parity.py tests/commands/test_verify_parity.py` -> **49 passed**
- `python3 -m pytest -q tests/commands/test_verify_parity.py tests/commands/test_verify_portfolio.py tests/core/test_config_phase3.py tests/test_session_context.py` -> **42 passed**

`tests/mcp/*` could not be re-run in this environment because the external `mcp` package is unavailable here.

---

## 7. Agreement Analysis

### Strong agreement

All three reviewers converged on the same core conclusion:

- the portfolio DB / FTS5 path is sound,
- the flock substrate migration does not appear to break existing CLI write paths,
- the Track A tool matrix and `workspace_id` routing are largely correct,
- the blocking problems are concentrated in `verify --portfolio` and the mixed-version config addition.

### Single-reviewer findings preserved

- **Dead bundle config** was flagged by the Peer and Adversarial reviewers, but not the Alignment reviewer.
- **Recent-log ordering drift** and **missing scanner collision warning** came from the Alignment reviewer only.
- **Stale atomic-write docstring** came from the Peer reviewer only.

### Disagreements

There was no material disagreement on the three blocking issues. The only real variation was on the `has_ontos` fallback:

- Reviewer 2 viewed it as too loose to merge without tightening,
- Reviewer 3 accepted the concept but only with shared parsing and stricter semantics,
- Reviewer 1 treated it as part of the broader verify/parser divergence.

The consolidated position is therefore **accept with conditions**, not unconditional acceptance.

---

## 8. Required Actions for Dev Team

1. Make `verify --portfolio` consume the same registry formats and identity rules as portfolio scanning.
2. Fix verifier handling for basename collisions so a DB built with scanner suffixes verifies cleanly.
3. Replace blanket unknown-key dropping in config loading with explicit legacy compatibility handling, or revert it.
4. Add tests for alternate registry shapes, basename collisions, and config typo / legacy-key behavior.
5. Either wire bundle config into runtime bundle construction or remove/defer those config fields.
6. Clean up deterministic ordering and warning-path follow-through in the bundler / scanner if those spec drifts are intended to stay.

---

## 9. Test Verification Requirements

| Fix | Verification |
|---|---|
| **B-1 Shared registry parsing** | Add tests where the registry uses `workspaces`, `entries`, `items`, and dict-shaped forms. `verify --portfolio` must accept the same shapes the scanner accepts. |
| **B-2 Collision-safe verification** | Add a regression test with two projects that share the same basename under different roots. The verifier must not report drift when the DB contains scanner-generated suffixes. |
| **B-3 Config validation semantics** | Add tests that keep `validation.strict -> hooks.strict`, but verify typos and unmapped keys still surface rather than silently disappearing. |
| **S-1 Bundle config wiring** | Add a runtime test proving `bundle_token_budget`, `bundle_max_logs`, and `bundle_log_window_days` actually change `get_context_bundle()` output, or remove those config fields. |
| **S-2 Deterministic log ordering** | Add a bundle test with multiple equal-date logs and verify stable ordering across repeated runs. |

---

## 10. Decision Summary

**Needs Fixes**

This PR is not ready to merge as-is. The team did not find a reimplementation-level problem in Track A; the portfolio index, FTS5 search, server registration, and lock migration all look fundamentally viable. But the verifier and config compatibility additions need another pass before merge:

- `verify --portfolio` currently cannot be trusted as a source of truth because it does not read the same portfolio inputs the rest of Track A accepts,
- the config compatibility change widens behavior silently in a way that can hide real mistakes.

These are fixable issues, but they are merge blockers.

---

## Cross-Platform Handoff Summary

**Headline:** Track A's core substrate looks sound, but the two organic additions are the blocking failures.  
**Codex verdict:** Needs Fixes.  
**Top 3 blocking issues:** shared-registry parsing mismatch in `verify --portfolio`; collision-unsafe verifier slugging; overly permissive config compatibility behavior.  
**Out-of-spec position:** reject mixed-version config compat as implemented; accept `has_ontos` fallback only with tighter semantics and shared parsing.  
**Regression status:** regression found in config validation behavior and verifier trustworthiness; no lock-substrate regression found in existing CLI write paths.  
**Cross-platform attention:** validate whether other platforms also see the verifier/parser contract drift as the real blocker rather than the portfolio DB / server surface.
