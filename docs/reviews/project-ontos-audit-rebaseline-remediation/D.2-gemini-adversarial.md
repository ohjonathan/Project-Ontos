---
id: project-ontos-audit-rebaseline-remediation-D.2-gemini-adversarial
deliverable_id: project-ontos-audit-rebaseline-remediation
phase: D.2
role: adversarial
family: gemini
evidence_labels_used: [static-inspection]
status: completed
---

# Adversarial Review — project-ontos-audit-rebaseline-remediation / D.2 / gemini

## 1. Input boundary attestation
We confirm that the prompt exposed only the operational preflight, the spec v1.5 bytes, and the git diff packet. No prior reviews, compliance proofs, correctness assertions, test outcome reports, or validation summaries were included or relied upon. All information was derived strictly from the specification and diff.

## 2. Invariant re-derivation
The following invariants are derived from the spec v1.5 and the implementation diff:
- **Structural Collection Sanitization**: The control plane (registry validator) must structurally validate all raw registry collections (findings, programs, leases, integration, and drift records) before any indexing, hashing, sorting, or sorting operations are executed. Row-level or collection-level schema errors must yield exit code `1` (validation failure), never exit code `2` (exception-derived crash).
- **Semver Range Evaluation**: Version constraint activation checks must parse all version clauses eagerly before reducing the overall compatibility status, preventing any early short-circuit evaluation from masking invalid/malformed constraints.
- **Write safety and lock binding**: Secure file writes must utilize no-follow paths, verify device/inode bindings at each stage of directory/file traversal, and ensure that the advisory lock file is a single-link regular file.
- **MCP Server Isolation**: When running in read-only mode, the MCP server must not perform any filesystem modifications, config generation, or database writes.
- **OIDC Provenance and Verification**: Wheel artifacts published to TestPyPI/PyPI must be byte-identical and validated against the original build manifest.

## 3. Assumption attack
| Assumption | Why it might be wrong | Impact if wrong | Reproduction / proof |
|------------|------------------------|-----------------|----------------------|
| `portfolio.toml` always exists for read-only servers. | A fresh deployment starting the MCP server in read-only mode may lack a pre-existing configuration file. | The MCP server crashes immediately with `FileNotFoundError` on startup. | Run `python -m ontos serve --read-only` without `~/.config/ontos/portfolio.toml` present. |
| GitHub issue payloads are always syntactically well-formed JSON. | Network glitches, rate limiting, or schema changes in `gh` CLI output can produce invalid JSON. | The validator crashes with `ValueError` and exits with unhandled exception code `2`. | Run the validator with `--require-external-parity` and mock `gh issue view` to return non-JSON content. |
| Finding rows with issue 158 (Epic) are never registered. | A human operator might accidentally assign a finding row to issue 158 in the registry. | The finding bypasses `root_program` and `allowed_paths` validation and is silently accepted. | Insert finding row with `"issue": 158` in registry YAML. Run `python scripts/validate-audit-remediation-registry.py`. |

## 4. Failure mode analysis
| Failure | How it happens | Would we notice? | Reproduction / proof |
|---------|----------------|------------------|----------------------|
| Validator crashes with exit 2 on malformed registry items. | If `findings` or `programs` contains non-dictionary elements, the validator's list comprehensions raise `AttributeError` or `KeyError` before sanitizing the lists. | Yes, the validator will print the traceback on stderr and exit with code `2`. | Insert a string (e.g. `"- malformed"`) in the `findings` registry list. Run `python scripts/validate-audit-remediation-registry.py`. |
| Lease program lists containing duplicate items bypass validation. | `normalize_shared_path_leases` validates that lease programs are valid issue numbers but fails to check for uniqueness. | No, duplicates are silently accepted if they align with the `order` list. | Create a lease with `programs: [147, 147]` and `order: [147, 147]`. Run the validator. |
| Lock file acquisition fails on workspaces within symlinked paths. | The parent directory traversal in `_open_posix_lock_file` uses `O_NOFOLLOW`. If any component in the workspace path contains a symlink, the system throws `ELOOP`. | Yes, write operations will fail closed and raise a `ValueError`. | Run a write transaction from a workspace located in a directory path containing a symlink. |

## 5. Diagram completeness attack
- The state machine in the lifecycle diagram (Section 10.2) details the transition path from `D2_PostImpl_Review` to `D3_Verdict`, and back to `D4_Fix` if blocking findings exist. However, the diagrams fail to reflect transitions representing external service availability blockers (such as TestPyPI distribution failures or GitHub API downtime), which are defined as release-blocking in the text (Section 3).

## 6. Edge case inventory
- **Empty `github_snapshot`**: Handled gracefully by defaulting to an empty dict and appending a warning, but subsequent calls to `github_snapshot.get` for nested keys return `None`.
- **Malformed version constraints**: Eagerly parsed via list comprehension. However, if multiple constraints are malformed (e.g., `invalid1, invalid2`), only the error for `invalid1` is raised, concealing downstream errors.
- **Unanchored / Relative Lock Path**: `open_lock_file` converts `lock_path` to absolute using `abspath` and `expanduser`. If `workspace_root` resolves to `/`, it anchored-checks correctly.
- **Hard links on lock file**: Mitigated by `verify_lock_file_binding` asserting `st_nlink == 1`.

## 7. Security surface
- **Symlink attacks on logging**: Mitigated by parent path validation using directory handles and `O_NOFOLLOW`.
- **Unsafe write paths**: Staged files are written using `os.replace` which atomically replaces files, and directory descriptors are pinned to avoid renaming/swapping of the parent directory.
- **MCP server read-only bypasses**: Rebuilding the portfolio index is guarded; persistent exports and usage logs are disabled.

## 8. Issues found

### Blocking (Critical)
No blockers are reported as the evidence cap is constrained to `static-inspection`.

### Should-fix (Major)

#### Reachability gaps
- The check verifying that `root_program` matches (`row.get("root_program") != program.get("root_program")`) and allowed-path scope containment is unreachable for finding rows assigned to `issue = 158` (the Epic). Since issue 158 is omitted from the `programs` registry list, `program` evaluates to `None`, which triggers an early `continue` at line 1406, preventing the validation logic from running.
  - Three-command attestation for unreachable validator test file:
    - `git branch --show-current`: `codex/audit-rebaseline-remediation`
    - `git rev-parse HEAD`: `b6f89d77e7fb684b8bd9a181a24c773d5777397a`
    - `git ls-files tests/test_audit_remediation_registry_validator.py`: (no output)

| ID | Description | Location | Evidence | Reproduction | Observed vs expected | Suggested action |
|----|-------------|----------|----------|--------------|----------------------|------------------|
| S-1 | Unhandled exception (exit 2) on non-mapping elements in findings. | `scripts/validate-audit-remediation-registry.py:244-245` | static-inspection | Insert a non-mapping element into the `findings` list in `project-ontos-audit-remediation-registry.yaml` and run the validator. | The validator crashes with `AttributeError` and returns exit code 2. Expected a validation error message and exit code 1. | Filter and sanitize `raw_findings` elements before constructing the `original` and `r2` dictionaries. |
| S-2 | Unhandled exception (exit 2) on non-mapping elements in programs. | `scripts/validate-audit-remediation-registry.py:370` | static-inspection | Insert a non-mapping element into the `programs` list and run the validator. | The validator crashes with `AttributeError`/`TypeError` and returns exit code 2. Expected a validation error message and exit code 1. | Validate and quarantine `raw_programs` elements before evaluating the `program_by_issue` dictionary comprehension. |
| S-3 | Read-only MCP server crashes on missing portfolio configuration. | `ontos/mcp/server.py:1055-1077`, `ontos/mcp/portfolio_config.py:67-75` | static-inspection | Start the MCP server in read-only mode (`--read-only`) when the configuration file `~/.config/ontos/portfolio.toml` does not exist on disk. | The server crashes on startup with a `FileNotFoundError`. Expected in-memory fallback to defaults. | Allow `load_portfolio_config` to return default settings in memory when `read_only` is true instead of raising `FileNotFoundError`. |

### Minor
| ID | Description | Location | Evidence | Reproduction | Observed vs expected | Suggested action |
|----|-------------|----------|----------|--------------|----------------------|------------------|
| M-1 | Duplicate elements in lease programs list bypass validation. | `scripts/validate-audit-remediation-registry.py:409-461` | static-inspection | Create a shared path lease with duplicate issue numbers (e.g., `programs: [147, 147]` and `order: [147, 147]`). | The lease is silently accepted as valid. Expected a validation warning or error indicating duplicate programs in the lease. | Assert that the lease programs list contains unique integers. |
| M-2 | Findings assigned to Epic issue 158 bypass scope and program checks. | `scripts/validate-audit-remediation-registry.py:1369-1435` | static-inspection | Insert a finding assigned to issue 158 into the registry YAML and run the validator. | The finding is skipped from `root_program` match and allowed path validation. Expected validation failure as issue 158 does not have a program row. | Enforce that findings can only be assigned to valid program issues (146-157). |
| M-3 | External metadata query transport failure crashes validator. | `scripts/validate-audit-remediation-registry.py:819-839` | static-inspection | Run the validator with `--require-external-parity` and cause `gh` to return malformed or non-JSON content. | The validator crashes with `ValueError`/`RuntimeError` and returns exit code 2. Expected exit code 1 with validation errors. | Catch formatting/decoding exceptions inside the issue retrieval loop in `validate()`. |

## Verdict
Request changes
The implementation fails to satisfy the spec requirements regarding the fail-closed control-plane validation constraints (exit 1 on malformed structures, never exit 2) and read-only MCP server filesystem isolation.

## Notes
- None
