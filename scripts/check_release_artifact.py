#!/usr/bin/env python3
"""Validate an Ontos wheel's identity and SHA-256 release manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from email.parser import Parser
from pathlib import Path
import sys
from zipfile import BadZipFile, ZipFile


MANIFEST_SCHEMA_VERSION = 1


def _normalized_distribution(value: str) -> str:
    return value.strip().lower().replace("_", "-").replace(".", "-")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inspect_wheel(wheel: Path) -> dict[str, str | int]:
    """Return stable identity fields from a wheel and its METADATA."""
    if not wheel.is_file() or wheel.suffix != ".whl":
        raise ValueError(f"Expected one wheel file, got: {wheel}")

    try:
        with ZipFile(wheel) as archive:
            metadata_names = [
                name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
            ]
            if len(metadata_names) != 1:
                raise ValueError(
                    "Wheel must contain exactly one .dist-info/METADATA file; "
                    f"found {len(metadata_names)}"
                )
            metadata_text = archive.read(metadata_names[0]).decode("utf-8")
    except (BadZipFile, UnicodeDecodeError) as exc:
        raise ValueError(f"Invalid wheel archive: {exc}") from exc

    metadata = Parser().parsestr(metadata_text)
    distribution = metadata.get("Name", "").strip()
    version = metadata.get("Version", "").strip()
    if not distribution or not version:
        raise ValueError("Wheel METADATA must contain Name and Version")

    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "distribution": distribution,
        "version": version,
        "filename": wheel.name,
        "sha256": _sha256(wheel),
        "size": wheel.stat().st_size,
    }


def validate_identity(
    artifact: dict[str, str | int],
    *,
    expected_distribution: str,
    expected_version: str,
) -> None:
    """Validate the expected project and release-tag version."""
    actual_distribution = _normalized_distribution(str(artifact["distribution"]))
    if actual_distribution != _normalized_distribution(expected_distribution):
        raise ValueError(
            f"Distribution mismatch: expected {expected_distribution!r}, "
            f"got {artifact['distribution']!r}"
        )
    if artifact["version"] != expected_version:
        raise ValueError(
            f"Version mismatch: expected {expected_version!r}, got {artifact['version']!r}"
        )


def write_manifest(path: Path, artifact: dict[str, str | int]) -> None:
    """Write the build job's immutable wheel identity manifest."""
    path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify_manifest(path: Path, artifact: dict[str, str | int]) -> None:
    """Require a downloaded wheel to be byte-identical to the build wheel."""
    try:
        expected = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read release manifest {path}: {exc}") from exc

    if expected != artifact:
        differing = sorted(
            key
            for key in set(expected) | set(artifact)
            if expected.get(key) != artifact.get(key)
        )
        raise ValueError(
            "Wheel does not match the build artifact manifest; differing fields: "
            + ", ".join(differing)
        )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", type=Path, help="Wheel file to inspect")
    parser.add_argument("--expected-version", required=True)
    parser.add_argument("--expected-distribution", default="ontos")
    manifest = parser.add_mutually_exclusive_group()
    manifest.add_argument("--write-manifest", type=Path)
    manifest.add_argument("--verify-manifest", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        artifact = inspect_wheel(args.wheel)
        validate_identity(
            artifact,
            expected_distribution=args.expected_distribution,
            expected_version=args.expected_version,
        )
        if args.write_manifest:
            write_manifest(args.write_manifest, artifact)
        if args.verify_manifest:
            verify_manifest(args.verify_manifest, artifact)
    except ValueError as exc:
        print(f"release artifact verification failed: {exc}", file=sys.stderr)
        return 1

    print(
        f"verified {artifact['filename']}: "
        f"{artifact['distribution']} {artifact['version']} sha256={artifact['sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
