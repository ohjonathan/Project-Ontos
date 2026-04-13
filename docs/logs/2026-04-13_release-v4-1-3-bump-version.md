---
id: log_20260413_release-v4-1-3-bump-version
type: log
status: active
event_type: release
source: codex
branch: main
created: 2026-04-13
---

# release(v4.1.3): bump version

## Goal

Cut the actual `v4.1.3` release for the Antigravity native MCP onboarding
work, verify that customer-facing documentation on `main` already reflected the
feature set, and confirm the full publish path through GitHub Releases,
TestPyPI, and PyPI.

## Root Cause

PR #100 merged the Antigravity onboarding feature and review-fix follow-ups,
but the package metadata still reported `4.1.2`. Because the publish workflow
is tag-driven and validates that the tag matches `ontos.__version__`, no
`v4.1.3` tag or PyPI release could succeed until the package version was
bumped.

## Key Decisions

- Audited README, manual, migration guide, and `docs/releases/v4.1.3.md`
  before changing anything; no additional customer-facing doc edits were
  needed because the Antigravity setup and support policy text were already on
  `main`.
- Kept the release commit narrowly scoped to the two version sources:
  `pyproject.toml` and `ontos/__init__.py`.
- Used the checked-in `docs/releases/v4.1.3.md` as the GitHub release body so
  the public release page matches the repo's release notes.
- Verified the publish pipeline end to end instead of stopping at tag push:
  watched the GitHub Actions run through TestPyPI verification and PyPI
  publication, then confirmed PyPI's public JSON API flipped to `4.1.3`.
- Left the tag on the version-bump commit and recorded the release wrap-up in
  this separate archive log commit on `main`.

## Alternatives Considered

- Bundling more doc edits into the release commit:
  rejected because the customer-facing docs already contained the Antigravity
  onboarding content and support-tier clarifications from the merged PR.
- Tagging `v4.1.3` before bumping package metadata:
  rejected because `.github/workflows/publish.yml` would fail the tag/version
  equality check.
- Treating GitHub release creation as sufficient:
  rejected because the user asked to make sure tagging and PyPI were both
  done, which required waiting for the publish workflow and checking PyPI
  directly.

## Impacts

- `main` now contains release commit `42ab0d0` with package version `4.1.3`.
- Git tag `v4.1.3` exists and backs the published GitHub release page.
- The `Publish to PyPI` workflow succeeded end to end for `v4.1.3`.
- PyPI now serves `ontos` version `4.1.3`.
- Customer-facing docs on `main` remain aligned with the released feature set:
  README, migration guide, manual, and release notes all describe
  Antigravity native onboarding.

## Testing

- `pytest tests/commands/test_mcp_command.py tests/commands/test_doctor_phase4.py tests/test_cli.py tests/test_cli_phase4.py tests/commands/test_antigravity_mcp_docs.py tests/commands/test_json_contract_a3.py tests/commands/test_mcp_write_tool_docs.py -v`
- `/Library/Developer/CommandLineTools/usr/bin/python3 -m build`
- `python3 -m ontos --version` -> `ontos 4.1.3`
- `gh run watch 24372398169 --repo ohjonathan/Project-Ontos --interval 10 --exit-status`
- `curl -s https://pypi.org/pypi/ontos/json` confirmed public version `4.1.3`
