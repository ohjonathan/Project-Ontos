#!/usr/bin/env python3
"""Create and verify immutable Ontos release bundles.

The release bundle has exactly this shape::

    release-bundle/
      release-manifest.json
      dist/
        ontos-<version>-*.whl
        ontos-<version>.tar.gz

Only Python's standard library is used so the verification gate does not need
to install code from either distribution index before validating artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.request
import zipfile
from email.parser import Parser
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Set, Tuple


MANIFEST_SCHEMA = "ontos.release-bundle/v1"
MANIFEST_FILENAME = "release-manifest.json"
PROJECT_NAME = "ontos"
TESTPYPI_JSON_URL = "https://test.pypi.org/pypi/{project}/{version}/json"
TESTPYPI_SIMPLE_URL = "https://test.pypi.org/simple/"
MAX_INDEX_RESPONSE_BYTES = 2 * 1024 * 1024
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SOURCE_SHA_RE = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")


class ReleaseArtifactError(RuntimeError):
    """Raised when release artifact provenance cannot be proven."""


class _RetryableIndexState(ReleaseArtifactError):
    """Raised when TestPyPI has not exposed every expected file yet."""


def _normalize_project_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def _version_from_tag(tag: str) -> str:
    if not tag.startswith("v") or len(tag) == 1:
        raise ReleaseArtifactError(f"release tag must have the form v<version>: {tag!r}")
    version = tag[1:]
    if any(character.isspace() for character in version):
        raise ReleaseArtifactError(f"release tag contains whitespace: {tag!r}")
    return version


def _validate_source_sha(source_sha: str) -> str:
    normalized = source_sha.lower()
    if not _SOURCE_SHA_RE.fullmatch(normalized):
        raise ReleaseArtifactError("source SHA must be a 40- or 64-character hexadecimal digest")
    return normalized


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_core_metadata(content: bytes, source: str) -> Tuple[str, str]:
    try:
        message = Parser().parsestr(content.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise ReleaseArtifactError(f"metadata is not UTF-8 in {source}") from exc
    name = message.get("Name")
    version = message.get("Version")
    if not name or not version:
        raise ReleaseArtifactError(f"metadata in {source} does not contain Name and Version")
    return name.strip(), version.strip()


def _wheel_metadata(path: Path) -> Tuple[str, str]:
    try:
        with zipfile.ZipFile(path) as archive:
            candidates = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
            if len(candidates) != 1:
                raise ReleaseArtifactError(
                    f"wheel must contain exactly one .dist-info/METADATA file: {path.name}"
                )
            return _parse_core_metadata(archive.read(candidates[0]), f"{path.name}:{candidates[0]}")
    except (OSError, zipfile.BadZipFile, KeyError) as exc:
        raise ReleaseArtifactError(f"cannot read wheel metadata from {path.name}: {exc}") from exc


def _sdist_metadata(path: Path) -> Tuple[str, str]:
    try:
        with tarfile.open(path, mode="r:gz") as archive:
            candidates = [
                member
                for member in archive.getmembers()
                if member.isfile() and member.name.endswith("/PKG-INFO")
            ]
            root_candidates = [member for member in candidates if len(Path(member.name).parts) == 2]
            if len(root_candidates) != 1:
                raise ReleaseArtifactError(
                    f"sdist must contain exactly one top-level PKG-INFO file: {path.name}"
                )
            handle = archive.extractfile(root_candidates[0])
            if handle is None:
                raise ReleaseArtifactError(f"cannot extract PKG-INFO from {path.name}")
            return _parse_core_metadata(
                handle.read(), f"{path.name}:{root_candidates[0].name}"
            )
    except (OSError, tarfile.TarError) as exc:
        raise ReleaseArtifactError(f"cannot read sdist metadata from {path.name}: {exc}") from exc


def _artifact_kind(path: Path) -> str:
    if path.name.endswith(".whl"):
        return "wheel"
    if path.name.endswith(".tar.gz"):
        return "sdist"
    raise ReleaseArtifactError(f"unexpected file in distribution directory: {path.name}")


def _distribution_paths(dist_dir: Path) -> List[Path]:
    if not dist_dir.is_dir():
        raise ReleaseArtifactError(f"distribution directory does not exist: {dist_dir}")
    paths = sorted(dist_dir.iterdir(), key=lambda path: path.name)
    if any(not path.is_file() or path.is_symlink() for path in paths):
        raise ReleaseArtifactError("distribution directory may contain only regular files")
    by_kind: Dict[str, List[Path]] = {"wheel": [], "sdist": []}
    for path in paths:
        by_kind[_artifact_kind(path)].append(path)
    if len(by_kind["wheel"]) != 1 or len(by_kind["sdist"]) != 1 or len(paths) != 2:
        raise ReleaseArtifactError("distribution directory must contain exactly one wheel and one sdist")
    return by_kind["wheel"] + by_kind["sdist"]


def _metadata_for(path: Path, kind: str) -> Tuple[str, str]:
    return _wheel_metadata(path) if kind == "wheel" else _sdist_metadata(path)


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def _artifact_record(path: Path, expected_version: str) -> Dict[str, Any]:
    kind = _artifact_kind(path)
    embedded_name, embedded_version = _metadata_for(path, kind)
    if _normalize_project_name(embedded_name) != PROJECT_NAME:
        raise ReleaseArtifactError(
            f"{path.name} embeds project name {embedded_name!r}, expected {PROJECT_NAME!r}"
        )
    if embedded_version != expected_version:
        raise ReleaseArtifactError(
            f"{path.name} embeds version {embedded_version!r}, expected {expected_version!r}"
        )
    return {
        "filename": path.name,
        "kind": kind,
        "size": path.stat().st_size,
        "sha256": _sha256(path),
        "embedded_name": embedded_name,
        "embedded_version": embedded_version,
    }


def create_manifest(dist_dir: Path, manifest_path: Path, tag: str, source_sha: str) -> Dict[str, Any]:
    """Create a manifest after validating both built distributions."""

    if _is_within(manifest_path, dist_dir):
        raise ReleaseArtifactError("release manifest must be outside the dist directory")
    version = _version_from_tag(tag)
    normalized_sha = _validate_source_sha(source_sha)
    artifacts = [_artifact_record(path, version) for path in _distribution_paths(dist_dir)]
    payload: Dict[str, Any] = {
        "schema": MANIFEST_SCHEMA,
        "tag": tag,
        "version": version,
        "source_sha": normalized_sha,
        "artifacts": artifacts,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = manifest_path.with_name(f".{manifest_path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, manifest_path)
    return payload


def _load_manifest(manifest_path: Path) -> Mapping[str, Any]:
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReleaseArtifactError(f"cannot read release manifest {manifest_path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ReleaseArtifactError("release manifest root must be an object")
    return payload


def _validated_manifest_rows(payload: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    required_root = {"schema", "tag", "version", "source_sha", "artifacts"}
    if set(payload) != required_root:
        raise ReleaseArtifactError("release manifest has an unexpected root schema")
    if payload.get("schema") != MANIFEST_SCHEMA:
        raise ReleaseArtifactError(f"unsupported release manifest schema: {payload.get('schema')!r}")
    if not isinstance(payload.get("tag"), str) or not isinstance(payload.get("version"), str):
        raise ReleaseArtifactError("release manifest tag and version must be strings")
    if _version_from_tag(payload["tag"]) != payload["version"]:
        raise ReleaseArtifactError("release manifest tag and version disagree")
    if not isinstance(payload.get("source_sha"), str):
        raise ReleaseArtifactError("release manifest source_sha must be a string")
    _validate_source_sha(payload["source_sha"])
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list) or len(artifacts) != 2:
        raise ReleaseArtifactError("release manifest must contain exactly two artifact rows")
    required_row = {
        "filename",
        "kind",
        "size",
        "sha256",
        "embedded_name",
        "embedded_version",
    }
    rows: List[Mapping[str, Any]] = []
    kinds: Set[str] = set()
    filenames: Set[str] = set()
    for artifact in artifacts:
        if not isinstance(artifact, dict) or set(artifact) != required_row:
            raise ReleaseArtifactError("release manifest contains an invalid artifact row")
        filename = artifact.get("filename")
        kind = artifact.get("kind")
        size = artifact.get("size")
        sha256 = artifact.get("sha256")
        if (
            not isinstance(filename, str)
            or Path(filename).name != filename
            or filename in {"", ".", ".."}
        ):
            raise ReleaseArtifactError("artifact filename must be a safe basename")
        if kind not in {"wheel", "sdist"}:
            raise ReleaseArtifactError(f"invalid artifact kind for {filename}")
        if not isinstance(size, int) or isinstance(size, bool) or size < 1:
            raise ReleaseArtifactError(f"invalid artifact size for {filename}")
        if not isinstance(sha256, str) or not _SHA256_RE.fullmatch(sha256):
            raise ReleaseArtifactError(f"invalid artifact SHA-256 for {filename}")
        if not isinstance(artifact.get("embedded_name"), str) or not isinstance(
            artifact.get("embedded_version"), str
        ):
            raise ReleaseArtifactError(f"invalid embedded metadata for {filename}")
        if _normalize_project_name(artifact["embedded_name"]) != PROJECT_NAME:
            raise ReleaseArtifactError(f"embedded project name mismatch for {filename}")
        if artifact["embedded_version"] != payload["version"]:
            raise ReleaseArtifactError(f"embedded version mismatch for {filename}")
        expected_suffix = ".whl" if kind == "wheel" else ".tar.gz"
        if not filename.endswith(expected_suffix):
            raise ReleaseArtifactError(f"artifact filename and kind disagree for {filename}")
        kinds.add(kind)
        if filename in filenames:
            raise ReleaseArtifactError(f"duplicate artifact filename: {filename}")
        filenames.add(filename)
        rows.append(artifact)
    if kinds != {"wheel", "sdist"}:
        raise ReleaseArtifactError("release manifest must contain one wheel and one sdist")
    return rows


def verify_bundle(bundle_dir: Path, expected_tag: str, expected_source_sha: str) -> Mapping[str, Any]:
    """Verify manifest identity and every byte and metadata field in a bundle."""

    manifest_path = bundle_dir / MANIFEST_FILENAME
    dist_dir = bundle_dir / "dist"
    payload = _load_manifest(manifest_path)
    rows = _validated_manifest_rows(payload)
    normalized_sha = _validate_source_sha(expected_source_sha)
    if payload["tag"] != expected_tag:
        raise ReleaseArtifactError(
            f"release manifest tag {payload['tag']!r} does not match {expected_tag!r}"
        )
    if payload["source_sha"] != normalized_sha:
        raise ReleaseArtifactError("release manifest source SHA does not match the workflow source SHA")

    actual_paths = _distribution_paths(dist_dir)
    actual_names = {path.name for path in actual_paths}
    manifest_names = {str(row["filename"]) for row in rows}
    if actual_names != manifest_names:
        raise ReleaseArtifactError("manifest and dist directory contain different filenames")
    expected_version = str(payload["version"])
    for row in rows:
        path = dist_dir / str(row["filename"])
        actual = _artifact_record(path, expected_version)
        if actual != dict(row):
            raise ReleaseArtifactError(f"artifact does not match manifest: {path.name}")
    return payload


def _fetch_json(url: str, timeout: float) -> Mapping[str, Any]:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        content = response.read(MAX_INDEX_RESPONSE_BYTES + 1)
    if len(content) > MAX_INDEX_RESPONSE_BYTES:
        raise ReleaseArtifactError("TestPyPI JSON response exceeds the safety limit")
    try:
        payload = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReleaseArtifactError(f"invalid TestPyPI JSON response: {exc}") from exc
    if not isinstance(payload, dict):
        raise ReleaseArtifactError("TestPyPI JSON response root must be an object")
    return payload


def _verify_index_payload(payload: Mapping[str, Any], manifest: Mapping[str, Any]) -> None:
    info = payload.get("info")
    urls = payload.get("urls")
    if not isinstance(info, dict) or not isinstance(urls, list):
        raise ReleaseArtifactError("TestPyPI response does not contain info and urls")
    if _normalize_project_name(str(info.get("name", ""))) != PROJECT_NAME:
        raise ReleaseArtifactError("TestPyPI project name does not match the release manifest")
    if info.get("version") != manifest["version"]:
        raise ReleaseArtifactError("TestPyPI version does not match the release manifest")

    manifest_rows = {str(row["filename"]): row for row in _validated_manifest_rows(manifest)}
    index_rows: Dict[str, Mapping[str, Any]] = {}
    for row in urls:
        if not isinstance(row, dict) or not isinstance(row.get("filename"), str):
            raise ReleaseArtifactError("TestPyPI response contains an invalid file row")
        filename = row["filename"]
        if filename in index_rows:
            raise ReleaseArtifactError(f"TestPyPI response repeats filename {filename}")
        index_rows[filename] = row

    expected_names = set(manifest_rows)
    index_names = set(index_rows)
    extras = index_names - expected_names
    if extras:
        raise ReleaseArtifactError(
            "TestPyPI version contains unexpected files: " + ", ".join(sorted(extras))
        )
    missing = expected_names - index_names
    if missing:
        raise _RetryableIndexState(
            "TestPyPI is still missing files: " + ", ".join(sorted(missing))
        )

    package_types = {"wheel": "bdist_wheel", "sdist": "sdist"}
    for filename, expected in manifest_rows.items():
        actual = index_rows[filename]
        digests = actual.get("digests")
        if not isinstance(digests, dict) or digests.get("sha256") != expected["sha256"]:
            raise ReleaseArtifactError(f"TestPyPI SHA-256 mismatch for {filename}")
        if actual.get("size") != expected["size"]:
            raise ReleaseArtifactError(f"TestPyPI size mismatch for {filename}")
        if actual.get("packagetype") != package_types[expected["kind"]]:
            raise ReleaseArtifactError(f"TestPyPI package kind mismatch for {filename}")


def verify_testpypi(
    manifest_path: Path,
    attempts: int,
    delay: float,
    timeout: float,
    url_template: str = TESTPYPI_JSON_URL,
    fetcher: Callable[[str, float], Mapping[str, Any]] = _fetch_json,
    sleeper: Callable[[float], None] = time.sleep,
) -> Mapping[str, Any]:
    """Poll TestPyPI a bounded number of times, then verify its exact file set."""

    if attempts < 1:
        raise ReleaseArtifactError("attempts must be at least 1")
    if delay < 0 or timeout <= 0:
        raise ReleaseArtifactError("delay must be non-negative and timeout must be positive")
    manifest = _load_manifest(manifest_path)
    _validated_manifest_rows(manifest)
    url = url_template.format(project=PROJECT_NAME, version=manifest["version"])
    last_retryable: Optional[BaseException] = None
    for attempt in range(1, attempts + 1):
        try:
            payload = fetcher(url, timeout)
            _verify_index_payload(payload, manifest)
            return payload
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                raise ReleaseArtifactError(f"TestPyPI request failed with HTTP {exc.code}") from exc
            last_retryable = exc
        except _RetryableIndexState as exc:
            last_retryable = exc
        except urllib.error.URLError as exc:
            last_retryable = exc
        if attempt != attempts:
            sleeper(delay)
    raise ReleaseArtifactError(
        f"TestPyPI did not expose the exact release bundle after {attempts} attempts: {last_retryable}"
    )


def write_requirement(manifest_path: Path, output_path: Path) -> str:
    """Write a hash-locked requirement for the manifest's exact wheel."""

    manifest = _load_manifest(manifest_path)
    rows = _validated_manifest_rows(manifest)
    wheel = next(row for row in rows if row["kind"] == "wheel")
    requirement = f"{PROJECT_NAME}=={manifest['version']} --hash=sha256:{wheel['sha256']}\n"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_name(f".{output_path.name}.{os.getpid()}.tmp")
    temporary.write_text(requirement, encoding="utf-8")
    os.replace(temporary, output_path)
    return requirement


def verify_downloaded_wheel(manifest_path: Path, download_dir: Path) -> Path:
    """Prove that pip downloaded the wheel bound into the CI manifest."""

    manifest = _load_manifest(manifest_path)
    rows = _validated_manifest_rows(manifest)
    wheel_row = next(row for row in rows if row["kind"] == "wheel")
    paths = sorted(download_dir.iterdir()) if download_dir.is_dir() else []
    if len(paths) != 1 or not paths[0].is_file() or paths[0].is_symlink():
        raise ReleaseArtifactError("download directory must contain exactly one regular wheel")
    wheel = paths[0]
    if wheel.name != wheel_row["filename"]:
        raise ReleaseArtifactError("downloaded wheel filename does not match the release manifest")
    actual = _artifact_record(wheel, str(manifest["version"]))
    if actual != dict(wheel_row):
        raise ReleaseArtifactError("downloaded wheel does not match the release manifest")
    return wheel


def _version_not_found(output: str, requirement: str) -> bool:
    """Return whether pip reports that the exact release version is unavailable."""

    lowered = output.lower()
    if "packages do not match the hashes" in lowered or "expected sha256" in lowered:
        return False
    messages = (
        f"Could not find a version that satisfies the requirement {requirement}",
        f"No matching distribution found for {requirement}",
    )
    return any(message in output for message in messages)


def download_testpypi_wheel(
    manifest_path: Path,
    requirement_path: Path,
    download_dir: Path,
    attempts: int,
    delay: float,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    sleeper: Callable[[float], None] = time.sleep,
) -> Path:
    """Download and verify the exact TestPyPI wheel with bounded propagation retries.

    Only pip's exact-version-not-found result is retryable. Hash failures, other pip
    errors, and downloaded-wheel provenance mismatches fail immediately.
    """

    if attempts < 1:
        raise ReleaseArtifactError("attempts must be at least 1")
    if delay < 0:
        raise ReleaseArtifactError("delay must be non-negative")

    manifest = _load_manifest(manifest_path)
    rows = _validated_manifest_rows(manifest)
    requirement = f"{PROJECT_NAME}=={manifest['version']}"
    wheel = next(row for row in rows if row["kind"] == "wheel")
    expected_locked_requirement = (
        f"{requirement} --hash=sha256:{wheel['sha256']}\n"
    )
    try:
        locked_requirement = requirement_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ReleaseArtifactError(f"cannot read hash-locked requirement: {exc}") from exc
    if locked_requirement != expected_locked_requirement:
        raise ReleaseArtifactError("hash-locked requirement does not match the release manifest")
    if os.path.lexists(download_dir) and download_dir.is_symlink():
        raise ReleaseArtifactError("download directory must not be a symlink")
    if download_dir.exists() and not download_dir.is_dir():
        raise ReleaseArtifactError("download directory path is not a directory")
    if download_dir.exists() and any(download_dir.iterdir()):
        raise ReleaseArtifactError("download directory must be absent or empty")

    for attempt in range(1, attempts + 1):
        attempt_dir = download_dir.with_name(
            f".{download_dir.name}.attempt-{os.getpid()}-{attempt}"
        )
        if attempt_dir.exists():
            raise ReleaseArtifactError(f"temporary download directory already exists: {attempt_dir}")
        attempt_dir.mkdir(parents=True)
        result = runner(
            [
                sys.executable,
                "-m",
                "pip",
                "--isolated",
                "download",
                "--index-url",
                TESTPYPI_SIMPLE_URL,
                "--no-deps",
                "--only-binary=:all:",
                "--require-hashes",
                "--dest",
                str(attempt_dir),
                "--requirement",
                str(requirement_path),
            ],
            capture_output=True,
            text=True,
        )
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)

        if result.returncode == 0:
            wheel = verify_downloaded_wheel(manifest_path, attempt_dir)
            if download_dir.exists():
                download_dir.rmdir()
            os.replace(attempt_dir, download_dir)
            return download_dir / wheel.name

        output = f"{result.stdout}\n{result.stderr}"
        shutil.rmtree(attempt_dir)
        if not _version_not_found(output, requirement):
            raise ReleaseArtifactError(
                f"TestPyPI wheel download failed with non-retryable pip exit {result.returncode}"
            )
        if attempt != attempts:
            sleeper(delay)

    raise ReleaseArtifactError(
        f"TestPyPI Simple API did not expose {requirement} after {attempts} attempts"
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="create a manifest for a built dist directory")
    create.add_argument("--dist-dir", type=Path, required=True)
    create.add_argument("--manifest", type=Path, required=True)
    create.add_argument("--tag", required=True)
    create.add_argument("--source-sha", required=True)

    verify = subparsers.add_parser("verify", help="verify an immutable release bundle")
    verify.add_argument("--bundle-dir", type=Path, required=True)
    verify.add_argument("--tag", required=True)
    verify.add_argument("--source-sha", required=True)

    index = subparsers.add_parser("verify-testpypi", help="verify TestPyPI's exact file set")
    index.add_argument("--manifest", type=Path, required=True)
    index.add_argument("--attempts", type=int, default=12)
    index.add_argument("--delay", type=float, default=10.0)
    index.add_argument("--timeout", type=float, default=15.0)

    requirement = subparsers.add_parser(
        "write-requirement", help="write the manifest's hash-locked wheel requirement"
    )
    requirement.add_argument("--manifest", type=Path, required=True)
    requirement.add_argument("--output", type=Path, required=True)

    downloaded = subparsers.add_parser(
        "verify-downloaded-wheel", help="verify the wheel downloaded from TestPyPI"
    )
    downloaded.add_argument("--manifest", type=Path, required=True)
    downloaded.add_argument("--download-dir", type=Path, required=True)

    download = subparsers.add_parser(
        "download-testpypi-wheel",
        help="download and verify the exact TestPyPI wheel with bounded retries",
    )
    download.add_argument("--manifest", type=Path, required=True)
    download.add_argument("--requirement", type=Path, required=True)
    download.add_argument("--download-dir", type=Path, required=True)
    download.add_argument("--attempts", type=int, default=12)
    download.add_argument("--delay", type=float, default=10.0)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "create":
            create_manifest(args.dist_dir, args.manifest, args.tag, args.source_sha)
        elif args.command == "verify":
            verify_bundle(args.bundle_dir, args.tag, args.source_sha)
        elif args.command == "verify-testpypi":
            verify_testpypi(args.manifest, args.attempts, args.delay, args.timeout)
        elif args.command == "write-requirement":
            write_requirement(args.manifest, args.output)
        elif args.command == "verify-downloaded-wheel":
            verify_downloaded_wheel(args.manifest, args.download_dir)
        elif args.command == "download-testpypi-wheel":
            download_testpypi_wheel(
                args.manifest,
                args.requirement,
                args.download_dir,
                args.attempts,
                args.delay,
            )
        else:  # pragma: no cover - argparse rejects unknown commands
            raise AssertionError(args.command)
    except ReleaseArtifactError as exc:
        print(f"release artifact verification failed: {exc}", file=sys.stderr)
        return 1
    print(f"release artifact {args.command} verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
