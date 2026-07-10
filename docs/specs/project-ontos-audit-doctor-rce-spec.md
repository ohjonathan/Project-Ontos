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

Lifecycle state: `code_fixed_evidence_pending`. Implementation baseline
`c8672e90f2382f4147ef61b4fba918969483e73e`; fixed implementation
`03c36e6ac999d2c411c13252baa2e8fcff60e6ed`. This revision supersedes the
prefix-only launcher contract that the original Phase A review approved.

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
- For project-scope Cursor config, `ontos doctor` must not run a direct initialize probe unless the command line exactly matches the managed argv Ontos generates from `resolve_ontos_launcher()`.
- A managed match requires the resolved executable and launcher prefix plus the complete suffix `serve --workspace <current-project-root>`, with only an optional final `--read-only`. Extra, duplicated, reordered, or separator-hidden tokens are rejected.
- Unmanaged project-scope commands remain warning-level diagnostics, not hard failures, so `ontos doctor` can still complete in an untrusted clone.
- User-scope managed config is pinned to the workspace it declares; unmanaged probing is disabled by default on both direct and doctor call paths.
- The lower-level helper may expose an explicit opt-in for a trusted caller, but omission of the flag must be safe.

## 4. Implementation

- Add `is_ontos_managed_serve_argv` in `ontos/core/mcp_shared.py`; compare the full normalized argv against the one Ontos would generate for the expected workspace.
- Extend `inspect_cursor_ontos_config` in `ontos/core/cursor_mcp.py` with an explicit `allow_unmanaged_probe` flag. When false and the config is unmanaged, return `code="unmanaged_probe_skipped"`, `ok=False`, with no `probe` object and no subprocess call.
- Update `ontos/commands/doctor.py` so `_run_doctor_command` calls `check_cursor_mcp(..., allow_project_unmanaged_probe=False)`. Both `allow_unmanaged_probe` and `allow_project_unmanaged_probe` default to false.
- Update `SECURITY.md` to state that `--read-only` omits write tools and that writable server mode exposes `scaffold_document`, `log_session`, `session_end`, `promote_document`, and `rename_document`.

## 5. Tests

`tests/test_doctor_mcp_probe_regression.py` is the five-case executable contract:

1. End-to-end hostile repo case: a repo-local Python payload does not execute and doctor reports `probe skipped`.
2. Positive managed case: the exact managed launcher argv still runs a valid initialize probe.
3. Trusted-launcher smuggling case: `scaffold --apply -- serve ...` is rejected without executing the launcher.
4. Duplicate workspace case: a second `--workspace` is rejected without executing the launcher.
5. Safe-default case: a direct caller that omits the opt-out flag remains protected.

Required verification:

```bash
.venv/bin/python -m pytest tests/test_doctor_mcp_probe_regression.py -q  # 5 passed
.venv/bin/python -m pytest tests/ -q
git diff --check
bash .llm-dev/framework/scripts/verify-all.sh
bash .llm-dev/framework/scripts/verify-changed-path-scope.sh \
  --manifest manifests/project-ontos-audit-doctor-rce.yaml \
  --base c8672e90f2382f4147ef61b4fba918969483e73e
```

Strict-P3 closure additionally requires:

```bash
bash .llm-dev/framework/scripts/verify-lifecycle.sh manifests/project-ontos-audit-doctor-rce.yaml --mode strict-p3
```

## 6. Out of Scope

- No changes under `ontos/mcp/`.
- No changes to serializer/parser files leased to #146, especially `ontos/core/schema.py` and `ontos/io/yaml.py`.
- No product-code changes during the evidence refresh unless a fresh wrapper-dispatched review identifies a blocker requiring a new implementation round.
- No receipt reconstruction. Existing prose artifacts without wrapper capture IDs and hashes remain historical, non-certifying context.
- GitHub issue #147 is reopened with the evidence-pending contract; release certification remains pending on a separate axis.
