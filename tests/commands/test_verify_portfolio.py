from __future__ import annotations

import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from textwrap import dedent


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
