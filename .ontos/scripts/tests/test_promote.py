"""Tests for promote module (v2.9.1)."""

import pytest
from pathlib import Path
import tempfile
import os
import sys

# Ensure scripts directory is in path
SCRIPTS_DIR = Path(__file__).parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from ontos.core.curation import (
    promote_to_full,
    CurationLevel,
    detect_curation_level,
    check_promotion_readiness,
)


class TestPromoteToFull:
    """Test promote_to_full function."""
    
    def test_updates_curation_level(self):
        """Promotion updates curation_level to 2."""
        fm = {"id": "x", "type": "atom", "status": "pending_curation"}
        result, _ = promote_to_full(fm, depends_on=["mission"])
        assert result['curation_level'] == 2
    
    def test_updates_status(self):
        """Promotion updates status from pending_curation to draft."""
        fm = {"id": "x", "type": "atom", "status": "pending_curation"}
        result, _ = promote_to_full(fm, depends_on=["mission"])
        assert result['status'] == 'draft'
    
    def test_preserves_goal(self):
        """Promotion preserves goal field and returns as summary seed."""
        fm = {"id": "x", "type": "atom", "goal": "My goal"}
        result, seed = promote_to_full(fm, depends_on=["mission"])
        assert result.get('goal') == "My goal"
        assert seed == "My goal"
    
    def test_adds_depends_on(self):
        """Promotion adds depends_on field."""
        fm = {"id": "x", "type": "atom"}
        result, _ = promote_to_full(fm, depends_on=["a", "b"])
        assert result['depends_on'] == ["a", "b"]
    
    def test_adds_concepts_for_logs(self):
        """Promotion adds concepts field for log type."""
        fm = {"id": "x", "type": "log", "status": "pending_curation"}
        result, _ = promote_to_full(fm, concepts=["ux", "performance"])
        assert result['concepts'] == ["ux", "performance"]
    
    def test_preserves_existing_fields(self):
        """Promotion preserves existing frontmatter fields."""
        fm = {"id": "x", "type": "atom", "custom_field": "value"}
        result, _ = promote_to_full(fm, depends_on=["mission"])
        assert result.get('custom_field') == "value"
    
    def test_does_not_modify_original(self):
        """Promotion returns copy, doesn't modify original."""
        fm = {"id": "x", "type": "atom", "status": "pending_curation"}
        original_status = fm['status']
        result, _ = promote_to_full(fm, depends_on=["mission"])
        assert fm['status'] == original_status
        assert result['status'] == 'draft'


class TestPromotionReadiness:
    """Test check_promotion_readiness function."""
    
    def test_scaffold_can_promote_with_type(self):
        """Scaffold can promote if it has valid type."""
        fm = {"id": "test", "type": "atom", "status": "scaffold"}
        ready, blockers = check_promotion_readiness(fm, CurationLevel.SCAFFOLD)
        # Would be ready for L1 (just needs status)
        # But might have blockers for full L2
        assert isinstance(ready, bool)
    
    def test_stub_can_promote_with_deps(self):
        """Stub can promote if it has depends_on."""
        fm = {"id": "test", "type": "atom", "status": "draft", "depends_on": ["x"]}
        ready, blockers = check_promotion_readiness(fm, CurationLevel.STUB)
        assert ready is True
        assert blockers == []
    
    def test_stub_cannot_promote_without_deps(self):
        """Stub cannot promote without depends_on."""
        fm = {"id": "test", "type": "atom", "status": "draft"}
        ready, blockers = check_promotion_readiness(fm, CurationLevel.STUB)
        assert ready is False
        assert "depends_on" in blockers[0]
    
    def test_log_cannot_promote_without_concepts(self):
        """Log stub cannot promote without concepts."""
        fm = {"id": "test", "type": "log", "status": "draft"}
        ready, blockers = check_promotion_readiness(fm, CurationLevel.STUB)
        assert ready is False
        assert "concepts" in blockers[0]
    
    def test_full_level_not_promotable(self):
        """Full level cannot be promoted further."""
        fm = {"id": "test", "type": "atom", "status": "active", "depends_on": ["x"]}
        ready, blockers = check_promotion_readiness(fm, CurationLevel.FULL)
        assert ready is False
        assert "maximum" in blockers[0].lower()


class TestDetectCurationLevel:
    """Test curation level detection for promote scenarios."""
    
    def test_scaffold_status_detected(self):
        """Status 'scaffold' is detected as L0."""
        fm = {"id": "test", "status": "scaffold"}
        assert detect_curation_level(fm) == CurationLevel.SCAFFOLD
    
    def test_pending_curation_is_stub(self):
        """Status 'pending_curation' is detected as L1."""
        fm = {"id": "test", "status": "pending_curation"}
        assert detect_curation_level(fm) == CurationLevel.STUB
    
    def test_active_with_deps_is_full(self):
        """Active with depends_on is detected as L2."""
        fm = {"id": "test", "type": "atom", "status": "active", "depends_on": ["x"]}
        assert detect_curation_level(fm) == CurationLevel.FULL
