"""Integration tests for `ontos link-check` command."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _run_ontos(repo_root: Path, *args: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    return subprocess.run(
        [sys.executable, "-m", "ontos", *args],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        env=env,
    )


def _init_repo(tmp_path: Path, extra_config: str = "") -> None:
    (tmp_path / ".ontos.toml").write_text(
        "[ontos]\nversion='3.2'\n" + extra_config,
        encoding="utf-8",
    )
    (tmp_path / "docs").mkdir(exist_ok=True)


def _write_doc(
    path: Path,
    doc_id: str,
    *,
    doc_type: str = "atom",
    depends_on: Optional[str] = None,
    impacts: Optional[str] = None,
    describes: Optional[str] = None,
    body: str = "Body",
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        f"id: {doc_id}",
        f"type: {doc_type}",
        "status: active",
    ]
    if depends_on is not None:
        lines.append(f"depends_on: {depends_on}")
    if impacts is not None:
        lines.append(f"impacts: {impacts}")
    if describes is not None:
        lines.append(f"describes: {describes}")
    lines.extend(["---", body, ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def test_link_check_clean_library_exit_0(tmp_path: Path):
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "a.md", "a")
    _write_doc(tmp_path / "docs" / "b.md", "b", depends_on="[a]", body="See a.")

    result = _run_ontos(tmp_path, "link-check")

    assert result.returncode == 0
    assert "clean" in result.stdout.lower()


def test_link_check_broken_refs_exit_1(tmp_path: Path):
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "broken.md", "broken_doc", doc_type="strategy", depends_on="[missing_doc]")

    result = _run_ontos(tmp_path, "link-check")

    assert result.returncode == 1
    assert "broken" in result.stdout.lower()


def test_link_check_orphans_only_exit_3(tmp_path: Path):
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "orphan.md", "orphan_doc", doc_type="strategy")

    result = _run_ontos(tmp_path, "link-check")

    assert result.returncode == 3
    assert "orphan" in result.stdout.lower()


def test_link_check_duplicates_exit_1(tmp_path: Path):
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "a.md", "dup")
    _write_doc(tmp_path / "docs" / "b.md", "dup")

    result = _run_ontos(tmp_path, "link-check")

    assert result.returncode == 1
    assert "duplicate" in result.stdout.lower()


def test_link_check_cross_scope_reference_is_external(tmp_path: Path):
    _init_repo(tmp_path, extra_config="\n[validation]\nallowed_orphan_types=['atom','strategy']\n")
    _write_doc(
        tmp_path / "docs" / "docs.md",
        "docs_doc",
        doc_type="strategy",
        depends_on="[internal_doc]",
    )
    _write_doc(tmp_path / ".ontos-internal" / "internal.md", "internal_doc", doc_type="strategy")

    result = _run_ontos(tmp_path, "--json", "link-check")

    assert result.returncode == 0
    payload = json.loads(result.stdout)["data"]
    assert payload["summary"]["external_references"] == 1
    assert payload["summary"]["broken_references"] == 0


def test_link_check_json_schema_locations(tmp_path: Path):
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "target.md", "target_doc")
    _write_doc(
        tmp_path / "docs" / "source.md",
        "source_doc",
        depends_on="[missing_doc]",
        body="See missing_doc and [bad](missing_doc).",
    )

    result = _run_ontos(tmp_path, "--json", "link-check")
    envelope = json.loads(result.stdout)
    payload = envelope["data"]

    assert result.returncode == 1
    # Transport status stays "success" with findings; result quality is in data.
    assert envelope["status"] == "success"
    assert envelope["exit_code"] == 1
    assert envelope["error"] is None
    assert payload["result_status"] == "failing"
    assert payload["scope"] == "docs"
    assert "summary" in payload
    assert "broken_references" in payload

    frontmatter_items = [item for item in payload["broken_references"] if item["field"] == "depends_on"]
    body_items = [item for item in payload["broken_references"] if item["field"].startswith("body.")]
    assert frontmatter_items
    assert body_items
    assert frontmatter_items[0]["location"] is None
    assert body_items[0]["location"]["line"] >= 1


def test_link_check_quiet_suppresses_sections(tmp_path: Path):
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "broken.md", "broken_doc", doc_type="strategy", depends_on="[missing_doc]")

    result = _run_ontos(tmp_path, "link-check", "--quiet")
    assert result.returncode == 1
    assert "Scope + Census" not in result.stdout
    assert "status:" in result.stdout


def test_link_check_uses_config_default_scope_without_cli(tmp_path: Path):
    _init_repo(tmp_path, extra_config="\n[scanning]\ndefault_scope='library'\n")
    _write_doc(tmp_path / "docs" / "a.md", "a")
    _write_doc(tmp_path / ".ontos-internal" / "b.md", "b")

    result = _run_ontos(tmp_path, "--json", "link-check")
    envelope = json.loads(result.stdout)
    payload = envelope["data"]

    assert result.returncode == 0
    assert payload["scope"] == "library"
    assert payload["summary"]["documents_loaded"] == 2


def test_link_check_broken_impacts_frontmatter_exit_1_json(tmp_path: Path):
    _init_repo(tmp_path)
    _write_doc(
        tmp_path / "docs" / "source.md",
        "source_doc",
        impacts="[missing_impacts_target]",
    )

    result = _run_ontos(tmp_path, "--json", "link-check")
    envelope = json.loads(result.stdout)
    payload = envelope["data"]

    assert result.returncode == 1
    assert payload["summary"]["broken_references"] >= 1
    assert any(item["field"] == "impacts" for item in payload["broken_references"])


def test_link_check_broken_describes_frontmatter_exit_1_json(tmp_path: Path):
    _init_repo(tmp_path)
    _write_doc(
        tmp_path / "docs" / "source.md",
        "source_doc",
        describes="[missing_describes_target]",
    )

    result = _run_ontos(tmp_path, "--json", "link-check")
    envelope = json.loads(result.stdout)
    payload = envelope["data"]

    assert result.returncode == 1
    assert payload["summary"]["broken_references"] >= 1
    assert any(item["field"] == "describes" for item in payload["broken_references"])


def test_link_check_scope_library_includes_internal_docs_json(tmp_path: Path):
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "docs_doc.md", "docs_doc")
    _write_doc(tmp_path / ".ontos-internal" / "internal_doc.md", "internal_doc")

    result = _run_ontos(tmp_path, "--json", "link-check", "--scope", "library")
    envelope = json.loads(result.stdout)
    payload = envelope["data"]

    assert result.returncode == 0
    assert payload["scope"] == "library"
    assert payload["summary"]["documents_loaded"] == 2


def test_link_check_parse_failed_candidates_cli_json(tmp_path: Path):
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "known.md", "known_doc")
    (tmp_path / "docs" / "broken.md").write_text(
        "---\nid: [\n---\nSee known_doc in body.\n",
        encoding="utf-8",
    )

    result = _run_ontos(tmp_path, "--json", "link-check")
    envelope = json.loads(result.stdout)
    payload = envelope["data"]

    assert result.returncode == 0
    assert payload["summary"]["parse_failed_candidates"] >= 1
    assert payload["summary"]["broken_references"] == 0
    assert payload["result_status"] == "incomplete"
    assert envelope["result"]["status"] == "incomplete"


def test_link_check_version_like_doc_id_not_broken_with_body_ref(tmp_path: Path):
    """A doc ID matching a filtered pattern (e.g., v3.2) referenced in body text
    should NOT be reported as broken when the doc exists — the known-ID pass
    ensures it is detected even though _looks_like_doc_id would reject it."""
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "version_doc.md", "v3.2")
    _write_doc(
        tmp_path / "docs" / "referrer.md",
        "referrer",
        depends_on="[v3.2]",
        body="This document references v3.2 in body text.",
    )

    result = _run_ontos(tmp_path, "--json", "link-check")
    envelope = json.loads(result.stdout)
    payload = envelope["data"]

    assert result.returncode == 0
    assert payload["summary"]["broken_references"] == 0


def test_link_check_broken_ref_matching_filtered_pattern_not_detected_in_generic_scan(tmp_path: Path):
    """Known tradeoff: a broken bare-token reference whose ID matches a
    filtered pattern (e.g., short label 'A2') is NOT detected by the generic
    scan. This is intentional — these patterns overwhelmingly match non-doc
    content (audit labels, curation levels, config constants). The known-ID
    scan (Pass 1) still detects all references to *existing* docs with
    filtered-pattern names. See PR #77 for the precision/recall rationale."""
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "doc_a1.md", "A1", body="Roadmap references A2.")

    result = _run_ontos(tmp_path, "--json", "link-check")
    envelope = json.loads(result.stdout)
    payload = envelope["data"]

    # A2 is not detected as broken because _SHORT_LABEL_RE filters it
    # in the generic scan. This is the accepted tradeoff for eliminating
    # ~60+ false positives from short labels in audit/curation content.
    assert payload["summary"]["broken_references"] == 0


def test_link_check_short_label_doc_id_detected_when_exists(tmp_path: Path):
    """Short-label doc IDs (e.g., 'A1') are detected by the known-ID scan
    (Pass 1) even though _looks_like_doc_id would reject them in Pass 2."""
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "doc_a1.md", "A1")
    _write_doc(tmp_path / "docs" / "referrer.md", "referrer", body="See A1 for details.")

    result = _run_ontos(tmp_path, "--json", "link-check")
    envelope = json.loads(result.stdout)
    payload = envelope["data"]

    assert result.returncode == 0
    assert payload["summary"]["broken_references"] == 0


# =============================================================================
# (#131) Standard envelope contract
# =============================================================================


def test_link_check_json_emits_standard_envelope(tmp_path: Path):
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "broken.md", "broken_doc", doc_type="strategy", depends_on="[missing_doc]")

    result = _run_ontos(tmp_path, "--json", "link-check")
    envelope = json.loads(result.stdout)

    assert set(envelope) == {
        "schema_version", "command", "status", "exit_code",
        "message", "result", "data", "warnings", "error",
    }
    assert envelope["schema_version"] == "4.0"
    assert envelope["command"] == "link-check"
    assert envelope["status"] == "success"
    assert envelope["error"] is None
    assert envelope["result"]["status"] == "findings"
    assert envelope["result"]["exit_category"] == "findings"
    # Shell exit code mirrors the envelope's exit_code.
    assert result.returncode == envelope["exit_code"] == 1
    assert envelope["data"]["result_status"] == "failing"


def test_link_check_json_error_path_uses_envelope(tmp_path: Path):
    # No .ontos.toml and no markers — command cannot run.
    result = _run_ontos(tmp_path, "--json", "link-check")
    envelope = json.loads(result.stdout)

    assert envelope["command"] == "link-check"
    assert envelope["status"] == "error"
    assert envelope["error"]["code"] == "E_COMMAND_FAILED"
    assert result.returncode == 1


def test_link_check_result_status_mapping(tmp_path: Path):
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "a.md", "a")
    _write_doc(tmp_path / "docs" / "b.md", "b", depends_on="[a]", body="See a.")

    result = _run_ontos(tmp_path, "--json", "link-check")
    envelope = json.loads(result.stdout)
    assert result.returncode == 0
    assert envelope["data"]["result_status"] == "clean"


# =============================================================================
# (#135) Output controls, timings, progress
# =============================================================================


def _broken_repo(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "target.md", "target_doc")
    for i in range(3):
        _write_doc(
            tmp_path / "docs" / f"source_{i}.md",
            f"source_{i}",
            depends_on=f"[missing_doc_{i}]",
            body=f"See missing_doc_{i}.",
        )


def test_link_check_summary_mode_empties_lists_keeps_counts(tmp_path: Path):
    _broken_repo(tmp_path)

    result = _run_ontos(tmp_path, "--json", "link-check", "--summary")
    envelope = json.loads(result.stdout)
    data = envelope["data"]

    assert data["mode"] == "summary"
    assert data["broken_references"] == []
    assert data["orphans"] == []
    # Counters always reflect full totals.
    assert data["summary"]["broken_references"] >= 3
    assert data["findings_truncated"] is True
    assert "broken_references" in data["truncated_sections"]
    # Summary mode skips suggestion work entirely.
    assert data["options"]["suggestions"] is False
    assert result.returncode == envelope["exit_code"] == 1


def test_link_check_limit_caps_lists(tmp_path: Path):
    _broken_repo(tmp_path)

    result = _run_ontos(tmp_path, "--json", "link-check", "--limit", "1")
    data = json.loads(result.stdout)["data"]

    assert len(data["broken_references"]) == 1
    assert data["summary"]["broken_references"] >= 3
    assert data["findings_truncated"] is True
    assert "broken_references" in data["truncated_sections"]


def test_link_check_no_suggestions_flag(tmp_path: Path):
    _broken_repo(tmp_path)

    result = _run_ontos(tmp_path, "--json", "link-check", "--no-suggestions")
    data = json.loads(result.stdout)["data"]

    assert data["options"]["suggestions"] is False
    assert all(item["suggestions"] == [] for item in data["broken_references"])


def test_link_check_suggestions_present_by_default(tmp_path: Path):
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "target_document.md", "target_document")
    _write_doc(
        tmp_path / "docs" / "source.md",
        "source_doc",
        depends_on="[target_documnet]",  # typo → fuzzy suggestion
    )

    result = _run_ontos(tmp_path, "--json", "link-check")
    data = json.loads(result.stdout)["data"]

    broken = [i for i in data["broken_references"] if i["value"] == "target_documnet"]
    assert broken
    assert broken[0]["suggestions"]
    assert broken[0]["suggestions"][0]["candidate"] == "target_document"


def test_link_check_frontmatter_only_skips_body(tmp_path: Path):
    _init_repo(tmp_path)
    _write_doc(
        tmp_path / "docs" / "source.md",
        "source_doc",
        body="See [bad](missing_body_only_doc).",
    )

    result = _run_ontos(tmp_path, "--json", "link-check", "--frontmatter-only")
    data = json.loads(result.stdout)["data"]

    assert data["summary"]["broken_body"] == 0
    assert data["options"]["body_scan"] is False


def test_link_check_no_orphans_drops_exit_2(tmp_path: Path):
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "orphan.md", "orphan_doc", doc_type="strategy")

    default = _run_ontos(tmp_path, "--json", "link-check")
    assert default.returncode == 3

    no_orphans = _run_ontos(tmp_path, "--json", "link-check", "--no-orphans")
    data = json.loads(no_orphans.stdout)["data"]
    assert no_orphans.returncode == 0
    assert data["summary"]["orphans"] == 0
    assert data["options"]["orphans"] is False


def test_link_check_json_includes_timings(tmp_path: Path):
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "a.md", "a")

    result = _run_ontos(tmp_path, "--json", "link-check")
    data = json.loads(result.stdout)["data"]

    timings = data["timings_ms"]
    for phase in ("load", "external_scope", "frontmatter", "body_scan",
                  "suggestions", "parse_failed_scan", "orphans", "total"):
        assert phase in timings, f"missing timing phase {phase}"
        assert isinstance(timings[phase], int)


def test_link_check_human_run_emits_stage_markers_on_stderr(tmp_path: Path):
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "a.md", "a")

    result = _run_ontos(tmp_path, "link-check")
    assert "Loading" in result.stderr or "Checking" in result.stderr
    assert "⏳" not in result.stdout


def test_link_check_json_and_quiet_keep_stderr_silent(tmp_path: Path):
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "a.md", "a")

    json_run = _run_ontos(tmp_path, "--json", "link-check")
    assert json_run.stderr.strip() == ""
    json.loads(json_run.stdout)  # stdout stays one parseable document

    quiet_run = _run_ontos(tmp_path, "link-check", "--quiet")
    assert quiet_run.stderr.strip() == ""


# =============================================================================
# (#134) file_dependencies bucket in CLI JSON
# =============================================================================


def test_link_check_json_file_dependencies_bucket(tmp_path: Path):
    _init_repo(
        tmp_path,
        extra_config=(
            "\n[validation]\n"
            "allowed_orphan_types=['atom']\n"
            "allowed_external_dependency_paths=['apps/**']\n"
        ),
    )
    (tmp_path / "apps").mkdir()
    (tmp_path / "apps" / "real.py").write_text("code", encoding="utf-8")
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "other.py").write_text("code", encoding="utf-8")
    _write_doc(
        tmp_path / "docs" / "handoff.md",
        "handoff_doc",
        depends_on="[apps/real.py, tools/other.py]",
    )

    result = _run_ontos(tmp_path, "--json", "link-check")
    envelope = json.loads(result.stdout)
    data = envelope["data"]

    assert data["summary"]["file_dependencies"] == 2
    assert data["summary"]["unallowlisted_file_dependencies"] == 1
    assert data["summary"]["broken_references"] == 0
    assert data["summary"]["broken_frontmatter"] == 0
    items = {item["value"]: item for item in data["file_dependencies"]}
    assert items["apps/real.py"]["allowlisted"] is True
    assert items["apps/real.py"]["severity"] == "info"
    assert items["tools/other.py"]["allowlisted"] is False
    # The unallowlisted file dep preserves exit-1 semantics.
    assert result.returncode == envelope["exit_code"] == 1


def test_link_check_all_allowlisted_file_deps_exit_0(tmp_path: Path):
    _init_repo(
        tmp_path,
        extra_config=(
            "\n[validation]\n"
            "allowed_orphan_types=['atom']\n"
            "allowed_external_dependency_paths=['apps/**']\n"
        ),
    )
    (tmp_path / "apps").mkdir()
    (tmp_path / "apps" / "real.py").write_text("code", encoding="utf-8")
    _write_doc(
        tmp_path / "docs" / "handoff.md",
        "handoff_doc",
        depends_on="[apps/real.py]",
    )

    result = _run_ontos(tmp_path, "--json", "link-check")
    envelope = json.loads(result.stdout)

    assert result.returncode == envelope["exit_code"] == 0
    assert envelope["data"]["result_status"] == "clean"


def test_link_check_json_invalid_limit_keeps_envelope(tmp_path: Path):
    """(#139 review) --limit < 1 must fail inside the JSON envelope."""
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "a.md", "a")

    result = _run_ontos(tmp_path, "--json", "link-check", "--limit", "0")
    assert result.returncode == 2
    envelope = json.loads(result.stdout)
    assert envelope["command"] == "link-check"
    assert envelope["status"] == "error"
    assert envelope["error"]["code"] == "E_USER_INPUT"
    assert envelope["result"]["exit_category"] == "usage"

    human = _run_ontos(tmp_path, "link-check", "--limit", "-1")
    assert human.returncode == 2
    assert "--limit must be >= 1" in human.stderr


def test_link_check_human_output_respects_limit(tmp_path: Path):
    """(#139 review) --limit bounds the human findings sections too."""
    _broken_repo(tmp_path)  # 3 broken depends_on + 3 broken body refs

    result = _run_ontos(tmp_path, "link-check", "--limit", "1")
    out = result.stdout
    assert "... and" in out  # capped sections advertise the remainder
    # Only one depends_on finding line is printed.
    depends_lines = [
        line for line in out.splitlines()
        if line.startswith("    - source_") and "missing_doc" in line
    ]
    # one for depends_on group + one for body group at most
    assert len(depends_lines) <= 2
