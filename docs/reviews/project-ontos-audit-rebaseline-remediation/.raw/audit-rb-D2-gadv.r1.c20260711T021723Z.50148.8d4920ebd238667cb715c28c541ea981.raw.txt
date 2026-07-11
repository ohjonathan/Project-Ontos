---
id: audit-rb-D2-gadv
deliverable_id: project-ontos-audit-rebaseline-remediation
phase: D.2
role: adversarial
family: gemini
evidence_labels_used: [static-inspection]
status: completed
---

# Adversarial Review — project-ontos-audit-rebaseline-remediation / D.2 / gemini

## 1. Input boundary attestation
The prompt successfully exposed the operational preflight, diff/artifact bytes, and spec/reference bytes only. No prior correctness claims, test suite outcomes, or alignment/peer verdicts were prefilled as factual inputs. The input boundary is clean and compliant.

## 2. Invariant re-derivation
Based on the spec and diff, we derive the following core system invariants:
- **Registry Validity Invariant**: All registry and child-manifest collections must be typed, and every row validated, before consumption. Malformed records must be quarantined, and the validator must exit with code `1`, never raising unhandled exceptions or exiting with code `2`.
- **Advisory Lock Invariant**: Lock files must be created as single-link regular files with no-follow/reparse protection. The lock must fail if the path is a symlink, junction, directory, or multi-link inode.
- **Log Write Invariant**: Every session log write (including Markdown and `.ontos/session_archived` marker) must be workspace-contained and follow the no-follow pipeline, refusing collisions with existing logs and returning exit `3` with warning metadata on marker failure.
- **Serializer Invariant**: IDs must match `^[A-Za-z0-9](?:[A-Za-z0-9_.-]*[A-Za-z0-9])?$`. The YAML loader must validate types and prevent coercion of non-string IDs.
- **Activation Invariant**: Activation must validate `required_version` against the repository configuration, and try candidate runtimes in a strict order, halting on failure without fallback if a terminal error (like version incompatibility) is encountered.

## 3. Assumption attack
| Assumption | Why it might be wrong | Impact if wrong | Reproduction / proof |
|---|---|---|---|
| Falling back to alternative runtimes (`python3 -m ontos`, PATH `ontos`) when the repository runtime is incompatible is safe. | The fallback runtimes might be older versions of Ontos that do not implement or check `required_version`, bypassing constraints. | Silent bypass of version checks, configuration corruption, or invalid state write. | Configure a workspace with `required_version = ">=4.7.0, <5.0.0"`. If the repository runtime is version 4.6.0, activation falls back to a global PATH `ontos` (version 3.0.0) which succeeds silently. |
| Downstream consumers are safe when malformed program rows are quarantined and ignored. | Downstream checks (such as GitHub epic checklist) operate only on the normalized program set, silently ignoring the missing program instead of failing. | False-green validation of incomplete/malformed registry state. | Introduce a type error in program row `#146`. The validator quarantines it. Downstream validation passes because it only checks the normalized set, skipping `#146` entirely. |
| Using `os.replace` to rename staged files is atomic and immune to symlink swaps. | A concurrent process can swap the target path with a symlink pointing outside the workspace between the check and the replacement. | Unsafe file overwrite outside the workspace. | Intercept the thread after the target check but before `os.replace` execution, swap target path with a symlink to a system file, and verify it is overwritten. |
| Ancillary log markers can fail without affecting primary log write integrity. | If the write to `.ontos/session_archived` fails due to permissions, the command exits with code 3. If CI/CD ignores warning exit codes, it might push without the archive marker. | Out-of-sync audit trail and unarchived sessions. | Write-protect `.ontos/session_archived`, run `ontos log`, verify exit 3 but log is created and pushed. |

## 4. Failure mode analysis
| Failure | How it happens | Would we notice? | Reproduction / proof |
|---|---|---|---|
| Fallthrough of version incompatibility to looser tier | If local repository runtime fails activation with incompatible version, fallback to PATH `ontos` executes. | Yes, the tool will execute, but it might not enforce version checks. | Run activation where local runtime fails compatibility check; verify PATH runtime runs instead of a terminal halt. |
| JSON parsing/sorting crash on date-like or numeric IDs | Date-like or integer IDs are loaded as python `datetime.date` or `int` objects and passed to string-only APIs. | Yes, a `TypeError` will be raised by the Python interpreter. | Create a document with `id: 2026-07-10` (unquoted) and run `ontos map`. |
| Symlink escape via default `logs_dir` | If `docs/logs` is a symlink pointing outside the workspace, log writes follow it if no-follow check is skipped on default paths. | Yes, files are written outside the workspace. | Create a symlink `docs/logs -> /tmp/outside` and write log without configuring custom `logs_dir`. |

## 5. Diagram completeness attack
- **State Machine vs. Prose mismatch**: The state machine diagram shows `Loose_Falsification` returning to `D4_Fix` on a "reproducible catch", but it does not specify how verification failures map to D.5 or the exact return logic to D.2 on fix rerun.
- **Component Diagram vs. Implementation mismatch**: The architecture diagram lacks a direct edge from the Validator/Control Plane to the CLI/MCP Contracts, even though CLI execution (e.g. `activate` or `link-check`) directly invokes the validator.

## 6. Edge case inventory
- **Empty / Null / Falsy**: Empty `required_version = ""` or missing program rows in `manifests/project-ontos-audit-remediation-registry.yaml`.
- **Malformed / Missing**: Invalid comparisons in version ranges (e.g. `>>=4.7.0`) or missing required fields in leases.
- **Duplicate**: Duplicate program IDs or duplicate lease records in the registry.
- **Type-edge / Boundary-order**: Unquoted date-like and numeric IDs parsed as non-string YAML values.
- **Encoding / Normalization**: Unicode path differences on case-insensitive filesystems (macOS vs. Linux).

## 7. Security surface
- **Workspace Escape**: Writing logs to symlinked directories pointing outside the workspace.
- **TOCTOU**: Renaming staged files using name-based path operations without holding directory file descriptors.
- **Arbitrary Code Execution**: Execution of untrusted runtimes searched from path/environment variables.
- **Information Disclosure**: Exposure of live GitHub metadata in log outputs on transport failure.

## 8. Issues found

### Blocking (Critical)
None due to the `static-inspection` evidence cap.

### Should-fix (Major)

| ID | Description | Location | Evidence | Reproduction | Observed vs expected | Suggested action |
|----|-------------|----------|----------|--------------|----------------------|------------------|
| S-1 | Runtime Activation Fallback bypasses version constraints. | `AGENTS.md` and `docs/reference/Migration_v3_to_v4.md` | static-inspection | Configure a workspace with `required_version = ">=4.7.0, <5.0.0"`. If the repository runtime is version 4.6.0, activation falls back to a global PATH `ontos` (version 3.0.0) which succeeds silently. | Observed: Fallback runtimes execute when the preferred runtime is incompatible. Expected: Incompatibility must be terminal to prevent bypass. | Halt immediately when the repository runtime is incompatible rather than falling back. |
| S-2 | Malformed program quarantine causes downstream silent passes (Tier-Fallthrough). | `scripts/validate-audit-remediation-registry.py` | static-inspection | Introduce a type error in program row `#146`. The validator quarantines it. Downstream validation passes because it only checks the normalized set, skipping `#146` entirely. | Observed: Downstream checks ignore quarantined programs. Expected: Quarantined programs must fail downstream checks. | Enforce that normalized programs match the static expected list exactly. |
| S-3 | Inode validation TOCTOU in file rename/replace. | `ontos/core/context.py` | static-inspection | Intercept the thread after the target check but before `os.replace` execution, swap target path with a symlink to a system file, and verify it is overwritten. | Observed: Target files are replaced via name-based paths post-validation. Expected: Open descriptors must be held to avoid directory swapping. | Anchoring file mutations via directory descriptors. |
| S-4 | Non-string document IDs parsed as YAML objects crash sorting consumers. | `ontos/core/schema.py` and `ontos/io/files.py` | static-inspection | Create a document with `id: 2026-07-10` (unquoted) and run `ontos map`. | Observed: Date-like/numeric YAML values coerce to non-strings, crashing sorting/dictionary operations. Expected: Rigid string type validation upon loading. | Reject non-string IDs immediately at the loader level. |

### Minor

| ID | Description | Location | Evidence | Reproduction | Observed vs expected | Suggested action |
|----|-------------|----------|----------|--------------|----------------------|------------------|
| M-1 | Unchecked command verification target defaults. | `ontos/commands/verify.py` | static-inspection | Run `ontos verify` without target arguments in a dirty repository. | Observed: Runs check against default workspace regardless of checkout state. Expected: Require explicit path targets or check safety. | Prompt or warn the user when target arguments are omitted. |
| M-2 | Redundant logging of deleted init logs. | `.ontos-internal/logs/` | static-inspection | Check `Ontos_Context_Map.md` for references to deleted log files like `2026-07-02_init.md`. | Observed: Deleted log files remain in context map index. Expected: Map generation should cleanly sync references. | Re-generate context maps to purge references to deleted files. |

## Verdict
Request changes

The implementation contains several tier-fallthrough soundness issues: version incompatibility fallback logic bypasses repository constraints, and malformed program quarantine allows downstream checks to pass silently. Inode verification remains susceptible to TOCTOU directory swapping during replacement.

| Attack surface | In scope? | Evidence attempted | Result |
|---|---|---|---|
| Activation version constraints fallback | Yes | static-inspection | Found S-1: fallthrough to global runtime bypasses version requirements |
| Control-plane program validation quarantine | Yes | static-inspection | Found S-2: quarantined programs are silently omitted from downstream verification |
| File mutation and rename race conditions | Yes | static-inspection | Found S-3: name-based rename is vulnerable to concurrent symlink swaps |
| Document ID schema validation | Yes | static-inspection | Found S-4: YAML loader fails to validate ID types, leading to crash |
| Windows-specific locking backend | No | None | Out of scope per OPERATIONAL PREFLIGHT; no physical Windows runner available in local static execution |
| Release build/packaging verification | No | None | Out of scope per spec nonclaims; TestPyPI download verification requires a tag run |

## Notes
The review was performed entirely via static inspection of the provided diff and specification contents to comply with the negative constraints and evidence cap.
