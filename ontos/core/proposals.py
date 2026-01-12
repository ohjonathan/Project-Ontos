"""Proposal management helpers.

This module contains functions for finding and validating proposals.
"""

import os
import re
from datetime import datetime
from typing import List, Dict

from ontos.core.paths import get_proposals_dir, get_decision_history_path


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
    history_path = get_decision_history_path()
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
    proposals_dir = get_proposals_dir()
    if not proposals_dir or not os.path.exists(proposals_dir):
        return []

    # Get current ONTOS_VERSION for matching
    try:
        from ontos_config_defaults import ONTOS_VERSION
    except ImportError:
        ONTOS_VERSION = None

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
