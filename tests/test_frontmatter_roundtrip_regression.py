"""P0 regression net for every document-frontmatter writer surface."""

from __future__ import annotations

from pathlib import Path

import pytest

from ontos.commands.stub import write_stub_to_context
from ontos.core.context import SessionContext
from ontos.core.schema import serialize_frontmatter
from ontos.io.yaml import parse_frontmatter_content
from ontos.ui.output import OutputHandler


@pytest.mark.parametrize(
    "value",
    [
        'embedded "quote"',
        "alpha, beta",
        "true",
        "null",
        "# leading hash",
        "2026-07-10",
        "phase --- two",
        "first line\nsecond line",
        "Unicode: café 東京 🚀",
    ],
)
def test_safe_serializer_round_trips_adversarial_scalars(value: str) -> None:
    frontmatter = {
        "id": "roundtrip_fixture",
        "type": "atom",
        "status": "active",
        "summary": value,
        "depends_on": [value, "second, item"],
    }
    serialized = serialize_frontmatter(frontmatter)
    parsed, _ = parse_frontmatter_content(f"---\n{serialized}\n---\n")
    assert parsed == frontmatter


def test_stub_writer_round_trips_goal_and_list_values(tmp_path: Path) -> None:
    path = tmp_path / "stub.md"
    frontmatter = {
        "id": "writer_stub",
        "type": "spec",
        "status": "pending_curation",
        "curation_level": 1,
        "goal": 'Keep "quotes", # hashes, dates like 2026-07-10, and café',
        "depends_on": ["alpha, beta", "null", "#hash"],
    }
    context = SessionContext(repo_root=tmp_path, config={})
    assert write_stub_to_context(
        path,
        frontmatter,
        context,
        OutputHandler(quiet=True),
    )
    context.commit()
    parsed, _ = parse_frontmatter_content(path.read_text(encoding="utf-8"))
    assert parsed == frontmatter


def test_all_frontmatter_writer_modules_use_the_safe_pipeline() -> None:
    root = Path(__file__).resolve().parents[1]
    serializer_writers = {
        "ontos/commands/stub.py": "serialize_frontmatter",
        "ontos/commands/scaffold.py": "serialize_frontmatter",
        "ontos/commands/log.py": "serialize_frontmatter",
        "ontos/commands/retrofit.py": "dump_yaml",
        "ontos/commands/promote.py": "patch_frontmatter_fields",
        "ontos/commands/migrate.py": "patch_frontmatter_fields",
        "ontos/commands/verify.py": "patch_frontmatter_fields",
        "ontos/mcp/writes.py": "serialize_frontmatter",
    }
    for relative_path, safe_symbol in serializer_writers.items():
        source = (root / relative_path).read_text(encoding="utf-8")
        assert safe_symbol in source, relative_path
        assert ".split('---', 2)" not in source, relative_path
        assert '.split("---", 2)' not in source, relative_path

    for relative_path in (
        "ontos/commands/promote.py",
        "ontos/commands/migrate.py",
        "ontos/commands/verify.py",
        "ontos/mcp/writes.py",
    ):
        source = (root / relative_path).read_text(encoding="utf-8")
        assert ".read_text(" not in source, f"newline-normalizing read in {relative_path}"
