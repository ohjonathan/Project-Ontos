from __future__ import annotations

from argparse import Namespace
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from textwrap import dedent

import pytest

from ontos.cli import _cmd_verify
import ontos.commands.verify as verify_module
import ontos.mcp.portfolio_config as portfolio_config_module


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_verify_portfolio_cli_accepts_dev_root_relative_registry(tmp_path):
    home = tmp_path / "home"
    dev_root = tmp_path / "Dev"
    workspace = dev_root / "alpha.project"
    workspace.mkdir(parents=True)
    (workspace / ".ontos.toml").write_text("[ontos]\nversion = '4.0'\n", encoding="utf-8")

    registry_path = tmp_path / "registry" / "projects.json"
    registry_path.parent.mkdir(parents=True)
    registry_path.write_text(
        json.dumps(
            {
                "dev_root": str(dev_root),
                "projects": [
                    {
                        "path": "alpha.project",
                        "status": "documented",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    _write_portfolio_config(home, registry_path)
    _write_portfolio_db(
        home / ".config" / "ontos" / "portfolio.db",
        [
            {
                "slug": "alpha-project",
                "path": str(workspace),
                "status": "documented",
                "has_ontos": 1,
            }
        ],
    )

    result = _run_verify_portfolio(home)

    assert result.returncode == 0
    assert "No discrepancies found." in result.stdout


def test_verify_portfolio_cli_reports_mismatches_in_json_mode(tmp_path):
    home = tmp_path / "home"
    workspace = tmp_path / "Dev" / "alpha"
    workspace.mkdir(parents=True)
    (workspace / ".ontos.toml").write_text("[ontos]\nversion = '4.0'\n", encoding="utf-8")

    registry_path = tmp_path / "registry" / "projects.json"
    registry_path.parent.mkdir(parents=True)
    registry_path.write_text(
        json.dumps(
            {
                "projects": [
                    {
                        "path": str(workspace),
                        "status": "documented",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    _write_portfolio_config(home, registry_path)
    _write_portfolio_db(
        home / ".config" / "ontos" / "portfolio.db",
        [
            {
                "slug": "alpha",
                "path": str(workspace),
                "status": "partial",
                "has_ontos": 1,
            }
        ],
    )

    result = _run_verify_portfolio(home, "--json")
    payload = json.loads(result.stdout)

    assert result.returncode == 1
    assert payload["clean"] is False
    assert payload["summary"] == "1 discrepancies found."
    assert payload["field_mismatches"] == [
        {
            "slug": "alpha",
            "field": "status",
            "db_value": "partial",
            "json_value": "documented",
        }
    ]


def test_verify_portfolio_cli_errors_when_db_missing(tmp_path):
    home = tmp_path / "home"
    registry_path = tmp_path / "registry" / "projects.json"
    registry_path.parent.mkdir(parents=True)
    registry_path.write_text(json.dumps({"projects": []}), encoding="utf-8")
    _write_portfolio_config(home, registry_path)

    result = _run_verify_portfolio(home)

    assert result.returncode == 2
    assert "Run `ontos serve --portfolio` first." in result.stdout


def test_verify_portfolio_scopes_to_workspace_id(tmp_path, capsys):
    db_path = tmp_path / "portfolio.db"
    alpha_path = tmp_path / "Dev" / "alpha"
    beta_path = tmp_path / "Dev" / "beta"
    alpha_path.mkdir(parents=True)
    beta_path.mkdir(parents=True)
    (alpha_path / ".ontos.toml").write_text("[ontos]\nversion = '4.0'\n", encoding="utf-8")
    (beta_path / ".ontos.toml").write_text("[ontos]\nversion = '4.0'\n", encoding="utf-8")

    registry_path = tmp_path / "registry" / "projects.json"
    registry_path.parent.mkdir(parents=True)
    registry_path.write_text(
        json.dumps({"projects": [{"path": str(alpha_path), "status": "documented"}]}),
        encoding="utf-8",
    )

    _write_portfolio_db(
        db_path,
        [
            {"slug": "alpha", "path": str(alpha_path), "status": "documented", "has_ontos": 1},
            {"slug": "beta", "path": str(beta_path), "status": "documented", "has_ontos": 1},
        ],
    )

    result = verify_module.verify_portfolio(
        portfolio_db_path=db_path,
        registry_path=registry_path,
        workspace_id="alpha",
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "No discrepancies found." in captured.out


def test_verify_portfolio_handles_same_basename_collision(tmp_path):
    db_path = tmp_path / "portfolio.db"
    root_one = tmp_path / "DevA"
    root_two = tmp_path / "DevB"
    workspace_one = root_one / "sample-app"
    workspace_two = root_two / "sample-app"
    workspace_one.mkdir(parents=True)
    workspace_two.mkdir(parents=True)
    (workspace_one / ".ontos.toml").write_text("[ontos]\nversion = '4.0'\n", encoding="utf-8")
    (workspace_two / ".ontos.toml").write_text("[ontos]\nversion = '4.0'\n", encoding="utf-8")

    registry_path = tmp_path / "registry" / "projects.json"
    registry_path.parent.mkdir(parents=True)
    registry_path.write_text(
        json.dumps(
            {
                "projects": [
                    {"path": str(workspace_one), "status": "documented"},
                    {"path": str(workspace_two), "status": "documented"},
                ]
            }
        ),
        encoding="utf-8",
    )

    _write_portfolio_db(
        db_path,
        [
            {
                "slug": "sample-app",
                "path": str(workspace_one),
                "status": "documented",
                "has_ontos": 1,
            },
            {
                "slug": "sample-app-2",
                "path": str(workspace_two),
                "status": "documented",
                "has_ontos": 1,
            },
        ],
    )

    exit_code = verify_module.verify_portfolio(
        portfolio_db_path=db_path,
        registry_path=registry_path,
        json_output=True,
    )

    assert exit_code == 0


@pytest.mark.parametrize("registry_key", ["projects", "workspaces", "entries", "items"])
def test_verify_portfolio_accepts_all_registry_list_shapes(tmp_path, registry_key):
    db_path = tmp_path / "portfolio.db"
    workspace = tmp_path / "Dev" / "alpha"
    workspace.mkdir(parents=True)
    (workspace / ".ontos.toml").write_text("[ontos]\nversion = '4.0'\n", encoding="utf-8")

    registry_path = tmp_path / "registry" / "projects.json"
    registry_path.parent.mkdir(parents=True)
    registry_path.write_text(
        json.dumps({registry_key: [{"path": str(workspace), "status": "documented"}]}),
        encoding="utf-8",
    )

    _write_portfolio_db(
        db_path,
        [{"slug": "alpha", "path": str(workspace), "status": "documented", "has_ontos": 1}],
    )

    exit_code = verify_module.verify_portfolio(portfolio_db_path=db_path, registry_path=registry_path)
    assert exit_code == 0


def test_verify_portfolio_accepts_dict_shaped_registry(tmp_path):
    db_path = tmp_path / "portfolio.db"
    workspace = tmp_path / "Dev" / "alpha"
    workspace.mkdir(parents=True)
    (workspace / ".ontos.toml").write_text("[ontos]\nversion = '4.0'\n", encoding="utf-8")

    registry_path = tmp_path / "registry" / "projects.json"
    registry_path.parent.mkdir(parents=True)
    registry_path.write_text(
        json.dumps({"alpha": {"path": str(workspace), "status": "documented"}}),
        encoding="utf-8",
    )

    _write_portfolio_db(
        db_path,
        [{"slug": "alpha", "path": str(workspace), "status": "documented", "has_ontos": 1}],
    )

    exit_code = verify_module.verify_portfolio(portfolio_db_path=db_path, registry_path=registry_path)
    assert exit_code == 0


def test_verify_portfolio_string_false_not_truthy(tmp_path):
    db_path = tmp_path / "portfolio.db"
    workspace = tmp_path / "Dev" / "alpha"
    workspace.mkdir(parents=True)
    (workspace / ".ontos.toml").write_text("[ontos]\nversion = '4.0'\n", encoding="utf-8")

    registry_path = tmp_path / "registry" / "projects.json"
    registry_path.parent.mkdir(parents=True)
    registry_path.write_text(
        json.dumps(
            {
                "projects": [
                    {
                        "path": str(workspace),
                        "status": "partial",
                        "has_ontos": "false",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    _write_portfolio_db(
        db_path,
        [{"slug": "alpha", "path": str(workspace), "status": "partial", "has_ontos": 0}],
    )

    exit_code = verify_module.verify_portfolio(
        portfolio_db_path=db_path,
        registry_path=registry_path,
        json_output=True,
    )

    assert exit_code == 0


def test_cmd_verify_portfolio_handles_malformed_config(monkeypatch, capsys):
    args = Namespace(portfolio=True, json=False, workspace_id=None)

    def _boom():
        raise ValueError("Invalid TOML structure")

    monkeypatch.setattr(portfolio_config_module, "load_portfolio_config", _boom)

    result = _cmd_verify(args)
    captured = capsys.readouterr()

    assert result == 2
    assert "Invalid portfolio config: Invalid TOML structure" in captured.out
    assert "Traceback" not in captured.out
    assert "Traceback" not in captured.err


def test_cmd_verify_portfolio_threads_workspace_id(monkeypatch):
    args = Namespace(portfolio=True, json=False, workspace_id="alpha")
    calls: list[object] = []

    class _Config:
        registry_path = None

    def _load_config():
        return _Config()

    def _fake_verify_portfolio(**kwargs):
        calls.append(kwargs.get("workspace_id"))
        return 0

    monkeypatch.setattr(portfolio_config_module, "load_portfolio_config", _load_config)
    monkeypatch.setattr(verify_module, "verify_portfolio", _fake_verify_portfolio)

    assert _cmd_verify(args) == 0
    assert calls == ["alpha"]


def _run_verify_portfolio(home: Path, *extra_args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["PYTHONPATH"] = str(REPO_ROOT)
    return subprocess.run(
        [sys.executable, "-m", "ontos.cli", "verify", "--portfolio", *extra_args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        env=env,
    )


def _write_portfolio_config(home: Path, registry_path: Path) -> None:
    config_path = home / ".config" / "ontos" / "portfolio.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        dedent(
            f"""
            [portfolio]
            scan_roots = ["~/Dev"]
            exclude = ["~/Dev/.dev-hub", "~/Dev/archive"]
            registry_path = "{registry_path}"

            [bundle]
            token_budget = 8192
            max_logs = 5
            log_window_days = 14
            """
        ).lstrip(),
        encoding="utf-8",
    )


def _write_portfolio_db(db_path: Path, rows: list[dict[str, object]]) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            """
            CREATE TABLE projects (
                slug TEXT PRIMARY KEY,
                path TEXT NOT NULL,
                status TEXT NOT NULL,
                has_ontos INTEGER NOT NULL
            )
            """
        )
        connection.executemany(
            "INSERT INTO projects(slug, path, status, has_ontos) VALUES(?, ?, ?, ?)",
            [
                (
                    str(row["slug"]),
                    str(row["path"]),
                    str(row["status"]),
                    int(row["has_ontos"]),
                )
                for row in rows
            ],
        )
        connection.commit()
    finally:
        connection.close()
