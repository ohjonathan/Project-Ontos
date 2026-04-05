import pytest

from ontos.core.errors import OntosUserError
from ontos.mcp import tools

from tests.mcp import build_cache, create_workspace


def test_get_document_by_id_and_path(tmp_path):
    root = create_workspace(tmp_path)
    cache = build_cache(root)

    by_id = tools.get_document(cache, document_id="atom_doc")
    by_path = tools.get_document(cache, path="docs/atom.md", include_content=False)

    assert by_id["id"] == "atom_doc"
    assert "content" in by_id
    assert by_path["id"] == "atom_doc"
    assert "content" not in by_path
    assert "depends_on" not in by_path["metadata"]


def test_get_document_rejects_outside_path(tmp_path):
    cache = build_cache(create_workspace(tmp_path))

    with pytest.raises(OntosUserError):
        tools.get_document(cache, path="../outside.md")
