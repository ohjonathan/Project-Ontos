#!/usr/bin/env python3
"""Verify the compact product-branch index for an out-of-tree evidence ref."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path, PurePosixPath

import yaml


def _git(root: Path, *args: str, text: bool = False):
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, check=False, text=text
    )


def verify(index_path: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []
    payload = yaml.safe_load(index_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        return ["index must be a schema_version: 1 mapping"]
    evidence_ref = payload.get("evidence_ref")
    evidence_root = payload.get("evidence_root")
    entries = payload.get("entries")
    if not isinstance(evidence_ref, str) or not evidence_ref:
        errors.append("evidence_ref must be a non-empty string")
    if not isinstance(evidence_root, str) or not evidence_root:
        errors.append("evidence_root must be a non-empty string")
    if not isinstance(entries, list) or not entries:
        errors.append("entries must contain at least one indexed artifact")
    if errors:
        return errors

    resolved = _git(repo_root, "rev-parse", "--verify", f"{evidence_ref}^{{commit}}", text=True)
    if resolved.returncode:
        return [f"evidence ref cannot be resolved: {evidence_ref}"]

    indexed: set[str] = set()
    required = {"path", "sha256", "phase", "role", "family", "product_head"}
    for position, entry in enumerate(entries):
        if not isinstance(entry, dict) or not required.issubset(entry):
            errors.append(f"entry {position} is missing required fields")
            continue
        path = entry["path"]
        if not isinstance(path, str) or PurePosixPath(path).is_absolute() or ".." in PurePosixPath(path).parts:
            errors.append(f"entry {position} has an unsafe path")
            continue
        if not path.startswith(evidence_root.rstrip("/") + "/"):
            errors.append(f"entry {position} is outside evidence_root")
            continue
        if path in indexed:
            errors.append(f"duplicate indexed path: {path}")
            continue
        indexed.add(path)
        shown = _git(repo_root, "show", f"{evidence_ref}:{path}")
        if shown.returncode:
            errors.append(f"missing evidence artifact: {path}")
            continue
        actual = hashlib.sha256(shown.stdout).hexdigest()
        if actual != entry["sha256"]:
            errors.append(f"sha256 mismatch: {path}")

    tree = _git(repo_root, "ls-tree", "-r", "--name-only", evidence_ref, "--", evidence_root, text=True)
    if tree.returncode:
        errors.append(f"cannot list evidence root: {evidence_root}")
    else:
        present = {line for line in tree.stdout.splitlines() if line}
        for orphan in sorted(present - indexed):
            errors.append(f"unindexed evidence artifact: {orphan}")
        for missing in sorted(indexed - present):
            errors.append(f"indexed artifact absent from evidence tree: {missing}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("index", type=Path)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    args = parser.parse_args()
    errors = verify(args.index, args.repo.resolve())
    if errors:
        for error in errors:
            print(f"evidence-ref: ERROR: {error}", file=sys.stderr)
        return 1
    print("evidence-ref: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
