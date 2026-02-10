---
id: readme_pypi_links_proposal
type: atom
status: active
depends_on: []
---

# Proposal: Fix PyPI Documentation Links in README

**Date:** 2026-01-19
**Status:** Active
**Target Version:** v3.0.5
**Context:** PyPI package description

## Problem
The `README.md` uses relative links for documentation (e.g., `docs/reference/Ontos_Manual.md`). When rendered on PyPI (pypi.org/project/ontos), these links resolve relative to the PyPI domain (e.g., `pypi.org/.../docs/...`), resulting in 404 errors. This prevents users from accessing critical documentation directly from the PyPI page.

## Proposed Solution
Update `README.md` to use absolute URLs pointing to the GitHub repository's `main` branch for all documentation links.

**Tradeoff:** This means the documentation links will always point to the *latest* code, which might differ slightly from the installed package version.
**Mitigation:** We will add a short note in the README clarifying that links point to the latest source.

### Changes Required

1.  **Add Note:** Insert a disclaimer at the top of the "Documentation" section:
    > *Note: Documentation links below point to the latest source on GitHub and may reflect features not yet released.*

2.  **Convert Links:** Change the following relative links to absolute URLs (Base: `https://github.com/ohjona/Project-Ontos/blob/main/`):
    - **Ontos Manual:** `docs/reference/Ontos_Manual.md` → `.../docs/reference/Ontos_Manual.md`
    - **Agent Instructions:** `docs/reference/Ontos_Agent_Instructions.md` → `.../docs/reference/Ontos_Agent_Instructions.md`
    - **Migration Guide:** `docs/reference/Migration_v2_to_v3.md` → `.../docs/reference/Migration_v2_to_v3.md`
    - **Minimal Example:** `examples/minimal/README.md` → `.../examples/minimal/README.md`
    - **Changelog:** `Ontos_CHANGELOG.md` → `.../Ontos_CHANGELOG.md`
    - **License:** `LICENSE` → `.../LICENSE` (Retained for human visibility in the README body)

**Maintenance Note:** If the GitHub repository is renamed or moved, these hardcoded links will break and require a manual update.

## Alternatives Considered
- **Release Tag Links (e.g., `blob/v3.0.5/...`):**
  - *Pros:* Documentation exactly matches the installed package version. Git tags are immutable and stable.
  - *Cons:* Higher maintenance burden. Requires updating the README for every single release (manual or automated script).
  - *Verdict:* Rejected for now to prioritize ease of maintenance, but may be reconsidered if we add release automation later.
- **Separate PyPI README:** Creating a specific README for PyPI would keep the GitHub README cleaner with relative links.
  - *Verdict:* Rejected. Adds unnecessary build complexity.

## Decision
**Accept.** We accept the tradeoff of linking to the `main` branch to ensure links work immediately on PyPI without complex per-release updates. The disclaimer note mitigates confusion regarding version mismatches.

## Implementation Checklist
- [ ] Update `README.md` with absolute URLs
- [ ] Add the version/source disclaimer to `README.md`
- [ ] Run `python3 -m build` to generate the distribution
- [ ] Run `twine check dist/*` to verify ReStructuredText rendering (catch markdown-to-rst issues)

## Verification
1.  **Local Check:**
    - Run `twine check dist/*`.
    - **Success Criterion:** Output must say `Passed` with no warnings about invalid links or markdown syntax.
2.  **TestPyPI Upload:**
    - `twine upload --repository testpypi dist/*`
3.  **Live Check:**
    - Visit `https://test.pypi.org/project/ontos/`
    - **Success Criterion:**
        1. All 6 links are clickable.
        2. All 6 links open the correct GitHub page.
        3. No relative links (404s) remain in the description.
