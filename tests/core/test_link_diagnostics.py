"""Core diagnostics tests for link-check shared engine."""

from pathlib import Path
from typing import Optional

from ontos.core.link_diagnostics import run_link_diagnostics
from ontos.io.config import load_project_config
from ontos.io.files import load_documents
from ontos.io.scan_scope import ScanScope, collect_scoped_documents
from ontos.io.yaml import parse_frontmatter_content


def _init_project(tmp_path: Path, extra_config: str = "") -> None:
    (tmp_path / ".ontos.toml").write_text(
        "[ontos]\nversion='3.2'\n"
        + extra_config,
        encoding="utf-8",
    )
    (tmp_path / "docs").mkdir(exist_ok=True)


def _write_doc(
    path: Path,
    doc_id: str,
    *,
    doc_type: str = "atom",
    status: str = "active",
    depends_on: Optional[str] = None,
    impacts: Optional[str] = None,
    describes: Optional[str] = None,
    body: str = "Body",
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frontmatter = [
        "---",
        f"id: {doc_id}",
        f"type: {doc_type}",
        f"status: {status}",
    ]
    if depends_on is not None:
        frontmatter.append(f"depends_on: {depends_on}")
    if impacts is not None:
        frontmatter.append(f"impacts: {impacts}")
    if describes is not None:
        frontmatter.append(f"describes: {describes}")
    frontmatter.extend(["---", body, ""])
    path.write_text("\n".join(frontmatter), encoding="utf-8")


def _run(tmp_path: Path, scope: ScanScope):
    config = load_project_config(config_path=tmp_path / ".ontos.toml", repo_root=tmp_path)
    paths = collect_scoped_documents(
        tmp_path,
        config,
        scope,
        base_skip_patterns=list(config.scanning.skip_patterns),
    )
    load_result = load_documents(paths, parse_frontmatter_content)
    return run_link_diagnostics(
        repo_root=tmp_path,
        config=config,
        doc_paths=paths,
        scope=scope,
        load_result=load_result,
    )


def test_clean_library_returns_exit_0(tmp_path: Path):
    _init_project(tmp_path)
    _write_doc(tmp_path / "docs" / "a.md", "a", doc_type="atom")
    _write_doc(tmp_path / "docs" / "b.md", "b", doc_type="atom", depends_on="[a]", body="See a.")

    result = _run(tmp_path, ScanScope.LIBRARY)

    assert result.exit_code == 0
    assert result.summary.broken_references == 0
    assert result.summary.duplicate_ids == 0


def test_broken_depends_on_returns_exit_1(tmp_path: Path):
    _init_project(tmp_path)
    _write_doc(
        tmp_path / "docs" / "broken.md",
        "broken_doc",
        doc_type="strategy",
        depends_on="[missing_doc]",
    )

    result = _run(tmp_path, ScanScope.LIBRARY)

    assert result.exit_code == 1
    assert result.summary.broken_frontmatter == 1
    assert any(finding.field == "depends_on" for finding in result.broken_references)


def test_orphans_only_returns_exit_3(tmp_path: Path):
    _init_project(tmp_path)
    _write_doc(tmp_path / "docs" / "orphan.md", "orphan_doc", doc_type="strategy")

    result = _run(tmp_path, ScanScope.LIBRARY)

    assert result.exit_code == 3
    assert result.summary.broken_references == 0
    assert result.summary.orphans == 1


def test_duplicate_ids_return_exit_1(tmp_path: Path):
    _init_project(tmp_path)
    _write_doc(tmp_path / "docs" / "a.md", "duplicate_doc")
    _write_doc(tmp_path / "docs" / "b.md", "duplicate_doc")

    result = _run(tmp_path, ScanScope.LIBRARY)

    assert result.exit_code == 1
    assert result.summary.duplicate_ids == 1
    assert "duplicate_doc" in result.duplicates


def test_cross_scope_reference_is_external_not_broken(tmp_path: Path):
    _init_project(tmp_path, extra_config="\n[validation]\nallowed_orphan_types=['atom', 'strategy']\n")
    _write_doc(
        tmp_path / "docs" / "doc.md",
        "docs_doc",
        doc_type="strategy",
        depends_on="[internal_doc]",
    )
    _write_doc(tmp_path / ".ontos-internal" / "internal.md", "internal_doc", doc_type="strategy")

    result = _run(tmp_path, ScanScope.DOCS)

    assert result.summary.broken_references == 0
    assert result.summary.external_references == 1
    assert result.exit_code == 0


def test_parse_failed_candidates_reported_without_affecting_exit(tmp_path: Path):
    _init_project(tmp_path)
    _write_doc(tmp_path / "docs" / "known.md", "known_doc")
    (tmp_path / "docs" / "broken.md").write_text(
        "---\nid: [\n---\nSee known_doc in body.\n",
        encoding="utf-8",
    )

    result = _run(tmp_path, ScanScope.LIBRARY)

    assert result.summary.parse_failed_candidates >= 1
    assert result.exit_code == 0


def test_body_broken_reference_gets_suggestion(tmp_path: Path):
    # (#117) Broken bare-id-token detection in body text now requires an
    # explicit `[[id]]` wikilink sigil. The prose-token heuristic was
    # disabled in link-check after producing ~11k false positives per
    # 163-doc corpus; deliberate references still surface via the sigil.
    _init_project(tmp_path)
    _write_doc(tmp_path / "docs" / "target.md", "v3_2_1")
    _write_doc(
        tmp_path / "docs" / "source.md",
        "source_doc",
        body="See [[v3_2]] for details.",
    )

    result = _run(tmp_path, ScanScope.LIBRARY)

    assert result.exit_code == 1
    body_broken = [finding for finding in result.broken_references if finding.field == "body.bare_id_token"]
    assert body_broken
    assert body_broken[0].suggestions


def test_broken_depends_on_value_with_apostrophe_uses_structured_context(tmp_path: Path):
    _init_project(tmp_path)
    _write_doc(
        tmp_path / "docs" / "broken.md",
        "broken_doc",
        depends_on='["don\'t-exist"]',
    )

    result = _run(tmp_path, ScanScope.LIBRARY)

    assert [finding.value for finding in result.broken_references] == ["don't-exist"]


def test_body_location_is_physical_file_line_not_body_relative(tmp_path: Path):
    _init_project(tmp_path)
    _write_doc(
        tmp_path / "docs" / "source.md",
        "source_doc",
        body="\n\nSee [[missing_doc]].",
    )

    result = _run(tmp_path, ScanScope.LIBRARY)

    finding = next(
        item for item in result.broken_references if item.value == "missing_doc"
    )
    assert finding.location is not None
    assert finding.location.line == 8


def test_markdown_path_resolves_loaded_doc_with_stem_id_mismatch(tmp_path: Path):
    _init_project(tmp_path)
    _write_doc(tmp_path / "docs" / "Ontos_Manual.md", "ontos_manual")
    _write_doc(
        tmp_path / "docs" / "source.md",
        "source_doc",
        body="See [the manual](Ontos_Manual.md).",
    )

    result = _run(tmp_path, ScanScope.LIBRARY)

    assert result.summary.broken_body == 0
    assert result.summary.file_dependencies == 0


def test_canonical_document_id_precedes_same_named_file_resolution(tmp_path: Path):
    _init_project(tmp_path)
    _write_doc(tmp_path / "docs" / "actual.md", "target_id")
    (tmp_path / "docs" / "target_id").write_text("not a document", encoding="utf-8")
    _write_doc(
        tmp_path / "docs" / "source.md",
        "source_doc",
        body="See [target](target_id).",
    )

    result = _run(tmp_path, ScanScope.LIBRARY)

    assert result.summary.broken_body == 0
    assert result.summary.file_dependencies == 0


def test_markdown_loaded_doc_path_is_case_insensitive_and_collision_aware(tmp_path: Path):
    _init_project(tmp_path)
    _write_doc(tmp_path / "docs" / "Ontos_Manual.md", "ontos_manual")
    _write_doc(
        tmp_path / "docs" / "source.md",
        "source_doc",
        body="See [the manual](ONTOS_MANUAL.MD).",
    )

    result = _run(tmp_path, ScanScope.LIBRARY)

    assert result.summary.broken_body == 0


def test_markdown_source_file_with_line_anchor_is_informational_file_reference(
    tmp_path: Path,
):
    _init_project(tmp_path)
    source_file = tmp_path / "ontos" / "core" / "graph.py"
    source_file.parent.mkdir(parents=True)
    source_file.write_text("# source\n", encoding="utf-8")
    _write_doc(
        tmp_path / "docs" / "review.md",
        "review_doc",
        body="See [implementation](ontos/core/graph.py:170).",
    )

    result = _run(tmp_path, ScanScope.LIBRARY)

    assert result.summary.broken_body == 0
    assert result.summary.file_dependencies == 1
    assert result.summary.unallowlisted_file_dependencies == 0
    reference = result.file_dependencies[0]
    assert reference.field == "body.markdown_link_target"
    assert reference.value == "ontos/core/graph.py:170"
    assert reference.resolved_path == "ontos/core/graph.py"
    assert reference.allowlisted is True


def test_markdown_path_to_external_scope_uses_actual_external_id(tmp_path: Path):
    _init_project(
        tmp_path,
        extra_config="\n[validation]\nallowed_orphan_types=['atom', 'strategy']\n",
    )
    _write_doc(
        tmp_path / ".ontos-internal" / "Internal_Artifact.md",
        "internal_doc",
    )
    _write_doc(
        tmp_path / "docs" / "source.md",
        "source_doc",
        body="See [internal](../.ontos-internal/Internal_Artifact.md).",
    )

    result = _run(tmp_path, ScanScope.DOCS)

    assert result.summary.broken_body == 0
    assert result.summary.external_references == 1
    assert result.external_references[0].resolved_external_id == "internal_doc"


def test_body_scanner_runs_once_per_loaded_document(tmp_path: Path, monkeypatch):
    _init_project(tmp_path)
    _write_doc(tmp_path / "docs" / "a.md", "a")
    _write_doc(tmp_path / "docs" / "b.md", "b")

    from ontos.core import link_diagnostics

    real_scan = link_diagnostics.scan_body_references
    calls = []

    def counted_scan(*args, **kwargs):
        calls.append(kwargs.get("body", ""))
        return real_scan(*args, **kwargs)

    monkeypatch.setattr(link_diagnostics, "scan_body_references", counted_scan)

    _run(tmp_path, ScanScope.LIBRARY)

    assert len(calls) == 2


# =============================================================================
# (#135) include_orphans, timings, progress, suggestion memoization
# =============================================================================


def test_include_orphans_false_skips_orphan_detection(tmp_path: Path):
    _init_project(tmp_path)
    _write_doc(tmp_path / "docs" / "orphan.md", "orphan_doc", doc_type="strategy")

    config = load_project_config(config_path=tmp_path / ".ontos.toml", repo_root=tmp_path)
    paths = collect_scoped_documents(
        tmp_path, config, ScanScope.LIBRARY,
        base_skip_patterns=list(config.scanning.skip_patterns),
    )
    result = run_link_diagnostics(
        repo_root=tmp_path,
        config=config,
        doc_paths=paths,
        scope=ScanScope.LIBRARY,
        include_orphans=False,
    )

    assert result.orphans == []
    assert result.summary.orphans == 0
    assert result.exit_code == 0  # exit-2 outcome removed


def test_timings_ms_records_all_phases(tmp_path: Path):
    _init_project(tmp_path)
    _write_doc(tmp_path / "docs" / "a.md", "a")

    result = _run(tmp_path, ScanScope.LIBRARY)

    for phase in ("load", "external_scope", "frontmatter", "body_scan",
                  "suggestions", "parse_failed_scan", "orphans", "total"):
        assert phase in result.timings_ms
        assert isinstance(result.timings_ms[phase], int)
    # load_result was pre-supplied in _run, so load time is recorded as 0.
    assert result.timings_ms["load"] == 0


def test_progress_callback_receives_stage_markers(tmp_path: Path):
    _init_project(tmp_path)
    _write_doc(tmp_path / "docs" / "source.md", "source_doc", depends_on="[missing_doc]")

    config = load_project_config(config_path=tmp_path / ".ontos.toml", repo_root=tmp_path)
    paths = collect_scoped_documents(
        tmp_path, config, ScanScope.LIBRARY,
        base_skip_patterns=list(config.scanning.skip_patterns),
    )
    stages = []
    run_link_diagnostics(
        repo_root=tmp_path,
        config=config,
        doc_paths=paths,
        scope=ScanScope.LIBRARY,
        progress=stages.append,
    )

    joined = " | ".join(stages)
    assert "Loading" in joined
    assert "frontmatter references" in joined
    assert "body references" in joined
    assert "suggestions" in joined
    assert "orphans" in joined


def test_suggestions_memoized_for_repeated_values(tmp_path: Path):
    """The same broken value declared from several docs gets identical
    suggestion objects without recomputation."""
    _init_project(tmp_path)
    _write_doc(tmp_path / "docs" / "target_document.md", "target_document")
    for i in range(3):
        _write_doc(
            tmp_path / "docs" / f"source_{i}.md",
            f"source_{i}",
            depends_on="[target_documnet]",
        )

    result = _run(tmp_path, ScanScope.LIBRARY)

    findings = [f for f in result.broken_references if f.value == "target_documnet"]
    assert len(findings) == 3
    suggestion_lists = [
        [(s.candidate, s.confidence, s.reason) for s in f.suggestions]
        for f in findings
    ]
    assert suggestion_lists[0] == suggestion_lists[1] == suggestion_lists[2]
    assert suggestion_lists[0][0][0] == "target_document"


def test_to_data_payload_summary_and_limit_modes(tmp_path: Path):
    _init_project(tmp_path)
    _write_doc(tmp_path / "docs" / "s1.md", "s1", depends_on="[missing_1]")
    _write_doc(tmp_path / "docs" / "s2.md", "s2", depends_on="[missing_2]")

    result = _run(tmp_path, ScanScope.LIBRARY)

    full = result.to_data_payload()
    assert full["mode"] == "full"
    assert full["findings_truncated"] is False
    assert len(full["broken_references"]) == 2

    capped = result.to_data_payload(limit=1)
    assert len(capped["broken_references"]) == 1
    assert capped["findings_truncated"] is True
    assert capped["summary"]["broken_references"] == 2

    summary = result.to_data_payload(summary_only=True)
    assert summary["mode"] == "summary"
    assert summary["broken_references"] == []
    assert summary["summary"]["broken_references"] == 2


# =============================================================================
# (#134) file_dependencies re-bucketing and exit codes
# =============================================================================


def _file_dep_project(tmp_path: Path, allowlist: str = "") -> None:
    extra = ""
    if allowlist:
        extra = f"\n[validation]\nallowed_external_dependency_paths={allowlist}\n"
    _init_project(tmp_path, extra_config=extra)
    (tmp_path / "apps").mkdir(exist_ok=True)
    (tmp_path / "apps" / "real.py").write_text("code", encoding="utf-8")
    (tmp_path / "tools").mkdir(exist_ok=True)
    (tmp_path / "tools" / "other.py").write_text("code", encoding="utf-8")


def test_allowlisted_file_dep_rebucketed_and_exit_0(tmp_path: Path):
    _file_dep_project(tmp_path, allowlist="['apps/**']")
    _write_doc(
        tmp_path / "docs" / "handoff.md",
        "handoff_doc",
        depends_on="[apps/real.py]",
    )

    result = _run(tmp_path, ScanScope.LIBRARY)

    assert result.summary.file_dependencies == 1
    assert result.summary.unallowlisted_file_dependencies == 0
    assert result.summary.broken_references == 0
    assert result.summary.broken_frontmatter == 0
    assert result.exit_code == 0
    item = result.file_dependencies[0]
    assert item.allowlisted is True
    assert item.value == "apps/real.py"
    assert item.resolved_path == "apps/real.py"
    assert item.severity == "info"


def test_unallowlisted_file_dep_keeps_exit_1(tmp_path: Path):
    _file_dep_project(tmp_path, allowlist="['apps/**']")
    _write_doc(
        tmp_path / "docs" / "handoff.md",
        "handoff_doc",
        depends_on="[tools/other.py]",
    )

    result = _run(tmp_path, ScanScope.LIBRARY)

    assert result.summary.file_dependencies == 1
    assert result.summary.unallowlisted_file_dependencies == 1
    assert result.summary.broken_references == 0
    assert result.exit_code == 1


def test_unconfigured_repo_file_dep_still_exit_1(tmp_path: Path):
    # No allowlist configured: resolved-on-disk deps move buckets but keep
    # the historical exit-1 semantics.
    _file_dep_project(tmp_path)
    _write_doc(
        tmp_path / "docs" / "handoff.md",
        "handoff_doc",
        depends_on="[apps/real.py]",
    )

    result = _run(tmp_path, ScanScope.LIBRARY)

    assert result.summary.unallowlisted_file_dependencies == 1
    assert result.exit_code == 1


def test_missing_dep_still_broken_reference(tmp_path: Path):
    _file_dep_project(tmp_path, allowlist="['apps/**']")
    _write_doc(
        tmp_path / "docs" / "handoff.md",
        "handoff_doc",
        depends_on="[apps/missing.py]",
    )

    result = _run(tmp_path, ScanScope.LIBRARY)

    assert result.summary.file_dependencies == 0
    assert result.summary.broken_references == 1
    assert result.exit_code == 1


def test_to_data_payload_includes_file_dependencies(tmp_path: Path):
    _file_dep_project(tmp_path, allowlist="['apps/**']")
    _write_doc(
        tmp_path / "docs" / "handoff.md",
        "handoff_doc",
        depends_on="[apps/real.py, tools/other.py]",
    )

    result = _run(tmp_path, ScanScope.LIBRARY)
    payload = result.to_data_payload()

    assert payload["summary"]["file_dependencies"] == 2
    assert payload["summary"]["unallowlisted_file_dependencies"] == 1
    items = {item["value"]: item for item in payload["file_dependencies"]}
    assert items["apps/real.py"]["allowlisted"] is True
    assert items["tools/other.py"]["allowlisted"] is False
    assert items["tools/other.py"]["field"] == "depends_on"
