# Claude current-head route canary for Ontos 5.0.0

This is a bounded provider-route canary, not a lifecycle review and not a
strict-P3 receipt. Do exactly these checks:

1. Run `git merge-base --is-ancestor bce26f53349ad61073fff7aa4bf932bad98d982b HEAD`.
2. Run `git diff --quiet bce26f53349ad61073fff7aa4bf932bad98d982b HEAD -- ontos tests pyproject.toml .github/workflows/ci.yml .pre-commit-config.yaml scripts/verify_lifecycle_evidence_ref.py`.
3. Confirm `pyproject.toml` declares version `5.0.0`.

Then write exactly one file:
`docs/reviews/project-ontos-v5-0-0/canary/claude-opus-canary-v3.md`.

If all checks pass, write exactly this Markdown structure (you may replace
only the checkout SHA in the evidence sentence with the observed `HEAD`):

---
phase: B.1
role: peer
family: claude
deliverable_id: project-ontos-v5-0-0
status: completed
---
# Claude current-head route canary

## Verdict

Approve

## Evidence

PR head `bce26f53349ad61073fff7aa4bf932bad98d982b` is an ancestor of the
checkout at `<observed-HEAD>`, the reviewed product surfaces are byte-identical,
and `pyproject.toml` declares version `5.0.0`.

The first non-blank line after `## Verdict` must be the single bare word
`Approve`; no prose may appear before it. If any check fails, use the bare
verdict `Request changes` and explain the failure under `## Evidence`. Do not
modify any other file.
