"""Parity tests for stub command."""
import sys

import subprocess
import os
from pathlib import Path

import pytest

from ontos.commands.stub import _VALID_DOC_TYPES, _validate_stub_params
from ontos.core.errors import OntosUserError
from ontos.core.ontology import get_valid_types
from ontos.core.schema import validate_document_id


def test_stub_help_parity():
    """Native --help matches legacy."""
    result = subprocess.run(
        [sys.executable, "-m", "ontos.cli", "stub", "--help"],
        capture_output=True,
        text=True,
        env=os.environ.copy()
    )
    assert "--goal" in result.stdout
    assert "--type" in result.stdout
    assert "--output" in result.stdout
    assert "stub" in result.stdout.lower()


def test_stub_file_creation_parity(tmp_path):
    """Stub command creates file with correct frontmatter."""
    (tmp_path / ".ontos.toml").write_text(
        "[ontos]\nversion = '3.0'\n",
        encoding="utf-8",
    )
    output_file = tmp_path / "test_stub.md"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[2])
    
    # Run native command
    result = subprocess.run(
        [sys.executable, "-m", "ontos.cli", "stub", 
         "--id", "test_stub", 
         "--type", "atom", 
         "--goal", "Test Goal",
         "--output", str(output_file)],
        capture_output=True,
        text=True,
        env=os.environ.copy(),
        cwd=tmp_path,
    )

    assert result.returncode == 0
    assert output_file.exists()
    
    content = output_file.read_text()
    assert "id: test_stub" in content
    assert "type: atom" in content
    assert "status: pending_curation" in content
    assert "curation_level: 1" in content
    assert "goal: Test Goal" in content
    assert "# Test Stub" in content


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unavailable")
def test_stub_rejects_symlinked_parent_without_creating_external_directory(
    tmp_path,
):
    (tmp_path / ".ontos.toml").write_text(
        "[ontos]\nversion = '4.7'\n",
        encoding="utf-8",
    )
    outside = tmp_path.parent / f"{tmp_path.name}-stub-outside"
    outside.mkdir()
    redirected = tmp_path / "docs"
    try:
        redirected.symlink_to(outside, target_is_directory=True)
    except OSError as exc:  # pragma: no cover - platform policy.
        pytest.skip(f"symlink creation unavailable: {exc}")

    output_file = redirected / "new-parent" / "unsafe.md"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[2])
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ontos.cli",
            "stub",
            "--id",
            "unsafe_stub",
            "--type",
            "atom",
            "--goal",
            "Test Goal",
            "--output",
            str(output_file),
        ],
        capture_output=True,
        text=True,
        env=env,
        cwd=tmp_path,
    )

    assert result.returncode == 1
    assert not (outside / "new-parent").exists()


def test_stub_types_derive_from_canonical_ontology():
    assert _VALID_DOC_TYPES == frozenset(get_valid_types())


@pytest.mark.parametrize("doc_type", sorted(get_valid_types()))
def test_stub_accepts_every_canonical_document_type(doc_type):
    _validate_stub_params(
        {"id": f"{doc_type}_stub", "type": doc_type, "depends_on": None}
    )


def test_stub_rejects_noncanonical_unknown_type():
    with pytest.raises(OntosUserError, match="Invalid --type"):
        _validate_stub_params(
            {"id": "unknown_stub", "type": "unknown", "depends_on": None}
        )


def test_stub_invalid_id_uses_canonical_copy_and_user_error_code():
    params = {"id": "bad id", "type": "atom", "depends_on": None}
    with pytest.raises(ValueError) as canonical:
        validate_document_id(params["id"])

    with pytest.raises(OntosUserError) as cli_error:
        _validate_stub_params(params)

    assert str(cli_error.value) == str(canonical.value)
    assert cli_error.value.code == "E_USER_INPUT"
