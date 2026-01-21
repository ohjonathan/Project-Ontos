## Summary

v3.0.5 patch release addressing tech debt and UX improvements.

## Changes

### VER-1: Version String Fix
- Updated `ONTOS_VERSION` in legacy scripts to "3.0.5"
- Updated `__version__` in `ontos/__init__.py` to "3.0.5"
- Updated `version` in `pyproject.toml` to "3.0.5"

### MCP-1: MCP Import Warning
- Added `FutureWarning` when importing placeholder `ontos.mcp` module

### UX-1: Init Hooks Consent
- Added preflight message showing hooks to be installed
- Added TTY confirmation prompt: `Install git hooks? [Y/n]`
- Added `--yes/-y` flag for non-interactive mode
- CI/scripts (non-TTY) proceed without prompt
- `--skip-hooks` takes precedence over `--yes`
- Ctrl+C aborts entire init and cleans up partial state

### WRP-1: Wrapper Command Testing
- Tested all 7 wrapper commands
- Documented status and limitations in README

### UX-2: Known Issues Update
- Updated README Known Issues for v3.0.5
- Documented wrapper command limitations

## Testing

- [x] All existing tests pass (427 tests)
- [x] New tests added for hook confirmation flow (including Ctrl+C)
- [x] Manual verification of TTY prompt behavior
- [x] Manual verification of --yes and --skip-hooks flags
- [x] Manual verification of Ctrl+C abort behavior

## Checklist

- [x] VER-1: Version constant updated
- [x] MCP-1: Warning emits on import
- [x] UX-1: Consent flow works in TTY
- [x] UX-1: --yes bypasses prompt
- [x] UX-1: --skip-hooks takes precedence
- [x] UX-1: Non-TTY proceeds without prompt
- [x] UX-1: Ctrl+C aborts and cleans up
- [x] WRP-1: All wrappers tested
- [x] UX-2: README updated
