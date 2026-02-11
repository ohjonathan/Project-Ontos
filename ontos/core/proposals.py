"""Proposal management helpers.

This module contains functions for finding and validating proposals.
"""

import os
import re
from datetime import datetime
from typing import List, Dict

from ontos.core.paths import resolve_config, _warn_deprecated

try:
    from ontos import __version__ as ONTOS_VERSION
except ImportError:
    ONTOS_VERSION = None

_TABLE_SEPARATOR_RE = re.compile(r"^\|\s*:?-{3,}\s*(\|\s*:?-{3,}\s*)+\|?$")


def _find_runtime_project_root(start_path: str = None) -> str:
    """Find project root relative to current execution context."""
    current = os.path.abspath(start_path or os.getcwd())
    while True:
        if (
            os.path.exists(os.path.join(current, ".ontos.toml"))
            or os.path.exists(os.path.join(current, ".ontos"))
            or os.path.exists(os.path.join(current, ".ontos-internal"))
            or os.path.exists(os.path.join(current, ".git"))
        ):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            return os.path.abspath(start_path or os.getcwd())
        current = parent


def _resolve_runtime_docs_dir(root: str) -> tuple:
    """Resolve docs directory from runtime root + config."""
    docs_dir_cfg = None
    try:
        from pathlib import Path
        from ontos.io.config import load_project_config

        config = load_project_config(repo_root=Path(root))
        docs_dir_cfg = str(config.paths.docs_dir).strip()
    except Exception:
        docs_dir_cfg = str(resolve_config("DOCS_DIR", "docs")).strip()

    if os.path.isabs(docs_dir_cfg):
        return docs_dir_cfg, docs_dir_cfg
    return os.path.join(root, docs_dir_cfg), docs_dir_cfg


def _resolve_runtime_proposals_dir(root: str) -> str:
    """Resolve proposals directory relative to runtime root."""
    if os.path.exists(os.path.join(root, ".ontos-internal")):
        return os.path.join(root, ".ontos-internal", "strategy", "proposals")
    docs_dir, _ = _resolve_runtime_docs_dir(root)
    return os.path.join(docs_dir, "strategy", "proposals")


def _resolve_runtime_decision_history_path(root: str) -> str:
    """Resolve decision_history path relative to runtime root."""
    if os.path.exists(os.path.join(root, ".ontos-internal")):
        return os.path.join(root, ".ontos-internal", "reference", "decision_history.md")

    docs_dir, docs_dir_cfg = _resolve_runtime_docs_dir(root)
    new_path = os.path.join(docs_dir, "strategy", "decision_history.md")
    if os.path.exists(new_path):
        return new_path

    old_path = os.path.join(docs_dir, "decision_history.md")
    if os.path.exists(old_path):
        _warn_deprecated(
            f"{docs_dir_cfg}/decision_history.md",
            f"{docs_dir_cfg}/strategy/decision_history.md",
        )
        return old_path

    return new_path


def load_decision_history_entries() -> dict:
    """Load decision_history.md entries for validation.
    
    Parses the decision history ledger to enable validation that 
    rejected/approved proposals are properly recorded.
    
    v2.6.1: Improved parsing for deterministic matching by slug and archive path.
    
    Returns:
        Dict with:
          - 'archive_paths': dict mapping archive_path -> slug
          - 'slugs': set of all slugs in ledger
          - 'rejected_slugs': set of slugs with REJECTED in outcome
          - 'approved_slugs': set of slugs with APPROVED in outcome
          - 'outcomes': dict mapping slug -> full outcome text
    """
    root = _find_runtime_project_root()
    history_path = _resolve_runtime_decision_history_path(root)
    entries = {
        'archive_paths': {},  # Now a dict: path -> slug
        'slugs': set(),
        'rejected_slugs': set(),
        'approved_slugs': set(),
        'outcomes': {}
    }
    
    if os.path.exists(history_path):
        with open(history_path, 'r', encoding='utf-8') as f:
            for line in f:
                # Parse table rows: | date | slug | event | outcome | impacted | archive_path |
                if line.startswith('|') and not line.startswith('|:') and not line.startswith('| Date'):
                    if _TABLE_SEPARATOR_RE.match(line.strip()):
                        continue
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 7:
                        slug = parts[2]
                        outcome = parts[4]
                        archive_path = parts[6].strip('`')  # Remove backticks
                        
                        if slug:
                            entries['slugs'].add(slug)
                            entries['outcomes'][slug] = outcome
                            
                            # Deterministic outcome classification
                            outcome_upper = outcome.upper()
                            if 'REJECTED' in outcome_upper:
                                entries['rejected_slugs'].add(slug)
                            if 'APPROVED' in outcome_upper:
                                entries['approved_slugs'].add(slug)
                        
                        if archive_path:
                            entries['archive_paths'][archive_path] = slug
    return entries


def find_draft_proposals() -> List[Dict]:
    """Find all draft proposals that may need review.

    v2.6.1: Used by Maintain Ontos to prompt for graduation.

    Returns:
        List of dicts with 'id', 'filepath', 'version', 'age_days'.
    """
    root = _find_runtime_project_root()
    proposals_dir = _resolve_runtime_proposals_dir(root)
    if not proposals_dir or not os.path.exists(proposals_dir):
        return []

    draft_proposals = []

    for root, dirs, files in os.walk(proposals_dir):
        for file in files:
            if not file.endswith('.md'):
                continue

            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read(1000)  # Just need frontmatter

                # Check if it's a draft
                if 'status: draft' not in content:
                    continue

                # Extract ID
                id_match = re.search(r'^id:\s*(.+)$', content, re.MULTILINE)
                if not id_match:
                    continue

                doc_id = id_match.group(1).strip()

                # Extract version from filepath or ID (e.g., v2.6, v2_6)
                version_match = re.search(r'v?(\d+)[._-](\d+)', filepath + doc_id)
                version = f'{version_match.group(1)}.{version_match.group(2)}' if version_match else None

                # Get file age
                mtime = os.path.getmtime(filepath)
                age_days = (datetime.now().timestamp() - mtime) / 86400

                # Check if version matches current ONTOS_VERSION
                version_match_current = False
                if version and ONTOS_VERSION:
                    version_match_current = ONTOS_VERSION.startswith(version)

                draft_proposals.append({
                    'id': doc_id,
                    'filepath': filepath,
                    'version': version,
                    'age_days': int(age_days),
                    'version_match': version_match_current,
                })

            except (IOError, OSError):
                continue

    # Sort by version match (True first), then by age
    draft_proposals.sort(key=lambda x: (not x['version_match'], -x['age_days']))

    return draft_proposals
