"""Contract tests for load_frontmatter error handling."""

from pathlib import Path

from ontos.io.files import load_frontmatter
from ontos.io.yaml import parse_frontmatter_content


def test_load_frontmatter_malformed_yaml_returns_none_and_records_issue(tmp_path: Path):
    """Malformed YAML should not raise and should emit a parse issue."""
    path = tmp_path / "broken.md"
    path.write_text(
        "---\n"
        "id: bad\n"
        "depends_on: [missing\n"
        "---\n"
        "body\n",
        encoding="utf-8",
    )

    issues = []
    fm, body = load_frontmatter(path, parse_frontmatter_content, on_issue=issues.append)

    assert fm is None
    assert body is None
    assert len(issues) == 1
    assert issues[0].code == "parse_error"
    assert issues[0].path == path
