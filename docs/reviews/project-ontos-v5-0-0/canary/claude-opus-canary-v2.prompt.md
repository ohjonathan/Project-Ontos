# Claude route canary v2 for Ontos 5.0.0

This is a bounded provider-route canary, not a lifecycle review and not a
strict-P3 receipt. Do exactly these checks:

1. Run `git merge-base --is-ancestor 5678e910ce11ed7a3546822cf3e34d50c5741681 HEAD`.
2. Confirm `pyproject.toml` declares version `5.0.0`.

Then write exactly one file:
`docs/reviews/project-ontos-v5-0-0/canary/claude-opus-canary-v2.md`.

If both checks pass, write exactly this Markdown structure (you may replace
only the evidence sentence with the observed HEAD):

---
phase: B.1
role: peer
family: claude
deliverable_id: project-ontos-v5-0-0
status: completed
---
# Claude route canary v2

## Verdict

Approve

## Evidence

Product head `5678e910ce11ed7a3546822cf3e34d50c5741681` is an ancestor of
the checkout and `pyproject.toml` declares version `5.0.0`.

The first non-blank line after `## Verdict` must be the single bare word
`Approve`; no prose may appear before it. If either check fails, use the bare
verdict `Request changes` and explain the failure under `## Evidence`. Do not
modify any other file.

