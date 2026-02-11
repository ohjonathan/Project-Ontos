"""Shared scan scope utilities for markdown document discovery."""

from __future__ import annotations

import warnings
from enum import Enum
from pathlib import Path
from typing import List, Optional

from ontos.core.config import OntosConfig
from ontos.io.files import scan_documents


class ScanScope(str, Enum):
    """Supported document scan scopes."""

    DOCS = "docs"
    LIBRARY = "library"


_VALID_SCOPES = {ScanScope.DOCS.value, ScanScope.LIBRARY.value}


def _normalize_scope_value(scope_value: Optional[str]) -> Optional[str]:
    if scope_value is None:
        return None
    return str(scope_value).strip().lower()


def resolve_scan_scope(
    cli_scope: Optional[str],
    config_default_scope: Optional[str],
) -> ScanScope:
    """Resolve effective scope with precedence: CLI > config > docs."""

    candidate = _normalize_scope_value(cli_scope)
    if candidate is None:
        candidate = _normalize_scope_value(config_default_scope)
    if candidate is None:
        candidate = ScanScope.DOCS.value

    if candidate not in _VALID_SCOPES:
        warnings.warn(
            (
                f"Invalid scanning.default_scope '{candidate}'. "
                "Falling back to 'docs'."
            ),
            RuntimeWarning,
            stacklevel=2,
        )
        return ScanScope.DOCS

    return ScanScope(candidate)


def build_scope_roots(
    repo_root: Path,
    config: OntosConfig,
    scope: ScanScope,
) -> List[Path]:
    """Build root directories for the selected scope."""

    roots: List[Path] = [repo_root / config.paths.docs_dir]
    roots.extend(repo_root / path for path in config.scanning.scan_paths)

    if scope == ScanScope.LIBRARY:
        roots.append(repo_root / ".ontos-internal")

    deduped: List[Path] = []
    seen = set()
    for root in roots:
        resolved = root.resolve()
        if resolved in seen:
            continue
        deduped.append(root)
        seen.add(resolved)

    return deduped


def collect_scoped_documents(
    repo_root: Path,
    config: OntosConfig,
    scope: ScanScope,
    *,
    base_skip_patterns: Optional[List[str]] = None,
    extra_skip_patterns: Optional[List[str]] = None,
    explicit_dirs: Optional[List[Path]] = None,
) -> List[Path]:
    """Collect markdown documents for a scope or explicit directory override."""

    if explicit_dirs:
        roots = []
        for directory in explicit_dirs:
            roots.append(directory if directory.is_absolute() else repo_root / directory)
    else:
        roots = build_scope_roots(repo_root, config, scope)

    skip_patterns: List[str] = []
    if base_skip_patterns:
        skip_patterns.extend(base_skip_patterns)
    if extra_skip_patterns:
        skip_patterns.extend(extra_skip_patterns)

    return scan_documents(roots, skip_patterns=skip_patterns)
