"""Load the project-level concept vocabulary used by full validation."""

from __future__ import annotations

from pathlib import Path


def concept_vocabulary_paths(repo_root: Path) -> tuple[Path, Path]:
    """Return vocabulary candidates in authoritative precedence order."""
    return (
        repo_root / ".ontos-internal" / "reference" / "Common_Concepts.md",
        repo_root / "docs" / "reference" / "Common_Concepts.md",
    )


def load_known_concepts(repo_root: Path) -> set[str]:
    """Return concepts declared by the authoritative ``Common_Concepts.md``.

    An absent or unreadable vocabulary disables concept-membership checks while
    leaving structural validation enabled, matching the historical map command
    contract.
    """

    for candidate in concept_vocabulary_paths(repo_root):
        if not candidate.exists():
            continue
        try:
            content = candidate.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue

        concepts: set[str] = set()
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped.startswith("|") or "`" not in stripped:
                continue
            cells = stripped.split("|")
            if len(cells) < 2:
                continue
            cell = cells[1].strip()
            if cell.startswith("`") and cell.endswith("`"):
                concepts.add(cell[1:-1])
        return concepts

    return set()
