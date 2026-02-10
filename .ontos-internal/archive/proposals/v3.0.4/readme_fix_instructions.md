# Implementation Instructions: Fix PyPI Documentation Links

**Goal:** Fix 404 errors on PyPI by replacing relative documentation links in `README.md` with absolute GitHub URLs.

**Target File:** `README.md`
**GitHub Base URL:** `https://github.com/ohjona/Project-Ontos/blob/main/`

---

## 1. Add Disclaimer Note
Locate the **"Documentation"** section near the end of the file. Insert this note immediately after the header:

> *Note: Documentation links below point to the latest source on GitHub and may reflect features not yet released.*

## 2. Convert Relative Links to Absolute
Replace the following relative paths with absolute URLs using the Base URL above.

| Link Text | Find (Relative) | Replace With (Absolute) |
| :--- | :--- | :--- |
| **Ontos Manual** | `docs/reference/Ontos_Manual.md` | `https://github.com/ohjona/Project-Ontos/blob/main/docs/reference/Ontos_Manual.md` |
| **Agent Instructions** | `docs/reference/Ontos_Agent_Instructions.md` | `https://github.com/ohjona/Project-Ontos/blob/main/docs/reference/Ontos_Agent_Instructions.md` |
| **Migration Guide v2→v3** | `docs/reference/Migration_v2_to_v3.md` | `https://github.com/ohjona/Project-Ontos/blob/main/docs/reference/Migration_v2_to_v3.md` |
| **Minimal Example** | `examples/minimal/README.md` | `https://github.com/ohjona/Project-Ontos/blob/main/examples/minimal/README.md` |
| **Changelog** | `Ontos_CHANGELOG.md` | `https://github.com/ohjona/Project-Ontos/blob/main/Ontos_CHANGELOG.md` |
| **License** (Badge/Section) | `LICENSE` | `https://github.com/ohjona/Project-Ontos/blob/main/LICENSE` |

*Check both the "Documentation" section and the badges/footer for these links.*

## 3. Verify
Run the following commands to ensure the package description renders correctly for PyPI:

```bash
# 1. Build the package
python3 -m build

# 2. Check description rendering
twine check dist/*
```

**Success Criterion:** Output must include `PASSED`.
