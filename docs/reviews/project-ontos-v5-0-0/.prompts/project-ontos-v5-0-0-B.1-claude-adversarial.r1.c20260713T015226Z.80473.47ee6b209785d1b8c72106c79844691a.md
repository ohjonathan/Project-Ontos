# Ontos 5.0.0 B.1 adversarial review

You are the independent Claude-family adversarial reviewer for
`project-ontos-v5-0-0`. Review commit
`8f4fc8842bd8346b541a9c5a08a9d196ee1a6319` in this checkout against:

- `docs/specs/project-ontos-v5-0-0-spec.md`
- `manifests/project-ontos-v5-0-0.yaml`
- `docs/releases/v5.0.0.md`
- the diff from `454b102b033310517dd4623b7eaa3a42b271f32d`

Focus on contract violations, unsafe rename recovery, CLI/JSON inconsistencies,
scope leakage, missing migration disclosures, and tests that fail to establish
the claimed behavior. You may inspect files and run focused read-only tests.

Return only a verdict-shaped Markdown artifact. Begin with exactly one H1.
List findings with severity and file:line evidence. End with exactly one line:
`VERDICT: Approve` or `VERDICT: Request Further Fixes`.
