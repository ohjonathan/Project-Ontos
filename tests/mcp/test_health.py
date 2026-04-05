import json
from pathlib import Path

from tests.mcp import build_cache, create_workspace, log_usage

from ontos.mcp import tools


def test_health_payload_fields(tmp_path):
    cache = build_cache(create_workspace(tmp_path))

    payload = tools.health(cache)

    assert payload["doc_count"] == 8
    assert payload["workspace"] == "workspace"
    assert payload["workspace_path"].endswith("/workspace")
    assert payload["freshness_mode"] == "file-mtime-fingerprint"
    assert payload["last_indexed"].endswith("Z")


def test_usage_logging_default_off_and_opt_in(tmp_path, monkeypatch):
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))

    cache = build_cache(create_workspace(tmp_path / "off", usage_logging=False))
    log_usage(cache, "health")
    assert not (home / ".config/ontos/usage.jsonl").exists()

    cache = build_cache(create_workspace(tmp_path / "on", usage_logging=True))
    log_usage(cache, "health")
    usage_path = cache.config.mcp.usage_log_path
    assert usage_path is not None
    usage_path = Path(usage_path).expanduser()
    assert usage_path.exists()
    entry = json.loads(usage_path.read_text(encoding="utf-8").strip())
    assert entry["tool_name"] == "health"
