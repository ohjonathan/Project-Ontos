---
id: project-ontos-audit-serializer-corruption-spec
deliverable_id: project-ontos-audit-serializer-corruption
type: atom
role: spec-author
family: codex
version: 1.0
status: draft
depends_on:
  - project_ontos_audit_remediation_2026_07_dispatch_146
  - project-ontos-fable-repo-audit-2026-07
---

# Spec v1.0 - project-ontos-audit-serializer-corruption

## 1. Overview

This deliverable fixes GitHub issue #146 / audit finding `D2b-roundtrip-3` for v4.7.1. A document whose frontmatter is valid before an Ontos write must remain parseable and semantically identical after:

- `ontos promote`
- `ontos schema-migrate --apply` through `ontos/commands/migrate.py`
- MCP `promote_document`

Risk level: high. The existing serializer can corrupt user-authored YAML silently and the MCP path can run without a human reviewing the rewritten file.

## 2. Scope

In scope:

- Replace `ontos/core/schema.py::serialize_frontmatter` internals so scalar and list values are emitted with PyYAML-safe quoting and escaping.
- Keep the existing public function name and field-order contract.
- Update `ontos/io/yaml.py::dump_yaml` so it is the shared PyYAML wrapper used by this fix.
- Add `ontos/io/yaml.py::assert_frontmatter_roundtrip(expected, yaml_text)` for pre-write validation.
- Call the assertion before buffering writes in `ontos/commands/promote.py`, `ontos/commands/migrate.py`, and `ontos/mcp/writes.py::_promote_document_impl`.
- Add `tests/test_frontmatter_roundtrip_regression.py` with the four audit fixtures.

Out of scope:

- No changes to `ontos/commands/log.py`; the #148 follow-up will route log writes later.
- No parser consolidation beyond the assertion helper.
- No changes to `ontos/core/body_refs.py`, `ontos/cli.py`, unrelated MCP modules, `.pre-commit-config.yaml`, or `.ontos/scripts/`.
- No release actions: commit, tag, push, PR, merge, release, and issue closure remain maintainer-deferred.

## 3. Dependencies

Prerequisites already verified:

- `docs/reviews/2026-07-02-fable-repo-audit.md` contains `D2b-roundtrip-3` and the four fixtures.
- `ontos/core/schema.py` still contains the unsafe `_serialize_field` implementation.
- `pyproject.toml` and `requirements.txt` declare PyYAML as a hard dependency.
- `docs/trackers/project-ontos-audit-remediation-release-line.md` leases the required code paths to #146.
- `scripts/llm-dev doctor` passes for the adopter setup.

The implementation may use PyYAML in this hotfix. The old `STDLIB ONLY` comment in `schema.py` is superseded for serialization because the audit and package metadata establish PyYAML as required runtime dependency.

## 4. Technical Design

`ontos/core/schema.py`:

- Keep `serialize_frontmatter(fm: Dict[str, Any]) -> str`.
- Preserve the current key ordering: ordered Ontos fields first, remaining keys in insertion order.
- Remove `_serialize_field` and all hand-built YAML branches.
- For each ordered single-field mapping, call `ontos.io.yaml.dump_yaml({key: value}, default_flow_style=<mode>)`.
- Use `default_flow_style=None` for list values so simple lists remain inline (`depends_on: [a, b]`) while unsafe list items are quoted (`depends_on: ['design_v1,final']`).
- Use `default_flow_style=False` for scalars and dictionaries so single-field mappings remain block mappings (`title: 'Q3 plan: "final" version'`), not `{title: ...}`.
- Strip trailing document terminators and blank lines from PyYAML output before joining field blocks with `\n`.

`ontos/io/yaml.py`:

- Change `dump_yaml` to call `yaml.safe_dump`, not `yaml.dump`.
- Set `sort_keys=False` and `allow_unicode=True`.
- Add `assert_frontmatter_roundtrip(expected, yaml_text)`:
  - parse `---\n{yaml_text}\n---\n` with `parse_frontmatter_content`;
  - compare the parsed mapping with `expected`;
  - raise `ValueError("Serialized frontmatter failed round-trip validation")` with useful mismatch context if parsing fails or values differ.

Write paths:

- In `promote.py`, serialize `new_fm`, assert the round trip, then build `new_content` and `ctx.buffer_write`.
- In `migrate.py`, serialize `new_fm`, assert the round trip, then build `new_content` and `ctx.buffer_write`.
- In `writes.py::_promote_document_impl`, serialize mutated `frontmatter`, assert the round trip, then build `document` and `ctx.buffer_write`.

Failure behavior:

- A serializer regression should fail before a file write is buffered.
- Existing command-level exception handling remains in place and surfaces a failed promote/migrate/write-tool result.

## 5. Open Questions

All implementation decisions are resolved.

| Question | Decision | Authority |
|----------|----------|-----------|
| Preserve inline simple lists or switch all lists to block style? | Preserve inline simple lists where PyYAML can safely do so. | Existing `tests/core/test_schema.py` asserts `depends_on: [a, b]`. |
| Should `log.py` be fixed here? | No. | Dispatch #146 explicitly excludes it. |
| Should schema.py keep the stdlib-only claim? | No, update the comment to reflect PyYAML-backed serialization. | Audit `D2b-roundtrip-3` and `pyproject.toml` dependency. |

## 6. Test Strategy

Unit regression:

- `tests/test_frontmatter_roundtrip_regression.py::test_serializer_roundtrips_audit_fixture` parametrizes the four audit fixtures and asserts exact dict equality after `serialize_frontmatter -> parse_frontmatter_content`.
- `test_assert_frontmatter_roundtrip_accepts_safe_output` covers the new helper on safe output.
- `test_assert_frontmatter_roundtrip_rejects_semantic_drift` proves the helper fails on a deliberately mismatched serialized payload.

Targeted suites:

- `.venv/bin/python -m pytest tests/test_frontmatter_roundtrip_regression.py -q`
- `.venv/bin/python -m pytest tests/core/test_schema.py tests/commands/test_promote_parity.py tests/commands/test_migrate_parity.py tests/mcp/test_write_tools.py -q`

Final validation:

- `.venv/bin/python -m pytest tests/ -q`
- `.venv/bin/python -m pytest tests/test_frontmatter_roundtrip_regression.py -q`
- `git diff --check`
- `bash .llm-dev/framework/scripts/verify-all.sh`
- `bash .llm-dev/framework/scripts/verify-lifecycle.sh manifests/project-ontos-audit-serializer-corruption.yaml --mode strict-p3`

## 7. Migration / Compatibility

This is a backward-compatible bug fix. The public Python function remains `serialize_frontmatter(fm) -> str`, and caller behavior stays string-based.

Formatting may change for unsafe values because PyYAML will add quotes where needed. That is intended and required. Simple scalar and simple inline-list output should remain familiar enough to avoid broad fixture churn.

Rollback is straightforward: revert the code and test changes in the leased paths. No data migration is introduced.

## 8. Risk Assessment

Primary risks:

- PyYAML formatting differences could break overly exact tests. Mitigation: preserve field order and simple inline-list behavior; update only tests whose exact expectations were unsafe.
- A write path could serialize safely but skip the pre-write assertion. Mitigation: explicit call-site edits in all three leased paths and D.2 review focus.
- A future writer could call `serialize_frontmatter` without checking. Mitigation: `serialize_frontmatter` itself becomes safe; the assertion is defense in depth for high-risk rewrite paths.

## 9. Exclusion List

Do not:

- edit `ontos/commands/log.py`;
- edit parser consolidation surfaces outside the named helper;
- edit `ontos/core/body_refs.py`;
- edit `ontos/cli.py`;
- edit unrelated MCP files;
- edit `.pre-commit-config.yaml` or `.ontos/scripts/`;
- commit, tag, push, create a PR, merge, release, or close issue #146.

## 10. Diagrams

### 10.1 Architecture / Component Diagram

```text
[CLI promote] ----\
[CLI migrate] -----+--> [serialize_frontmatter in ontos/core/schema.py]
[MCP promote] ----/                  |
                                      v
                         [dump_yaml in ontos/io/yaml.py]
                                      |
                                      v
                         [PyYAML safe_dump]
                                      |
                                      v
                         [round-trip assertion]
                                      |
                                      v
                         [SessionContext.buffer_write]
```

All three writers continue to own their existing command/MCP error handling. The shared serializer is the only formatting authority.

### 10.2 Sequence Diagram

```text
writer -> serialize_frontmatter: frontmatter dict
serialize_frontmatter -> dump_yaml: one-field mapping
dump_yaml -> PyYAML safe_dump: safe scalar/list emission
serialize_frontmatter -> writer: yaml_text
writer -> assert_frontmatter_roundtrip: expected dict + yaml_text
assert_frontmatter_roundtrip -> parse_frontmatter_content: fenced yaml
parse_frontmatter_content -> assert_frontmatter_roundtrip: parsed dict
assert_frontmatter_roundtrip -> writer: ok or ValueError
writer -> SessionContext: buffer_write only after ok
```

Error path: if parse fails or the mapping changes type/content, the assertion raises before the buffered write.

## 11. Contract enumeration checklist

| Enum table (§ref) | Enum value | Implementation anchor | Anchor type |
|-------------------|------------|-----------------------|-------------|
| §2 write paths | `promote` | `ontos/commands/promote.py::apply_promotion` assertion call | function |
| §2 write paths | `schema-migrate` | `ontos/commands/migrate.py::_run_migrate_command` assertion call | function |
| §2 write paths | `mcp-promote-document` | `ontos/mcp/writes.py::_promote_document_impl` assertion call | function |
| §6 fixtures | `embedded-quotes` | `tests/test_frontmatter_roundtrip_regression.py` fixture `Q3 plan` | test |
| §6 fixtures | `comma-list-item` | `tests/test_frontmatter_roundtrip_regression.py` fixture `design_v1,final` | test |
| §6 fixtures | `quoted-scalar-types` | `tests/test_frontmatter_roundtrip_regression.py` fixture `4.10`, `007`, `no` | test |
| §6 fixtures | `hash-leading-value` | `tests/test_frontmatter_roundtrip_regression.py` fixture `#42 follow-up` | test |

## 12. Helper-divergence disclosure

| Helper (path / signature) | Existing consumer shape | New consumer need | Disposition | Rationale |
|---------------------------|-------------------------|-------------------|-------------|-----------|
| `ontos/io/yaml.py::dump_yaml(data, default_flow_style=False)` | Existing unused PyYAML wrapper returns YAML text. | Safe frontmatter field emission from `serialize_frontmatter`. | Extend | Change to `safe_dump`, preserve signature compatibility, and allow `default_flow_style=None`. |
| `ontos/io/yaml.py::parse_frontmatter_content(content)` | Existing parse helper used by loaders and commands. | Re-parse serialized frontmatter before writes. | Extend | Add a new assertion helper beside the parser instead of duplicating parse logic at each writer. |

## A.5 self-review

- No TBD or placeholder content remains: direct inspection.
- A developer can implement from this spec: paths, helper signatures, and call sites are named.
- Two text diagrams are present and include the error path.
- Open questions are resolved.
- Referenced paths were inspected in the current repo.
