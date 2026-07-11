"""Regression tests for malformed audit-registry rows."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate-audit-remediation-registry.py"
FINDING_REQUIRED_FIELDS = [
    "id",
    "origin",
    "baseline_commit",
    "severity",
    "root_program",
    "issue",
    "release",
    "status",
    "fix_commit",
    "verification_evidence",
    "allowed_paths",
    "lifecycle_state",
    "base_sha",
]
PROGRAM_REQUIRED_FIELDS = [
    "id",
    "root_program",
    "issue",
    "max_severity",
    "implementation_ref",
    "lifecycle_state",
    "lease_state",
    "allowed_paths",
    "base_sha",
    "default_release",
    "github_state",
    "github_milestone",
]
LEASE_REQUIRED_FIELDS = ["path", "programs", "order"]
INTEGRATION_REQUIRED_FIELDS = [
    "status",
    "release_blocking",
    "affected_issues",
    "reason",
]
EXTERNAL_DRIFT_REQUIRED_FIELDS = [
    "issue",
    "field",
    "observed",
    "expected",
    "status",
    "reason",
]


@pytest.fixture
def validator_module():
    spec = importlib.util.spec_from_file_location(
        "audit_registry_validator",
        VALIDATOR_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _validate_registry(
    validator_module,
    monkeypatch,
    tmp_path,
    registry,
    *,
    require_external_parity=False,
):
    registry_path = tmp_path / "registry.yaml"
    registry_path.write_text(
        yaml.safe_dump(registry, sort_keys=False),
        encoding="utf-8",
    )
    monkeypatch.setattr(validator_module, "REGISTRY_PATH", registry_path)
    return validator_module.validate(require_external_parity)


def _run_main_with_registry(
    validator_module,
    monkeypatch,
    tmp_path,
    registry,
):
    registry_path = tmp_path / "registry.yaml"
    registry_path.write_text(
        yaml.safe_dump(registry, sort_keys=False),
        encoding="utf-8",
    )
    monkeypatch.setattr(validator_module, "REGISTRY_PATH", registry_path)
    monkeypatch.setattr(validator_module.sys, "argv", [str(VALIDATOR_PATH)])
    return validator_module.main()


def _run_main_with_child_manifest(
    validator_module,
    monkeypatch,
    tmp_path,
    *,
    issue,
    manifest,
):
    manifest_path = tmp_path / f"manifest-{issue}.yaml"
    manifest_path.write_text(
        yaml.safe_dump(manifest, sort_keys=False),
        encoding="utf-8",
    )
    constant = (
        "SERIALIZER_MANIFEST_PATH" if issue == 146 else "DOCTOR_MANIFEST_PATH"
    )
    monkeypatch.setattr(validator_module, constant, manifest_path)
    monkeypatch.setattr(validator_module.sys, "argv", [str(VALIDATOR_PATH)])
    return validator_module.main()


def _external_issue_payloads(registry):
    programs = {program["issue"]: program for program in registry["programs"]}
    milestone_titles = {
        1: "Audit Release N — hotfix",
        2: "Audit Release N+1",
        3: "Audit Release N+2",
    }
    payloads = {}
    for issue in range(146, 159):
        rows = [row for row in registry["findings"] if row["issue"] == issue]
        if issue == 158:
            rows = [
                row
                for row in registry["findings"]
                if row["origin"] == "codex_revalidation"
            ]
        body_lines = [
            f"- [{'x' if row['status'] == 'code_fixed' else ' '}] {row['id']}"
            for row in rows
        ]
        if issue == 158:
            body_lines.append("v4.7.1 v4.9.0")
        program = programs.get(issue)
        milestone = (program or {}).get("github_milestone", 1)
        payloads[issue] = {
            "number": issue,
            "state": "OPEN",
            "title": f"Issue {issue}",
            "labels": [
                {"name": f"{(program or {}).get('max_severity', 'P1')}: audit"}
            ],
            "milestone": {"title": milestone_titles[milestone]},
            "body": "\n".join(body_lines),
        }
    return payloads


@pytest.mark.parametrize(
    "missing_field",
    FINDING_REQUIRED_FIELDS,
)
def test_every_missing_required_finding_field_is_collected_without_traceback(
    validator_module,
    monkeypatch,
    tmp_path,
    missing_field,
):
    registry = validator_module.load_yaml(validator_module.REGISTRY_PATH)
    registry = copy.deepcopy(registry)
    registry["findings"][0].pop(missing_field)

    errors = _validate_registry(
        validator_module,
        monkeypatch,
        tmp_path,
        registry,
    )

    assert any(
        "missing fields" in error and missing_field in error
        for error in errors
    )


@pytest.mark.parametrize("program_index", [0, 1])
@pytest.mark.parametrize("missing_field", PROGRAM_REQUIRED_FIELDS)
def test_every_missing_required_child_program_field_is_collected_without_traceback(
    validator_module,
    monkeypatch,
    tmp_path,
    program_index,
    missing_field,
):
    registry = copy.deepcopy(
        validator_module.load_yaml(validator_module.REGISTRY_PATH)
    )
    registry["programs"][program_index].pop(missing_field)

    errors = _validate_registry(
        validator_module,
        monkeypatch,
        tmp_path,
        registry,
    )

    assert any(
        "program" in error
        and "missing fields" in error
        and missing_field in error
        for error in errors
    )


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("id", None),
        ("origin", []),
        ("baseline_commit", []),
        ("severity", []),
        ("root_program", {}),
        ("issue", []),
        ("release", 1),
        ("status", {}),
        ("fix_commit", []),
        ("verification_evidence", [None]),
        ("allowed_paths", [None]),
        ("lifecycle_state", []),
        ("base_sha", []),
    ],
)
def test_malformed_finding_values_are_quarantined_without_traceback(
    validator_module,
    monkeypatch,
    tmp_path,
    field,
    invalid_value,
):
    registry = copy.deepcopy(
        validator_module.load_yaml(validator_module.REGISTRY_PATH)
    )
    registry["findings"][0][field] = invalid_value

    errors = _validate_registry(
        validator_module,
        monkeypatch,
        tmp_path,
        registry,
    )

    assert any(f"invalid {field}" in error for error in errors)


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("id", None),
        ("root_program", []),
        ("issue", []),
        ("max_severity", []),
        ("implementation_ref", []),
        ("lifecycle_state", []),
        ("lease_state", []),
        ("allowed_paths", [None]),
        ("base_sha", []),
        ("default_release", []),
        ("github_state", []),
        ("github_milestone", []),
    ],
)
def test_malformed_program_values_are_quarantined_without_traceback(
    validator_module,
    monkeypatch,
    tmp_path,
    field,
    invalid_value,
):
    registry = copy.deepcopy(
        validator_module.load_yaml(validator_module.REGISTRY_PATH)
    )
    registry["programs"][0][field] = invalid_value

    errors = _validate_registry(
        validator_module,
        monkeypatch,
        tmp_path,
        registry,
    )

    assert any(f"invalid {field}" in error for error in errors)


@pytest.mark.parametrize(
    ("collection", "field", "invalid_value"),
    [
        ("findings", "status", "confirmed_opne"),
        ("findings", "lifecycle_state", "implementation_commited"),
        ("programs", "lifecycle_state", "implementation_commited"),
        ("programs", "lease_state", "actve"),
    ],
)
def test_state_enum_typos_are_rejected_before_rows_can_be_filtered(
    validator_module,
    monkeypatch,
    tmp_path,
    collection,
    field,
    invalid_value,
):
    registry = copy.deepcopy(
        validator_module.load_yaml(validator_module.REGISTRY_PATH)
    )
    registry[collection][0][field] = invalid_value

    errors = _validate_registry(
        validator_module,
        monkeypatch,
        tmp_path,
        registry,
    )

    assert any(f"invalid {field}" in error for error in errors)


def test_valid_status_change_still_fails_immutable_distribution_parity(
    validator_module,
    monkeypatch,
    tmp_path,
):
    """A valid enum value must not bypass the frozen 41/40/7/2/1 counts."""
    registry = copy.deepcopy(
        validator_module.load_yaml(validator_module.REGISTRY_PATH)
    )
    finding = next(
        row
        for row in registry["findings"]
        if row["origin"] == "fable_audit"
        and row["status"] == "confirmed_open"
    )
    finding["status"] = "code_fixed"

    errors = _validate_registry(
        validator_module,
        monkeypatch,
        tmp_path,
        registry,
    )

    assert any(
        "original committed-snapshot status totals are wrong" in error
        for error in errors
    )
    assert not any("invalid status" in error for error in errors)


@pytest.mark.parametrize(
    ("field", "replacement", "expected_fragment"),
    [
        (
            "baseline_commit",
            "bf91b42f4eb5ba2ed6e0e3ea5e76d22ec6d7ec95",
            "baseline_commit mismatch",
        ),
        (
            "base_sha",
            "c8672e90f2382f4147ef61b4fba918969483e73e",
            "base_sha mismatch",
        ),
        ("release", "v4.9.0", "finding release distribution mismatch"),
        (
            "fix_commit",
            "b6f89d77e7fb684b8bd9a181a24c773d5777397a",
            "confirmed_open row must have null fix_commit",
        ),
    ],
)
def test_finding_authority_fields_cannot_drift_silently(
    validator_module,
    monkeypatch,
    tmp_path,
    field,
    replacement,
    expected_fragment,
):
    registry = copy.deepcopy(
        validator_module.load_yaml(validator_module.REGISTRY_PATH)
    )
    finding = next(
        row
        for row in registry["findings"]
        if row["issue"] == 148
        and row["status"] == "confirmed_open"
        and row["release"] == "v4.8.0"
    )
    finding[field] = replacement

    errors = _validate_registry(
        validator_module,
        monkeypatch,
        tmp_path,
        registry,
    )

    assert any(expected_fragment in error for error in errors)


def test_control_plane_row_binds_phase_c_close_snapshot(
    validator_module,
    monkeypatch,
    tmp_path,
):
    registry = copy.deepcopy(
        validator_module.load_yaml(validator_module.REGISTRY_PATH)
    )
    finding = next(
        row
        for row in registry["findings"]
        if row["id"] == "R2-control-plane-parity-1"
    )
    finding["fix_commit"] = validator_module.INTEGRATION_COMMIT
    finding["status"] = "implemented_committed_verification_pending"
    finding["lifecycle_state"] = "implementation_committed_lifecycle_pending"

    errors = _validate_registry(
        validator_module,
        monkeypatch,
        tmp_path,
        registry,
    )

    assert any("must bind its fix commit to Phase C close I1" in e for e in errors)
    assert any("status mismatch" in e for e in errors)
    assert any("lifecycle mismatch" in e for e in errors)


@pytest.mark.parametrize(
    ("field", "replacement", "expected_fragment"),
    [
        (
            "base_sha",
            "c8672e90f2382f4147ef61b4fba918969483e73e",
            "program #148 base_sha mismatch",
        ),
        (
            "implementation_ref",
            "03c36e6ac999d2c411c13252baa2e8fcff60e6ed",
            "program #148 implementation_ref mismatch",
        ),
        ("default_release", "v4.9.0", "program #148 default_release mismatch"),
    ],
)
def test_program_provenance_fields_cannot_drift_silently(
    validator_module,
    monkeypatch,
    tmp_path,
    field,
    replacement,
    expected_fragment,
):
    registry = copy.deepcopy(
        validator_module.load_yaml(validator_module.REGISTRY_PATH)
    )
    program = next(row for row in registry["programs"] if row["issue"] == 148)
    program[field] = replacement

    errors = _validate_registry(
        validator_module,
        monkeypatch,
        tmp_path,
        registry,
    )

    assert any(expected_fragment in error for error in errors)


def test_finding_root_program_must_match_owning_program(
    validator_module,
    monkeypatch,
    tmp_path,
):
    registry = copy.deepcopy(
        validator_module.load_yaml(validator_module.REGISTRY_PATH)
    )
    finding = next(row for row in registry["findings"] if row["issue"] == 146)
    finding["root_program"] = "project-ontos-audit-doctor-rce"

    errors = _validate_registry(
        validator_module,
        monkeypatch,
        tmp_path,
        registry,
    )

    assert any("root_program mismatch for issue #146" in error for error in errors)


@pytest.mark.parametrize(
    ("field", "replacement", "expected_fragment"),
    [
        (
            "root_program",
            "project-ontos-audit-remediation-wrong-owner",
            "root_program mismatch for issue #158",
        ),
        (
            "allowed_paths",
            ["SECURITY.md"],
            "finding scope exceeds owner #158",
        ),
    ],
)
def test_issue_158_control_plane_finding_is_checked_against_synthetic_owner(
    validator_module,
    monkeypatch,
    tmp_path,
    capsys,
    field,
    replacement,
    expected_fragment,
):
    registry = copy.deepcopy(
        validator_module.load_yaml(validator_module.REGISTRY_PATH)
    )
    finding = next(
        row
        for row in registry["findings"]
        if row["id"] == "R2-control-plane-parity-1"
    )
    finding[field] = replacement

    exit_code = _run_main_with_registry(
        validator_module,
        monkeypatch,
        tmp_path,
        registry,
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "audit-registry: FAILED" in captured.err
    assert expected_fragment in captured.err
    assert "audit-registry: ERROR" not in captured.err


@pytest.mark.parametrize(
    ("control_issue", "other_issue"),
    [(157, 158)],
)
def test_control_plane_finding_id_and_issue_158_are_reserved_as_a_pair(
    validator_module,
    monkeypatch,
    tmp_path,
    capsys,
    control_issue,
    other_issue,
):
    registry = copy.deepcopy(
        validator_module.load_yaml(validator_module.REGISTRY_PATH)
    )
    control_finding = next(
        row
        for row in registry["findings"]
        if row["id"] == "R2-control-plane-parity-1"
    )
    other_finding = next(
        row
        for row in registry["findings"]
        if row["issue"] == control_issue
        and row["id"] != "R2-control-plane-parity-1"
    )
    control_finding["issue"] = control_issue
    other_finding["issue"] = other_issue

    exit_code = _run_main_with_registry(
        validator_module,
        monkeypatch,
        tmp_path,
        registry,
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "R2-control-plane-parity-1 must be assigned to issue #158" in captured.err
    assert f"{other_finding['id']} cannot be assigned to reserved issue #158" in captured.err
    assert "audit-registry: ERROR" not in captured.err


@pytest.mark.parametrize(
    ("collection", "field", "invalid_path", "expected_fragment"),
    [
        ("findings", "verification_evidence", "/tmp/external", "evidence path"),
        ("findings", "verification_evidence", "../SECURITY.md", "evidence path"),
        ("findings", "verification_evidence", "SECURITY.md\x00", "evidence path"),
        ("findings", "allowed_paths", "/tmp/external", "allowed_paths"),
        ("findings", "allowed_paths", "docs/../SECURITY.md", "allowed_paths"),
        ("programs", "allowed_paths", "/tmp/external", "allowed_paths"),
        ("programs", "allowed_paths", "../SECURITY.md", "allowed_paths"),
        ("shared_path_leases", "path", "/tmp/external", "invalid path"),
        ("shared_path_leases", "path", "docs/../logs/", "invalid path"),
    ],
)
def test_control_plane_paths_must_be_canonical_repo_relative(
    validator_module,
    monkeypatch,
    tmp_path,
    collection,
    field,
    invalid_path,
    expected_fragment,
):
    registry = copy.deepcopy(
        validator_module.load_yaml(validator_module.REGISTRY_PATH)
    )
    if field == "path":
        registry[collection][0][field] = invalid_path
    else:
        registry[collection][0][field] = [invalid_path]

    errors = _validate_registry(
        validator_module,
        monkeypatch,
        tmp_path,
        registry,
    )

    assert any(expected_fragment in error for error in errors)


@pytest.mark.parametrize("collection", ["findings", "programs"])
def test_non_mapping_rows_are_quarantined_without_traceback(
    validator_module,
    monkeypatch,
    tmp_path,
    collection,
):
    registry = copy.deepcopy(
        validator_module.load_yaml(validator_module.REGISTRY_PATH)
    )
    registry[collection][0] = "not-a-mapping"

    errors = _validate_registry(
        validator_module,
        monkeypatch,
        tmp_path,
        registry,
    )

    singular = "finding" if collection == "findings" else "program"
    assert f"{singular} row 0 is not a mapping" in errors


@pytest.mark.parametrize("missing_field", LEASE_REQUIRED_FIELDS)
def test_every_missing_shared_path_lease_field_is_quarantined(
    validator_module,
    monkeypatch,
    tmp_path,
    missing_field,
):
    registry = copy.deepcopy(
        validator_module.load_yaml(validator_module.REGISTRY_PATH)
    )
    registry["shared_path_leases"][0].pop(missing_field)

    errors = _validate_registry(
        validator_module,
        monkeypatch,
        tmp_path,
        registry,
    )

    assert any(
        "shared_path_leases row 0 missing fields" in error
        and missing_field in error
        for error in errors
    )


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("path", []),
        ("programs", [146, {}]),
        ("order", [146, None]),
        ("policy", []),
    ],
)
def test_malformed_shared_path_lease_values_are_quarantined(
    validator_module,
    monkeypatch,
    tmp_path,
    field,
    invalid_value,
):
    registry = copy.deepcopy(
        validator_module.load_yaml(validator_module.REGISTRY_PATH)
    )
    registry["shared_path_leases"][0][field] = invalid_value

    errors = _validate_registry(
        validator_module,
        monkeypatch,
        tmp_path,
        registry,
    )

    assert any(
        f"shared_path_leases row 0 has invalid {field}" in error
        for error in errors
    )


@pytest.mark.parametrize(
    ("field", "duplicate_values", "rendered_row"),
    [
        (
            "programs",
            [146, 147, 147],
            "| `docs/logs/` | #146, #147, #147 | #146 → #147 | ordered |",
        ),
        (
            "order",
            [146, 147, 147],
            "| `docs/logs/` | #146, #147 | #146 → #147 → #147 | ordered |",
        ),
    ],
)
def test_duplicate_lease_lists_fail_even_when_o5_is_synchronized(
    validator_module,
    monkeypatch,
    tmp_path,
    capsys,
    field,
    duplicate_values,
    rendered_row,
):
    registry = copy.deepcopy(
        validator_module.load_yaml(validator_module.REGISTRY_PATH)
    )
    registry["shared_path_leases"][0][field] = duplicate_values

    original_row = (
        "| `docs/logs/` | #146, #147 | #146 → #147 | ordered |"
    )
    ledger = validator_module.LEDGER_PATH.read_text(encoding="utf-8")
    assert original_row in ledger
    ledger_path = tmp_path / "ledger.md"
    ledger_path.write_text(
        ledger.replace(original_row, rendered_row, 1),
        encoding="utf-8",
    )
    monkeypatch.setattr(validator_module, "LEDGER_PATH", ledger_path)

    exit_code = _run_main_with_registry(
        validator_module,
        monkeypatch,
        tmp_path,
        registry,
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "audit-registry: FAILED" in captured.err
    assert f"shared_path_leases row 0 has duplicate {field}" in captured.err
    assert "audit-registry: ERROR" not in captured.err


@pytest.mark.parametrize("missing_field", INTEGRATION_REQUIRED_FIELDS)
def test_every_missing_shared_tree_integration_field_is_quarantined(
    validator_module,
    monkeypatch,
    tmp_path,
    missing_field,
):
    registry = copy.deepcopy(
        validator_module.load_yaml(validator_module.REGISTRY_PATH)
    )
    registry["shared_tree_integration"].pop(missing_field)

    errors = _validate_registry(
        validator_module,
        monkeypatch,
        tmp_path,
        registry,
    )

    assert any(
        "shared_tree_integration missing fields" in error
        and missing_field in error
        for error in errors
    )


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("status", []),
        ("release_blocking", 1),
        ("affected_issues", [146, {}]),
        ("reason", []),
    ],
)
def test_malformed_shared_tree_integration_values_are_quarantined(
    validator_module,
    monkeypatch,
    tmp_path,
    field,
    invalid_value,
):
    registry = copy.deepcopy(
        validator_module.load_yaml(validator_module.REGISTRY_PATH)
    )
    registry["shared_tree_integration"][field] = invalid_value

    errors = _validate_registry(
        validator_module,
        monkeypatch,
        tmp_path,
        registry,
    )

    assert any(
        f"shared_tree_integration has invalid {field}" in error
        for error in errors
    )


@pytest.mark.parametrize(
    "case",
    [
        "lease_non_mapping",
        "lease_missing_path",
        "lease_unhashable_program",
        "lease_unhashable_order",
        "integration_non_mapping",
        "integration_missing_status",
        "integration_unhashable_issue",
        "missing_program_146",
        "missing_program_147",
    ],
)
def test_malformed_control_plane_collection_returns_exit_one_never_two(
    validator_module,
    monkeypatch,
    tmp_path,
    capsys,
    case,
):
    registry = copy.deepcopy(
        validator_module.load_yaml(validator_module.REGISTRY_PATH)
    )
    if case == "lease_non_mapping":
        registry["shared_path_leases"][0] = "not-a-mapping"
    elif case == "lease_missing_path":
        registry["shared_path_leases"][0].pop("path")
    elif case == "lease_unhashable_program":
        registry["shared_path_leases"][0]["programs"] = [146, {}]
    elif case == "lease_unhashable_order":
        registry["shared_path_leases"][0]["order"] = [146, []]
    elif case == "integration_non_mapping":
        registry["shared_tree_integration"] = ["not-a-mapping"]
    elif case == "integration_missing_status":
        registry["shared_tree_integration"].pop("status")
    elif case == "integration_unhashable_issue":
        registry["shared_tree_integration"]["affected_issues"] = [146, {}]
    elif case.startswith("missing_program_"):
        issue = int(case.rsplit("_", 1)[1])
        registry["programs"] = [
            program for program in registry["programs"]
            if program["issue"] != issue
        ]
    else:  # pragma: no cover - the parameter table is closed above
        raise AssertionError(case)

    exit_code = _run_main_with_registry(
        validator_module,
        monkeypatch,
        tmp_path,
        registry,
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "audit-registry: FAILED" in captured.err
    assert "audit-registry: ERROR" not in captured.err
    if case.startswith("missing_program_"):
        issue = int(case.rsplit("_", 1)[1])
        assert f"required program membership mismatch: missing=[{issue}]" in captured.err


@pytest.mark.parametrize("invalid_root", [None, [], "not-a-mapping", 47])
def test_malformed_registry_root_returns_exit_one_never_two(
    validator_module,
    monkeypatch,
    tmp_path,
    capsys,
    invalid_root,
):
    exit_code = _run_main_with_registry(
        validator_module,
        monkeypatch,
        tmp_path,
        invalid_root,
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "audit-registry: FAILED" in captured.err
    assert "registry root must be a YAML mapping" in captured.err
    assert "audit-registry: ERROR" not in captured.err


def test_malformed_registry_yaml_returns_exit_one_never_two(
    validator_module,
    monkeypatch,
    tmp_path,
    capsys,
):
    registry_path = tmp_path / "registry.yaml"
    registry_path.write_text("findings: [\n", encoding="utf-8")
    monkeypatch.setattr(validator_module, "REGISTRY_PATH", registry_path)
    monkeypatch.setattr(validator_module.sys, "argv", [str(VALIDATOR_PATH)])

    exit_code = validator_module.main()
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "audit-registry: FAILED" in captured.err
    assert f"invalid YAML in {registry_path}" in captured.err
    assert "audit-registry: ERROR" not in captured.err


@pytest.mark.parametrize("issue", [146, 147])
def test_malformed_child_manifest_yaml_returns_exit_one_never_two(
    validator_module,
    monkeypatch,
    tmp_path,
    capsys,
    issue,
):
    manifest_path = tmp_path / f"manifest-{issue}.yaml"
    manifest_path.write_text("scope: [\n", encoding="utf-8")
    constant = (
        "SERIALIZER_MANIFEST_PATH" if issue == 146 else "DOCTOR_MANIFEST_PATH"
    )
    monkeypatch.setattr(validator_module, constant, manifest_path)
    monkeypatch.setattr(validator_module.sys, "argv", [str(VALIDATOR_PATH)])

    exit_code = validator_module.main()
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "audit-registry: FAILED" in captured.err
    assert f"invalid YAML in {manifest_path}" in captured.err
    assert "audit-registry: ERROR" not in captured.err


@pytest.mark.parametrize("failure", ["read", "decode"])
def test_registry_yaml_input_failures_return_exit_one_never_two(
    validator_module,
    monkeypatch,
    tmp_path,
    capsys,
    failure,
):
    registry_path = tmp_path / "registry.yaml"
    if failure == "decode":
        registry_path.write_bytes(b"findings: \xff\n")
    monkeypatch.setattr(validator_module, "REGISTRY_PATH", registry_path)
    monkeypatch.setattr(validator_module.sys, "argv", [str(VALIDATOR_PATH)])

    exit_code = validator_module.main()
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "audit-registry: FAILED" in captured.err
    assert f"cannot read YAML input {registry_path}" in captured.err
    assert "audit-registry: ERROR" not in captured.err


def test_unexpected_validator_runtime_error_remains_exit_two(
    validator_module,
    monkeypatch,
    capsys,
):
    def raise_unexpected(_require_external_parity):
        raise RuntimeError("unexpected invariant failure")

    monkeypatch.setattr(validator_module, "validate", raise_unexpected)
    monkeypatch.setattr(validator_module.sys, "argv", [str(VALIDATOR_PATH)])

    exit_code = validator_module.main()
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "audit-registry: ERROR: unexpected invariant failure" in captured.err
    assert "audit-registry: FAILED" not in captured.err


@pytest.mark.parametrize("issue", [146, 147])
@pytest.mark.parametrize(
    "case",
    ["root", "scope", "allowed_paths_root", "allowed_paths_item"],
)
def test_malformed_child_manifest_scope_returns_exit_one_never_two(
    validator_module,
    monkeypatch,
    tmp_path,
    capsys,
    issue,
    case,
):
    source_path = (
        validator_module.SERIALIZER_MANIFEST_PATH
        if issue == 146
        else validator_module.DOCTOR_MANIFEST_PATH
    )
    manifest = copy.deepcopy(validator_module.load_yaml(source_path))
    if case == "root":
        manifest = []
    elif case == "scope":
        manifest["scope"] = []
    elif case == "allowed_paths_root":
        manifest["scope"]["allowed_paths"] = {}
    elif case == "allowed_paths_item":
        manifest["scope"]["allowed_paths"] = [{}]

    exit_code = _run_main_with_child_manifest(
        validator_module,
        monkeypatch,
        tmp_path,
        issue=issue,
        manifest=manifest,
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "audit-registry: FAILED" in captured.err
    assert f"#{issue} manifest" in captured.err
    assert "audit-registry: ERROR" not in captured.err


@pytest.mark.parametrize(
    ("issue", "field", "invalid_value"),
    [
        (147, "implementation_sequencing", []),
        (147, "required_dispatch_bundles", None),
        (147, "historical_receipt_gaps", None),
        (146, "gate_prerequisites", [None]),
    ],
)
def test_malformed_child_manifest_consumers_return_exit_one_never_two(
    validator_module,
    monkeypatch,
    tmp_path,
    capsys,
    issue,
    field,
    invalid_value,
):
    source_path = (
        validator_module.SERIALIZER_MANIFEST_PATH
        if issue == 146
        else validator_module.DOCTOR_MANIFEST_PATH
    )
    manifest = copy.deepcopy(validator_module.load_yaml(source_path))
    manifest[field] = invalid_value

    exit_code = _run_main_with_child_manifest(
        validator_module,
        monkeypatch,
        tmp_path,
        issue=issue,
        manifest=manifest,
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "audit-registry: FAILED" in captured.err
    assert f"#{issue} manifest {field}" in captured.err
    assert "audit-registry: ERROR" not in captured.err


def test_malformed_doctor_receipt_inventory_returns_exit_one_never_two(
    validator_module,
    monkeypatch,
    tmp_path,
    capsys,
):
    inventory_path = tmp_path / "inventory.yaml"
    inventory_path.write_text("[]\n", encoding="utf-8")
    monkeypatch.setattr(
        validator_module,
        "DOCTOR_RECEIPT_INVENTORY_PATH",
        inventory_path,
    )
    monkeypatch.setattr(validator_module.sys, "argv", [str(VALIDATOR_PATH)])

    exit_code = validator_module.main()
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "#147 receipt inventory root must be a mapping" in captured.err
    assert "audit-registry: ERROR" not in captured.err


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("github_state", []),
        ("github_milestone", []),
        ("max_severity", []),
    ],
)
def test_malformed_program_metadata_cannot_crash_external_parity(
    validator_module,
    monkeypatch,
    tmp_path,
    field,
    invalid_value,
):
    registry = copy.deepcopy(
        validator_module.load_yaml(validator_module.REGISTRY_PATH)
    )
    payloads = _external_issue_payloads(registry)
    registry["programs"][0][field] = invalid_value
    monkeypatch.setattr(
        validator_module,
        "live_github_issue",
        lambda issue: payloads[issue],
    )

    errors = _validate_registry(
        validator_module,
        monkeypatch,
        tmp_path,
        registry,
        require_external_parity=True,
    )

    assert any(f"invalid {field}" in error for error in errors)


@pytest.mark.parametrize("invalid_snapshot", [None, [], "not-a-mapping"])
def test_malformed_github_snapshot_root_is_a_validation_error(
    validator_module,
    monkeypatch,
    tmp_path,
    invalid_snapshot,
):
    registry = copy.deepcopy(
        validator_module.load_yaml(validator_module.REGISTRY_PATH)
    )
    registry["github_snapshot"] = invalid_snapshot

    errors = _validate_registry(
        validator_module,
        monkeypatch,
        tmp_path,
        registry,
    )

    assert "registry github_snapshot must be a mapping" in errors


@pytest.mark.parametrize(
    "count_field",
    ["issue_finding_counts", "registry_finding_counts"],
)
@pytest.mark.parametrize("invalid_counts", [None, [], "not-a-mapping"])
def test_malformed_snapshot_count_maps_are_validation_errors(
    validator_module,
    monkeypatch,
    tmp_path,
    count_field,
    invalid_counts,
):
    registry = copy.deepcopy(
        validator_module.load_yaml(validator_module.REGISTRY_PATH)
    )
    registry["github_snapshot"][count_field] = invalid_counts

    errors = _validate_registry(
        validator_module,
        monkeypatch,
        tmp_path,
        registry,
    )

    assert f"github_snapshot.{count_field} must be a mapping" in errors


@pytest.mark.parametrize(
    "count_field",
    ["issue_finding_counts", "registry_finding_counts"],
)
@pytest.mark.parametrize("invalid_count", [None, [], {}, True, "one"])
def test_malformed_snapshot_count_values_are_validation_errors(
    validator_module,
    monkeypatch,
    tmp_path,
    count_field,
    invalid_count,
):
    registry = copy.deepcopy(
        validator_module.load_yaml(validator_module.REGISTRY_PATH)
    )
    registry["github_snapshot"][count_field][146] = invalid_count

    errors = _validate_registry(
        validator_module,
        monkeypatch,
        tmp_path,
        registry,
    )

    assert any(
        f"github_snapshot.{count_field}[146] has invalid count" in error
        for error in errors
    )


@pytest.mark.parametrize("invalid_key", [True, "not-an-issue"])
def test_malformed_snapshot_count_keys_are_validation_errors(
    validator_module,
    monkeypatch,
    tmp_path,
    invalid_key,
):
    registry = copy.deepcopy(
        validator_module.load_yaml(validator_module.REGISTRY_PATH)
    )
    registry["github_snapshot"]["registry_finding_counts"][invalid_key] = 1

    errors = _validate_registry(
        validator_module,
        monkeypatch,
        tmp_path,
        registry,
    )

    assert any(
        "github_snapshot.registry_finding_counts has invalid issue key" in error
        for error in errors
    )


def test_duplicate_normalized_snapshot_count_key_is_a_validation_error(
    validator_module,
    monkeypatch,
    tmp_path,
):
    registry = copy.deepcopy(
        validator_module.load_yaml(validator_module.REGISTRY_PATH)
    )
    registry["github_snapshot"]["registry_finding_counts"]["146"] = 2

    errors = _validate_registry(
        validator_module,
        monkeypatch,
        tmp_path,
        registry,
    )

    assert any("duplicate normalized issue key: 146" in error for error in errors)


@pytest.mark.parametrize("invalid_drift", [None, {}, "not-a-list"])
def test_malformed_external_drift_root_is_a_validation_error(
    validator_module,
    monkeypatch,
    tmp_path,
    invalid_drift,
):
    registry = copy.deepcopy(
        validator_module.load_yaml(validator_module.REGISTRY_PATH)
    )
    registry["github_snapshot"]["external_drift"] = invalid_drift

    errors = _validate_registry(
        validator_module,
        monkeypatch,
        tmp_path,
        registry,
    )

    assert "github_snapshot.external_drift must be a list" in errors


@pytest.mark.parametrize("invalid_row", [None, [], "not-a-mapping"])
def test_non_mapping_external_drift_rows_are_quarantined(
    validator_module,
    monkeypatch,
    tmp_path,
    invalid_row,
):
    registry = copy.deepcopy(
        validator_module.load_yaml(validator_module.REGISTRY_PATH)
    )
    registry["github_snapshot"]["external_drift"][0] = invalid_row

    errors = _validate_registry(
        validator_module,
        monkeypatch,
        tmp_path,
        registry,
    )

    assert "github_snapshot.external_drift row 0 is not a mapping" in errors


@pytest.mark.parametrize("missing_field", EXTERNAL_DRIFT_REQUIRED_FIELDS)
def test_every_missing_external_drift_field_is_collected_without_traceback(
    validator_module,
    monkeypatch,
    tmp_path,
    missing_field,
):
    registry = copy.deepcopy(
        validator_module.load_yaml(validator_module.REGISTRY_PATH)
    )
    registry["github_snapshot"]["external_drift"][0].pop(missing_field)

    errors = _validate_registry(
        validator_module,
        monkeypatch,
        tmp_path,
        registry,
    )

    assert any(
        "external_drift row 0 missing fields" in error and missing_field in error
        for error in errors
    )


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("issue", []),
        ("field", []),
        ("observed", []),
        ("expected", {}),
        ("status", []),
        ("reason", []),
    ],
)
def test_malformed_external_drift_values_are_quarantined(
    validator_module,
    monkeypatch,
    tmp_path,
    field,
    invalid_value,
):
    registry = copy.deepcopy(
        validator_module.load_yaml(validator_module.REGISTRY_PATH)
    )
    registry["github_snapshot"]["external_drift"][0][field] = invalid_value

    errors = _validate_registry(
        validator_module,
        monkeypatch,
        tmp_path,
        registry,
    )

    assert any(
        f"external_drift row 0 has invalid {field}" in error for error in errors
    )


@pytest.mark.parametrize(
    ("case", "expected_error"),
    [
        ("payload", "payload is not a mapping"),
        ("number", "has mismatched number"),
        ("title", "has invalid title"),
        ("body", "has invalid body"),
        ("state", "has invalid state"),
        ("milestone", "has invalid milestone"),
        ("milestone_title", "has invalid milestone title"),
        ("labels", "has invalid labels"),
        ("label_row", "label 0 is not a mapping"),
        ("label_name", "label 0 has invalid name"),
        ("duplicate_checklist", "has invalid checklist body"),
    ],
)
def test_malformed_live_github_payload_is_a_parity_error(
    validator_module,
    monkeypatch,
    tmp_path,
    case,
    expected_error,
):
    registry = copy.deepcopy(
        validator_module.load_yaml(validator_module.REGISTRY_PATH)
    )
    payloads = _external_issue_payloads(registry)
    if case == "payload":
        payloads[146] = []
    elif case == "number":
        payloads[146]["number"] = 147
    elif case == "title":
        payloads[146]["title"] = "   "
    elif case in {"body", "state", "milestone"}:
        payloads[146][case] = []
    elif case == "labels":
        payloads[146]["labels"] = {}
    elif case == "milestone_title":
        payloads[146]["milestone"]["title"] = []
    elif case == "label_row":
        payloads[146]["labels"][0] = []
    elif case == "label_name":
        payloads[146]["labels"][0]["name"] = []
    elif case == "duplicate_checklist":
        payloads[146]["body"] += "\n- [ ] D2b-roundtrip-3"
    monkeypatch.setattr(
        validator_module,
        "live_github_issue",
        lambda issue: payloads[issue],
    )

    errors = _validate_registry(
        validator_module,
        monkeypatch,
        tmp_path,
        registry,
        require_external_parity=True,
    )

    assert any(
        f"live GitHub issue #146 {expected_error}" in error for error in errors
    )


def test_live_epic_rejects_phantom_checklist_ids(
    validator_module,
    monkeypatch,
    tmp_path,
):
    registry = copy.deepcopy(
        validator_module.load_yaml(validator_module.REGISTRY_PATH)
    )
    payloads = _external_issue_payloads(registry)
    payloads[158]["body"] += "\n- [ ] D6a-test-gaps-3"
    monkeypatch.setattr(
        validator_module,
        "live_github_issue",
        lambda issue: payloads[issue],
    )

    errors = _validate_registry(
        validator_module,
        monkeypatch,
        tmp_path,
        registry,
        require_external_parity=True,
    )

    assert any(
        "live GitHub issue #158 finding checklist mismatch" in error
        and "D6a-test-gaps-3" in error
        for error in errors
    )


@pytest.mark.parametrize("stdout", ["[]", "not-json"])
def test_successful_transport_with_malformed_json_is_quarantined(
    validator_module,
    monkeypatch,
    stdout,
):
    result = type(
        "Completed",
        (),
        {"returncode": 0, "stdout": stdout, "stderr": ""},
    )()
    monkeypatch.setattr(
        validator_module.subprocess,
        "run",
        lambda *args, **kwargs: result,
    )

    payload = validator_module.live_github_issue(146)
    errors = []
    validator_module.normalize_live_issue_payload(146, payload, errors)

    assert "live GitHub issue #146 payload is not a mapping" in errors


@pytest.mark.parametrize("external", [False, True])
def test_malformed_parity_metadata_returns_validation_exit_one(
    validator_module,
    monkeypatch,
    tmp_path,
    capsys,
    external,
):
    registry = copy.deepcopy(
        validator_module.load_yaml(validator_module.REGISTRY_PATH)
    )
    payloads = _external_issue_payloads(registry)
    if external:
        payloads[146]["body"] = []
        monkeypatch.setattr(
            validator_module,
            "live_github_issue",
            lambda issue: payloads[issue],
        )
    else:
        registry["github_snapshot"]["issue_finding_counts"][146] = []
    registry_path = tmp_path / "registry.yaml"
    registry_path.write_text(
        yaml.safe_dump(registry, sort_keys=False),
        encoding="utf-8",
    )
    monkeypatch.setattr(validator_module, "REGISTRY_PATH", registry_path)
    argv = [str(VALIDATOR_PATH)]
    if external:
        argv.append("--require-external-parity")
    monkeypatch.setattr(validator_module.sys, "argv", argv)

    exit_code = validator_module.main()
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "audit-registry: FAILED" in captured.err
    assert "audit-registry: ERROR" not in captured.err


def test_regression_matrix_matches_validator_required_fields(validator_module):
    assert set(FINDING_REQUIRED_FIELDS) == validator_module.REQUIRED_FINDING_FIELDS
    assert set(PROGRAM_REQUIRED_FIELDS) == validator_module.REQUIRED_PROGRAM_FIELDS
    assert set(LEASE_REQUIRED_FIELDS) == validator_module.REQUIRED_LEASE_FIELDS
    assert (
        set(INTEGRATION_REQUIRED_FIELDS)
        == validator_module.REQUIRED_INTEGRATION_FIELDS
    )
    assert (
        set(EXTERNAL_DRIFT_REQUIRED_FIELDS)
        == validator_module.REQUIRED_EXTERNAL_DRIFT_FIELDS
    )


def test_distinct_missing_required_fields_are_collected_without_traceback(
    validator_module,
    monkeypatch,
    tmp_path,
):
    """The first structural guard collects omissions before parity analysis."""
    registry = copy.deepcopy(
        validator_module.load_yaml(validator_module.REGISTRY_PATH)
    )
    registry["findings"][0].pop("id")
    registry["findings"][1].pop("issue")

    errors = _validate_registry(
        validator_module,
        monkeypatch,
        tmp_path,
        registry,
    )

    assert any("missing fields: ['id']" in error for error in errors)
    assert any("missing fields: ['issue']" in error for error in errors)


def test_missing_and_none_ids_do_not_create_duplicate_none_diagnostic(
    validator_module,
    monkeypatch,
    tmp_path,
):
    registry = copy.deepcopy(
        validator_module.load_yaml(validator_module.REGISTRY_PATH)
    )
    registry["findings"][0].pop("id")
    registry["findings"][1]["id"] = None

    errors = _validate_registry(
        validator_module,
        monkeypatch,
        tmp_path,
        registry,
    )

    assert any("missing fields: ['id']" in error for error in errors)
    assert not any(
        "duplicate registry IDs" in error and "None" in error
        for error in errors
    )


@pytest.mark.parametrize("require_external_parity", [False, True])
def test_valid_registry_preserves_local_and_synthetic_external_parity(
    validator_module,
    monkeypatch,
    tmp_path,
    require_external_parity,
):
    registry = copy.deepcopy(
        validator_module.load_yaml(validator_module.REGISTRY_PATH)
    )
    if require_external_parity:
        payloads = _external_issue_payloads(registry)
        monkeypatch.setattr(
            validator_module,
            "live_github_issue",
            lambda issue: payloads[issue],
        )

    errors = _validate_registry(
        validator_module,
        monkeypatch,
        tmp_path,
        registry,
        require_external_parity=require_external_parity,
    )

    assert errors == []


def test_o4_rendered_provenance_must_match_registry_exactly(
    validator_module,
    monkeypatch,
    tmp_path,
):
    ledger = validator_module.LEDGER_PATH.read_text(encoding="utf-8")
    corrupted = ledger.replace(
        "base `bf91b42f4eb5ba2ed6e0e3ea5e76d22ec6d7ec95`; "
        "implementation `b6f89d77e7fb684b8bd9a181a24c773d5777397a`",
        "base `0000000000000000000000000000000000000000`; "
        "implementation `1111111111111111111111111111111111111111`",
        1,
    )
    ledger_path = tmp_path / "ledger.md"
    ledger_path.write_text(corrupted, encoding="utf-8")
    monkeypatch.setattr(validator_module, "LEDGER_PATH", ledger_path)

    errors = validator_module.validate(False)

    assert any("O4 row #146 differs from registry authority" in error for error in errors)


def test_o5_rendered_lease_order_must_match_registry_exactly(
    validator_module,
    monkeypatch,
    tmp_path,
):
    ledger = validator_module.LEDGER_PATH.read_text(encoding="utf-8")
    corrupted = ledger.replace(
        "| `ontos/core/schema.py` | #146, #151 | #146 → #151 | ordered |",
        "| `ontos/core/schema.py` | #146, #151 | #151 → #146 | ordered |",
        1,
    )
    ledger_path = tmp_path / "ledger.md"
    ledger_path.write_text(corrupted, encoding="utf-8")
    monkeypatch.setattr(validator_module, "LEDGER_PATH", ledger_path)

    errors = validator_module.validate(False)

    assert any(
        "O5 lease ontos/core/schema.py differs from registry authority" in error
        for error in errors
    )
