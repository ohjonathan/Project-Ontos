"""Portfolio project discovery utilities."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import sys
from typing import Any

from ontos.io.snapshot import create_snapshot

__all__ = [
    "ProjectEntry",
    "RegistryRecord",
    "slugify",
    "discover_projects",
    "load_registry_records",
    "allocate_slug",
]


@dataclass(frozen=True)
class ProjectEntry:
    slug: str
    path: Path
    status: str
    has_ontos: bool
    has_readme: bool
    doc_count: int
    tags: list[str]
    metadata: dict[str, Any]


@dataclass(frozen=True)
class RegistryRecord:
    path: Path
    status: str | None
    tags: list[str]
    metadata: dict[str, Any]
    has_ontos_raw: object | None


def slugify(directory_name: str) -> str:
    """Convert a directory name to a URL-safe workspace slug."""
    slug = directory_name.lower().replace(".", "-").replace(" ", "-")
    slug = re.sub(r"[^a-z0-9-]+", "-", slug)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug or "workspace"


def discover_projects(
    scan_roots: list[Path],
    exclude: list[str],
    registry_path: Path | None,
) -> list[ProjectEntry]:
    """Discover candidate workspaces across scan roots and registry entries."""
    exclude_prefixes, exclude_patterns = _compile_excludes(exclude)
    registry_records = load_registry_records(registry_path)

    discovered_paths: set[Path] = set()
    for scan_root in scan_roots:
        root = scan_root.expanduser().resolve(strict=False)
        if not root.is_dir():
            continue
        for candidate in sorted(root.iterdir()):
            if not candidate.is_dir():
                continue
            resolved = candidate.resolve(strict=False)
            if _is_excluded(resolved, exclude_prefixes, exclude_patterns):
                continue
            if (resolved / ".git").is_dir():
                discovered_paths.add(resolved)

    for registry_record in registry_records:
        record_path = registry_record.path
        if not record_path.exists() or not record_path.is_dir():
            continue
        if _is_excluded(record_path, exclude_prefixes, exclude_patterns):
            continue
        discovered_paths.add(record_path)

    records_by_path = {record.path: record for record in registry_records}
    used_slugs: dict[str, int] = {}
    results: list[ProjectEntry] = []

    for path in sorted(discovered_paths):
        registry_record = records_by_path.get(path)
        has_ontos = (path / ".ontos.toml").exists()
        has_readme = (path / "README.md").exists() or (path / "readme.md").exists()
        doc_count = _count_documents(path, has_ontos)

        registry_tags = registry_record.tags if registry_record else []
        registry_metadata = dict(registry_record.metadata) if registry_record else {}
        status = _classify_status(
            has_ontos=has_ontos,
            has_readme=has_readme,
            doc_count=doc_count,
            metadata=registry_metadata,
        )
        if registry_record and registry_record.status:
            status = registry_record.status

        base_slug = slugify(path.name)
        slug = allocate_slug(base_slug, used_slugs)
        if slug != base_slug:
            print(
                f"[ontos] slug collision: '{base_slug}' -> '{slug}' for workspace '{path}'",
                file=sys.stderr,
            )
        results.append(
            ProjectEntry(
                slug=slug,
                path=path,
                status=status,
                has_ontos=has_ontos,
                has_readme=has_readme,
                doc_count=doc_count,
                tags=registry_tags,
                metadata=registry_metadata,
            )
        )

    return sorted(results, key=lambda item: item.slug)


def _compile_excludes(exclude: list[str]) -> tuple[list[Path], list[str]]:
    prefixes: list[Path] = []
    patterns: list[str] = []
    for raw in exclude:
        text = raw.strip()
        if not text:
            continue
        expanded = Path(text).expanduser()
        if expanded.is_absolute():
            prefixes.append(expanded.resolve(strict=False))
        patterns.append(text)
    return prefixes, patterns


def _is_excluded(path: Path, exclude_prefixes: list[Path], exclude_patterns: list[str]) -> bool:
    resolved = path.resolve(strict=False)
    for prefix in exclude_prefixes:
        if resolved == prefix or resolved.is_relative_to(prefix):
            return True

    posix_path = resolved.as_posix()
    for pattern in exclude_patterns:
        expanded = str(Path(pattern).expanduser())
        if not expanded:
            continue
        if expanded in posix_path:
            return True
    return False


def load_registry_records(
    registry_path: Path | None,
    *,
    tolerate_errors: bool = True,
) -> list[RegistryRecord]:
    if registry_path is None:
        return []
    expanded = registry_path.expanduser().resolve(strict=False)
    if not expanded.exists():
        return []

    try:
        raw = json.loads(expanded.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        if tolerate_errors:
            return []
        raise

    registry_root = _registry_root(raw, expanded.parent)
    items = _extract_registry_items(raw)
    results: list[RegistryRecord] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        path_text = _first_string(item, "path", "workspace", "root", "repo_root", "repoPath")
        if not path_text:
            continue
        path = Path(path_text).expanduser()
        if not path.is_absolute():
            path = (registry_root / path).resolve(strict=False)
        else:
            path = path.resolve(strict=False)

        status = item.get("status")
        tags = item.get("tags")
        metadata = item.get("metadata")
        archived = item.get("archived")

        normalized_tags = [tag for tag in tags if isinstance(tag, str)] if isinstance(tags, list) else []
        normalized_metadata = metadata if isinstance(metadata, dict) else {}
        if isinstance(archived, bool):
            normalized_metadata.setdefault("archived", archived)

        normalized_status: str | None = status if isinstance(status, str) else None
        if normalized_status is None and bool(normalized_metadata.get("archived")):
            normalized_status = "archived"

        results.append(
            RegistryRecord(
                path=path,
                status=normalized_status,
                tags=normalized_tags,
                metadata=normalized_metadata,
                has_ontos_raw=item.get("has_ontos") if "has_ontos" in item else None,
            )
        )
    return results


def _load_registry_records(registry_path: Path | None) -> list[RegistryRecord]:
    """Backward-compatible alias for internal callers."""
    return load_registry_records(registry_path)


def _registry_root(raw: object, default_root: Path) -> Path:
    if isinstance(raw, dict):
        dev_root = raw.get("dev_root")
        if isinstance(dev_root, str) and dev_root.strip():
            return Path(dev_root).expanduser().resolve(strict=False)
    return default_root.resolve(strict=False)


def _extract_registry_items(raw: object) -> list[object]:
    if isinstance(raw, list):
        return raw

    if isinstance(raw, dict):
        for key in ("projects", "workspaces", "entries", "items"):
            value = raw.get(key)
            if isinstance(value, list):
                return value

        # m-1: the dict fallback previously walked every key at the top
        # level, which meant any top-level metadata dict (for example a
        # nested ``metadata`` block, schema info, or a generator note that
        # happened to be a mapping) was silently coerced into a project
        # entry. Restrict this path to keys whose values resolve to
        # project-shaped payloads (path-like field present) and explicitly
        # skip reserved top-level metadata names.
        dict_items: list[object] = []
        for slug, payload in raw.items():
            if slug in _REGISTRY_RESERVED_KEYS:
                continue
            if not isinstance(payload, dict):
                continue
            if not _looks_like_project_payload(payload):
                continue
            merged = dict(payload)
            merged.setdefault("slug", slug)
            dict_items.append(merged)
        return dict_items

    return []


_REGISTRY_RESERVED_KEYS: frozenset[str] = frozenset(
    {
        "dev_root",
        "generated_at",
        "generator",
        "metadata",
        "projects",
        "schema",
        "schema_version",
        "version",
        "workspaces",
        "entries",
        "items",
    }
)

_REGISTRY_PROJECT_PATH_KEYS: tuple[str, ...] = (
    "path",
    "workspace",
    "root",
    "repo_root",
    "repoPath",
)


def _looks_like_project_payload(payload: dict[str, Any]) -> bool:
    """True when the dict payload carries a path-like field identifying a project."""
    return any(
        isinstance(payload.get(key), str) and payload.get(key)
        for key in _REGISTRY_PROJECT_PATH_KEYS
    )


def _first_string(item: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _count_documents(workspace_root: Path, has_ontos: bool) -> int:
    if not has_ontos:
        return 0

    try:
        snapshot = create_snapshot(
            root=workspace_root,
            include_content=False,
            filters=None,
            git_commit_provider=None,
            scope=None,
        )
        return len(snapshot.documents)
    except Exception:
        docs_dir = workspace_root / "docs"
        if not docs_dir.is_dir():
            return 0
        return sum(1 for path in docs_dir.rglob("*.md") if path.is_file() and not path.name.startswith("_"))


def _classify_status(
    *,
    has_ontos: bool,
    has_readme: bool,
    doc_count: int,
    metadata: dict[str, Any],
) -> str:
    if bool(metadata.get("archived")):
        return "archived"
    if has_ontos and doc_count >= 5:
        return "documented"
    if (has_readme and not has_ontos) or (has_ontos and doc_count < 5):
        return "partial"
    return "undocumented"


def allocate_slug(base_slug: str, used_slugs: dict[str, int]) -> str:
    if base_slug not in used_slugs:
        used_slugs[base_slug] = 1
        return base_slug
    used_slugs[base_slug] += 1
    return f"{base_slug}-{used_slugs[base_slug]}"


def _allocate_slug(base_slug: str, used_slugs: dict[str, int]) -> str:
    """Backward-compatible alias for internal callers."""
    return allocate_slug(base_slug, used_slugs)
