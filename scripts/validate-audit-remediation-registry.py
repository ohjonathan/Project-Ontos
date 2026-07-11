#!/usr/bin/env python3
"""Validate the audit registry and its local rendered control-plane artifacts."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "manifests/project-ontos-audit-remediation-registry.yaml"
AUDIT_PATH = ROOT / "docs/reviews/2026-07-02-fable-repo-audit.md"
LEDGER_PATH = ROOT / "docs/trackers/project-ontos-audit-remediation-release-line.md"
REVALIDATION_PATH = ROOT / "docs/reviews/2026-07-10-codex-audit-revalidation.md"
DOCTOR_MANIFEST_PATH = ROOT / "manifests/project-ontos-audit-doctor-rce.yaml"
SERIALIZER_MANIFEST_PATH = ROOT / "manifests/project-ontos-audit-serializer-corruption.yaml"
DOCTOR_RECEIPT_INVENTORY_PATH = (
    ROOT
    / "docs/reviews/project-ontos-audit-doctor-rce/lifecycle-receipt-inventory.yaml"
)
GITHUB_REPOSITORY = "ohjonathan/Project-Ontos"
AUDIT_BASELINE_COMMIT = "589d919"
REVALIDATION_COMMIT = "bf91b42f4eb5ba2ed6e0e3ea5e76d22ec6d7ec95"
INTEGRATION_COMMIT = "b6f89d77e7fb684b8bd9a181a24c773d5777397a"
CONTROL_PLANE_FIX_COMMIT = "05b090d53f7b0c9c4afdbb5fb23ab58cdfa01fa0"
DOCTOR_BASE_COMMIT = "c8672e90f2382f4147ef61b4fba918969483e73e"
DOCTOR_FIX_COMMIT = "03c36e6ac999d2c411c13252baa2e8fcff60e6ed"
CONTROL_PLANE_FINDING_ID = "R2-control-plane-parity-1"
CONTROL_PLANE_ISSUE = 158
CONTROL_PLANE_OWNER = {
    "id": "project-ontos-audit-remediation-2026-07",
    "root_program": "project-ontos-audit-remediation-2026-07",
    "issue": CONTROL_PLANE_ISSUE,
    "base_sha": REVALIDATION_COMMIT,
    "allowed_paths": (
        "manifests/project-ontos-audit-remediation-registry.yaml",
        "docs/reviews/2026-07-10-codex-audit-revalidation.md",
        "docs/trackers/project-ontos-audit-remediation-release-line.md",
        "docs/handoffs/project-ontos-audit-remediation-2026-07-*.md",
        "scripts/validate-audit-remediation-registry.py",
        "tests/test_audit_remediation_registry_validator.py",
    ),
}

REQUIRED_FINDING_FIELDS = {
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
}
REQUIRED_PROGRAM_FIELDS = {
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
}
REQUIRED_LEASE_FIELDS = {"path", "programs", "order"}
REQUIRED_INTEGRATION_FIELDS = {
    "status",
    "release_blocking",
    "affected_issues",
    "reason",
}
REQUIRED_PROGRAM_ISSUES = set(range(146, 158))
FINDING_ORIGINS = {"fable_audit", "codex_revalidation"}
FINDING_SEVERITIES = {"P0", "P1", "P2"}
FINDING_STATUSES = {
    "confirmed_open",
    "code_fixed",
    "code_fixed_evidence_pending",
    "implemented_committed_parity_verified",
    "implemented_committed_verification_pending",
    "partial_implementation_committed_verification_pending",
}
FINDING_LIFECYCLE_STATES = {
    "code_fixed_evidence_pending",
    "implementation_committed_lifecycle_pending",
    "parity_verified_lifecycle_pending",
    "partial_implementation_committed_lifecycle_pending",
}
PROGRAM_LIFECYCLE_STATES = {
    "code_fixed_evidence_pending",
    "implementation_committed_lifecycle_pending",
    "partial_implementation_committed_lifecycle_pending",
}
PROGRAM_LEASE_STATES = {
    "active",
    "evidence_only",
    "implementation_committed_integration_pending",
}
REQUIRED_EXTERNAL_DRIFT_FIELDS = {
    "issue",
    "field",
    "observed",
    "expected",
    "status",
    "reason",
}
EXPECTED_R2_IDS = {
    "R2-test-hermeticity-1",
    "R2-context-tmp-symlink-1",
    "R2-loader-id-type-1",
    "R2-windows-fcntl-import-1",
    "R2-lifecycle-type-enumeration-1",
    "R2-testpypi-provenance-1",
    "R2-activation-version-skew-1",
    "R2-mcp-readonly-export-1",
    "R2-control-plane-parity-1",
}
EXPECTED_IMPLEMENTED_COMMITTED_ORIGINAL_IDS = {
    "D1a-graph-link-1",
    "D1a-graph-link-2",
    "D1a-graph-link-3",
    "D1a-graph-link-4",
    "D1a-graph-link-5",
    "D1a-graph-link-6",
    "D1a-graph-link-7",
    "D1a-graph-link-8",
    "D1a-graph-link-9",
    "D1c-envelope-4",
    "D1c-envelope-5",
    "D2a-write-safety-2",
    "D2a-write-safety-7",
    "D2a-write-safety-9",
    "D2b-roundtrip-1",
    "D2b-roundtrip-4",
    "D2b-roundtrip-5",
    "D3a-parsers-2",
    "D3a-parsers-3",
    "D3b-structure-1",
    "D3b-structure-2",
    "D4a-config-2",
    "D5a-repo-redundancy-1",
    "D5a-repo-redundancy-2",
    "D5b-dead-code-7",
    "D6a-test-gaps-10",
    "D6a-test-gaps-2",
    "D6a-test-gaps-4",
    "D6a-test-gaps-6",
    "D6a-test-gaps-8",
    "D6b-test-quality-1",
    "D6b-test-quality-5",
    "D6b-test-quality-9",
    "D7-cli-consistency-10",
    "D7-cli-consistency-2",
    "D7-cli-consistency-3",
    "D7-cli-consistency-4",
    "D7-cli-consistency-6",
    "D7-cli-consistency-7",
    "D7-cli-consistency-8",
}
EXPECTED_PARTIAL_COMMITTED_ORIGINAL_IDS = {
    "D2a-write-safety-6",
    "D3b-structure-6",
    "D5a-repo-redundancy-3",
    "D6a-test-gaps-7",
    "D6a-test-gaps-9",
    "D6b-test-quality-6",
    "D7-cli-consistency-5",
}
EXPECTED_DEFAULT_RELEASES = {
    146: "v4.7.1",
    147: "v4.7.1",
    148: "v4.8.0",
    149: "v4.8.0",
    150: "v4.8.0",
    151: "v4.8.0",
    152: "v4.8.0",
    153: "v4.8.0",
    154: "v4.9.0",
    155: "v4.9.0",
    156: "v4.8.0",
    157: "v4.9.0",
}
EXPECTED_RELEASE_COUNTS = Counter(
    {
        (146, "v4.7.1"): 2,
        (147, "v4.7.1"): 2,
        (148, "v4.7.1"): 3,
        (148, "v4.8.0"): 9,
        (149, "v4.7.1"): 2,
        (149, "v4.8.0"): 19,
        (150, "v4.7.1"): 1,
        (150, "v4.8.0"): 15,
        (151, "v4.7.1"): 1,
        (151, "v4.8.0"): 5,
        (152, "v4.8.0"): 6,
        (153, "v4.7.1"): 1,
        (153, "v4.8.0"): 11,
        (154, "v4.9.0"): 14,
        (155, "v4.9.0"): 1,
        (156, "v4.8.0"): 2,
        (156, "v4.9.0"): 3,
        (157, "v4.9.0"): 2,
        (158, "v4.7.1"): 1,
    }
)


class ControlPlaneInputError(Exception):
    """A malformed or unreadable operator-controlled YAML input."""


def load_yaml(path: Path) -> Any:
    """Load YAML without imposing a root type on every document.

    Root-shape checks belong to the individual control-plane validators so a
    malformed registry or child manifest is a normal validation failure
    (exit 1), not an exception-derived validator error (exit 2).
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ControlPlaneInputError(
            f"cannot read YAML input {path}: {exc}"
        ) from exc
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ControlPlaneInputError(f"invalid YAML in {path}: {exc}") from exc


def audit_register() -> dict[str, str]:
    severity: str | None = None
    result: dict[str, str] = {}
    for line in AUDIT_PATH.read_text(encoding="utf-8").splitlines():
        if line.startswith("## P0 "):
            severity = "P0"
        elif line.startswith("## P1 "):
            severity = "P1"
        elif line.startswith("## P2 "):
            severity = "P2"
        elif line.startswith("### D"):
            finding_id = line[4:].split(" — ", 1)[0].strip()
            if severity is None:
                raise ValueError(f"finding {finding_id} appears outside a severity section")
            if finding_id in result:
                raise ValueError(f"duplicate audit finding heading: {finding_id}")
            result[finding_id] = severity
    return result


def path_is_directory(path: str) -> bool:
    return path.endswith("/")


def overlapping_path(left: str, right: str) -> str | None:
    if left == right:
        return left
    if path_is_directory(left) and right.startswith(left):
        return right
    if path_is_directory(right) and left.startswith(right):
        return left
    return None


def lease_covers(lease_path: str, overlap: str) -> bool:
    return lease_path == overlap or (path_is_directory(lease_path) and overlap.startswith(lease_path))


def path_scope_covers(parent: str, child: str) -> bool:
    return parent == child or (path_is_directory(parent) and child.startswith(parent))


def is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def is_string_list(value: Any) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(is_nonempty_string(item) for item in value)
    )


def is_canonical_repo_path(value: Any) -> bool:
    """Return whether *value* is a canonical, non-escaping repo path.

    Directory scopes may retain one trailing slash.  Absolute paths, Windows
    separators/drives, empty or dot segments, and parent traversal are
    rejected lexically before any filesystem lookup.
    """
    if not is_nonempty_string(value) or value != value.strip():
        return False
    if "\x00" in value or "\\" in value or re.match(r"^[A-Za-z]:", value):
        return False
    directory_scope = value.endswith("/")
    core = value[:-1] if directory_scope else value
    if not core or core.startswith("/"):
        return False
    parts = core.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return False
    return PurePosixPath(core).as_posix() == core


def is_issue_number(value: Any, *, include_epic: bool) -> bool:
    upper_bound = 159 if include_epic else 158
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and value in range(146, upper_bound)
    )


def is_commit_ref(value: Any) -> bool:
    return bool(
        isinstance(value, str)
        and re.fullmatch(r"[0-9a-f]{7,40}", value)
    )


def commit_exists(value: str) -> bool:
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{value}^{{commit}}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def normalize_snapshot_counts(
    value: Any,
    *,
    field: str,
    errors: list[str],
) -> dict[int, int]:
    if not isinstance(value, dict):
        errors.append(f"github_snapshot.{field} must be a mapping")
        return {}

    normalized: dict[int, int] = {}
    for raw_issue, raw_count in value.items():
        if isinstance(raw_issue, int) and not isinstance(raw_issue, bool):
            issue = raw_issue
        elif isinstance(raw_issue, str) and raw_issue.isdecimal():
            issue = int(raw_issue)
        else:
            errors.append(
                f"github_snapshot.{field} has invalid issue key: {raw_issue!r}"
            )
            continue
        if issue not in range(146, 159):
            errors.append(
                f"github_snapshot.{field} has out-of-range issue key: {raw_issue!r}"
            )
            continue
        if issue in normalized:
            errors.append(
                f"github_snapshot.{field} has duplicate normalized issue key: {issue}"
            )
            continue
        if (
            not isinstance(raw_count, int)
            or isinstance(raw_count, bool)
            or raw_count < 0
        ):
            errors.append(
                f"github_snapshot.{field}[{raw_issue!r}] has invalid count: "
                f"{raw_count!r}"
            )
            continue
        normalized[issue] = raw_count
    return normalized


def normalize_external_drift(value: Any, errors: list[str]) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        errors.append("github_snapshot.external_drift must be a list")
        return []

    normalized: list[dict[str, Any]] = []
    scalar_types = (str, int, float, bool, type(None))
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            errors.append(f"github_snapshot.external_drift row {index} is not a mapping")
            continue
        item_invalid = False
        missing = sorted(REQUIRED_EXTERNAL_DRIFT_FIELDS - item.keys())
        if missing:
            errors.append(
                f"github_snapshot.external_drift row {index} missing fields: {missing}"
            )
            item_invalid = True
        if "issue" in item and not is_issue_number(item.get("issue"), include_epic=True):
            errors.append(
                f"github_snapshot.external_drift row {index} has invalid issue: "
                f"{item.get('issue')!r}"
            )
            item_invalid = True
        for field in ("field", "status", "reason"):
            if field in item and not is_nonempty_string(item.get(field)):
                errors.append(
                    f"github_snapshot.external_drift row {index} has invalid {field}: "
                    f"{item.get(field)!r}"
                )
                item_invalid = True
        for field in ("observed", "expected"):
            if field in item and not isinstance(item.get(field), scalar_types):
                errors.append(
                    f"github_snapshot.external_drift row {index} has invalid {field}: "
                    f"{item.get(field)!r}"
                )
                item_invalid = True
        if not item_invalid:
            normalized.append(item)
    return normalized


def normalize_shared_path_leases(
    value: Any,
    errors: list[str],
) -> list[dict[str, Any]]:
    """Return only structurally safe shared-path lease rows."""
    if not isinstance(value, list):
        errors.append("registry shared_path_leases must be a list")
        return []

    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            errors.append(f"shared_path_leases row {index} is not a mapping")
            continue
        item_invalid = False
        missing = sorted(REQUIRED_LEASE_FIELDS - item.keys())
        if missing:
            errors.append(
                f"shared_path_leases row {index} missing fields: {missing}"
            )
            item_invalid = True
        if "path" in item and not is_canonical_repo_path(item.get("path")):
            errors.append(
                f"shared_path_leases row {index} has invalid path: "
                f"{item.get('path')!r}"
            )
            item_invalid = True
        for field in ("programs", "order"):
            issue_values = item.get(field)
            if field in item and (
                not isinstance(issue_values, list)
                or not issue_values
                or not all(
                    is_issue_number(issue, include_epic=False)
                    for issue in issue_values
                )
            ):
                errors.append(
                    f"shared_path_leases row {index} has invalid {field}: "
                    f"{issue_values!r}"
                )
                item_invalid = True
            elif field in item and len(set(issue_values)) != len(issue_values):
                errors.append(
                    f"shared_path_leases row {index} has duplicate {field}: "
                    f"{issue_values!r}"
                )
                item_invalid = True
        if "policy" in item and not is_nonempty_string(item.get("policy")):
            errors.append(
                f"shared_path_leases row {index} has invalid policy: "
                f"{item.get('policy')!r}"
            )
            item_invalid = True
        if not item_invalid:
            normalized.append(item)
    return normalized


def normalize_shared_tree_integration(
    value: Any,
    errors: list[str],
) -> dict[str, Any] | None:
    """Validate the shared-tree integration record before any consumer."""
    if not isinstance(value, dict):
        errors.append("registry shared_tree_integration must be a mapping")
        return None

    invalid = False
    missing = sorted(REQUIRED_INTEGRATION_FIELDS - value.keys())
    if missing:
        errors.append(f"shared_tree_integration missing fields: {missing}")
        invalid = True
    for field in ("status", "reason"):
        if field in value and not is_nonempty_string(value.get(field)):
            errors.append(
                f"shared_tree_integration has invalid {field}: {value.get(field)!r}"
            )
            invalid = True
    if "release_blocking" in value and not isinstance(
        value.get("release_blocking"), bool
    ):
        errors.append(
            "shared_tree_integration has invalid release_blocking: "
            f"{value.get('release_blocking')!r}"
        )
        invalid = True
    affected_issues = value.get("affected_issues")
    if "affected_issues" in value and (
        not isinstance(affected_issues, list)
        or not affected_issues
        or not all(
            is_issue_number(issue, include_epic=False)
            for issue in affected_issues
        )
    ):
        errors.append(
            "shared_tree_integration has invalid affected_issues: "
            f"{affected_issues!r}"
        )
        invalid = True
    elif isinstance(affected_issues, list) and len(set(affected_issues)) != len(
        affected_issues
    ):
        errors.append(
            "shared_tree_integration has duplicate affected_issues: "
            f"{affected_issues!r}"
        )
        invalid = True
    return None if invalid else value


def normalize_live_issue_payload(
    issue: int,
    value: Any,
    errors: list[str],
) -> tuple[str, str, str, set[str]]:
    if not isinstance(value, dict):
        errors.append(f"live GitHub issue #{issue} payload is not a mapping")
        return "", "", "", set()

    number = value.get("number")
    if (
        not isinstance(number, int)
        or isinstance(number, bool)
        or number != issue
    ):
        errors.append(
            f"live GitHub issue #{issue} has mismatched number: {number!r}"
        )

    title = value.get("title")
    if not is_nonempty_string(title):
        errors.append(
            f"live GitHub issue #{issue} has invalid title: {title!r}"
        )

    body = value.get("body")
    if not isinstance(body, str):
        errors.append(
            f"live GitHub issue #{issue} has invalid body: {body!r}"
        )
        body = ""

    state = value.get("state")
    if not is_nonempty_string(state):
        errors.append(
            f"live GitHub issue #{issue} has invalid state: {state!r}"
        )
        state = ""

    milestone = value.get("milestone")
    milestone_title = ""
    if not isinstance(milestone, dict):
        errors.append(
            f"live GitHub issue #{issue} has invalid milestone: {milestone!r}"
        )
    elif not is_nonempty_string(milestone.get("title")):
        errors.append(
            f"live GitHub issue #{issue} has invalid milestone title: "
            f"{milestone.get('title')!r}"
        )
    else:
        milestone_title = milestone["title"]

    labels = value.get("labels")
    label_names: set[str] = set()
    if not isinstance(labels, list):
        errors.append(
            f"live GitHub issue #{issue} has invalid labels: {labels!r}"
        )
    else:
        for index, label in enumerate(labels):
            if not isinstance(label, dict):
                errors.append(
                    f"live GitHub issue #{issue} label {index} is not a mapping"
                )
                continue
            name = label.get("name")
            if not is_nonempty_string(name):
                errors.append(
                    f"live GitHub issue #{issue} label {index} has invalid name: "
                    f"{name!r}"
                )
                continue
            label_names.add(name)

    return body, state, milestone_title, label_names


def normalized_manifest_scope(
    manifest: Any,
    *,
    issue: int,
    errors: list[str],
) -> set[str]:
    """Return a structurally safe child-manifest scope for parity checks."""
    label = f"#{issue} manifest"
    if not isinstance(manifest, dict):
        errors.append(f"{label} root must be a mapping")
        return set()

    scope = manifest.get("scope")
    if not isinstance(scope, dict):
        errors.append(f"{label} scope must be a mapping")
        return set()

    raw_paths = scope.get("allowed_paths")
    if not isinstance(raw_paths, list) or not raw_paths:
        errors.append(f"{label} scope.allowed_paths must be a nonempty list")
        paths: set[str] = set()
    else:
        paths = set()
        for index, path in enumerate(raw_paths):
            if not is_canonical_repo_path(path):
                errors.append(
                    f"{label} scope.allowed_paths[{index}] is not a canonical "
                    f"repo-relative path: {path!r}"
                )
                continue
            paths.add(path)

    raw_patterns = scope.get("allowed_path_patterns", [])
    if not isinstance(raw_patterns, list):
        errors.append(f"{label} scope.allowed_path_patterns must be a list")
        return paths
    for index, pattern in enumerate(raw_patterns):
        if not is_canonical_repo_path(pattern):
            errors.append(
                f"{label} scope.allowed_path_patterns[{index}] is not a canonical "
                f"repo-relative pattern: {pattern!r}"
            )
            continue
        if pattern.endswith("/**"):
            paths.add(pattern[:-2])
    return paths


def normalize_child_manifest(
    manifest: Any,
    *,
    issue: int,
    errors: list[str],
) -> dict[str, Any]:
    """Quarantine every child-manifest collection used downstream."""
    label = f"#{issue} manifest"
    if not isinstance(manifest, dict):
        errors.append(f"{label} root must be a mapping")
        return {}

    normalized = dict(manifest)
    fallback_mode = manifest.get("fallback_evidence_mode")
    if not is_nonempty_string(fallback_mode):
        errors.append(f"{label} fallback_evidence_mode must be a nonempty string")
        normalized["fallback_evidence_mode"] = ""

    sequencing = manifest.get("implementation_sequencing")
    if sequencing is None and issue == 146:
        normalized["implementation_sequencing"] = {}
    elif not isinstance(sequencing, dict):
        errors.append(f"{label} implementation_sequencing must be a mapping")
        normalized["implementation_sequencing"] = {}
    else:
        implementation_ref = sequencing.get("implementation_ref")
        if issue == 147 and not is_nonempty_string(implementation_ref):
            errors.append(
                f"{label} implementation_sequencing.implementation_ref must "
                "be a nonempty string"
            )
            sequencing = {**sequencing, "implementation_ref": ""}
        normalized["implementation_sequencing"] = sequencing

    for field in ("required_dispatch_bundles", "historical_receipt_gaps"):
        raw_rows = manifest.get(field)
        if not isinstance(raw_rows, list):
            errors.append(f"{label} {field} must be a list")
            normalized[field] = []
            continue
        safe_rows: list[dict[str, Any]] = []
        for index, row in enumerate(raw_rows):
            if not isinstance(row, dict):
                errors.append(f"{label} {field}[{index}] must be a mapping")
                continue
            if field == "required_dispatch_bundles":
                required = {"phase", "intent_path", "result_path"}
                missing = sorted(required - row.keys())
                if missing:
                    errors.append(
                        f"{label} {field}[{index}] missing fields: {missing}"
                    )
                    continue
                if row.get("phase") not in {"B.1", "D.2", "D.5"}:
                    errors.append(
                        f"{label} {field}[{index}] has invalid phase: "
                        f"{row.get('phase')!r}"
                    )
                    continue
                if not all(
                    is_canonical_repo_path(row.get(path_field))
                    for path_field in ("intent_path", "result_path")
                ):
                    errors.append(
                        f"{label} {field}[{index}] has invalid bundle paths"
                    )
                    continue
            else:
                required = {
                    "id",
                    "affected_phase",
                    "artifact_paths",
                    "disposition",
                    "strict_p3_certified",
                }
                missing = sorted(required - row.keys())
                if missing:
                    errors.append(
                        f"{label} {field}[{index}] missing fields: {missing}"
                    )
                    continue
                if (
                    not is_nonempty_string(row.get("id"))
                    or row.get("affected_phase") not in {"B.1", "D.2", "D.5"}
                    or not is_string_list(row.get("artifact_paths"))
                    or not all(
                        is_canonical_repo_path(path)
                        for path in row.get("artifact_paths", [])
                    )
                    or not is_nonempty_string(row.get("disposition"))
                    or not isinstance(row.get("strict_p3_certified"), bool)
                ):
                    errors.append(
                        f"{label} {field}[{index}] has invalid typed fields"
                    )
                    continue
            safe_rows.append(row)
        normalized[field] = safe_rows

    raw_gates = manifest.get("gate_prerequisites")
    if not isinstance(raw_gates, list):
        errors.append(f"{label} gate_prerequisites must be a list")
        normalized["gate_prerequisites"] = []
    else:
        gates: list[dict[str, Any]] = []
        for index, gate in enumerate(raw_gates):
            if not isinstance(gate, dict):
                errors.append(
                    f"{label} gate_prerequisites[{index}] must be a mapping"
                )
                continue
            gate_id = gate.get("id")
            verification = gate.get("verification")
            if not is_nonempty_string(gate_id):
                errors.append(
                    f"{label} gate_prerequisites[{index}].id must be a "
                    "nonempty string"
                )
                continue
            if not isinstance(verification, dict):
                errors.append(
                    f"{label} gate_prerequisites[{index}].verification must "
                    "be a mapping"
                )
                continue
            command = verification.get("command")
            if not is_nonempty_string(command):
                errors.append(
                    f"{label} gate_prerequisites[{index}].verification.command "
                    "must be a nonempty string"
                )
                continue
            gates.append(gate)
        normalized["gate_prerequisites"] = gates
    return normalized


def normalize_receipt_inventory(value: Any, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append("#147 receipt inventory root must be a mapping")
        return {"receipts": []}
    receipts = value.get("receipts")
    if not isinstance(receipts, list):
        errors.append("#147 receipt inventory receipts must be a list")
        return {**value, "receipts": []}
    return value


def markdown_table_after_heading(text: str, heading: str) -> list[list[str]]:
    """Return data cells from the first Markdown table after *heading*."""
    lines = text.splitlines()
    try:
        start = lines.index(heading) + 1
    except ValueError:
        return []
    table_lines: list[str] = []
    in_table = False
    for line in lines[start:]:
        if line.startswith("|"):
            in_table = True
            table_lines.append(line)
        elif in_table:
            break
    if len(table_lines) < 2:
        return []
    rows: list[list[str]] = []
    for line in table_lines[2:]:
        rows.append([cell.strip() for cell in line.strip("|").split("|")])
    return rows


def unquote_code(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value.startswith("`") and value.endswith("`"):
        return value[1:-1]
    return value


def live_github_issue(issue: int) -> Any:
    result = subprocess.run(
        [
            "gh",
            "issue",
            "view",
            str(issue),
            "--repo",
            GITHUB_REPOSITORY,
            "--json",
            "number,state,title,labels,milestone,body",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"unable to read live GitHub issue #{issue}: "
            f"{(result.stderr or result.stdout).strip()}"
        )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        # A successful transport with malformed response data is a parity
        # validation error, not an exception-derived validator failure.
        return f"invalid JSON response: {exc}"


def github_checkbox_states(body: str) -> dict[str, bool]:
    states: dict[str, bool] = {}
    for line in body.splitlines():
        match = re.match(r"^\s*-\s*\[([ xX])\]", line)
        if match is None:
            continue
        finding_ids = re.findall(
            r"(?<![A-Za-z0-9-])(?:D[0-9][A-Za-z0-9-]*|R2-[A-Za-z0-9-]+)",
            line,
        )
        for finding_id in finding_ids:
            if finding_id in states:
                raise ValueError(f"duplicate GitHub checklist row for {finding_id}")
            states[finding_id] = match.group(1).lower() == "x"
    return states


def validate(require_external_parity: bool) -> list[str]:
    errors: list[str] = []
    registry = load_yaml(REGISTRY_PATH)
    if not isinstance(registry, dict):
        return ["registry root must be a YAML mapping"]
    for field, expected in (
        ("audit_baseline_commit", AUDIT_BASELINE_COMMIT),
        ("revalidation_commit", REVALIDATION_COMMIT),
        ("integration_commit", INTEGRATION_COMMIT),
    ):
        if registry.get(field) != expected:
            errors.append(
                f"registry {field} mismatch: {registry.get(field)!r} != {expected!r}"
            )
    audit = audit_register()
    raw_findings = registry.get("findings")
    raw_programs = registry.get("programs")
    raw_leases = registry.get("shared_path_leases")
    if (
        not isinstance(raw_findings, list)
        or not isinstance(raw_programs, list)
        or not isinstance(raw_leases, list)
    ):
        return ["registry findings, programs, and shared_path_leases must be lists"]

    leases = normalize_shared_path_leases(raw_leases, errors)
    integration = normalize_shared_tree_integration(
        registry.get("shared_tree_integration"),
        errors,
    )

    raw_github_snapshot = registry.get("github_snapshot")
    if not isinstance(raw_github_snapshot, dict):
        errors.append("registry github_snapshot must be a mapping")
        github_snapshot: dict[str, Any] = {}
    else:
        github_snapshot = raw_github_snapshot
    normalized_snapshot_counts = normalize_snapshot_counts(
        github_snapshot.get("issue_finding_counts"),
        field="issue_finding_counts",
        errors=errors,
    )
    normalized_registry_counts = normalize_snapshot_counts(
        github_snapshot.get("registry_finding_counts"),
        field="registry_finding_counts",
        errors=errors,
    )
    external_drift = normalize_external_drift(
        github_snapshot.get("external_drift"),
        errors,
    )

    findings: list[dict[str, Any]] = []
    for index, row in enumerate(raw_findings):
        if not isinstance(row, dict):
            errors.append(f"finding row {index} is not a mapping")
            continue
        row_label = row.get("id", index)
        row_invalid = False
        missing = sorted(REQUIRED_FINDING_FIELDS - row.keys())
        if missing:
            errors.append(f"{row_label} missing fields: {missing}")
            row_invalid = True

        for field in (
            "id",
            "baseline_commit",
            "root_program",
            "release",
            "base_sha",
        ):
            if field in row and not is_nonempty_string(row.get(field)):
                errors.append(f"{row_label} has invalid {field}: {row.get(field)!r}")
                row_invalid = True
        for field in ("baseline_commit", "base_sha"):
            if field in row and is_nonempty_string(row.get(field)) and not is_commit_ref(
                row.get(field)
            ):
                errors.append(
                    f"{row_label} has invalid commit reference in {field}: "
                    f"{row.get(field)!r}"
                )
                row_invalid = True
        if "origin" in row:
            origin = row.get("origin")
            if not is_nonempty_string(origin) or origin not in FINDING_ORIGINS:
                errors.append(f"{row_label} has invalid origin: {origin!r}")
                row_invalid = True
        if "severity" in row:
            severity = row.get("severity")
            if not is_nonempty_string(severity) or severity not in FINDING_SEVERITIES:
                errors.append(f"{row_label} has invalid severity: {severity!r}")
                row_invalid = True
        if "status" in row:
            status = row.get("status")
            if not is_nonempty_string(status) or status not in FINDING_STATUSES:
                errors.append(f"{row_label} has invalid status: {status!r}")
                row_invalid = True
        if "lifecycle_state" in row:
            lifecycle_state = row.get("lifecycle_state")
            if (
                not is_nonempty_string(lifecycle_state)
                or lifecycle_state not in FINDING_LIFECYCLE_STATES
            ):
                errors.append(
                    f"{row_label} has invalid lifecycle_state: "
                    f"{lifecycle_state!r}"
                )
                row_invalid = True
        if "issue" in row and not is_issue_number(row.get("issue"), include_epic=True):
            errors.append(
                f"{row_label} has invalid issue assignment {row.get('issue')!r}"
            )
            row_invalid = True
        if "fix_commit" in row and row.get("fix_commit") is not None and not is_nonempty_string(
            row.get("fix_commit")
        ):
            errors.append(
                f"{row_label} has invalid fix_commit: {row.get('fix_commit')!r}"
            )
            row_invalid = True
        elif row.get("fix_commit") is not None and not is_commit_ref(
            row.get("fix_commit")
        ):
            errors.append(
                f"{row_label} has invalid commit reference in fix_commit: "
                f"{row.get('fix_commit')!r}"
            )
            row_invalid = True

        verification_evidence = row.get("verification_evidence")
        if "verification_evidence" in row and not is_string_list(verification_evidence):
            errors.append(
                f"{row_label} has invalid verification_evidence: "
                f"{verification_evidence!r}"
            )
            row_invalid = True
        elif is_string_list(verification_evidence):
            for evidence_path in verification_evidence:
                if not is_canonical_repo_path(evidence_path):
                    errors.append(
                        f"{row_label} evidence path is not a canonical "
                        f"repo-relative path: {evidence_path!r}"
                    )
                    row_invalid = True
                    continue
                if not (ROOT / evidence_path).exists():
                    errors.append(
                        f"{row_label} evidence path is missing: {evidence_path!r}"
                    )
        if "allowed_paths" in row and not is_string_list(row.get("allowed_paths")):
            errors.append(
                f"{row_label} has invalid allowed_paths: {row.get('allowed_paths')!r}"
            )
            row_invalid = True
        elif is_string_list(row.get("allowed_paths")):
            invalid_paths = [
                path
                for path in row["allowed_paths"]
                if not is_canonical_repo_path(path)
            ]
            if invalid_paths:
                errors.append(
                    f"{row_label} allowed_paths must be canonical repo-relative "
                    f"paths: {invalid_paths!r}"
                )
                row_invalid = True

        if row_invalid:
            # Quarantine structurally invalid rows before counters, path
            # calculations, or local/external parity logic consume them.
            continue
        findings.append(row)

    ids = [row["id"] for row in findings]
    duplicate_ids = sorted(key for key, count in Counter(ids).items() if count > 1)
    if duplicate_ids:
        errors.append(f"duplicate registry IDs: {duplicate_ids}")

    programs: list[dict[str, Any]] = []
    program_issues: list[int] = []
    for index, program in enumerate(raw_programs):
        if not isinstance(program, dict):
            errors.append(f"program row {index} is not a mapping")
            continue
        program_label = program.get("id", index)
        program_invalid = False
        missing = sorted(REQUIRED_PROGRAM_FIELDS - program.keys())
        if missing:
            errors.append(f"program {program_label} missing fields: {missing}")
            program_invalid = True

        for field in (
            "id",
            "root_program",
            "implementation_ref",
            "base_sha",
            "default_release",
            "github_state",
        ):
            if field in program and not is_nonempty_string(program.get(field)):
                errors.append(
                    f"program {program_label} has invalid {field}: {program.get(field)!r}"
                )
                program_invalid = True
        for field in ("implementation_ref", "base_sha"):
            if field in program and is_nonempty_string(
                program.get(field)
            ) and not is_commit_ref(program.get(field)):
                errors.append(
                    f"program {program_label} has invalid commit reference in "
                    f"{field}: {program.get(field)!r}"
                )
                program_invalid = True
        if "lifecycle_state" in program:
            lifecycle_state = program.get("lifecycle_state")
            if (
                not is_nonempty_string(lifecycle_state)
                or lifecycle_state not in PROGRAM_LIFECYCLE_STATES
            ):
                errors.append(
                    f"program {program_label} has invalid lifecycle_state: "
                    f"{lifecycle_state!r}"
                )
                program_invalid = True
        if "lease_state" in program:
            lease_state = program.get("lease_state")
            if (
                not is_nonempty_string(lease_state)
                or lease_state not in PROGRAM_LEASE_STATES
            ):
                errors.append(
                    f"program {program_label} has invalid lease_state: "
                    f"{lease_state!r}"
                )
                program_invalid = True
        issue = program.get("issue")
        if "issue" in program and not is_issue_number(issue, include_epic=False):
            errors.append(f"program {program_label} has invalid issue {issue!r}")
            program_invalid = True
        if "max_severity" in program:
            max_severity = program.get("max_severity")
            if (
                not is_nonempty_string(max_severity)
                or max_severity not in FINDING_SEVERITIES
            ):
                errors.append(
                    f"program {program_label} has invalid max_severity: "
                    f"{max_severity!r}"
                )
                program_invalid = True
        if "github_milestone" in program:
            github_milestone = program.get("github_milestone")
            if (
                not isinstance(github_milestone, int)
                or isinstance(github_milestone, bool)
                or github_milestone not in {1, 2, 3}
            ):
                errors.append(
                    f"program {program_label} has invalid github_milestone: "
                    f"{github_milestone!r}"
                )
                program_invalid = True
        if "allowed_paths" in program and not is_string_list(program.get("allowed_paths")):
            errors.append(
                f"program {program_label} has invalid allowed_paths: "
                f"{program.get('allowed_paths')!r}"
            )
            program_invalid = True
        elif is_string_list(program.get("allowed_paths")):
            invalid_paths = [
                path
                for path in program["allowed_paths"]
                if not is_canonical_repo_path(path)
            ]
            if invalid_paths:
                errors.append(
                    f"program {program_label} allowed_paths must be canonical "
                    f"repo-relative paths: {invalid_paths!r}"
                )
                program_invalid = True

        if program_invalid:
            # Invalid programs must not reach path overlap checks, hard-coded
            # child-manifest parity, or GitHub metadata comparisons.
            continue
        programs.append(program)
        program_issues.append(issue)
    duplicate_program_issues = sorted(
        issue for issue, count in Counter(program_issues).items() if count > 1
    )
    if duplicate_program_issues:
        errors.append(f"duplicate program issues: {duplicate_program_issues}")
    observed_program_issues = set(program_issues)
    if observed_program_issues != REQUIRED_PROGRAM_ISSUES:
        errors.append(
            "required program membership mismatch: "
            f"missing={sorted(REQUIRED_PROGRAM_ISSUES - observed_program_issues)}, "
            f"extra={sorted(observed_program_issues - REQUIRED_PROGRAM_ISSUES)}"
        )

    original = {
        row.get("id"): row
        for row in findings
        if row.get("origin") == "fable_audit" and isinstance(row.get("id"), str)
    }
    r2 = {
        row.get("id"): row
        for row in findings
        if row.get("origin") == "codex_revalidation" and isinstance(row.get("id"), str)
    }
    if set(original) != set(audit):
        errors.append(
            "original register mismatch: "
            f"missing={sorted(set(audit) - set(original))}, extra={sorted(set(original) - set(audit))}"
        )
    for finding_id in sorted(set(original) & set(audit)):
        if original[finding_id].get("severity") != audit[finding_id]:
            errors.append(
                f"severity mismatch for {finding_id}: registry={original[finding_id].get('severity')} "
                f"report={audit[finding_id]}"
            )
    original_counts = Counter(row.get("severity") for row in original.values())
    if original_counts != Counter({"P0": 1, "P1": 27, "P2": 63}):
        errors.append(f"original severity totals are wrong: {dict(original_counts)}")
    if set(r2) != EXPECTED_R2_IDS:
        errors.append(
            f"R2 register mismatch: missing={sorted(EXPECTED_R2_IDS - set(r2))}, "
            f"extra={sorted(set(r2) - EXPECTED_R2_IDS)}"
        )
    if "D6a-test-gaps-3" in original:
        errors.append("phantom roadmap ID D6a-test-gaps-3 must not enter the registry")

    fixed_original = {
        row.get("id")
        for row in original.values()
        if row.get("status") == "code_fixed"
    }
    if fixed_original != {"D4b-trust-1", "D4b-trust-2"}:
        errors.append(f"unexpected committed code-fixed original set: {sorted(fixed_original)}")
    serializer_row = original.get("D2b-roundtrip-3", {})
    if (
        serializer_row.get("status") != "code_fixed_evidence_pending"
        or serializer_row.get("fix_commit")
        != "b6f89d77e7fb684b8bd9a181a24c773d5777397a"
    ):
        errors.append(
            "D2b-roundtrip-3 must be committed at I0 and remain "
            "code_fixed_evidence_pending"
        )
    implemented_original = {
        row.get("id")
        for row in original.values()
        if row.get("status") == "implemented_committed_verification_pending"
    }
    if implemented_original != EXPECTED_IMPLEMENTED_COMMITTED_ORIGINAL_IDS:
        errors.append(
            "implemented-committed original set mismatch: "
            f"missing={sorted(EXPECTED_IMPLEMENTED_COMMITTED_ORIGINAL_IDS - implemented_original)}, "
            f"extra={sorted(implemented_original - EXPECTED_IMPLEMENTED_COMMITTED_ORIGINAL_IDS)}"
        )
    partial_original = {
        row.get("id")
        for row in original.values()
        if row.get("status") == "partial_implementation_committed_verification_pending"
    }
    if partial_original != EXPECTED_PARTIAL_COMMITTED_ORIGINAL_IDS:
        errors.append(
            "partial-committed original set mismatch: "
            f"missing={sorted(EXPECTED_PARTIAL_COMMITTED_ORIGINAL_IDS - partial_original)}, "
            f"extra={sorted(partial_original - EXPECTED_PARTIAL_COMMITTED_ORIGINAL_IDS)}"
        )
    expected_status_counts = Counter(
        {
            "confirmed_open": 41,
            "implemented_committed_verification_pending": 40,
            "partial_implementation_committed_verification_pending": 7,
            "code_fixed": 2,
            "code_fixed_evidence_pending": 1,
        }
    )
    status_counts = Counter(row.get("status") for row in original.values())
    if status_counts != expected_status_counts:
        errors.append(
            f"original committed-snapshot status totals are wrong: {dict(status_counts)}"
        )
    for finding_id in sorted(implemented_original | partial_original):
        row = original[finding_id]
        if row.get("fix_commit") != "b6f89d77e7fb684b8bd9a181a24c773d5777397a":
            errors.append(f"{finding_id} must bind its fix commit to I0")
        expected_lifecycle = (
            "implementation_committed_lifecycle_pending"
            if finding_id in implemented_original
            else "partial_implementation_committed_lifecycle_pending"
        )
        if row.get("lifecycle_state") != expected_lifecycle:
            errors.append(
                f"{finding_id} lifecycle mismatch: {row.get('lifecycle_state')!r} "
                f"!= {expected_lifecycle!r}"
            )
    for finding_id, row in r2.items():
        is_control_plane = finding_id == "R2-control-plane-parity-1"
        expected_status = (
            "implemented_committed_parity_verified"
            if is_control_plane
            else "implemented_committed_verification_pending"
        )
        if row.get("status") != expected_status:
            errors.append(
                f"{finding_id} status mismatch: {row.get('status')!r} != {expected_status!r}"
            )
        expected_fix_commit = (
            CONTROL_PLANE_FIX_COMMIT if is_control_plane else INTEGRATION_COMMIT
        )
        if row.get("fix_commit") != expected_fix_commit:
            checkpoint = "Phase C close I1" if is_control_plane else "I0"
            errors.append(
                f"{finding_id} must bind its fix commit to {checkpoint}"
            )
        expected_lifecycle = (
            "parity_verified_lifecycle_pending"
            if is_control_plane
            else "implementation_committed_lifecycle_pending"
        )
        if row.get("lifecycle_state") != expected_lifecycle:
            errors.append(
                f"{finding_id} lifecycle mismatch: {row.get('lifecycle_state')!r} "
                f"!= {expected_lifecycle!r}"
            )

    calculated_counts = Counter(row.get("issue") for row in original.values())
    if dict(sorted(calculated_counts.items())) != dict(sorted(normalized_snapshot_counts.items())):
        errors.append(
            "GitHub issue finding-count snapshot mismatch: "
            f"registry={dict(sorted(calculated_counts.items()))}, snapshot={normalized_snapshot_counts}"
        )
    calculated_registry_counts = Counter(row.get("issue") for row in findings)
    if dict(sorted(calculated_registry_counts.items())) != dict(
        sorted(normalized_registry_counts.items())
    ):
        errors.append(
            "GitHub all-finding count snapshot mismatch: "
            f"registry={dict(sorted(calculated_registry_counts.items()))}, "
            f"snapshot={normalized_registry_counts}"
        )
    if sum(calculated_registry_counts.values()) != len(findings) or len(findings) != 100:
        errors.append(
            "registry count invariant failed: "
            f"mapped={sum(calculated_registry_counts.values())}, rows={len(findings)}, expected=100"
        )

    severity_rank = {"P0": 0, "P1": 1, "P2": 2}
    by_issue: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in original.values():
        issue = row.get("issue")
        if isinstance(issue, int):
            by_issue[issue].append(row)
    program_by_issue = {
        program.get("issue"): program
        for program in programs
        if isinstance(program.get("issue"), int)
    }
    finding_owner_by_issue = {
        **program_by_issue,
        CONTROL_PLANE_ISSUE: CONTROL_PLANE_OWNER,
    }
    for issue, program in sorted(program_by_issue.items()):
        expected_base = (
            DOCTOR_BASE_COMMIT if issue == 147 else REVALIDATION_COMMIT
        )
        expected_implementation = (
            DOCTOR_FIX_COMMIT if issue == 147 else INTEGRATION_COMMIT
        )
        if program.get("root_program") != program.get("id"):
            errors.append(
                f"program #{issue} root_program must equal its id: "
                f"{program.get('root_program')!r} != {program.get('id')!r}"
            )
        if program.get("base_sha") != expected_base:
            errors.append(
                f"program #{issue} base_sha mismatch: "
                f"{program.get('base_sha')!r} != {expected_base!r}"
            )
        if program.get("implementation_ref") != expected_implementation:
            errors.append(
                f"program #{issue} implementation_ref mismatch: "
                f"{program.get('implementation_ref')!r} != "
                f"{expected_implementation!r}"
            )
        expected_release = EXPECTED_DEFAULT_RELEASES.get(issue)
        if program.get("default_release") != expected_release:
            errors.append(
                f"program #{issue} default_release mismatch: "
                f"{program.get('default_release')!r} != {expected_release!r}"
            )

    release_counts = Counter(
        (row.get("issue"), row.get("release")) for row in findings
    )
    if release_counts != EXPECTED_RELEASE_COUNTS:
        errors.append(
            "finding release distribution mismatch: "
            f"observed={dict(sorted(release_counts.items()))}, "
            f"expected={dict(sorted(EXPECTED_RELEASE_COUNTS.items()))}"
        )

    commit_refs: set[str] = {
        AUDIT_BASELINE_COMMIT,
        REVALIDATION_COMMIT,
        INTEGRATION_COMMIT,
        DOCTOR_BASE_COMMIT,
        DOCTOR_FIX_COMMIT,
    }
    for row in findings:
        issue = row.get("issue")
        finding_id = row.get("id", "<missing-id>")
        if finding_id == CONTROL_PLANE_FINDING_ID and issue != CONTROL_PLANE_ISSUE:
            errors.append(
                f"{CONTROL_PLANE_FINDING_ID} must be assigned to issue "
                f"#{CONTROL_PLANE_ISSUE}, not #{issue}"
            )
        if issue == CONTROL_PLANE_ISSUE and finding_id != CONTROL_PLANE_FINDING_ID:
            errors.append(
                f"{finding_id} cannot be assigned to reserved issue "
                f"#{CONTROL_PLANE_ISSUE}"
            )
        owner = finding_owner_by_issue.get(issue)
        expected_baseline = (
            AUDIT_BASELINE_COMMIT
            if row.get("origin") == "fable_audit"
            else REVALIDATION_COMMIT
        )
        if row.get("baseline_commit") != expected_baseline:
            errors.append(
                f"{finding_id} baseline_commit mismatch: "
                f"{row.get('baseline_commit')!r} != {expected_baseline!r}"
            )
        expected_base = owner.get("base_sha") if owner is not None else REVALIDATION_COMMIT
        if row.get("base_sha") != expected_base:
            errors.append(
                f"{finding_id} base_sha mismatch: "
                f"{row.get('base_sha')!r} != {expected_base!r}"
            )
        if row.get("status") == "confirmed_open" and row.get("fix_commit") is not None:
            errors.append(f"{finding_id} confirmed_open row must have null fix_commit")
        for commit_field in ("baseline_commit", "base_sha", "fix_commit"):
            commit_value = row.get(commit_field)
            if isinstance(commit_value, str) and is_commit_ref(commit_value):
                commit_refs.add(commit_value)
        if owner is None:
            errors.append(f"{finding_id} has no owning program row")
            continue
        if row.get("root_program") != owner.get("root_program"):
            errors.append(
                f"{finding_id} root_program mismatch for issue #{issue}: "
                f"finding={row.get('root_program')!r}, "
                f"owner={owner.get('root_program')!r}"
            )
        uncovered = [
            path
            for path in row.get("allowed_paths", [])
            if not any(
                path_scope_covers(owner_path, path)
                for owner_path in owner.get("allowed_paths", [])
            )
        ]
        if uncovered:
            owner_label = (
                f"owner #{issue}"
                if issue == CONTROL_PLANE_ISSUE
                else f"program #{issue}"
            )
            errors.append(
                f"{finding_id} finding scope exceeds {owner_label}: {uncovered}"
            )
    for program in programs:
        for commit_field in ("base_sha", "implementation_ref"):
            commit_value = program.get(commit_field)
            if isinstance(commit_value, str) and is_commit_ref(commit_value):
                commit_refs.add(commit_value)
    for commit_ref in sorted(commit_refs):
        if not commit_exists(commit_ref):
            errors.append(f"registry references missing commit: {commit_ref}")
    expected_milestones = {
        146: 1,
        147: 1,
        148: 2,
        149: 2,
        150: 2,
        151: 2,
        152: 2,
        153: 2,
        154: 3,
        155: 3,
        156: 2,
        157: 3,
    }
    for issue, rows in sorted(by_issue.items()):
        severities = [row.get("severity") for row in rows]
        unknown_severities = sorted(
            {severity for severity in severities if severity not in severity_rank},
            key=repr,
        )
        if unknown_severities:
            errors.append(
                f"issue #{issue} has unknown severities: {unknown_severities}"
            )
            continue
        maximum = min(severities, key=severity_rank.__getitem__)
        if program_by_issue.get(issue, {}).get("max_severity") != maximum:
            errors.append(
                f"issue #{issue} max severity mismatch: registry rows={maximum}, "
                f"program={program_by_issue.get(issue, {}).get('max_severity')}"
            )
    if program_by_issue.get(149, {}).get("max_severity") != "P1":
        errors.append("issue #149 must be classified P1-containing")
    for issue, milestone in expected_milestones.items():
        program = program_by_issue.get(issue, {})
        if program.get("github_state") != "open":
            errors.append(f"issue #{issue} must be open in the synchronized GitHub snapshot")
        if program.get("github_milestone") != milestone:
            errors.append(
                f"issue #{issue} milestone mismatch: {program.get('github_milestone')} != {milestone}"
            )

    expected_integration_issues = {
        program.get("issue")
        for program in programs
        if program.get("lease_state") == "implementation_committed_integration_pending"
        and isinstance(program.get("issue"), int)
    } | {146}
    if integration is not None:
        observed_integration_issues = set(integration["affected_issues"])
        if integration["status"] != "unproven_rebaseline_integration":
            errors.append("shared-tree integration must remain explicitly unproven")
        if integration["release_blocking"] is not True:
            errors.append("unproven shared-tree integration must remain release-blocking")
        if observed_integration_issues != expected_integration_issues:
            errors.append(
                "shared-tree integration issue set mismatch: "
                f"expected={sorted(expected_integration_issues)}, "
                f"observed={sorted(observed_integration_issues)}"
            )

    child_manifests: dict[int, dict[str, Any]] = {}
    for issue, manifest_path in (
        (146, SERIALIZER_MANIFEST_PATH),
        (147, DOCTOR_MANIFEST_PATH),
    ):
        program = program_by_issue.get(issue)
        if program is None:
            errors.append(
                f"program #{issue} is unavailable for child-manifest scope parity"
            )
            continue
        raw_manifest = load_yaml(manifest_path)
        manifest = normalize_child_manifest(
            raw_manifest,
            issue=issue,
            errors=errors,
        )
        manifest_scope = normalized_manifest_scope(
            manifest,
            issue=issue,
            errors=errors,
        )
        child_manifests[issue] = manifest
        registry_scope = set(program.get("allowed_paths", []))
        if registry_scope != manifest_scope:
            errors.append(
                f"program #{issue} scope/manifest mismatch: "
                f"missing={sorted(manifest_scope - registry_scope)}, "
                f"extra={sorted(registry_scope - manifest_scope)}"
            )

    lease_rows: list[tuple[str, set[int]]] = []
    for lease in leases:
        path = lease["path"]
        issue_set = set(lease["programs"])
        order = lease["order"]
        if not path or len(issue_set) < 2:
            errors.append(f"invalid shared-path lease: {lease}")
            continue
        missing_programs = issue_set - set(program_by_issue)
        if missing_programs:
            errors.append(
                f"lease {path} references missing programs: {sorted(missing_programs)}"
            )
            continue
        if set(order) != issue_set or len(order) != len(issue_set):
            errors.append(f"lease order does not enumerate each program once for {path}")
        lease_rows.append((path, issue_set))

    for left_index, left in enumerate(programs):
        for right in programs[left_index + 1 :]:
            for left_path in left.get("allowed_paths", []):
                for right_path in right.get("allowed_paths", []):
                    overlap = overlapping_path(left_path, right_path)
                    if overlap is None:
                        continue
                    left_issue = left.get("issue")
                    right_issue = right.get("issue")
                    pair = {left_issue, right_issue}
                    matching_leases = [
                        path
                        for path, issues in lease_rows
                        if pair <= issues and lease_covers(path, overlap)
                    ]
                    if not matching_leases:
                        errors.append(
                            f"unleased overlap {overlap}: #{left_issue} and #{right_issue}"
                        )
                    elif len(matching_leases) > 1:
                        errors.append(
                            f"multiply leased overlap {overlap}: #{left_issue} and "
                            f"#{right_issue} via {matching_leases}"
                        )

    for lease_path, issues in lease_rows:
        participants: set[int] = set()
        issue_list = sorted(issues)
        for left_index, left_issue in enumerate(issue_list):
            left = program_by_issue.get(left_issue, {})
            for right_issue in issue_list[left_index + 1 :]:
                right = program_by_issue.get(right_issue, {})
                if any(
                    (overlap := overlapping_path(left_path, right_path)) is not None
                    and lease_covers(lease_path, overlap)
                    for left_path in left.get("allowed_paths", [])
                    for right_path in right.get("allowed_paths", [])
                ):
                    participants.update({left_issue, right_issue})
        if not participants:
            errors.append(f"lease {lease_path} does not correspond to an actual overlap")
        nonparticipants = issues - participants
        if nonparticipants:
            errors.append(
                f"lease {lease_path} lists programs without an actual overlap: "
                f"{sorted(nonparticipants)}"
            )

    active_programs = [program for program in programs if program.get("lease_state") == "active"]
    for left_index, left in enumerate(active_programs):
        for right in active_programs[left_index + 1 :]:
            for left_path in left.get("allowed_paths", []):
                for right_path in right.get("allowed_paths", []):
                    overlap = overlapping_path(left_path, right_path)
                    if overlap is not None:
                        errors.append(
                            f"simultaneously active leases overlap at {overlap}: "
                            f"#{left.get('issue')} and #{right.get('issue')}"
                        )

    ledger_text = LEDGER_PATH.read_text(encoding="utf-8")
    audit_text = AUDIT_PATH.read_text(encoding="utf-8")
    revalidation_text = REVALIDATION_PATH.read_text(encoding="utf-8")
    if "2026-07-10-codex-audit-revalidation.md" not in audit_text:
        errors.append("historical audit is missing the revalidation pointer")
    for marker in (
        "40 other original findings",
        "partial implementations for seven",
        "41 confirmed-open rows",
    ):
        if marker not in revalidation_text:
            errors.append(f"revalidation addendum is missing status summary marker: {marker!r}")
    o4_rows = markdown_table_after_heading(
        ledger_text,
        "## O4 — Cross-deliverable verification ledger",
    )
    rendered_programs: dict[int, list[str]] = {}
    for row_index, cells in enumerate(o4_rows):
        if len(cells) != 9:
            errors.append(f"O4 row {row_index} must have exactly nine cells")
            continue
        issue_match = re.fullmatch(r"#(\d+)", cells[1])
        if issue_match is None:
            errors.append(f"O4 row {row_index} has invalid issue cell: {cells[1]!r}")
            continue
        issue = int(issue_match.group(1))
        if issue in rendered_programs:
            errors.append(f"O4 has duplicate program row for #{issue}")
            continue
        rendered_programs[issue] = cells
    if set(rendered_programs) != set(program_by_issue):
        errors.append(
            "O4 program membership mismatch: "
            f"missing={sorted(set(program_by_issue) - set(rendered_programs))}, "
            f"extra={sorted(set(rendered_programs) - set(program_by_issue))}"
        )
    for issue, program in sorted(program_by_issue.items()):
        cells = rendered_programs.get(issue)
        if cells is None:
            continue
        finding_state_counts = Counter(
            row.get("status") for row in findings if row.get("issue") == issue
        )
        finding_states = "; ".join(
            f"{status}={count}"
            for status, count in sorted(finding_state_counts.items())
        )
        expected_cells = (
            program.get("id"),
            program.get("default_release"),
            program.get("max_severity"),
            program.get("lifecycle_state"),
            f"{program.get('github_state')}; M{program.get('github_milestone')}",
            "base "
            f"`{program.get('base_sha')}`; implementation "
            f"`{program.get('implementation_ref')}`",
            finding_states,
        )
        observed_cells = (
            unquote_code(cells[0]),
            cells[2],
            cells[3],
            unquote_code(cells[4]),
            cells[5],
            cells[6],
            cells[7],
        )
        if observed_cells != expected_cells:
            errors.append(
                f"O4 row #{issue} differs from registry authority: "
                f"observed={observed_cells!r}, expected={expected_cells!r}"
            )

    o5_rows = markdown_table_after_heading(ledger_text, "### Shared-path leases")
    rendered_leases: dict[str, list[str]] = {}
    for row_index, cells in enumerate(o5_rows):
        if len(cells) != 4:
            errors.append(f"O5 row {row_index} must have exactly four cells")
            continue
        path = unquote_code(cells[0])
        if path in rendered_leases:
            errors.append(f"O5 has duplicate lease row for {path!r}")
            continue
        rendered_leases[path] = cells
    lease_by_path = {lease["path"]: lease for lease in leases}
    if set(rendered_leases) != set(lease_by_path):
        errors.append(
            "O5 lease membership mismatch: "
            f"missing={sorted(set(lease_by_path) - set(rendered_leases))}, "
            f"extra={sorted(set(rendered_leases) - set(lease_by_path))}"
        )
    for path, lease in sorted(lease_by_path.items()):
        cells = rendered_leases.get(path)
        if cells is None:
            continue
        observed_programs = [int(item) for item in re.findall(r"#(\d+)", cells[1])]
        observed_order = [int(item) for item in re.findall(r"#(\d+)", cells[2])]
        expected_policy = lease.get("policy", "ordered")
        if (
            observed_programs != lease["programs"]
            or observed_order != lease["order"]
            or cells[3] != expected_policy
        ):
            errors.append(
                f"O5 lease {path} differs from registry authority: "
                f"programs={observed_programs!r}, order={observed_order!r}, "
                f"policy={cells[3]!r}"
            )
    if not any("#149" in line and "P1-containing" in line for line in ledger_text.splitlines()):
        errors.append("O4 must label #149 P1-containing")

    doctor_manifest = child_manifests.get(147, {})
    if doctor_manifest.get("fallback_evidence_mode") != "strict_p3":
        errors.append("#147 manifest must require fresh strict-P3 evidence")
    sequencing = doctor_manifest.get("implementation_sequencing", {})
    if sequencing.get("implementation_ref") != "03c36e6ac999d2c411c13252baa2e8fcff60e6ed":
        errors.append("#147 manifest is not pinned to the exact-argv implementation")
    if len(doctor_manifest.get("required_dispatch_bundles", [])) != 9:
        errors.append("#147 manifest must declare nine fresh B.1/D.2/D.5 dispatch bundles")
    if len(doctor_manifest.get("historical_receipt_gaps", [])) != 3:
        errors.append("#147 manifest must mark B.1/D.2/D.5 historical prose replay-required")
    inventory = normalize_receipt_inventory(
        load_yaml(DOCTOR_RECEIPT_INVENTORY_PATH),
        errors,
    )
    if inventory.get("receipts") != []:
        errors.append("#147 receipt inventory must stay empty until fresh wrapper dispatch")
    for relative in (
        "docs/specs/project-ontos-audit-doctor-rce-spec.md",
        "docs/reviews/project-ontos-audit-doctor-rce/final-approval.md",
        "docs/retros/project-ontos-audit-doctor-rce-retro.md",
        "docs/trackers/project-ontos-audit-doctor-rce.md",
    ):
        text = (ROOT / relative).read_text(encoding="utf-8")
        if "code_fixed_evidence_pending" not in text:
            errors.append(f"#147 lifecycle artifact lacks reopened status: {relative}")
    doctor_spec = (
        ROOT / "docs/specs/project-ontos-audit-doctor-rce-spec.md"
    ).read_text(encoding="utf-8")
    if "is_ontos_managed_serve_argv" not in doctor_spec or "five-case executable contract" not in doctor_spec:
        errors.append("#147 spec does not describe the exact-argv five-test contract")

    serializer_manifest = child_manifests.get(146, {})
    if serializer_manifest.get("fallback_evidence_mode") != "provider_limited_fallback":
        errors.append("#146 manifest must declare its authorized provider-limited mode")
    raw_serializer_scope = serializer_manifest.get("scope", {})
    serializer_scope = (
        raw_serializer_scope if isinstance(raw_serializer_scope, dict) else {}
    )
    if not serializer_scope.get("allowed_path_patterns"):
        errors.append("#146 manifest must activate the framework changed-path scope verifier")
    serializer_gates = {gate.get("id"): gate for gate in serializer_manifest.get("gate_prerequisites", [])}
    scope_command = serializer_gates.get("G-scope-1", {}).get("verification", {}).get("command", "")
    branch_command = serializer_gates.get("G-branch-1", {}).get("verification", {}).get("command", "")
    if "verify-changed-path-scope.sh" not in scope_command or "bf91b42f4eb5ba2ed6e0e3ea5e76d22ec6d7ec95" not in scope_command:
        errors.append("#146 scope gate must cover the registry base SHA")
    if "git branch --show-current" in branch_command or "merge-base --is-ancestor" not in branch_command:
        errors.append("#146 branch gate must use base ancestry, not a literal branch name")

    if require_external_parity:
        if github_snapshot.get("epic_release_line_synced") is not True:
            errors.append("external parity drift: epic #158 release line is not synchronized")
        if github_snapshot.get("r2_checklists_synced") is not True:
            errors.append("external parity drift: R2 checklist rows are not synchronized")
        if github_snapshot.get("original_checklist_policy") != "merged_and_verified_only":
            errors.append("external parity drift: original checklist completion policy is not recorded")
        if github_snapshot.get("uncertified_original_checklists_remain_unchecked") is not True:
            errors.append(
                "external parity drift: uncertified original rows must remain unchecked "
                "until merged and verified"
            )
        unresolved = [
            item for item in external_drift if item.get("status") != "resolved"
        ]
        for item in unresolved:
            errors.append(
                f"external parity drift: issue #{item.get('issue')} {item.get('field')} "
                f"observed={item.get('observed')} expected={item.get('expected')}"
            )
        for item in external_drift:
            if item.get("status") == "resolved" and item.get("observed") != item.get("expected"):
                errors.append(
                    f"external parity drift marked resolved with unequal values: "
                    f"issue #{item.get('issue')} {item.get('field')}"
                )

        rows_by_issue: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for row in findings:
            issue = row.get("issue")
            if isinstance(issue, int):
                rows_by_issue[issue].append(row)
        milestone_markers = {
            1: "Audit Release N",
            2: "Audit Release N+1",
            3: "Audit Release N+2",
        }
        live_epic_body = ""
        for issue in range(146, 159):
            live = live_github_issue(issue)
            body, live_state, milestone_title, label_names = (
                normalize_live_issue_payload(issue, live, errors)
            )
            program = program_by_issue.get(issue)
            expected_rows = rows_by_issue.get(issue, [])
            expected_ids = {
                row.get("id")
                for row in expected_rows
                if isinstance(row.get("id"), str)
            }
            if issue == 158:
                # The epic deliberately repeats the complete R2 assignment
                # checklist; child issues remain the canonical owners.
                expected_ids = EXPECTED_R2_IDS
                live_epic_body = body

            if issue == 158 and not expected_ids <= set(body.split()):
                # Epic punctuation/backticks make token equality inconvenient;
                # require every epic-owned ID literally in the body.
                missing = sorted(item for item in expected_ids if item not in body)
                if missing:
                    errors.append(f"live GitHub epic #158 is missing rows: {missing}")

            try:
                checkbox_states = github_checkbox_states(body)
            except ValueError as exc:
                errors.append(
                    f"live GitHub issue #{issue} has invalid checklist body: {exc}"
                )
                checkbox_states = {}
            if set(checkbox_states) != expected_ids:
                errors.append(
                    f"live GitHub issue #{issue} finding checklist mismatch: "
                    f"missing={sorted(expected_ids - set(checkbox_states))}, "
                    f"extra={sorted(set(checkbox_states) - expected_ids)}"
                )
            missing_checkboxes = expected_ids - set(checkbox_states)
            if missing_checkboxes:
                errors.append(
                    f"live GitHub issue #{issue} is missing checklist rows: "
                    f"{sorted(missing_checkboxes)}"
                )
            for row in expected_rows:
                finding_id = row.get("id")
                if not isinstance(finding_id, str) or finding_id not in checkbox_states:
                    continue
                expected_checked = row.get("status") == "code_fixed"
                if checkbox_states[finding_id] != expected_checked:
                    errors.append(
                        f"live GitHub checklist status mismatch for {finding_id}: "
                        f"checked={checkbox_states[finding_id]} expected={expected_checked}"
                    )

            expected_state = (program or {}).get("github_state", "open").upper()
            if live_state != expected_state:
                errors.append(
                    f"live GitHub issue #{issue} state mismatch: "
                    f"{live_state!r} != {expected_state!r}"
                )
            expected_milestone = (program or {}).get("github_milestone", 1)
            marker = milestone_markers[expected_milestone]
            if not milestone_title.startswith(marker):
                errors.append(
                    f"live GitHub issue #{issue} milestone mismatch: "
                    f"{milestone_title!r} does not start with {marker!r}"
                )
            if program is not None:
                expected_label_prefix = program.get("max_severity")
                if not any(name.startswith(expected_label_prefix) for name in label_names):
                    errors.append(
                        f"live GitHub issue #{issue} lacks {expected_label_prefix} severity label"
                    )
        if "v4.7.1" not in live_epic_body or "v4.9.0" not in live_epic_body:
            errors.append("live GitHub epic #158 lacks the revised three-release line")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--require-external-parity",
        action="store_true",
        help="query live GitHub issues and fail on state/milestone/label/checklist drift",
    )
    args = parser.parse_args()
    try:
        errors = validate(args.require_external_parity)
    except ControlPlaneInputError as exc:
        print("audit-registry: FAILED", file=sys.stderr)
        print(f"- {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # validation should fail closed with useful context
        print(f"audit-registry: ERROR: {exc}", file=sys.stderr)
        return 2
    if errors:
        print("audit-registry: FAILED", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    mode = "local+external" if args.require_external_parity else "local"
    print("audit-registry: PASS")
    print(f"mode: {mode}")
    print("original findings: 91 (P0=1, P1=27, P2=63)")
    print(
        "original status: committed_fixed=2, code_fixed_evidence_pending=1, "
        "implemented_committed_pending=40, partial_committed_pending=7, "
        "confirmed_open=41"
    )
    print("revalidation findings: 9")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
