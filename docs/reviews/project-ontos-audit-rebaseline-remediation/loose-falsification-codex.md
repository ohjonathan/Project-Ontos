---
id: project-ontos-audit-rebaseline-remediation-loose-falsification-codex
type: review
status: completed
depends_on:
  - project-ontos-audit-rebaseline-remediation-D.4-fix-summary
---

# Loose falsification — Codex

Stance: falsify the reviewed implementation; no runnable reproduction means no
finding. This pass is supplemental and carries no lifecycle receipt or
certification authority.

## LF-ID-1 — YAML-ambiguous rename IDs

Verdict: reproduced. Canonically valid strings `123`, `2026-07-10`, and `1.2`
were written unquoted and reloaded as `int`, `date`, and `float`, making the
renamed target unloadable. The regression covers the target ID plus scalar,
block-list, and inline-list references.

```bash
./.venv/bin/python -m pytest tests/commands/test_rename.py -q \
  -k yaml_like_ids_remain_strings
```

Pre-fix: `3 failed`. I3: `3 passed`.

## LF-CP-1 — duplicate program ownership identity

Verdict: reproduced. Making issue 146 share issue 147's program identity, while
synchronizing affected findings and O4, returned `audit-registry: PASS`/exit 0.
A collision with the synthetic issue-158 owner also passed.

```bash
./.venv/bin/python -m pytest tests/test_audit_remediation_registry_validator.py -q \
  -k program_identity_collision
```

Pre-fix: `2 failed` because both calls returned exit 0. I3: `2 passed`; each
collision now returns `audit-registry: FAILED`/exit 1 before O4 consumption.

## Disposition

Both findings are fixed at `859ecf778389aaa67f69146d7ae8cd2564445af5`.
Integrated verification: `5 passed`; complete suite: `1725 passed, 1 warning`.
No D.6, merge, release, or strict-P3 claim follows.
