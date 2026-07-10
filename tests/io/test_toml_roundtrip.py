from __future__ import annotations

from ontos.io.toml import load_config, load_config_if_exists, merge_configs, write_config


def test_write_config_round_trips_nested_tables_and_newlines(tmp_path) -> None:
    path = tmp_path / "config.toml"
    config = {
        "title": "line one\nline two",
        "service": {
            "endpoint": "https://example.test/a?x=1",
            "auth": {"method": "oidc", "audiences": ["alpha", "beta"]},
        },
        "optional": None,
    }
    write_config(path, config)
    assert load_config(path) == {
        "title": "line one\nline two",
        "service": config["service"],
    }


def test_load_config_if_exists_is_optional_and_fail_closed(tmp_path) -> None:
    missing = tmp_path / "missing.toml"
    malformed = tmp_path / "bad.toml"
    malformed.write_text("not = [valid", encoding="utf-8")
    assert load_config_if_exists(missing) is None
    assert load_config_if_exists(malformed) is None


def test_merge_configs_deep_merges_one_table_level() -> None:
    assert merge_configs(
        {"paths": {"docs_dir": "docs", "logs_dir": "logs"}},
        {"paths": {"logs_dir": "audit"}, "hooks": {"strict": True}},
    ) == {
        "paths": {"docs_dir": "docs", "logs_dir": "audit"},
        "hooks": {"strict": True},
    }
