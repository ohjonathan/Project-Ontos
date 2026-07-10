---
id: project-ontos-audit-serializer-corruption-B.1-claude-sonnet-peer
deliverable_id: project-ontos-audit-serializer-corruption
phase: B.1
role: peer
family: claude-sonnet
evidence_labels_used: []
status: completed
---

# Peer Review - project-ontos-audit-serializer-corruption / B.1 / claude-sonnet

## 1. Completeness Check

- Public API preserved: §4 keeps `serialize_frontmatter(fm: Dict[str, Any]) -> str` and the existing `field_order` list / insertion-order tail. Verified against the live `ontos/core/schema.py:312-333` — matches exactly.
- All three named write paths are covered with call-site-level precision, and each anchor was checked against the current tree: `apply_promotion` (`ontos/commands/promote.py:116`, serialize at 141, `ctx.buffer_write` at 144), `_run_migrate_command` (`ontos/commands/migrate.py:72`, serialize at 204, `buffer_write` at 209), `_promote_document_impl` (`ontos/mcp/writes.py:584`, serialize at 627, `buffer_write` at 636). All three anchors in §11 are accurate, not aspirational.
- `ontos/commands/log.py` exclusion is consistent across spec §2/§9, the dispatch, and the manifest's `forbidden_paths`. Confirmed `log.py` uses its own `_build_frontmatter` (never calls `serialize_frontmatter`), so excluding it doesn't leave a live corruption path unpatched.
- The two additional `serialize_frontmatter` call sites in `writes.py` (scaffold-document creation, ~L421-434 and ~L493-515) are correctly left out of the assertion requirement — those write brand-new frontmatter, not a re-parse of a pre-existing user file, so they're outside `D2b-roundtrip-3`'s claim. Not a gap.
- The four audit fixtures (`Q3 plan…`, `design_v1,final`, `4.10`/`007`/`no`, `#42 follow-up`) are enumerated in §6 and §11 and map 1:1 to the audit's verification evidence block. I independently reproduced all four through the proposed `dump_yaml`/`safe_dump` design (see §2) and all four round-trip correctly.
- PyYAML dependency claim (§3, "hard runtime dependency") checked against `pyproject.toml:31` and `requirements.txt:2` — accurate.
- `dump_yaml` has no other production callers (`ontos/io/__init__.py` only re-exports it) — the Helper-divergence table's "Extend" disposition is safe with zero blast radius outside this lease.

## 2. Quality Assessment

The spec is unusually well-grounded: every file/line/function anchor I spot-checked against the actual repo state was correct, and the core technical design (per-field `dump_yaml({key: value}, default_flow_style=<mode>)` calls, joined with `\n`) is precise enough to hand to a mid-level engineer without further decisions. I ran the described approach against Python/PyYAML directly:

```
depends_on: [a, b]                          # simple list stays inline
depends_on: ['design_v1,final']             # unsafe item quoted, no re-split
title: 'Q3 plan: "final" version'           # embedded quotes safe
version: '4.10'  build: '007'  flag: 'no'   # type-preserving quotes
note: '#42 follow-up'                       # no comment-null flip
```
All four fixtures round-trip byte-for-semantic-equality through `serialize_frontmatter → parse_frontmatter_content` under this design. §5's open questions are genuinely resolved, not deferred. §7's compatibility framing (formatting may change, function contract doesn't) is accurate and appropriately scoped.

The one real gap is in the `assert_frontmatter_roundtrip` design (§4, `ontos/io/yaml.py`), detailed below — it reuses the fence-splitting `parse_frontmatter_content` where a direct `parse_yaml` call would avoid a self-inflicted false-positive failure mode.

## 3. Issues Found

### Blocking

| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|

### Should-fix

| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| SF-1 | `assert_frontmatter_roundtrip` is specified to wrap `yaml_text` as `---\n{yaml_text}\n---\n` and re-parse it with `parse_frontmatter_content`, which does a naive `content.split('---', 2)` (not fence-aware). PyYAML's single-quote folding can legitimately render a field value containing a literal `---` line (e.g. a multi-line `summary`/`note` with a markdown horizontal rule) as a continuation line inside the quoted scalar. The split then cuts mid-scalar, `parse_yaml` throws a `yaml.YAMLError`, and `parse_frontmatter_content` re-raises `ValueError("Invalid YAML frontmatter: …")` — a **false-positive** round-trip failure on an otherwise-safe value that previously wrote successfully. This is exactly the write-blocking failure mode this hotfix is supposed to avoid introducing, on exactly the write paths (`promote`, `migrate`, autonomous MCP `promote_document`) the spec is hardening. | `docs/specs/project-ontos-audit-serializer-corruption-spec.md` §4 (`ontos/io/yaml.py::assert_frontmatter_roundtrip`) | Confirmed with the actual `ontos/io/yaml.py:parse_frontmatter_content` splitter logic (`content.split('---', 2)`, `ontos/io/yaml.py:60`). | `yaml.safe_dump({'summary': 'line1\n---\nline2'}, default_flow_style=False, sort_keys=False, allow_unicode=True)` → `"summary: 'line1\n\n  ---\n\n  line2'\n"`. Wrapping this in `---\n…\n---\n` and calling `.split('---', 2)` yields `parts[1] == "\nsummary: 'line1\n\n  "`, which is invalid YAML → `parse_yaml` raises. No test in the four mandated fixtures exercises this because none contain a literal `---` substring, so it will not be caught by the required regression suite. | Since `assert_frontmatter_roundtrip` only needs to validate the frontmatter mapping (§4: "compare the parsed mapping with expected"), have it call `ontos.io.yaml.parse_yaml(yaml_text)` directly — `yaml_text` is already fence-free — instead of wrapping in `---` and routing through the fence-splitting `parse_frontmatter_content`. This removes the false-positive class entirely with no loss of coverage. |

### Minor

| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| M-1 | At the MCP write path, a bare `ValueError` from `assert_frontmatter_roundtrip` is not an `OntosUserError`/`OntosInternalError`, so `_dispatch`'s generic `except Exception` handler (`ontos/mcp/writes.py:373-381`) catches it and returns a generic `E_INTERNAL "Unexpected exception… Check server logs and retry"` envelope. The write is correctly blocked (no silent corruption), but "retry" is misleading for a deterministic assertion failure, and every other raise in `writes.py` uses the structured `OntosUserError` taxonomy with a specific `code=`. The spec doesn't say whether the assertion failure should be translated into that taxonomy at the `writes.py` call site. | `docs/specs/project-ontos-audit-serializer-corruption-spec.md` §4 "Write paths" / §4 "Failure behavior"; `ontos/mcp/writes.py:373-381` | Read `_dispatch`'s exception handling chain directly. | N/A (code-path read, not executed) | Either note in §4 that the `writes.py::_promote_document_impl` call site should wrap the assertion in an `OntosUserError`/`OntosInternalError` with a serializer-specific code, or explicitly accept the generic `E_INTERNAL` envelope as intended behavior for defense-in-depth failures. |
| M-2 | `default_flow_style=None` for list values renders *any* simple list containing a string with a space as inline flow style (e.g. `concepts: [a b, c]`), not the multi-line dash format the current hand-rolled serializer produces for such lists. This is a silent formatting change beyond the four fixtures and beyond §7's stated "unsafe values" framing. It doesn't currently break `tests/core/test_schema.py` (no such case is asserted there), but it's worth a one-line callout so it isn't mistaken for a defect during D.2 review. | `docs/specs/project-ontos-audit-serializer-corruption-spec.md` §4, §7 | `yaml.safe_dump({'concepts': ['a b', 'cd']}, default_flow_style=None, sort_keys=False, allow_unicode=True)` → `'concepts: [a b, cd]\n'` | Ran directly against PyYAML 6.x as installed in the repo's `.venv`. | Add a one-line note to §7 acknowledging that space-containing (but otherwise safe) list items also move from multi-line to inline flow style, alongside the already-documented quoting changes. |

## 4. Positive Observations

- Every file/line/function anchor in §11's contract-enumeration checklist was independently verified against the current repo and is accurate — this is not a boilerplate table, it's load-bearing and correct.
- The core serializer redesign (per-field `dump_yaml` calls with mode-dependent `default_flow_style`) was empirically validated against all four audit fixtures plus several additional edge cases (nulls, bools, empty lists, multi-line strings, `#`/`---`/`...`-leading values) and produces correct, semantically round-trippable output in every case I tried except the one noted in SF-1.
- Scope discipline is tight and internally consistent: the spec's silence on `ontos/core/frontmatter*.py` (which the dispatch conditionally permits "if strictly required") correctly reflects that this design needs no changes there, and stays inside the manifest's stricter `allowed_paths` list without contradiction.
- The exclusion of the two `writes.py` scaffold-creation call sites from the assertion requirement is a well-reasoned scope boundary, not an oversight — those paths don't re-serialize pre-existing user frontmatter.
- §5's open questions are genuinely resolved with cited authority (existing test expectations, explicit dispatch exclusions), not left as disguised TODOs.

## Verdict
Request changes

## 5. Notes

The spec is implementable as written and would pass every gate and test currently specified in the manifest — SF-1's false-positive risk lives outside the four mandated fixtures, so it would not be caught by `G-test-1`/`G-cardinality-1` and would ship undetected unless fixed now. Given the fix is a one-line change (`parse_yaml(yaml_text)` instead of fence-wrap-and-split) with no loss of the stated validation guarantee, I'd recommend folding it into the spec before Phase C rather than catching it in D.2. M-1 and M-2 are non-blocking polish items the implementer or D.2 reviewers can reasonably decide either way.
