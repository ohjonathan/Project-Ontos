---
id: project-ontos-audit-doctor-rce-spec
deliverable_id: project-ontos-audit-doctor-rce
type: atom
status: active
phase: A
role: spec-author
family: codex
depends_on:
  - ontos_manual
  - ontology_spec
  - ontos_agent_instructions
  - project_ontos_audit_remediation_2026_07_dispatch_147
  - project_ontos_audit_remediation_release_line_tracker
---

# Spec — project-ontos-audit-doctor-rce

## 1. Goal

Close GitHub issue #147 / audit finding `D4b-trust-1`: running `ontos doctor` in a cloned untrusted repository must not execute a command read from repo-committed `.cursor/mcp.json`.

Also close `D4b-trust-2` by correcting `SECURITY.md`, which previously claimed all v4.0 MCP tools were read-only even though mutable tools are registered unless `ontos serve --read-only` is used.

## 2. Current Defect

The vulnerable path is:

- `ontos/commands/doctor.py` calls `check_cursor_mcp(repo_root)`.
- `check_cursor_mcp` inspects project scope before user scope.
- `ontos/core/cursor_mcp.py::inspect_cursor_ontos_config(scope="project")` validates shape, checks for `serve` and `--workspace`, then calls `probe_mcp_initialize(command, args)`.
- `ontos/core/mcp_shared.py::probe_mcp_initialize` runs `subprocess.run([command, *args])`.

A repo can therefore commit `.cursor/mcp.json` with:

```json
{
  "mcpServers": {
    "ontos": {
      "command": "python3",
      "args": ["-c", "<payload>", "serve", "--workspace", "/abs/repo"]
    }
  }
}
```

The existing shape checks all pass and the payload executes during a read-only diagnostic command.

## 3. Runtime Contract

- `ontos doctor` must continue reading project and user Cursor MCP config and reporting malformed or stale config as warnings.
- For project-scope Cursor config, `ontos doctor` must not run a direct initialize probe unless the command line matches Ontos's own managed launcher from `resolve_ontos_launcher()`.
- A managed launcher match requires the resolved executable to equal the resolved `resolve_ontos_launcher()` executable and the configured args to start with the launcher prefix args.
- Unmanaged project-scope commands remain warning-level diagnostics, not hard failures, so `ontos doctor` can still complete in an untrusted clone.
- User-scope Cursor config keeps the previous behavior because it is not repo-committed project input.
- The lower-level Cursor inspection helper may still support explicit unmanaged probing for direct callers/tests, but `ontos doctor` must pass the safe option for project scope.

## 4. Implementation

- Add a shared helper in `ontos/core/mcp_shared.py` that identifies Ontos-managed launcher command lines by comparing resolved executables and launcher prefix args.
- Extend `inspect_cursor_ontos_config` in `ontos/core/cursor_mcp.py` with an explicit `allow_unmanaged_probe` flag. When false and the config is unmanaged, return `code="unmanaged_probe_skipped"`, `ok=False`, with no `probe` object and no subprocess call.
- Update `ontos/commands/doctor.py` so `_run_doctor_command` calls `check_cursor_mcp(..., allow_project_unmanaged_probe=False)`. Direct `check_cursor_mcp` calls default to legacy opt-in behavior for compatibility.
- Update `SECURITY.md` to state that `--read-only` omits write tools and that writable server mode exposes `scaffold_document`, `log_session`, `session_end`, `promote_document`, and `rename_document`.

## 5. Tests

Add `tests/test_doctor_mcp_probe_regression.py` with:

- End-to-end hostile repo case: create a temp Ontos workspace with repo-local `.cursor/mcp.json` using `command="python3"` and `args=["-c", payload_that_writes_marker, "serve", "--workspace", abs_path]`; run `python -m ontos --json doctor`; assert the marker file does not exist and Cursor MCP reports a warning containing `probe skipped`.
- Positive managed case: monkeypatch `resolve_ontos_launcher()` to a fake Ontos launcher script that returns a valid MCP initialize response; inspect project config with `allow_unmanaged_probe=False`; assert the probe runs and returns `ok`.

Required verification:

```bash
.venv/bin/python -m pytest tests/test_doctor_mcp_probe_regression.py -q
.venv/bin/python -m pytest tests/ -q
git diff --check
bash .llm-dev/framework/scripts/verify-all.sh
```

Strict-P3 closure additionally requires:

```bash
bash .llm-dev/framework/scripts/verify-lifecycle.sh manifests/project-ontos-audit-doctor-rce.yaml --mode strict-p3
```

## 6. Out of Scope

- No changes under `ontos/mcp/`.
- No changes to serializer/parser files leased to #146, especially `ontos/core/schema.py` and `ontos/io/yaml.py`.
- No release actions: commit, tag, push, PR creation, merge, GitHub release, and issue closure remain maintainer-deferred.
