from pathlib import Path

from tests.mcp import build_cache, create_workspace, run_base_cli

from ontos.mcp import tools


def test_count_parity_and_cli_loader_parity(tmp_path):
    root = create_workspace(tmp_path)
    cache = build_cache(root)

    overview = tools.workspace_overview(cache)
    health = tools.health(cache)
    listing = tools.list_documents(cache)
    export = tools.export_graph(cache, summary_only=True)
    refreshed = tools.refresh(cache)

    counts = {
        overview["graph_stats"]["total"],
        health["doc_count"],
        listing["total_count"],
        export["summary"]["total_documents"],
        refreshed["doc_count"],
    }
    assert counts == {8}

    list_ids = run_base_cli(root, "query", "--list-ids", "--dir", "docs")
    health_cli = run_base_cli(root, "query", "--health", "--dir", "docs")
    assert list_ids.returncode == 0
    assert "_template" not in list_ids.stdout
    assert "reference_doc" in list_ids.stdout
    assert "Total documents: 8" in health_cli.stdout


def test_import_boundaries():
    for path in Path("ontos/core").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "ontos.mcp" not in text

    for path in Path("ontos/mcp").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "ontos.ui." not in text
