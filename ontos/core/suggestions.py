"""
Impact and concept suggestion algorithms for session logs.

Extracted from ontos_end_session.py during Phase 2 decomposition.

Phase 2 Decomposition - Created from Phase2-Implementation-Spec.md Section 4.4
"""

from __future__ import annotations
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from difflib import SequenceMatcher

from ontos.core.types import DocumentData


def load_document_index(context_map_content: str) -> Dict[str, str]:
    """Parse context map to build filepath -> doc_id mapping.

    Args:
        context_map_content: Content of Ontos_Context_Map.md

    Returns:
        Dictionary mapping filepath to doc_id
    """
    index: Dict[str, str] = {}

    # Parse table rows from context map
    # Format: | path/to/file.md | doc_id | type | status |
    for line in context_map_content.split('\n'):
        if '|' not in line or line.strip().startswith('|--'):
            continue
        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 3:
            filepath = parts[1]
            doc_id = parts[2]
            if filepath and doc_id and not filepath.startswith('Path'):
                index[filepath] = doc_id

    return index


def load_common_concepts(context_map_content: str) -> Set[str]:
    """Load common concepts from context map.

    Parses the ## Common Concepts section of the context map.

    Args:
        context_map_content: Content of Ontos_Context_Map.md

    Returns:
        Set of known concept strings
    """
    concepts: Set[str] = set()
    in_concepts_section = False

    for line in context_map_content.split('\n'):
        if line.startswith('## Common Concepts'):
            in_concepts_section = True
            continue
        if in_concepts_section:
            if line.startswith('## '):
                break  # Next section
            # Parse concept entries (typically comma-separated or bullet points)
            if line.strip().startswith('-'):
                concept = line.strip().lstrip('-').strip()
                if concept:
                    concepts.add(concept)
            elif ',' in line:
                for concept in line.split(','):
                    concept = concept.strip()
                    if concept:
                        concepts.add(concept)

    return concepts


def suggest_impacts(
    changed_files: List[str],
    document_index: Dict[str, str],
    commit_messages: List[str]
) -> List[str]:
    """Suggest document IDs that may be impacted by changes.

    Analyzes changed files and commit messages to identify related documents.

    Args:
        changed_files: List of file paths that changed
        document_index: Mapping of filepath to doc_id
        commit_messages: List of commit messages

    Returns:
        List of suggested doc_ids
    """
    suggestions: Set[str] = set()

    # Direct matches: changed file is a documented file
    for filepath in changed_files:
        if filepath in document_index:
            suggestions.add(document_index[filepath])

    # Indirect matches: filename appears in doc_id
    for filepath in changed_files:
        basename = os.path.basename(filepath)
        name_without_ext = os.path.splitext(basename)[0]

        for doc_id in document_index.values():
            # Check if file name appears in doc_id
            if name_without_ext.lower() in doc_id.lower():
                suggestions.add(doc_id)

    # Commit message analysis: extract potential doc references
    doc_id_pattern = re.compile(r'\b([a-z][a-z0-9_]+(?:_[a-z0-9]+)*)\b')
    all_doc_ids = set(document_index.values())

    for message in commit_messages:
        matches = doc_id_pattern.findall(message.lower())
        for match in matches:
            if match in all_doc_ids:
                suggestions.add(match)

    return sorted(suggestions)


def validate_concepts(
    concepts: List[str],
    known_concepts: Set[str]
) -> Tuple[List[str], List[str]]:
    """Validate concepts against known vocabulary.

    Args:
        concepts: List of concepts to validate
        known_concepts: Set of valid concept strings

    Returns:
        Tuple of (valid_concepts, unknown_concepts)
    """
    valid = []
    unknown = []

    for concept in concepts:
        if concept in known_concepts:
            valid.append(concept)
        else:
            unknown.append(concept)

    return valid, unknown


def extract_doc_ids_from_text(text: str, valid_ids: Set[str]) -> List[str]:
    """Extract document IDs mentioned in text.

    Args:
        text: Text to search (e.g., commit message, log content)
        valid_ids: Set of valid document IDs to match against

    Returns:
        List of matches found in text
    """
    found = []
    text_lower = text.lower()
    
    for doc_id in valid_ids:
        if doc_id.lower() in text_lower:
            found.append(doc_id)
    
    return found


def suggest_candidates_for_broken_ref(
    broken_ref: str,
    all_docs: Dict[str, DocumentData],
    referencing_doc: Optional[DocumentData] = None,
    threshold: float = 0.5
) -> List[Tuple[str, float, str]]:
    """
    Generate candidate suggestions for a broken reference.

    Uses three matching strategies:
    1. Substring match (broken_ref appears in doc_id) -> 0.85 confidence
    2. Alias match (broken_ref matches doc aliases) -> 0.85 confidence
    3. Levenshtein distance (fuzzy string similarity) -> actual ratio as confidence

    Args:
        broken_ref: The invalid document ID reference
        all_docs: Dictionary mapping doc_id to DocumentData
        referencing_doc: The DocumentData object containing the broken ref (optional)
        threshold: Minimum similarity ratio for fuzzy matching (0.0-1.0)
                   Note: 0.5 is baseline for fuzzy; 0.85 is fixed for substring/alias

    Returns:
        List of (doc_id, confidence_score, reason) tuples,
        sorted by confidence descending (then alphabetically for ties), max 3 results
    """
    if not broken_ref or not broken_ref.strip():
        return []
        
    candidates = []
    broken_lower = broken_ref.lower()

    for doc_id, doc in all_docs.items():
        doc_id_lower = doc_id.lower()

        # Strategy 1: Substring match (high confidence: 0.85)
        # broken_ref is contained in doc_id OR doc_id is contained in broken_ref
        if broken_lower in doc_id_lower or doc_id_lower in broken_lower:
            candidates.append((doc_id, 0.85, "substring match"))
            continue

        # Strategy 2: Alias match (high confidence: 0.85)
        aliases = doc.aliases if hasattr(doc, 'aliases') else []
        if aliases and any(broken_lower in alias.lower() for alias in aliases):
            candidates.append((doc_id, 0.85, "alias match"))
            continue

        # Strategy 3: Levenshtein distance via SequenceMatcher (variable confidence)
        ratio = SequenceMatcher(None, broken_lower, doc_id_lower).ratio()
        if ratio >= threshold:
            candidates.append((doc_id, ratio, f"similarity: {ratio:.0%}"))

    # v1.1: Sort by confidence descending, then alphabetically by doc_id for deterministic ties
    return sorted(candidates, key=lambda x: (-x[1], x[0]))[:3]
