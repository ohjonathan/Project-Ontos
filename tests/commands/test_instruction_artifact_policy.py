"""Repository policy tests for committed Ontos-generated artifacts."""

from pathlib import Path


def test_only_context_map_is_marked_generated() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    rules = [
        line.strip()
        for line in (repo_root / ".gitattributes").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]

    generated_rules = [rule for rule in rules if "linguist-generated" in rule]
    assert generated_rules == ["Ontos_Context_Map.md linguist-generated=true"]
    generated_artifacts = {
        "Ontos_Context_Map.md",
        "AGENTS.md",
        ".cursorrules",
        "CLAUDE.md",
    }
    artifact_rules = [
        rule for rule in rules if rule.split(maxsplit=1)[0] in generated_artifacts
    ]
    assert all("merge=" not in rule for rule in artifact_rules)
