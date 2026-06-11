"""(#133) Cross-command count-consistency regression.

One fixture repo, four health surfaces — activate, query --health,
link-check, doctor — must agree on warning/orphan counts (or label their
basis). This is the regression guarantee that the contradictory numbers
from the company-os RCA (657 vs 830 warnings, 241 vs 372 orphans) cannot
come back.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _run(root: Path, *args: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    return subprocess.run(
        [sys.executable, "-m", "ontos", *args],
        cwd=root,
        capture_output=True,
        text=True,
        env=env,
    )


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(content).lstrip(), encoding="utf-8")


@pytest.fixture
def fixture_repo(tmp_path: Path) -> Path:
    """Workspace with every count class: orphans (allowed + flagged), an
    allowlisted file dep, an unallowlisted file dep, a missing dep, logs
    under an allowed orphan path, and no kernel docs."""
    _write(
        tmp_path / ".ontos.toml",
        """
        [ontos]
        version = "3.0"

        [validation]
        allowed_orphan_types = ["atom"]
        allowed_orphan_paths = ["docs/logs/**"]
        allowed_external_dependency_paths = ["apps/**"]
        """,
    )
    # Real files for dependency targets.
    _write(tmp_path / "apps/real.py", "code\n")
    _write(tmp_path / "tools/real.py", "code\n")

    # An orphan strategy doc (strategy not in allowed types -> orphan warning).
    _write(
        tmp_path / "docs/strategy_orphan.md",
        """
        ---
        id: strategy_orphan
        type: strategy
        status: active
        ---
        Body.
        """,
    )
    # A log under the allowed orphan path -> never an orphan.
    _write(
        tmp_path / "docs/logs/2026-06-01_session.md",
        """
        ---
        id: log_2026_06_01
        type: log
        status: complete
        ---
        Log body.
        """,
    )
    # Atom doc with one allowlisted file dep, one unallowlisted file dep,
    # and one genuinely missing dep.
    _write(
        tmp_path / "docs/handoff.md",
        """
        ---
        id: handoff_doc
        type: atom
        status: active
        depends_on: [apps/real.py, tools/real.py, genuinely_missing_doc]
        ---
        Handoff body.
        """,
    )
    return tmp_path


def _payload(result: subprocess.CompletedProcess) -> dict:
    assert result.stdout, result.stderr
    return json.loads(result.stdout)


def test_health_surfaces_agree_on_counts(fixture_repo: Path) -> None:
    activate = _payload(_run(fixture_repo, "--json", "activate", "--warnings", "full"))
    doctor = _payload(_run(fixture_repo, "--json", "doctor"))
    link_check = _payload(_run(fixture_repo, "--json", "link-check"))
    query = _payload(_run(fixture_repo, "--json", "query", "--health"))

    activate_summary = activate["data"]["summary"]
    activate_warnings = activate["data"]["validation"]["warnings"]

    # --- (1) doctor activation_health counts == activate counts (exact) ---
    checks = {check["name"]: check for check in doctor["data"]["checks"]}
    activation_check = checks["activation_health"]
    assert activation_check["data"]["validation_errors"] == (
        activate_summary["validation_errors"]
    )
    assert activation_check["data"]["validation_warnings"] == (
        activate_summary["validation_warnings"]
    )
    assert activation_check["data"]["count_basis"] == "activation_pipeline"
    assert "activation pipeline" in activation_check["message"]

    # --- (2) orphan counts identical across activate / query / link-check ---
    activate_orphans = [
        w for w in activate_warnings if w.get("rule_id") == "orphan"
    ]
    query_data = query["data"]["results"] if "results" in query["data"] else query["data"]
    link_orphans = link_check["data"]["summary"]["orphans"]
    assert len(activate_orphans) == 1  # strategy_orphan only
    assert link_orphans == 1
    assert query_data["orphans"] == 1
    assert query_data["orphan_ids"] == ["strategy_orphan"]
    assert query_data["orphan_basis"] == "graph_validation"
    assert query_data["allowed_orphan_types"] == ["atom"]

    # --- (3) file dependency bucketing + exit codes ---
    link_summary = link_check["data"]["summary"]
    assert link_summary["file_dependencies"] == 2
    assert link_summary["unallowlisted_file_dependencies"] == 1
    # broken_references counts ONLY the genuinely missing doc.
    assert link_summary["broken_references"] >= 1
    broken_values = {
        item["value"] for item in link_check["data"]["broken_references"]
    }
    assert "genuinely_missing_doc" in broken_values
    assert "apps/real.py" not in broken_values
    assert "tools/real.py" not in broken_values
    assert link_check["exit_code"] == 1

    # --- (4) activate info bucket carries exactly the allowlisted dep ---
    assert activate_summary["validation_info"] == 1
    info_records = activate["data"]["validation"]["info"]
    assert info_records[0]["rule_id"] == "external_file_dependency"
    assert "apps/real.py" in info_records[0]["message"]

    # --- (5) connectivity reports not-applicable without kernel docs ---
    assert query_data["connectivity"] is None
    assert query_data["connectivity_basis"] == "not_applicable_no_kernel_docs"
    assert query_data["kernel_docs"] == 0

    # --- (6) every surface labels its count basis ---
    assert query_data["count_basis"] == "graph_validation"
    assert activation_check["data"]["count_basis"] == "activation_pipeline"
    validation_check = checks["validation"]
    assert validation_check["data"]["count_basis"] == "frontmatter_quick_scan"
    assert "quick scan" in validation_check["message"]


def test_orphan_counts_track_config_changes(fixture_repo: Path) -> None:
    """Allowing strategy orphans must change ALL surfaces in lockstep."""
    config_path = fixture_repo / ".ontos.toml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace(
            'allowed_orphan_types = ["atom"]',
            'allowed_orphan_types = ["atom", "strategy"]',
        ),
        encoding="utf-8",
    )

    activate = _payload(_run(fixture_repo, "--json", "activate", "--warnings", "full"))
    link_check = _payload(_run(fixture_repo, "--json", "link-check"))
    query = _payload(_run(fixture_repo, "--json", "query", "--health"))

    activate_orphans = [
        w for w in activate["data"]["validation"]["warnings"]
        if w.get("rule_id") == "orphan"
    ]
    query_data = query["data"]["results"] if "results" in query["data"] else query["data"]
    assert len(activate_orphans) == 0
    assert link_check["data"]["summary"]["orphans"] == 0
    assert query_data["orphans"] == 0


def test_query_health_human_output_handles_no_kernel(fixture_repo: Path) -> None:
    result = _run(fixture_repo, "query", "--health")
    assert result.returncode == 0
    assert "n/a (no kernel documents)" in result.stdout


def test_query_health_connectivity_with_kernel_docs(fixture_repo: Path) -> None:
    _write(
        fixture_repo / "docs/kernel.md",
        """
        ---
        id: kernel_doc
        type: kernel
        status: active
        ---
        Kernel body.
        """,
    )
    query = _payload(_run(fixture_repo, "--json", "query", "--health"))
    query_data = query["data"]["results"] if "results" in query["data"] else query["data"]
    assert query_data["kernel_docs"] == 1
    assert query_data["connectivity"] is not None
    assert query_data["connectivity_basis"] == "reverse_reachability_from_kernel"
