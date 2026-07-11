"""Static regression checks for CI isolation and release provenance gates."""

from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]


def _workflow(name: str) -> tuple[dict, str]:
    source = (REPO_ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")
    return yaml.safe_load(source), source


def _step(job: dict, name: str) -> dict:
    return next(step for step in job["steps"] if step.get("name") == name)


def test_ci_has_clean_tree_gate_and_windows_boundary_smokes():
    workflow, source = _workflow("ci.yml")

    clean_gate = _step(workflow["jobs"]["test"], "Verify tests left the checkout unchanged")
    assert "git status --porcelain=v1 --untracked-files=all" in clean_gate["run"]

    windows = workflow["jobs"]["windows-base-cli"]
    assert windows["runs-on"] == "windows-latest"
    assert windows["strategy"]["matrix"]["python-version"] == ["3.9", "3.14"]
    smoke = _step(windows, "Smoke-test import, locking, and CLI")["run"]
    assert "backend_name() == 'msvcrt'" in smoke
    assert "python -m ontos --help" in smoke
    assert ".ontos/scripts/tests" not in source


def test_ci_gates_measured_coverage_and_validates_audit_registry():
    workflow, _ = _workflow("ci.yml")
    test_job = workflow["jobs"]["test"]

    checkout = test_job["steps"][0]
    assert checkout["with"]["fetch-depth"] == 0

    coverage = _step(test_job, "Check coverage")
    assert coverage.get("continue-on-error") is not True
    assert "--cov-fail-under=70" in coverage["run"]
    assert "--cov-fail-under=82" in coverage["run"]

    registry = _step(test_job, "Validate audit remediation registry")
    assert registry["if"] == "matrix.python-version == '3.11'"
    assert registry["run"] == "python scripts/validate-audit-remediation-registry.py"


def test_local_coverage_outputs_are_ignored_by_git():
    ignored = set((REPO_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines())
    assert {".coverage", "coverage.xml"} <= ignored


def test_repository_hooks_delegate_to_package_cli():
    for relative in (
        ".ontos/hooks/pre-commit",
        ".ontos/hooks/pre-push",
        "ontos/_hooks/pre-commit",
        "ontos/_hooks/pre-push",
    ):
        source = (REPO_ROOT / relative).read_text(encoding="utf-8")
        assert "python3 -m ontos hook" in source
        assert ".ontos/scripts" not in source

    pre_commit = (REPO_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    assert ".ontos/scripts" not in pre_commit
    assert "python -m ontos" in pre_commit
    parsed = yaml.safe_load(pre_commit)
    hooks = parsed["repos"][0]["hooks"]
    for hook in hooks:
        assert hook["language"] == "python"
        assert "PyYAML>=6.0,<7.0" in hook["additional_dependencies"]
        assert "tomli_w>=1.2,<2.0" in hook["additional_dependencies"]


def test_publish_oidc_is_limited_to_publisher_jobs():
    workflow, _ = _workflow("publish.yml")

    assert workflow["permissions"] == {"contents": "read"}
    oidc_jobs = {
        name
        for name, job in workflow["jobs"].items()
        if job.get("permissions", {}).get("id-token") == "write"
    }
    assert oidc_jobs == {"publish-testpypi", "publish-pypi"}


def test_testpypi_verification_is_exact_and_byte_identical():
    workflow, source = _workflow("publish.yml")

    assert "skip-existing" not in source
    verify_job = workflow["jobs"]["verify-testpypi"]
    compare = _step(
        verify_job,
        "Download and compare the exact TestPyPI wheel",
    )["run"]
    install = _step(
        verify_job,
        "Install the exact TestPyPI version without dependencies",
    )["run"]

    assert "--verify-manifest release-integrity.json" in compare
    assert "--index-url https://test.pypi.org/simple/" in install
    assert "--no-deps" in install
    assert '"ontos==${expected_version}"' in install
    assert "python -m build --wheel" in source
    assert "Build sdist" not in source
