#!/usr/bin/env python3
"""Validate the audit registry and its local rendered control-plane artifacts."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
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
GITHUB_REPOSITORY = "ohjonathan/Project-Ontos"

REQUIRED_FINDING_FIELDS = {
    "id",
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
EXPECTED_IMPLEMENTED_UNCOMMITTED_ORIGINAL_IDS = {
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
EXPECTED_PARTIAL_UNCOMMITTED_ORIGINAL_IDS = {
    "D2a-write-safety-6",
    "D3b-structure-6",
    "D5a-repo-redundancy-3",
    "D6a-test-gaps-7",
    "D6a-test-gaps-9",
    "D6b-test-quality-6",
    "D7-cli-consistency-5",
}


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return data


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


def normalized_manifest_scope(manifest: dict[str, Any]) -> set[str]:
    scope = manifest.get("scope", {})
    paths = set(scope.get("allowed_paths", []))
    for pattern in scope.get("allowed_path_patterns", []):
        if isinstance(pattern, str) and pattern.endswith("/**"):
            paths.add(pattern[:-2])
    return paths


def live_github_issue(issue: int) -> dict[str, Any]:
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
    payload = json.loads(result.stdout)
    if not isinstance(payload, dict):
        raise ValueError(f"live GitHub issue #{issue} did not return an object")
    return payload


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
    audit = audit_register()
    findings = registry.get("findings")
    programs = registry.get("programs")
    leases = registry.get("shared_path_leases")
    if not isinstance(findings, list) or not isinstance(programs, list) or not isinstance(leases, list):
        return ["registry findings, programs, and shared_path_leases must be lists"]

    ids = [row.get("id") for row in findings if isinstance(row, dict)]
    duplicate_ids = sorted(key for key, count in Counter(ids).items() if count > 1)
    if duplicate_ids:
        errors.append(f"duplicate registry IDs: {duplicate_ids}")

    for index, row in enumerate(findings):
        if not isinstance(row, dict):
            errors.append(f"finding row {index} is not a mapping")
            continue
        missing = sorted(REQUIRED_FINDING_FIELDS - row.keys())
        if missing:
            errors.append(f"{row.get('id', index)} missing fields: {missing}")
        if not isinstance(row.get("verification_evidence"), list) or not row.get("verification_evidence"):
            errors.append(f"{row.get('id', index)} has no verification evidence")
        else:
            for evidence_path in row["verification_evidence"]:
                if not isinstance(evidence_path, str) or not (ROOT / evidence_path).exists():
                    errors.append(
                        f"{row.get('id', index)} evidence path is missing: {evidence_path!r}"
                    )
        if not isinstance(row.get("allowed_paths"), list) or not row.get("allowed_paths"):
            errors.append(f"{row.get('id', index)} has no allowed paths")
        if row.get("issue") not in range(146, 159):
            errors.append(f"{row.get('id', index)} has invalid issue assignment {row.get('issue')!r}")

    original = {row["id"]: row for row in findings if row.get("origin") == "fable_audit"}
    r2 = {row["id"]: row for row in findings if row.get("origin") == "codex_revalidation"}
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

    fixed_original = {row["id"] for row in original.values() if row.get("status") == "code_fixed"}
    if fixed_original != {"D4b-trust-1", "D4b-trust-2"}:
        errors.append(f"unexpected committed code-fixed original set: {sorted(fixed_original)}")
    serializer_row = original.get("D2b-roundtrip-3", {})
    if serializer_row.get("status") != "code_fixed_evidence_pending" or serializer_row.get("fix_commit") is not None:
        errors.append("D2b-roundtrip-3 must be uncommitted code_fixed_evidence_pending")
    implemented_original = {
        row["id"]
        for row in original.values()
        if row.get("status") == "implemented_uncommitted_verification_pending"
    }
    if implemented_original != EXPECTED_IMPLEMENTED_UNCOMMITTED_ORIGINAL_IDS:
        errors.append(
            "implemented-uncommitted original set mismatch: "
            f"missing={sorted(EXPECTED_IMPLEMENTED_UNCOMMITTED_ORIGINAL_IDS - implemented_original)}, "
            f"extra={sorted(implemented_original - EXPECTED_IMPLEMENTED_UNCOMMITTED_ORIGINAL_IDS)}"
        )
    partial_original = {
        row["id"]
        for row in original.values()
        if row.get("status") == "partial_implementation_uncommitted_verification_pending"
    }
    if partial_original != EXPECTED_PARTIAL_UNCOMMITTED_ORIGINAL_IDS:
        errors.append(
            "partial-uncommitted original set mismatch: "
            f"missing={sorted(EXPECTED_PARTIAL_UNCOMMITTED_ORIGINAL_IDS - partial_original)}, "
            f"extra={sorted(partial_original - EXPECTED_PARTIAL_UNCOMMITTED_ORIGINAL_IDS)}"
        )
    expected_status_counts = Counter(
        {
            "confirmed_open": 41,
            "implemented_uncommitted_verification_pending": 40,
            "partial_implementation_uncommitted_verification_pending": 7,
            "code_fixed": 2,
            "code_fixed_evidence_pending": 1,
        }
    )
    status_counts = Counter(row.get("status") for row in original.values())
    if status_counts != expected_status_counts:
        errors.append(
            f"original working-tree status totals are wrong: {dict(status_counts)}"
        )
    for finding_id in sorted(implemented_original | partial_original):
        row = original[finding_id]
        if row.get("fix_commit") is not None:
            errors.append(f"{finding_id} must not claim a fix commit for dirty-tree work")
        expected_lifecycle = (
            "implementation_uncommitted_lifecycle_pending"
            if finding_id in implemented_original
            else "partial_implementation_uncommitted_lifecycle_pending"
        )
        if row.get("lifecycle_state") != expected_lifecycle:
            errors.append(
                f"{finding_id} lifecycle mismatch: {row.get('lifecycle_state')!r} "
                f"!= {expected_lifecycle!r}"
            )
    for finding_id, row in r2.items():
        expected_status = (
            "implemented_uncommitted_parity_verified"
            if finding_id == "R2-control-plane-parity-1"
            else "implemented_uncommitted_verification_pending"
        )
        if row.get("status") != expected_status:
            errors.append(
                f"{finding_id} status mismatch: {row.get('status')!r} != {expected_status!r}"
            )
        if row.get("fix_commit") is not None:
            errors.append(f"{finding_id} must not claim a fix commit for dirty-tree work")

    snapshot_counts = registry.get("github_snapshot", {}).get("issue_finding_counts", {})
    calculated_counts = Counter(row["issue"] for row in original.values())
    normalized_snapshot_counts = {int(key): int(value) for key, value in snapshot_counts.items()}
    if dict(sorted(calculated_counts.items())) != dict(sorted(normalized_snapshot_counts.items())):
        errors.append(
            "GitHub issue finding-count snapshot mismatch: "
            f"registry={dict(sorted(calculated_counts.items()))}, snapshot={normalized_snapshot_counts}"
        )
    registry_snapshot_counts = (
        registry.get("github_snapshot", {}).get("registry_finding_counts", {})
    )
    calculated_registry_counts = Counter(row["issue"] for row in findings)
    normalized_registry_counts = {
        int(key): int(value) for key, value in registry_snapshot_counts.items()
    }
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
        by_issue[row["issue"]].append(row)
    program_by_issue = {program["issue"]: program for program in programs}
    for row in findings:
        program = program_by_issue.get(row["issue"])
        if program is None:
            if row["issue"] != 158:
                errors.append(f"{row['id']} has no owning program row")
            continue
        uncovered = [
            path
            for path in row.get("allowed_paths", [])
            if not any(
                path_scope_covers(program_path, path)
                for program_path in program.get("allowed_paths", [])
            )
        ]
        if uncovered:
            errors.append(
                f"{row['id']} finding scope exceeds program #{row['issue']}: {uncovered}"
            )
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
        maximum = min((row["severity"] for row in rows), key=severity_rank.__getitem__)
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

    integration = registry.get("shared_tree_integration", {})
    expected_integration_issues = {
        program["issue"]
        for program in programs
        if program.get("lease_state") == "implementation_uncommitted_integration_pending"
    } | {146}
    observed_integration_issues = set(integration.get("affected_issues", []))
    if integration.get("status") != "unproven_rebaseline_integration":
        errors.append("shared-tree integration must remain explicitly unproven")
    if integration.get("release_blocking") is not True:
        errors.append("unproven shared-tree integration must remain release-blocking")
    if observed_integration_issues != expected_integration_issues:
        errors.append(
            "shared-tree integration issue set mismatch: "
            f"expected={sorted(expected_integration_issues)}, "
            f"observed={sorted(observed_integration_issues)}"
        )

    for issue, manifest_path in (
        (146, SERIALIZER_MANIFEST_PATH),
        (147, DOCTOR_MANIFEST_PATH),
    ):
        manifest_scope = normalized_manifest_scope(load_yaml(manifest_path))
        registry_scope = set(program_by_issue[issue].get("allowed_paths", []))
        if registry_scope != manifest_scope:
            errors.append(
                f"program #{issue} scope/manifest mismatch: "
                f"missing={sorted(manifest_scope - registry_scope)}, "
                f"extra={sorted(registry_scope - manifest_scope)}"
            )

    lease_rows: list[tuple[str, set[int]]] = []
    for lease in leases:
        path = lease.get("path")
        issue_set = set(lease.get("programs", []))
        order = lease.get("order", [])
        if not path or len(issue_set) < 2:
            errors.append(f"invalid shared-path lease: {lease}")
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
                    pair = {left["issue"], right["issue"]}
                    matching_leases = [
                        path
                        for path, issues in lease_rows
                        if pair <= issues and lease_covers(path, overlap)
                    ]
                    if not matching_leases:
                        errors.append(
                            f"unleased overlap {overlap}: #{left['issue']} and #{right['issue']}"
                        )
                    elif len(matching_leases) > 1:
                        errors.append(
                            f"multiply leased overlap {overlap}: #{left['issue']} and "
                            f"#{right['issue']} via {matching_leases}"
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
                            f"#{left['issue']} and #{right['issue']}"
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
    for program in programs:
        marker = f"#{program['issue']}"
        state = f"`{program['lifecycle_state']}`"
        if not any(marker in line and state in line for line in ledger_text.splitlines()):
            errors.append(f"O4 is missing #{program['issue']} lifecycle state {state}")
    for path, issues in lease_rows:
        expected_path = f"`{path}`"
        matching_lines = [line for line in ledger_text.splitlines() if expected_path in line]
        if not matching_lines:
            errors.append(f"O5 is missing shared-path lease {path}")
            continue
        if not any(all(f"#{issue}" in line for issue in issues) for line in matching_lines):
            errors.append(f"O5 lease {path} is missing one or more program issue IDs")
    if not any("#149" in line and "P1-containing" in line for line in ledger_text.splitlines()):
        errors.append("O4 must label #149 P1-containing")

    doctor_manifest = load_yaml(DOCTOR_MANIFEST_PATH)
    if doctor_manifest.get("fallback_evidence_mode") != "strict_p3":
        errors.append("#147 manifest must require fresh strict-P3 evidence")
    sequencing = doctor_manifest.get("implementation_sequencing", {})
    if sequencing.get("implementation_ref") != "03c36e6ac999d2c411c13252baa2e8fcff60e6ed":
        errors.append("#147 manifest is not pinned to the exact-argv implementation")
    if len(doctor_manifest.get("required_dispatch_bundles", [])) != 9:
        errors.append("#147 manifest must declare nine fresh B.1/D.2/D.5 dispatch bundles")
    if len(doctor_manifest.get("historical_receipt_gaps", [])) != 3:
        errors.append("#147 manifest must mark B.1/D.2/D.5 historical prose replay-required")
    inventory = load_yaml(
        ROOT / "docs/reviews/project-ontos-audit-doctor-rce/lifecycle-receipt-inventory.yaml"
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

    serializer_manifest = load_yaml(SERIALIZER_MANIFEST_PATH)
    if serializer_manifest.get("fallback_evidence_mode") != "provider_limited_fallback":
        errors.append("#146 manifest must declare its authorized provider-limited mode")
    serializer_scope = serializer_manifest.get("scope", {})
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
        github_snapshot = registry.get("github_snapshot", {})
        if github_snapshot.get("epic_release_line_synced") is not True:
            errors.append("external parity drift: epic #158 release line is not synchronized")
        if github_snapshot.get("r2_checklists_synced") is not True:
            errors.append("external parity drift: R2 checklist rows are not synchronized")
        if github_snapshot.get("original_checklist_policy") != "merged_and_verified_only":
            errors.append("external parity drift: original checklist completion policy is not recorded")
        if github_snapshot.get("uncommitted_original_checklists_remain_unchecked") is not True:
            errors.append(
                "external parity drift: uncommitted original rows must remain unchecked until merged and verified"
            )
        drift = github_snapshot.get("external_drift", [])
        unresolved = [item for item in drift if item.get("status") != "resolved"]
        for item in unresolved:
            errors.append(
                f"external parity drift: issue #{item.get('issue')} {item.get('field')} "
                f"observed={item.get('observed')} expected={item.get('expected')}"
            )
        for item in drift:
            if item.get("status") == "resolved" and item.get("observed") != item.get("expected"):
                errors.append(
                    f"external parity drift marked resolved with unequal values: "
                    f"issue #{item.get('issue')} {item.get('field')}"
                )

        rows_by_issue: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for row in findings:
            rows_by_issue[row["issue"]].append(row)
        milestone_markers = {
            1: "Audit Release N",
            2: "Audit Release N+1",
            3: "Audit Release N+2",
        }
        for issue in range(146, 159):
            live = live_github_issue(issue)
            program = program_by_issue.get(issue)
            expected_rows = rows_by_issue.get(issue, [])
            expected_ids = {row["id"] for row in expected_rows}
            body = live.get("body") or ""

            if issue == 158 and not expected_ids <= set(body.split()):
                # Epic punctuation/backticks make token equality inconvenient;
                # require every epic-owned ID literally in the body.
                missing = sorted(item for item in expected_ids if item not in body)
                if missing:
                    errors.append(f"live GitHub epic #158 is missing rows: {missing}")

            checkbox_states = github_checkbox_states(body)
            if issue <= 157 and set(checkbox_states) != expected_ids:
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
                if row["id"] not in checkbox_states:
                    continue
                expected_checked = row.get("status") == "code_fixed"
                if checkbox_states[row["id"]] != expected_checked:
                    errors.append(
                        f"live GitHub checklist status mismatch for {row['id']}: "
                        f"checked={checkbox_states[row['id']]} expected={expected_checked}"
                    )

            expected_state = (program or {}).get("github_state", "open").upper()
            if live.get("state") != expected_state:
                errors.append(
                    f"live GitHub issue #{issue} state mismatch: "
                    f"{live.get('state')!r} != {expected_state!r}"
                )
            expected_milestone = (program or {}).get("github_milestone", 1)
            milestone_title = (live.get("milestone") or {}).get("title", "")
            marker = milestone_markers[expected_milestone]
            if not milestone_title.startswith(marker):
                errors.append(
                    f"live GitHub issue #{issue} milestone mismatch: "
                    f"{milestone_title!r} does not start with {marker!r}"
                )
            if program is not None:
                label_names = {
                    item.get("name", "") for item in live.get("labels", [])
                }
                expected_label_prefix = program["max_severity"]
                if not any(name.startswith(expected_label_prefix) for name in label_names):
                    errors.append(
                        f"live GitHub issue #{issue} lacks {expected_label_prefix} severity label"
                    )
        live_epic = live_github_issue(158)
        if "v4.7.1" not in (live_epic.get("body") or "") or "v4.9.0" not in (
            live_epic.get("body") or ""
        ):
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
        "implemented_uncommitted=40, partial_uncommitted=7, confirmed_open=41"
    )
    print("revalidation findings: 9")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
