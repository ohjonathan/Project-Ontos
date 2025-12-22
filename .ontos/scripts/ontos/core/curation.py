"""Curation level validation and scaffolding.

This module provides tiered validation for Ontos documents:
    Level 0 - Scaffold: Auto-generated, minimal validation
    Level 1 - Stub: User provides goal, relaxed validation
    Level 2 - Full: Complete Ontos document, full validation

STDLIB ONLY: This module uses only Python standard library (3.9+).
"""

from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import re


class CurationLevel(IntEnum):
    """Document curation levels."""
    SCAFFOLD = 0  # Auto-generated placeholder
    STUB = 1      # User provides goal only
    FULL = 2      # Complete Ontos document


@dataclass
class CurationInfo:
    """Curation status of a document."""
    level: CurationLevel
    explicit: bool       # True if curation_level field present in frontmatter
    issues: List[str]    # Validation issues at current level
    promotable: bool     # Can be promoted to next level
    promotion_blockers: List[str]  # What's needed for promotion


# Type heuristics for scaffolding (using word boundaries per Claude feedback)
TYPE_HEURISTICS: Dict[str, List[str]] = {
    'kernel': [
        r'\bmission\b', r'\bprinciple\b', r'\bvalues\b', r'\bphilosophy\b',
    ],
    'strategy': [
        r'\bstrategy\b', r'\broadmap\b', r'\bplan\b', r'\bgoal\b', r'\bobjective\b',
    ],
    'product': [
        r'\bfeature\b', r'\brequirement\b', r'\bspec\b', r'\buser.*story\b', r'\bflow\b',
    ],
    'atom': [
        r'\bapi\b', r'\bimplementation\b', r'\btechnical\b', r'\barchitecture\b',
        r'\bmodule\b', r'\bcomponent\b', r'\bservice\b',
    ],
    'log': [
        r'\bsession\b', r'\blog\b', r'\bdecision\b', r'\d{4}-\d{2}-\d{2}',
    ],
}


def infer_type_from_path(filepath: Path) -> str:
    """Infer document type from file path.
    
    Args:
        filepath: Path to the document file.
        
    Returns:
        Inferred type string or 'unknown'.
        
    Examples:
        >>> infer_type_from_path(Path("docs/kernel/mission.md"))
        'kernel'
        >>> infer_type_from_path(Path("logs/2025-01-01_session.md"))
        'log'
    """
    # Normalize path to lowercase and ensure we match both /dir/ and dir/
    path_str = '/' + str(filepath).lower().lstrip('/')
    
    # Check directory names (patterns now match consistently)
    if '/kernel/' in path_str or '/mission/' in path_str:
        return 'kernel'
    if '/strategy/' in path_str or '/roadmap/' in path_str:
        return 'strategy'
    if '/product/' in path_str or '/features/' in path_str:
        return 'product'
    if '/logs/' in path_str or '/sessions/' in path_str:
        return 'log'
    if '/atom/' in path_str or '/technical/' in path_str:
        return 'atom'
    
    return 'unknown'


def infer_type_from_content(content: str) -> str:
    """Infer document type from content keywords.
    
    Args:
        content: Document content text.
        
    Returns:
        Inferred type string or 'unknown'.
        
    Examples:
        >>> infer_type_from_content("This document describes the API implementation")
        'atom'
    """
    content_lower = content.lower()
    
    scores = {t: 0 for t in TYPE_HEURISTICS}
    
    for doc_type, patterns in TYPE_HEURISTICS.items():
        for pattern in patterns:
            matches = len(re.findall(pattern, content_lower))
            scores[doc_type] += matches
    
    # Return type with highest score, or 'unknown'
    best_type = max(scores, key=scores.get)
    if scores[best_type] > 0:
        return best_type
    
    return 'unknown'


def generate_id_from_path(filepath: Path) -> str:
    """Generate document ID from file path.
    
    Args:
        filepath: Path to generate ID from.
        
    Returns:
        Snake_case ID string.
        
    Examples:
        >>> generate_id_from_path(Path("docs/my-feature.md"))
        'my_feature'
        >>> generate_id_from_path(Path("2025-01-01_session.md"))
        'doc_2025_01_01_session'
    """
    # Remove extension
    name = filepath.stem
    
    # Convert to snake_case
    name = re.sub(r'[-\s]+', '_', name)
    name = re.sub(r'[^a-zA-Z0-9_]', '', name)
    name = name.lower()
    
    # Ensure valid identifier (not starting with digit)
    if name and name[0].isdigit():
        name = 'doc_' + name
    
    return name or 'unnamed_doc'


def detect_curation_level(frontmatter: Dict[str, Any]) -> CurationLevel:
    """Detect curation level from frontmatter.
    
    Priority:
    1. Explicit curation_level field
    2. Infer from status field
    3. Infer from field presence
    
    Args:
        frontmatter: Document frontmatter dictionary.
        
    Returns:
        CurationLevel enum value.
        
    Examples:
        >>> detect_curation_level({"id": "test", "curation_level": 0})
        <CurationLevel.SCAFFOLD: 0>
        >>> detect_curation_level({"id": "test", "status": "scaffold"})
        <CurationLevel.SCAFFOLD: 0>
        >>> detect_curation_level({"id": "test", "type": "atom", "depends_on": ["x"]})
        <CurationLevel.FULL: 2>
    """
    # Explicit level takes precedence
    if 'curation_level' in frontmatter:
        level = frontmatter['curation_level']
        if isinstance(level, int) and 0 <= level <= 2:
            return CurationLevel(level)
    
    # Infer from status
    status = frontmatter.get('status', '')
    if status == 'scaffold':
        return CurationLevel.SCAFFOLD
    if status == 'pending_curation':
        return CurationLevel.STUB
    
    # Infer from field presence
    has_depends = bool(frontmatter.get('depends_on'))
    has_concepts = bool(frontmatter.get('concepts'))
    doc_type = frontmatter.get('type', '')
    
    if doc_type == 'unknown':
        return CurationLevel.SCAFFOLD
    
    # Logs need concepts for Level 2
    if doc_type == 'log':
        if has_concepts:
            return CurationLevel.FULL
        return CurationLevel.STUB
    
    # Kernel types are full if they have basic fields
    if doc_type == 'kernel':
        return CurationLevel.FULL
    
    # Non-kernel types need depends_on for Level 2
    if has_depends:
        return CurationLevel.FULL
    
    return CurationLevel.STUB


def validate_at_level(
    frontmatter: Dict[str, Any],
    level: CurationLevel
) -> Tuple[bool, List[str]]:
    """Validate frontmatter at specified curation level.
    
    Args:
        frontmatter: Document frontmatter dictionary.
        level: CurationLevel to validate against.
        
    Returns:
        Tuple of (is_valid, list of issue messages).
        
    Examples:
        >>> validate_at_level({"id": "test", "type": "atom"}, CurationLevel.SCAFFOLD)
        (True, [])
        >>> validate_at_level({"type": "atom"}, CurationLevel.SCAFFOLD)
        (False, ['Missing required field: id'])
    """
    issues = []
    
    # Level 0: Minimal validation
    if level == CurationLevel.SCAFFOLD:
        if 'id' not in frontmatter:
            issues.append("Missing required field: id")
        if 'type' not in frontmatter:
            issues.append("Missing required field: type")
        return (len(issues) == 0, issues)
    
    # Level 1: Relaxed validation
    if level == CurationLevel.STUB:
        if 'id' not in frontmatter:
            issues.append("Missing required field: id")
        if 'type' not in frontmatter:
            issues.append("Missing required field: type")
        elif frontmatter['type'] == 'unknown':
            issues.append("Type must be specified (not 'unknown') at Level 1")
        if 'status' not in frontmatter:
            issues.append("Missing required field: status")
        return (len(issues) == 0, issues)
    
    # Level 2: Full validation
    if level == CurationLevel.FULL:
        if 'id' not in frontmatter:
            issues.append("Missing required field: id")
        if 'type' not in frontmatter:
            issues.append("Missing required field: type")
        if 'status' not in frontmatter:
            issues.append("Missing required field: status")
        
        doc_type = frontmatter.get('type', '')
        status = frontmatter.get('status', '')
        
        # Status validation - Level 2 should not have scaffold statuses
        if status in ('scaffold', 'pending_curation'):
            issues.append(f"Status '{status}' not allowed at Level 2")
        
        # depends_on required for non-kernel, non-log types
        if doc_type not in ('kernel', 'log') and not frontmatter.get('depends_on'):
            issues.append(f"Type '{doc_type}' requires depends_on at Level 2")
        
        # concepts required for logs
        if doc_type == 'log' and not frontmatter.get('concepts'):
            issues.append("Type 'log' requires concepts at Level 2")
        
        return (len(issues) == 0, issues)
    
    return (True, [])


def check_promotion_readiness(
    frontmatter: Dict[str, Any],
    current_level: CurationLevel
) -> Tuple[bool, List[str]]:
    """Check if document is ready to be promoted to next level.
    
    Args:
        frontmatter: Document frontmatter dictionary.
        current_level: Current curation level.
        
    Returns:
        Tuple of (is_promotable, list of blocking issues).
        
    Examples:
        >>> check_promotion_readiness({"id": "x"}, CurationLevel.FULL)
        (False, ['Already at maximum curation level'])
    """
    if current_level == CurationLevel.FULL:
        return (False, ["Already at maximum curation level"])
    
    next_level = CurationLevel(current_level + 1)
    is_valid, issues = validate_at_level(frontmatter, next_level)
    
    return (is_valid, issues if not is_valid else [])


def get_curation_info(frontmatter: Dict[str, Any]) -> CurationInfo:
    """Get comprehensive curation information for a document.
    
    Args:
        frontmatter: Document frontmatter dictionary.
        
    Returns:
        CurationInfo with level, validation status, and promotion info.
    """
    level = detect_curation_level(frontmatter)
    explicit = 'curation_level' in frontmatter
    is_valid, issues = validate_at_level(frontmatter, level)
    promotable, blockers = check_promotion_readiness(frontmatter, level)
    
    return CurationInfo(
        level=level,
        explicit=explicit,
        issues=issues,
        promotable=promotable,
        promotion_blockers=blockers
    )


def create_scaffold(
    filepath: Path,
    content: Optional[str] = None
) -> Dict[str, Any]:
    """Create Level 0 scaffold frontmatter for a file.
    
    Args:
        filepath: Path to the file being scaffolded.
        content: Optional file content (read from disk if not provided).
        
    Returns:
        Frontmatter dictionary for Level 0 scaffold.
        
    Examples:
        >>> create_scaffold(Path("docs/feature.md"))
        {'id': 'feature', 'type': 'unknown', 'status': 'scaffold', ...}
    """
    if content is None:
        content = filepath.read_text() if filepath.exists() else ""
    
    # Generate ID from path
    doc_id = generate_id_from_path(filepath)
    
    # Infer type
    doc_type = infer_type_from_path(filepath)
    if doc_type == 'unknown':
        doc_type = infer_type_from_content(content)
    
    return {
        'id': doc_id,
        'type': doc_type,
        'status': 'scaffold',
        'curation_level': 0,
        'ontos_schema': '2.2',
        'generated_by': 'ontos_scaffold',
    }


def create_stub(
    doc_id: str,
    doc_type: str,
    goal: str,
    depends_on: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Create Level 1 stub frontmatter.
    
    Args:
        doc_id: Document ID.
        doc_type: Document type.
        goal: Goal description for the document.
        depends_on: Optional list of dependency IDs.
        
    Returns:
        Frontmatter dictionary for Level 1 stub.
        
    Examples:
        >>> create_stub("my_feature", "product", "Document the checkout flow")
        {'id': 'my_feature', 'type': 'product', 'status': 'pending_curation', ...}
    """
    result = {
        'id': doc_id,
        'type': doc_type,
        'status': 'pending_curation',
        'curation_level': 1,
        'ontos_schema': '2.2',
        'goal': goal,
    }
    
    if depends_on:
        result['depends_on'] = depends_on
    
    return result


def promote_to_full(
    frontmatter: Dict[str, Any],
    depends_on: Optional[List[str]] = None,
    concepts: Optional[List[str]] = None
) -> Tuple[Dict[str, Any], Optional[str]]:
    """Promote document to Level 2 (Full).
    
    Args:
        frontmatter: Current frontmatter dictionary.
        depends_on: Dependencies to add (required for non-kernel).
        concepts: Concepts to add (required for logs).
        
    Returns:
        Tuple of (updated frontmatter, optional summary seeded from goal).
    """
    result = frontmatter.copy()
    
    # Extract goal for summary seeding (don't discard it)
    goal = result.get('goal', '')
    summary_seed = goal if goal else None
    
    # Update level
    result['curation_level'] = 2
    
    # Update status (promote from pending_curation)
    if result.get('status') in ('scaffold', 'pending_curation'):
        result['status'] = 'draft'
    
    # Add dependencies if provided
    if depends_on:
        result['depends_on'] = depends_on
    
    # Add concepts if provided
    if concepts:
        result['concepts'] = concepts
    
    return (result, summary_seed)


def load_ontosignore(repo_root: Path) -> List[str]:
    """Load patterns from .ontosignore file.
    
    Args:
        repo_root: Path to repository root.
        
    Returns:
        List of ignore patterns.
    """
    ignore_file = repo_root / ".ontosignore"
    if not ignore_file.exists():
        return []
    
    patterns = []
    for line in ignore_file.read_text().split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            patterns.append(line)
    return patterns


def should_ignore(filepath: Path, patterns: List[str]) -> bool:
    """Check if file matches any ignore pattern.
    
    Args:
        filepath: Path to check.
        patterns: List of ignore patterns.
        
    Returns:
        True if file should be ignored.
    """
    import fnmatch
    path_str = str(filepath)
    for pattern in patterns:
        if fnmatch.fnmatch(path_str, f"*{pattern}*"):
            return True
    return False


def level_marker(level: CurationLevel) -> str:
    """Get display marker for curation level.
    
    Args:
        level: CurationLevel enum value.
        
    Returns:
        String like "[L0]", "[L1]", or "[L2]".
    """
    return f"[L{level.value}]"
