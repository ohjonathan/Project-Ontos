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

from ontos.commands.maintain import (
    MaintainContext,
    MaintainOptions,
    _scan_docs,
    _task_check_links,
)
from ontos.io.config import load_project_config
from ontos.mcp import tools as mcp_tools
from ontos.ui.output import OutputHandler
from tests.mcp_helpers import build_cache


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


def test_concept_warning_counts_agree_across_full_validation_surfaces(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / ".ontos.toml",
        """
        [ontos]
        version = "4.0"
        """,
    )
    _write(
        tmp_path / ".ontos-internal/reference/Common_Concepts.md",
        """
        | Concept | Description |
        |---|---|
        | `known` | Known concept |
        """,
    )
    _write(
        tmp_path / "docs/a.md",
        """
        ---
        id: a
        type: atom
        status: active
        concepts: [known, unknown]
        ---
        """,
    )

    map_payload = _payload(_run(tmp_path, "--json", "map", "--strict"))
    activate = _payload(
        _run(tmp_path, "--json", "activate", "--warnings", "full")
    )
    doctor = _payload(_run(tmp_path, "--json", "doctor"))
    doctor_checks = {check["name"]: check for check in doctor["data"]["checks"]}
    cache = build_cache(tmp_path)
    mcp_activate = mcp_tools.activate(cache)
    mcp_map = mcp_tools.context_map(cache, compact="full")

    assert map_payload["data"]["warnings"] == 1
    assert activate["data"]["summary"]["validation_warnings"] == 1
    assert doctor_checks["activation_health"]["data"]["validation_warnings"] == 1
    assert mcp_activate["warnings_total"] == 1
    assert len(mcp_map["validation"]["warnings"]) == 1
    assert mcp_map["validation"]["warnings"][0]["rule_id"] == "curation"


def test_configured_context_map_is_excluded_across_counted_surfaces(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / ".ontos.toml",
        """
        [ontos]
        version = "4.0"

        [paths]
        context_map = "docs/Ontos_Context_Map.md"
        """,
    )
    _write(
        tmp_path / "docs/a.md",
        """
        ---
        id: a
        type: atom
        status: active
        ---
        """,
    )
    _write(
        tmp_path / "docs/b.md",
        """
        ---
        id: b
        type: atom
        status: active
        depends_on: [a]
        ---
        """,
    )
    _write(
        tmp_path / "docs/Ontos_Context_Map.md",
        """
        ---
        id: ontos_context_map
        type: strategy
        status: complete
        ---
        Generated map.
        """,
    )

    map_payload = _payload(_run(tmp_path, "--json", "map"))
    activate = _payload(_run(tmp_path, "--json", "activate", "--warnings", "full"))
    doctor = _payload(_run(tmp_path, "--json", "doctor"))
    link_check = _payload(_run(tmp_path, "--json", "link-check"))
    query = _payload(_run(tmp_path, "--json", "query", "--health"))
    query_data = query["data"]["results"] if "results" in query["data"] else query["data"]

    config = load_project_config(repo_root=tmp_path)
    maintain_ctx = MaintainContext(
        repo_root=tmp_path,
        config=config,
        options=MaintainOptions(quiet=True),
        output=OutputHandler(quiet=True),
    )
    maintain_paths = _scan_docs(maintain_ctx)
    maintain = _task_check_links(maintain_ctx)
    cache = build_cache(tmp_path)
    mcp_map = mcp_tools.context_map(cache, compact="full")

    doctor_checks = {check["name"]: check for check in doctor["data"]["checks"]}
    assert map_payload["data"]["documents"] == 2
    assert activate["data"]["documents"] == 2
    assert "2 documents" in doctor_checks["docs_directory"]["message"]
    assert link_check["data"]["summary"]["documents_loaded"] == 2
    assert link_check["data"]["summary"]["orphans"] == 0
    assert query_data["total_docs"] == 2
    assert query_data["orphans"] == 0
    assert len(maintain_paths) == 2
    assert maintain.metrics["orphans"] == 0
    assert len(cache.snapshot.documents) == 2
    assert all(
        warning["rule_id"] != "orphan"
        for warning in mcp_map["validation"]["warnings"]
    )


def test_body_reference_counts_agree_between_link_check_and_maintain(
    tmp_path: Path,
) -> None:
    _write(tmp_path / ".ontos.toml", "[ontos]\nversion = '4.0'\n")
    _write(
        tmp_path / "docs/a.md",
        """
        ---
        id: a
        type: atom
        status: active
        ---
        See [[missing_body_doc]].
        """,
    )

    link_check = _payload(_run(tmp_path, "--json", "link-check"))
    config = load_project_config(repo_root=tmp_path)
    maintain = _task_check_links(
        MaintainContext(
            repo_root=tmp_path,
            config=config,
            options=MaintainOptions(quiet=True),
            output=OutputHandler(quiet=True),
        )
    )

    assert link_check["exit_code"] == 1
    assert link_check["data"]["summary"]["broken_references"] == 1
    assert link_check["data"]["summary"]["broken_body"] == 1
    assert maintain.status == "failed"
    assert maintain.exit_code == 1
    assert maintain.metrics["broken_links"] == 1


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


def test_external_dependent_orphan_divergence_is_labeled(fixture_repo: Path) -> None:
    """(#133 review) A docs-scope orphan depended on from .ontos-internal is
    filtered by link-check but not by activate/query (which never load the
    external scope). The counts legitimately differ — and link-check must
    LABEL its basis so the difference is explained, not contradictory."""
    _write(
        fixture_repo / ".ontos-internal/internal_doc.md",
        """
        ---
        id: internal_doc
        type: atom
        status: active
        depends_on: [strategy_orphan]
        ---
        Internal body.
        """,
    )

    activate = _payload(_run(fixture_repo, "--json", "activate", "--warnings", "full"))
    link_check = _payload(_run(fixture_repo, "--json", "link-check"))
    query = _payload(_run(fixture_repo, "--json", "query", "--health"))

    activate_orphans = [
        w for w in activate["data"]["validation"]["warnings"]
        if w.get("rule_id") == "orphan"
    ]
    query_data = query["data"]["results"] if "results" in query["data"] else query["data"]

    # activate/query still see the orphan (docs scope only)...
    assert len(activate_orphans) == 1
    assert query_data["orphans"] == 1
    # ...link-check filters it because an internal doc depends on it,
    # and says so via its basis label.
    assert link_check["data"]["summary"]["orphans"] == 0
    assert link_check["data"]["count_basis"]["orphans"] == (
        "graph_validation_excluding_external_dependents"
    )


def test_human_health_output_carries_basis_labels(fixture_repo: Path) -> None:
    """(#133 review) The text report mirrors the JSON basis labels."""
    result = _run(fixture_repo, "query", "--health")
    assert result.returncode == 0
    assert "Orphans: 1 (allowed types: atom)" in result.stdout
    assert "Count basis: graph_validation" in result.stdout


def test_orphan_basis_stays_default_when_filter_removes_nothing(fixture_repo: Path) -> None:
    """(#133 polish) An .ontos-internal doc whose deps are path-style (or
    point at non-orphans) must not flip the orphan basis label — the
    exclusion label is reserved for runs where an orphan was actually
    filtered."""
    _write(
        fixture_repo / ".ontos-internal/internal_doc.md",
        """
        ---
        id: internal_doc
        type: atom
        status: active
        depends_on: [apps/real.py]
        ---
        Internal body with a path-style dep only.
        """,
    )

    link_check = _payload(_run(fixture_repo, "--json", "link-check"))

    # The docs-scope orphan is untouched by the external index...
    assert link_check["data"]["summary"]["orphans"] == 1
    # ...so the basis stays the shared default.
    assert link_check["data"]["count_basis"]["orphans"] == "graph_validation"
