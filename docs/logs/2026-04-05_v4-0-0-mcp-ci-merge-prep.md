---
id: log_20260405_v4-0-0-mcp-ci-merge-prep
type: log
status: active
event_type: fix
source: cli
branch: v4.0_MCP_Server
created: 2026-04-05
---

# v4.0.0-mcp-ci-merge-prep

## Summary
Prepared the v4.0.0 MCP server branch for merge after GitHub Actions failures were traced to CI environment setup rather than MCP runtime regressions. Updated the main test-matrix workflow so Python 3.10+ installs the optional MCP extra while Python 3.9 stays on the base package path, reran the repository test gates locally, and archived the session.

## Root Cause
The PR added `tests/mcp/*`, and those tests intentionally require the external `mcp` package from site-packages. The GitHub Actions matrix job in `.github/workflows/ci.yml` originally installed only `-e ".[dev]"`, so all Python matrix jobs failed during test collection with `ImportError: Unable to load the external 'mcp' package from site-packages`. After correcting that, Python 3.9 still failed because `mcp>=1.2` requires Python 3.10+, so the workflow needed a version-aware split rather than a blanket MCP install.

## Fix Applied
Changed the editable-install step in the `test` matrix job to install `.[dev,mcp]` on Python 3.10+ and `.[dev]` on Python 3.9. The Python 3.9 leg now runs `tests/` with `--ignore=tests/mcp`, while Python 3.10+ continue to run the full suite. Left the `test-non-editable` job unchanged to preserve the base-install gate without the optional MCP extra.

## Testing
- `.venv/bin/python3.14 -m pytest tests/ -q`
- `.venv/bin/python3.14 -m pytest .ontos/scripts/tests/ -q`
- `gh pr checks 81`
- `gh run view 24006474923 --job 70010914507 --log`

## Goal
Get PR #81 back to a merge-ready state by fixing the failing GitHub Actions checks without broadening the product-change scope.

## Key Decisions
- Treat the failing matrix jobs as a CI packaging issue, not as a new MCP implementation defect.
- Install the MCP extra only where the interpreter supports it, and keep a 3.9 base-package lane instead of dropping 3.9 coverage entirely.
- Preserve the separate non-editable/base-install job as-is so it continues validating the no-extra install path.

## Alternatives Considered
- Make `mcp` part of the base install. Rejected because the approved design keeps MCP optional.
- Drop Python 3.9 from CI entirely. Rejected because the package still declares `requires-python = ">=3.9"` and should keep a base-package regression lane.
- Skip `tests/mcp/*` in CI. Rejected because those tests are part of the v4.0.0 merge gate.
- Relax the test package guard in `tests/mcp/__init__.py`. Rejected because the guard correctly enforces use of the real external package.

## Impacts
- GitHub Actions test matrix now matches the repository's intended optional-dependency contract.
- Base-install safety coverage remains intact through the unchanged `test-non-editable` job.
- The branch is ready for CI re-run and merge once the updated checks return green.
