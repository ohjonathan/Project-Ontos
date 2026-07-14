from pathlib import Path

import ontos


def test_source_and_packaging_versions_are_5_0_1() -> None:
    assert ontos.__version__ == "5.0.1"
    pyproject = Path(__file__).parents[1] / "pyproject.toml"
    assert 'version = "5.0.1"' in pyproject.read_text(encoding="utf-8")
