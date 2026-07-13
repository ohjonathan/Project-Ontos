import hashlib
import subprocess
from pathlib import Path

import yaml

from scripts.verify_lifecycle_evidence_ref import verify


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


def test_evidence_ref_verifier_checks_hashes_and_orphans(tmp_path: Path) -> None:
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test")
    evidence = tmp_path / "evidence" / "D.2.txt"
    evidence.parent.mkdir()
    evidence.write_bytes(b"review\n")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "evidence")
    _git(tmp_path, "branch", "evidence-ref")

    index = tmp_path / "index.yaml"
    payload = {
        "schema_version": 1,
        "evidence_ref": "evidence-ref",
        "evidence_root": "evidence",
        "entries": [{
            "path": "evidence/D.2.txt",
            "sha256": hashlib.sha256(b"review\n").hexdigest(),
            "phase": "D.2",
            "role": "peer",
            "family": "codex",
            "product_head": "a" * 40,
        }],
    }
    index.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    assert verify(index, tmp_path) == []
    payload["entries"][0]["sha256"] = "0" * 64
    index.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    assert any("sha256 mismatch" in error for error in verify(index, tmp_path))
