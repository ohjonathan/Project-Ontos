"""Regression tests for the release artifact provenance gate."""

from __future__ import annotations

import io
import json
import tarfile
import urllib.error
import zipfile
from pathlib import Path

import pytest
import yaml

from scripts.release_artifacts import (
    MANIFEST_SCHEMA,
    ReleaseArtifactError,
    create_manifest,
    verify_bundle,
    verify_downloaded_wheel,
    verify_testpypi,
    write_requirement,
)


SOURCE_SHA = "a" * 40
TAG = "v5.0.1"
VERSION = "5.0.1"


def _metadata(name: str = "ontos", version: str = VERSION) -> bytes:
    return f"Metadata-Version: 2.4\nName: {name}\nVersion: {version}\n\n".encode()


def _build_wheel(dist_dir: Path, version: str = VERSION, name: str = "ontos") -> Path:
    path = dist_dir / f"ontos-{version}-py3-none-any.whl"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(f"ontos-{version}.dist-info/METADATA", _metadata(name, version))
        archive.writestr("ontos/__init__.py", f'__version__ = "{version}"\n')
    return path


def _build_sdist(dist_dir: Path, version: str = VERSION, name: str = "ontos") -> Path:
    path = dist_dir / f"ontos-{version}.tar.gz"
    payload = _metadata(name, version)
    with tarfile.open(path, "w:gz") as archive:
        info = tarfile.TarInfo(f"ontos-{version}/PKG-INFO")
        info.size = len(payload)
        archive.addfile(info, io.BytesIO(payload))
    return path


def _make_bundle(tmp_path: Path) -> tuple[Path, dict]:
    bundle = tmp_path / "release-bundle"
    dist = bundle / "dist"
    dist.mkdir(parents=True)
    _build_wheel(dist)
    _build_sdist(dist)
    manifest = create_manifest(dist, bundle / "release-manifest.json", TAG, SOURCE_SHA)
    return bundle, manifest


def _index_payload(manifest: dict) -> dict:
    package_types = {"wheel": "bdist_wheel", "sdist": "sdist"}
    return {
        "info": {"name": "ontos", "version": manifest["version"]},
        "urls": [
            {
                "filename": artifact["filename"],
                "packagetype": package_types[artifact["kind"]],
                "size": artifact["size"],
                "digests": {"sha256": artifact["sha256"]},
            }
            for artifact in manifest["artifacts"]
        ],
    }


def test_create_and_verify_bundle_binds_bytes_metadata_tag_and_source(tmp_path):
    bundle, manifest = _make_bundle(tmp_path)

    assert manifest == verify_bundle(bundle, TAG, SOURCE_SHA)
    assert manifest["schema"] == MANIFEST_SCHEMA
    assert manifest["tag"] == TAG
    assert manifest["version"] == VERSION
    assert manifest["source_sha"] == SOURCE_SHA
    assert [row["kind"] for row in manifest["artifacts"]] == ["wheel", "sdist"]
    assert {row["embedded_name"] for row in manifest["artifacts"]} == {"ontos"}
    assert {row["embedded_version"] for row in manifest["artifacts"]} == {VERSION}
    assert {path.name for path in (bundle / "dist").iterdir()} == {
        row["filename"] for row in manifest["artifacts"]
    }


def test_create_rejects_manifest_inside_dist_and_unexpected_files(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    _build_wheel(dist)
    _build_sdist(dist)

    with pytest.raises(ReleaseArtifactError, match="outside the dist"):
        create_manifest(dist, dist / "manifest.json", TAG, SOURCE_SHA)

    (dist / "notes.txt").write_text("not a release artifact", encoding="utf-8")
    with pytest.raises(ReleaseArtifactError, match="unexpected file"):
        create_manifest(dist, tmp_path / "manifest.json", TAG, SOURCE_SHA)


@pytest.mark.parametrize("kind", ["wheel", "sdist"])
def test_create_rejects_embedded_version_that_differs_from_tag(tmp_path, kind):
    dist = tmp_path / "dist"
    dist.mkdir()
    if kind == "wheel":
        _build_wheel(dist, version="9.9.9")
        _build_sdist(dist)
    else:
        _build_wheel(dist)
        _build_sdist(dist, version="9.9.9")

    with pytest.raises(ReleaseArtifactError, match="embeds version"):
        create_manifest(dist, tmp_path / "manifest.json", TAG, SOURCE_SHA)


def test_verify_bundle_fails_closed_for_tampered_bytes_or_identity(tmp_path):
    bundle, manifest = _make_bundle(tmp_path)
    wheel = bundle / "dist" / manifest["artifacts"][0]["filename"]
    with wheel.open("ab") as handle:
        handle.write(b"tampered")

    with pytest.raises(ReleaseArtifactError, match="does not match manifest"):
        verify_bundle(bundle, TAG, SOURCE_SHA)
    with pytest.raises(ReleaseArtifactError, match="tag"):
        verify_bundle(bundle, "v5.0.2", SOURCE_SHA)
    with pytest.raises(ReleaseArtifactError, match="source SHA"):
        verify_bundle(bundle, TAG, "b" * 40)


def test_verify_bundle_rejects_manifest_schema_drift(tmp_path):
    bundle, _ = _make_bundle(tmp_path)
    manifest_path = bundle / "release-manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["unbound"] = True
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ReleaseArtifactError, match="root schema"):
        verify_bundle(bundle, TAG, SOURCE_SHA)


def test_testpypi_verification_requires_exact_file_set_hashes_sizes_and_kinds(tmp_path):
    bundle, manifest = _make_bundle(tmp_path)
    payload = _index_payload(manifest)
    seen = []

    def fetcher(url, timeout):
        seen.append((url, timeout))
        return payload

    result = verify_testpypi(
        bundle / "release-manifest.json",
        attempts=1,
        delay=0,
        timeout=4,
        fetcher=fetcher,
    )

    assert result == payload
    assert seen == [(f"https://test.pypi.org/pypi/ontos/{VERSION}/json", 4)]

    for field, replacement, expected_error in (
        ("size", 1, "size mismatch"),
        ("packagetype", "sdist", "package kind mismatch"),
    ):
        altered = _index_payload(manifest)
        altered["urls"][0][field] = replacement
        with pytest.raises(ReleaseArtifactError, match=expected_error):
            verify_testpypi(
                bundle / "release-manifest.json",
                attempts=3,
                delay=0,
                timeout=1,
                fetcher=lambda _url, _timeout, value=altered: value,
            )

    altered = _index_payload(manifest)
    altered["urls"][0]["digests"]["sha256"] = "0" * 64
    with pytest.raises(ReleaseArtifactError, match="SHA-256 mismatch"):
        verify_testpypi(
            bundle / "release-manifest.json",
            attempts=3,
            delay=0,
            timeout=1,
            fetcher=lambda _url, _timeout: altered,
        )


def test_testpypi_verification_retries_only_missing_or_unavailable_state(tmp_path):
    bundle, manifest = _make_bundle(tmp_path)
    complete = _index_payload(manifest)
    partial = {**complete, "urls": complete["urls"][:1]}
    responses = [urllib.error.URLError("not propagated"), partial, complete]
    sleeps = []

    def fetcher(_url, _timeout):
        response = responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response

    verify_testpypi(
        bundle / "release-manifest.json",
        attempts=3,
        delay=0.25,
        timeout=1,
        fetcher=fetcher,
        sleeper=sleeps.append,
    )
    assert sleeps == [0.25, 0.25]

    partial = {**complete, "urls": complete["urls"][:1]}
    with pytest.raises(ReleaseArtifactError, match="after 2 attempts"):
        verify_testpypi(
            bundle / "release-manifest.json",
            attempts=2,
            delay=0,
            timeout=1,
            fetcher=lambda _url, _timeout: partial,
        )


def test_testpypi_verification_fails_immediately_for_an_extra_file(tmp_path):
    bundle, manifest = _make_bundle(tmp_path)
    payload = _index_payload(manifest)
    payload["urls"].append(
        {
            "filename": "unexpected.whl",
            "packagetype": "bdist_wheel",
            "size": 10,
            "digests": {"sha256": "0" * 64},
        }
    )
    calls = 0

    def fetcher(_url, _timeout):
        nonlocal calls
        calls += 1
        return payload

    with pytest.raises(ReleaseArtifactError, match="unexpected files"):
        verify_testpypi(
            bundle / "release-manifest.json",
            attempts=5,
            delay=0,
            timeout=1,
            fetcher=fetcher,
        )
    assert calls == 1


def test_hash_locked_requirement_and_downloaded_wheel_match_manifest(tmp_path):
    bundle, manifest = _make_bundle(tmp_path)
    requirement = tmp_path / "requirement.txt"
    text = write_requirement(bundle / "release-manifest.json", requirement)
    wheel_row = next(row for row in manifest["artifacts"] if row["kind"] == "wheel")

    assert text == f"ontos=={VERSION} --hash=sha256:{wheel_row['sha256']}\n"
    assert requirement.read_text(encoding="utf-8") == text

    downloaded = tmp_path / "downloaded"
    downloaded.mkdir()
    original = bundle / "dist" / wheel_row["filename"]
    target = downloaded / original.name
    target.write_bytes(original.read_bytes())
    assert verify_downloaded_wheel(bundle / "release-manifest.json", downloaded) == target

    with target.open("ab") as handle:
        handle.write(b"tampered")
    with pytest.raises(ReleaseArtifactError, match="does not match"):
        verify_downloaded_wheel(bundle / "release-manifest.json", downloaded)


def test_publish_workflow_uses_one_verified_bundle_without_index_fallback():
    workflow = Path(".github/workflows/publish.yml").read_text(encoding="utf-8")
    parsed_workflow = yaml.safe_load(workflow)
    jobs = parsed_workflow["jobs"]

    assert "release-bundle-${{ github.sha }}" in workflow
    assert "--manifest release-bundle/release-manifest.json" in workflow
    assert "--source-sha \"$SOURCE_SHA\"" in workflow
    assert workflow.count("scripts/release_artifacts.py verify \\") == 4
    assert "scripts/release_artifacts.py verify-testpypi" in workflow
    assert "scripts/release_artifacts.py verify-downloaded-wheel" in workflow
    assert "--index-url https://test.pypi.org/simple/" in workflow
    assert "https://pypi.org/simple" not in workflow
    assert "--extra-index-url" not in workflow
    assert "skip-existing" not in workflow
    assert "--no-deps" in workflow
    assert "--only-binary=:all:" in workflow
    assert "--require-hashes" in workflow
    assert workflow.count("-m pip --isolated") == 3
    assert "--no-index" in workflow
    assert "scripts/release-smoke-requirements.txt" in workflow
    assert '"$VERIFY_VENV/bin/python" -I -c' in workflow
    assert workflow.count("packages-dir: release-bundle/dist/") == 2
    assert jobs["publish-pypi"]["needs"] == "verify-testpypi"
    assert jobs["publish-testpypi"]["permissions"] == {
        "contents": "read",
        "id-token": "write",
    }
    assert jobs["publish-pypi"]["permissions"] == {
        "contents": "read",
        "id-token": "write",
    }
    assert parsed_workflow["permissions"] == {"contents": "read"}
    assert jobs["test"].get("permissions") is None
    assert jobs["build"].get("permissions") is None
    assert jobs["verify-testpypi"].get("permissions") is None
    for job_name in ("publish-testpypi", "publish-pypi"):
        step_names = [step["name"] for step in jobs[job_name]["steps"] if "name" in step]
        verify_step = next(index for index, name in enumerate(step_names) if name.startswith("Verify bundle"))
        publish_step = next(index for index, name in enumerate(step_names) if name.startswith("Publish"))
        assert verify_step < publish_step
    assert "cd \"$SMOKE_DIR\"" in workflow
    assert "unset PYTHONPATH" in workflow
    assert "ontos.__version__ == expected" in workflow
    assert 'importlib.metadata.version("ontos") == expected' in workflow
    assert 'test "$("$VERIFY_VENV/bin/ontos" --version)" = "ontos $TAG_VERSION"' in workflow


def test_release_smoke_dependencies_are_exact_and_hash_locked():
    requirements = Path("scripts/release-smoke-requirements.txt").read_text(
        encoding="utf-8"
    )

    assert "PyYAML==6.0.3" in requirements
    assert "tomli_w==1.2.0" in requirements
    assert ">=" not in requirements
    assert requirements.count("--hash=sha256:") == 2
