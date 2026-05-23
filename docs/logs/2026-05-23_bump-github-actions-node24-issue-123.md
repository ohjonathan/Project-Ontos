---
id: log_20260523_bump-github-actions-node24-issue-123
type: log
status: active
event_type: chore
source: claude-opus-4-7
branch: codex/issue-123-node24-actions
created: 2026-05-23
---

# Bump GitHub Actions off Node.js 20 (closes #123)

## Summary

Closed [#123](https://github.com/ohjonathan/Project-Ontos/issues/123) by SHA-bumping four `actions/*` pins to their latest Node.js 24–compatible releases across `.github/workflows/{ci,golden-master,publish}.yml`, ahead of GitHub's 2026-06-02 soft enforcement and 2026-09-16 Node 20 runtime removal. Shipped via [PR #125](https://github.com/ohjonathan/Project-Ontos/pull/125), merged as merge commit [`6be21a5`](https://github.com/ohjonathan/Project-Ontos/commit/6be21a51ace830d689f0da5c31805c4e59d64e05). GitHub auto-closed #123 on merge.

## Goal

Eliminate the Node.js 20 deprecation warning surfaced on every workflow run (most recently during the v4.6.0 publish, run `26324102397`) by moving the four enumerated `actions/*` pins to Node 24–compatible releases while preserving the repo's strict SHA-pinning style. Scope was bounded by the issue body: the four `actions/*` pins only, not other third-party actions in the workflows.

## Key Decisions

- **Take the latest release in each major line, not the minimum Node-24 bump.** For `upload-artifact` (v6.0.0 minimum vs v7.0.1 latest) and `download-artifact` (v7.0.0 minimum vs v8.0.1 latest) the latest majors include behavior changes beyond a pure runtime bump. Picked latest because the v7/v8 changes are either opt-in (`upload-artifact` v7's `archive: false` direct-upload mode — no call site sets it) or safety improvements (`download-artifact` v8's default hash-mismatch erroring; artifacts are produced and consumed within the same run). Confirmed with the user via AskUserQuestion before locking the pin map.
- **Resolve every tag to a commit SHA via `gh api repos/<action>/commits/<tag>`, not the tag object.** All four tags happened to resolve directly to commit objects (verified via `git/refs/tags/<tag>`), so no annotated-tag dereferencing was needed. Pins recorded with matching `# v6` / `# v6` / `# v7` / `# v8` inline comments to keep the existing convention readable at a glance.
- **Hold the line on the issue's explicit scope.** `codecov/codecov-action@v4` (`ci.yml:62`) and `pypa/gh-action-pypi-publish@v1.13.0` (`publish.yml:85,127`) were left untouched. Issue #123 enumerated only the four `actions/*` pins; the user's runbook explicitly forbade expanding scope to other actions unless both the warning surface and the issue scope supported it. The codecov warning was confirmed post-merge in the CI log; pypa-publish was confirmed clean.
- **Discard incidental Ontos-generated churn from activation.** `ontos activate` regenerated `Ontos_Context_Map.md` (timestamp only) and `.ontos-internal/reference/decision_history.md` plus an empty `.ontos-internal/logs/2026-05-23_init.md` stub. Reverted/removed all three so the commit contained only the 15-line workflow edit.

## Alternatives Considered

- **Minimum-Node-24 bump for the artifact actions** (`upload-artifact` v6.0.0, `download-artifact` v7.0.0). Rejected per the user's preference for the latest of each — see Key Decisions. Downside flagged in the AskUserQuestion: the minimum-bump lines have no patch releases, so any future fix would force another bump within months.
- **Bundle the codecov-action bump into this PR.** Rejected because it falls outside issue #123's enumerated scope and the runbook's "scope limited to the Node 20 deprecation cleanup" constraint. Surfaced as a separate spawn_task chip instead (target: `codecov-action` v6.0.1, which also ships a VULN-1652 template-injection fix).
- **Use floating major tags (`@v6`, `@v7`, `@v8`) instead of SHA pins.** Rejected — the repo's entire workflow style is SHA-pinned with `# vN` comments. Drifting to floating tags would erase the supply-chain guarantee.

## Changes Made

- Resolved target pins via `gh api repos/<action>/releases` + `gh api repos/<action>/commits/<tag>`:
  - `actions/checkout` v4 → **v6.0.2** (`de0fac2e4500dabe0009e67214ff5f5447ce83dd`)
  - `actions/setup-python` v5 → **v6.2.0** (`a309ff8b426b58ec0e2a45f0f869d46889d02405`)
  - `actions/upload-artifact` v4 → **v7.0.1** (`043fb46d1a93c77aae656e7c1c64a875d1fc6a0a`)
  - `actions/download-artifact` v4 → **v8.0.1** (`3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c`)
- Edited 15 `uses:` lines across 3 workflow files (`+15 -15`, no other changes):
  - `.github/workflows/ci.yml` — 4 lines
  - `.github/workflows/golden-master.yml` — 3 lines
  - `.github/workflows/publish.yml` — 8 lines
- Branched from `main` (HEAD `61255ae`) as `codex/issue-123-node24-actions`; committed as `651956e`; pushed; opened [PR #125](https://github.com/ohjonathan/Project-Ontos/pull/125) ready-for-review with full pin table, compatibility notes, and verification trace.
- Merged via `gh pr merge 125 --merge` (matching repo convention from #121, #124) — merge commit `6be21a5`.
- Spawned a follow-up task chip for the remaining `codecov/codecov-action` Node 20 bump (target v6.0.1).

## Impacts

- **CI**: `ci.yml` and `golden-master.yml` no longer emit Node 20 deprecation warnings from the four bumped actions. The post-merge CI run confirmed this — the only residual `##[warning]Node.js 20 actions are deprecated` line now names `codecov/codecov-action` exclusively.
- **Release pipeline**: `publish.yml` is bumped but only exercised on `v*` tag push. The next release will run it; no behavior change expected since `upload-artifact` v7's new `archive` parameter is opt-in (defaults preserve v4 zipped-upload semantics) and `download-artifact` v8's ESM migration is transparent.
- **Issue tracker**: #123 auto-closed via `Closes #123` trailer.
- **Outstanding follow-up (non-blocking)**: `codecov/codecov-action@v4` still on Node 20 — spawn_task chip in flight, targeting v6.0.1. Must land before 2026-06-02 to fully clear the warning class.

## Testing

All local gates green on commit `651956e`, plus 5/5 CI checks on the same commit:

| Gate | Local result | Exit |
|---|---|---|
| `rg -n "actions/(checkout\|setup-python\|upload-artifact\|download-artifact)@" .github/workflows` | 15 matches, all on new SHAs | 0 |
| `rg -n "<4 old SHAs>" .github/workflows` | 0 matches | 1 (expected) |
| `python -c "import yaml; ... yaml.safe_load ..."` | `ok` on all 3 files | 0 |
| `scripts/llm-dev doctor` | PASS | 0 |
| `.venv/bin/python -m pytest -q` | 1339 passed, 2 skipped (53.13s) | 0 |
| `git status` | only the 3 intended workflow edits + known `.llm-dev/framework` submodule marker | n/a |

CI on PR #125 (run `26334160485`): `test (3.9)` 2m43s · `test (3.10)` 3m28s · `test (3.11)` 3m34s · `test (3.12)` 4m11s · `test-non-editable` 10s — all SUCCESS. Grep of the run log confirmed the four bumped actions no longer appear in any Node 20 deprecation warning.
