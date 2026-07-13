# Claude route canary for Ontos 5.0.0

This is a bounded provider-route canary, not a lifecycle review and not a
strict-P3 receipt. Work in the current checkout and do exactly these checks:

1. Confirm commit `5678e910ce11ed7a3546822cf3e34d50c5741681` is an ancestor
   of `HEAD` using Git.
2. Confirm `pyproject.toml` declares version `5.0.0`.
3. Write exactly one file:
   `docs/reviews/project-ontos-v5-0-0/canary/claude-opus-canary.md`.

The file must contain a valid F35 verdict artifact with YAML frontmatter keys
`phase`, `role`, `family`, `deliverable_id`, and `status`; one ATX H1; a
`## Verdict` section; and a bare final verdict word. State the two observed
facts and use `Approve` only if both checks pass. Do not modify any other file.

