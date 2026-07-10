"""Tests for release-wheel identity and integrity verification."""

import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile


REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKER = REPO_ROOT / "scripts" / "check_release_artifact.py"


def _write_wheel(path: Path, *, version: str = "4.7.1") -> None:
    with ZipFile(path, "w") as archive:
        archive.writestr("ontos/__init__.py", f"__version__ = {version!r}\n")
        archive.writestr(
            f"ontos-{version}.dist-info/METADATA",
            "Metadata-Version: 2.1\n"
            "Name: ontos\n"
            f"Version: {version}\n",
        )


def _run_checker(wheel: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(CHECKER),
            str(wheel),
            "--expected-version",
            "4.7.1",
            *args,
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_checker_records_and_reverifies_wheel_hash(tmp_path):
    wheel = tmp_path / "ontos-4.7.1-py3-none-any.whl"
    manifest = tmp_path / "release-integrity.json"
    _write_wheel(wheel)

    recorded = _run_checker(wheel, "--write-manifest", str(manifest))
    verified = _run_checker(wheel, "--verify-manifest", str(manifest))

    assert recorded.returncode == 0, recorded.stderr
    assert verified.returncode == 0, verified.stderr
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["distribution"] == "ontos"
    assert payload["version"] == "4.7.1"
    assert len(payload["sha256"]) == 64


def test_checker_rejects_wheel_with_wrong_version(tmp_path):
    wheel = tmp_path / "ontos-9.9.9-py3-none-any.whl"
    _write_wheel(wheel, version="9.9.9")

    result = _run_checker(wheel)

    assert result.returncode == 1
    assert "Version mismatch" in result.stderr


def test_checker_rejects_wheel_that_differs_from_build_manifest(tmp_path):
    built_wheel = tmp_path / "ontos-4.7.1-py3-none-any.whl"
    downloaded_dir = tmp_path / "downloaded"
    downloaded_dir.mkdir()
    downloaded_wheel = downloaded_dir / built_wheel.name
    manifest = tmp_path / "release-integrity.json"
    _write_wheel(built_wheel)
    assert _run_checker(
        built_wheel,
        "--write-manifest",
        str(manifest),
    ).returncode == 0
    _write_wheel(downloaded_wheel)
    with downloaded_wheel.open("ab") as handle:
        handle.write(b"tampered")

    result = _run_checker(
        downloaded_wheel,
        "--verify-manifest",
        str(manifest),
    )

    assert result.returncode == 1
    assert "differing fields" in result.stderr
    assert "sha256" in result.stderr
