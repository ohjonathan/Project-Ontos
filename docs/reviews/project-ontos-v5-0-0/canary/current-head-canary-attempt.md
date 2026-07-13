---
phase: B.1
role: orchestrator-preflight
family: codex
deliverable_id: project-ontos-v5-0-0
status: blocked
---

# Current-head Claude canary attempt

## Scope

- Reviewed PR head: `bce26f53349ad61073fff7aa4bf932bad98d982b`.
- Evidence checkout: `948623e601b8f0032d54d15903153266f855e3da`.
- Date: 2026-07-13.
- Classification: local execution-policy block before provider invocation.

## Verified preflight

- `bce26f53349ad61073fff7aa4bf932bad98d982b` is an ancestor of the evidence checkout.
- Product surfaces are byte-identical to that PR head.
- Claude resolves from `/Users/jonathanoh/.local/bin/claude` to
  `/Users/jonathanoh/.local/share/claude/versions/2.1.207`.
- CLI version is `2.1.207 (Claude Code)`, matching the previously proven route.
- The pending canary intent passes `verify-family-dispatch --allow-pending`.

## Dispatch outcome

The orchestrator attempted the framework-owned `dispatch-family-review.sh`
canary with family `claude`, model `auto`, and the exact
`--permission-mode bypassPermissions` execution route. The execution-policy
reviewer denied process creation because that permission mode could expose
private workspace data to an external service.

The denial happened before the wrapper or Claude process started. Therefore:

- no provider call occurred;
- no raw capture, stderr capture, dispatch result, or worker artifact exists;
- no lifecycle receipt was appended;
- this record is not strict-P3 evidence and grants no approval authority.

## Disposition

The required canary did not produce a genuine artifact. Strict-P3 was not
started, D.6 remains `WITHHELD`, and PR #163 remains under release hold. A
future retry requires explicit authorization after disclosure of the external
data-egress risk; the exact route must not be replaced with a weaker or indirect
surrogate.
