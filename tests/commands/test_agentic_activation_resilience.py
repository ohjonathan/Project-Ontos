"""CLI regressions for v4.4 agentic activation resilience."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from textwrap import dedent


REPO_ROOT = Path(__file__).resolve().parents[2]


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(content).lstrip(), encoding="utf-8")


def _run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT)
    return subprocess.run(
        [sys.executable, "-m", "ontos", *args],
        cwd=root,
        text=True,
        capture_output=True,
        env=env,
    )


def _workspace(root: Path) -> Path:
    _write(
        root / ".ontos.toml",
        """
        [ontos]
        version = "4.4"

        [scanning]
        skip_patterns = ["*/docs/reviews/*"]
        """,
    )
    _write(
        root / "docs/atom.md",
        """
        ---
        id: atom_doc
        type: atom
        status: active
        ---
        Atom body.
        """,
    )
    return root


def test_activate_json_generates_usable_context_map_with_valid_status(tmp_path: Path) -> None:
    root = _workspace(tmp_path)

    result = _run(root, "--json", "activate")
    payload = json.loads(result.stdout)

    assert result.returncode == 0, result.stderr
    assert payload["status"] == "success"
    assert payload["data"]["status"] in {"usable", "usable_with_warnings"}
    assert payload["data"]["map"]["refreshed"] is True
    assert payload["data"]["loaded_ids"] == ["atom_doc"]

    context_map = root / "Ontos_Context_Map.md"
    assert context_map.exists()
    assert "status: complete" in context_map.read_text(encoding="utf-8").split("---", 2)[1]


def test_activate_json_fails_explicitly_on_required_version_mismatch(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    config_path = root / ".ontos.toml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace(
            'version = "4.4"',
            'version = "4.4"\nrequired_version = ">=99.0.0"',
        ),
        encoding="utf-8",
    )

    result = _run(root, "--json", "activate")
    payload = json.loads(result.stdout)

    assert result.returncode == 1
    assert payload["status"] == "error"
    assert payload["data"]["status"] == "not_usable"
    assert "Incompatible Ontos version" in payload["data"]["reason"]
    assert not (root / "Ontos_Context_Map.md").exists()


def test_doctor_frontmatter_reports_precise_enum_diagnostics(tmp_path: Path) -> None:
    # (#117) `review` and `completed` are now canonical; use `proposal` and
    # `done` to exercise the invalid-enum path (proposal → strategy,
    # done → complete are still repairable aliases, not canonical).
    root = _workspace(tmp_path)
    _write(
        root / "docs/review.md",
        """
        ---
        id: review_doc
        type: proposal
        status: done
        ---
        Review body.
        """,
    )
    assert _run(root, "map").returncode == 0

    result = _run(root, "--json", "doctor", "--frontmatter")
    payload = json.loads(result.stdout)
    checks = {check["name"]: check for check in payload["data"]["checks"]}

    assert result.returncode == 0
    assert checks["frontmatter_enums"]["status"] == "warning"
    assert "2 invalid enum value(s)" in checks["frontmatter_enums"]["message"]
    assert "docs/review.md:3 type='proposal'" in checks["frontmatter_enums"]["details"]
    assert "docs/review.md:4 status='done'" in checks["frontmatter_enums"]["details"]

    human = _run(root, "doctor", "--frontmatter")

    assert human.returncode == 0
    assert "docs/review.md:3 type='proposal'" in human.stdout
    assert "docs/review.md:4 status='done'" in human.stdout


def test_maintain_fix_frontmatter_enums_dry_run_json(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    _write(
        root / "docs/review.md",
        """
        ---
        id: review_doc
        type: proposal
        status: done
        ---
        Review body.
        """,
    )

    result = _run(root, "--json", "maintain", "--fix-frontmatter-enums")
    payload = json.loads(result.stdout)

    assert result.returncode == 0, result.stderr
    assert payload["data"]["mode"] == "dry-run"
    assert payload["data"]["summary"]["repairable"] == 2
    assert payload["data"]["summary"]["unresolved"] == 0


def test_maintain_fix_frontmatter_enums_apply_preserves_original_values(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    target = root / "docs/review.md"
    _write(
        target,
        """
        ---
        id: review_doc
        type: proposal
        status: done
        ---
        Review body.
        """,
    )
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=ontos@example.test",
            "-c",
            "user.name=Ontos Test",
            "commit",
            "-m",
            "initial",
        ],
        cwd=root,
        check=True,
        capture_output=True,
    )

    result = _run(root, "--json", "maintain", "--fix-frontmatter-enums", "--apply")
    payload = json.loads(result.stdout)
    content = target.read_text(encoding="utf-8")

    assert result.returncode == 0, result.stderr
    assert payload["data"]["mode"] == "apply"
    assert payload["data"]["modified_files"] == ["docs/review.md"]
    assert "type: strategy" in content
    assert "original_type: proposal" in content
    assert "status: complete" in content
    assert "original_status: done" in content


def test_verify_all_uses_configured_scan_exclusions(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    _write(
        root / "docs/reviews/duplicate.md",
        """
        ---
        id: atom_doc
        type: atom
        status: active
        ---
        Excluded duplicate.
        """,
    )

    result = _run(root, "verify", "--all")

    assert result.returncode == 0, result.stderr
    assert "No stale documents found." in result.stdout


def test_doctor_git_hooks_recognizes_linked_worktree(tmp_path: Path) -> None:
    primary = tmp_path / "primary"
    primary.mkdir()
    subprocess.run(["git", "init"], cwd=primary, check=True, capture_output=True)
    _write(primary / "README.md", "primary\n")
    subprocess.run(["git", "add", "."], cwd=primary, check=True, capture_output=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=ontos@example.test",
            "-c",
            "user.name=Ontos Test",
            "commit",
            "-m",
            "initial",
        ],
        cwd=primary,
        check=True,
        capture_output=True,
    )
    worktree = tmp_path / "linked"
    subprocess.run(
        ["git", "worktree", "add", str(worktree)],
        cwd=primary,
        check=True,
        capture_output=True,
    )
    _workspace(worktree)

    from ontos.commands.doctor import check_git_hooks

    result = check_git_hooks(repo_root=worktree)

    assert result.status == "warning"
    assert result.message.startswith("Hooks missing:")
