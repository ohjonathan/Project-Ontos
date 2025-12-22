"""Tests for curation module (v2.9.1)."""

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
    CurationLevel,
    CurationInfo,
    infer_type_from_path,
    infer_type_from_content,
    generate_id_from_path,
    detect_curation_level,
    validate_at_level,
    check_promotion_readiness,
    get_curation_info,
    create_scaffold,
    create_stub,
    promote_to_full,
    load_ontosignore,
    should_ignore,
    level_marker,
)


class TestCurationLevel:
    """Test CurationLevel enum."""
    
    def test_level_values(self):
        """Test that levels have correct integer values."""
        assert CurationLevel.SCAFFOLD == 0
        assert CurationLevel.STUB == 1
        assert CurationLevel.FULL == 2
    
    def test_level_comparison(self):
        """Test that levels can be compared."""
        assert CurationLevel.SCAFFOLD < CurationLevel.STUB
        assert CurationLevel.STUB < CurationLevel.FULL


class TestInferTypeFromPath:
    """Test type inference from file paths."""
    
    def test_kernel_directory(self):
        """Test kernel type inference from path."""
        assert infer_type_from_path(Path("docs/kernel/mission.md")) == 'kernel'
    
    def test_strategy_directory(self):
        """Test strategy type inference from path."""
        assert infer_type_from_path(Path("strategy/roadmap.md")) == 'strategy'
    
    def test_product_directory(self):
        """Test product type inference from path."""
        assert infer_type_from_path(Path("docs/features/checkout.md")) == 'product'
    
    def test_log_directory(self):
        """Test log type inference from path."""
        assert infer_type_from_path(Path("docs/logs/2025-01-01.md")) == 'log'
    
    def test_atom_directory(self):
        """Test atom type inference from path."""
        assert infer_type_from_path(Path("technical/api.md")) == 'atom'
    
    def test_unknown_path(self):
        """Test unknown type for generic paths."""
        assert infer_type_from_path(Path("readme.md")) == 'unknown'


class TestInferTypeFromContent:
    """Test type inference from content."""
    
    def test_mission_content(self):
        """Test kernel type from mission content."""
        content = "# Our Mission\n\nThe core mission of this project is..."
        assert infer_type_from_content(content) == 'kernel'
    
    def test_api_content(self):
        """Test atom type from API content."""
        content = "This API implementation handles authentication."
        assert infer_type_from_content(content) == 'atom'
    
    def test_feature_content(self):
        """Test product type from feature content."""
        content = "Feature requirement: The user flow should support checkout."
        assert infer_type_from_content(content) == 'product'
    
    def test_empty_content(self):
        """Test unknown type for empty content."""
        assert infer_type_from_content("") == 'unknown'


class TestGenerateIdFromPath:
    """Test ID generation from file paths."""
    
    def test_simple_name(self):
        """Test simple filename to ID."""
        assert generate_id_from_path(Path("docs/feature.md")) == 'feature'
    
    def test_hyphenated_name(self):
        """Test hyphenated filename to snake_case."""
        assert generate_id_from_path(Path("my-feature.md")) == 'my_feature'
    
    def test_numeric_prefix(self):
        """Test numeric prefix handling."""
        assert generate_id_from_path(Path("2025-01-01_session.md")) == 'doc_2025_01_01_session'
    
    def test_special_characters(self):
        """Test special character removal."""
        assert generate_id_from_path(Path("foo@bar#baz.md")) == 'foobarbaz'


class TestDetectCurationLevel:
    """Test curation level detection."""
    
    def test_explicit_level_0(self):
        """Test explicit Level 0 detection."""
        fm = {"id": "test", "curation_level": 0}
        assert detect_curation_level(fm) == CurationLevel.SCAFFOLD
    
    def test_explicit_level_1(self):
        """Test explicit Level 1 detection."""
        fm = {"id": "test", "curation_level": 1}
        assert detect_curation_level(fm) == CurationLevel.STUB
    
    def test_explicit_level_2(self):
        """Test explicit Level 2 detection."""
        fm = {"id": "test", "curation_level": 2}
        assert detect_curation_level(fm) == CurationLevel.FULL
    
    def test_scaffold_status(self):
        """Test scaffold status inference."""
        fm = {"id": "test", "status": "scaffold"}
        assert detect_curation_level(fm) == CurationLevel.SCAFFOLD
    
    def test_pending_curation_status(self):
        """Test pending_curation status inference."""
        fm = {"id": "test", "status": "pending_curation"}
        assert detect_curation_level(fm) == CurationLevel.STUB
    
    def test_unknown_type_is_scaffold(self):
        """Test unknown type implies scaffold level."""
        fm = {"id": "test", "type": "unknown"}
        assert detect_curation_level(fm) == CurationLevel.SCAFFOLD
    
    def test_log_with_concepts_is_full(self):
        """Test log with concepts is Full level."""
        fm = {"id": "test", "type": "log", "concepts": ["ux"]}
        assert detect_curation_level(fm) == CurationLevel.FULL
    
    def test_log_without_concepts_is_stub(self):
        """Test log without concepts is Stub level."""
        fm = {"id": "test", "type": "log"}
        assert detect_curation_level(fm) == CurationLevel.STUB
    
    def test_atom_with_depends_is_full(self):
        """Test atom with depends_on is Full level."""
        fm = {"id": "test", "type": "atom", "depends_on": ["mission"]}
        assert detect_curation_level(fm) == CurationLevel.FULL
    
    def test_atom_without_depends_is_stub(self):
        """Test atom without depends_on is Stub level."""
        fm = {"id": "test", "type": "atom"}
        assert detect_curation_level(fm) == CurationLevel.STUB
    
    def test_kernel_is_always_full(self):
        """Test kernel type is always Full level."""
        fm = {"id": "mission", "type": "kernel"}
        assert detect_curation_level(fm) == CurationLevel.FULL


class TestValidateAtLevel:
    """Test validation at different levels."""
    
    def test_level_0_valid_minimal(self):
        """Test Level 0 accepts minimal frontmatter."""
        fm = {"id": "test", "type": "unknown"}
        valid, issues = validate_at_level(fm, CurationLevel.SCAFFOLD)
        assert valid
        assert issues == []
    
    def test_level_0_missing_id(self):
        """Test Level 0 requires id."""
        fm = {"type": "unknown"}
        valid, issues = validate_at_level(fm, CurationLevel.SCAFFOLD)
        assert not valid
        assert "id" in issues[0]
    
    def test_level_1_rejects_unknown_type(self):
        """Test Level 1 rejects unknown type."""
        fm = {"id": "test", "type": "unknown", "status": "draft"}
        valid, issues = validate_at_level(fm, CurationLevel.STUB)
        assert not valid
        assert "unknown" in issues[0].lower()
    
    def test_level_1_requires_status(self):
        """Test Level 1 requires status."""
        fm = {"id": "test", "type": "atom"}
        valid, issues = validate_at_level(fm, CurationLevel.STUB)
        assert not valid
        assert "status" in issues[0]
    
    def test_level_2_requires_depends_for_atom(self):
        """Test Level 2 requires depends_on for atom."""
        fm = {"id": "test", "type": "atom", "status": "active"}
        valid, issues = validate_at_level(fm, CurationLevel.FULL)
        assert not valid
        assert "depends_on" in issues[0]
    
    def test_level_2_requires_concepts_for_log(self):
        """Test Level 2 requires concepts for log."""
        fm = {"id": "test", "type": "log", "status": "active"}
        valid, issues = validate_at_level(fm, CurationLevel.FULL)
        assert not valid
        assert "concepts" in issues[0]
    
    def test_level_2_rejects_scaffold_status(self):
        """Test Level 2 rejects scaffold status."""
        fm = {"id": "test", "type": "atom", "status": "scaffold", "depends_on": ["x"]}
        valid, issues = validate_at_level(fm, CurationLevel.FULL)
        assert not valid
        assert "scaffold" in issues[0]


class TestCheckPromotionReadiness:
    """Test promotion readiness checking."""
    
    def test_full_level_not_promotable(self):
        """Test Full level cannot be promoted."""
        fm = {"id": "test", "type": "atom", "status": "active", "depends_on": ["x"]}
        ready, blockers = check_promotion_readiness(fm, CurationLevel.FULL)
        assert not ready
        assert "maximum" in blockers[0].lower()
    
    def test_stub_promotable_with_deps(self):
        """Test Stub is promotable if it has deps."""
        fm = {"id": "test", "type": "atom", "status": "draft", "depends_on": ["x"]}
        ready, blockers = check_promotion_readiness(fm, CurationLevel.STUB)
        assert ready
        assert blockers == []
    
    def test_stub_not_promotable_without_deps(self):
        """Test Stub not promotable without deps."""
        fm = {"id": "test", "type": "atom", "status": "draft"}
        ready, blockers = check_promotion_readiness(fm, CurationLevel.STUB)
        assert not ready
        assert "depends_on" in blockers[0]


class TestCreateScaffold:
    """Test scaffold creation."""
    
    def test_creates_scaffold_frontmatter(self):
        """Test scaffold creates correct frontmatter."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test Document\n\nSome content about API.")
            f.flush()
            
            try:
                fm = create_scaffold(Path(f.name))
                assert fm['id'] is not None
                assert fm['type'] == 'atom'  # API content should infer atom
                assert fm['status'] == 'scaffold'
                assert fm['curation_level'] == 0
                assert fm['ontos_schema'] == '2.2'
                assert fm['generated_by'] == 'ontos_scaffold'
            finally:
                os.unlink(f.name)
    
    def test_infers_type_from_path(self):
        """Test scaffold infers type from path."""
        fm = create_scaffold(Path("docs/kernel/mission.md"), "Some content")
        assert fm['type'] == 'kernel'


class TestCreateStub:
    """Test stub creation."""
    
    def test_creates_stub_frontmatter(self):
        """Test stub creates correct frontmatter."""
        fm = create_stub("my_feature", "product", "Document the checkout flow")
        assert fm['id'] == 'my_feature'
        assert fm['type'] == 'product'
        assert fm['status'] == 'pending_curation'
        assert fm['curation_level'] == 1
        assert fm['goal'] == 'Document the checkout flow'
    
    def test_stub_with_depends_on(self):
        """Test stub with dependencies."""
        fm = create_stub("my_feature", "product", "Goal", depends_on=["mission"])
        assert fm['depends_on'] == ["mission"]


class TestPromoteToFull:
    """Test promotion to Full level."""
    
    def test_promotion_updates_level(self):
        """Test promotion updates curation level."""
        fm = {"id": "test", "type": "atom", "status": "pending_curation"}
        result, _ = promote_to_full(fm, depends_on=["mission"])
        assert result['curation_level'] == 2
        assert result['status'] == 'draft'  # Promoted from pending_curation
    
    def test_promotion_preserves_goal_as_seed(self):
        """Test promotion returns goal as summary seed."""
        fm = {"id": "test", "type": "atom", "goal": "Document the API"}
        result, summary_seed = promote_to_full(fm, depends_on=["mission"])
        assert summary_seed == "Document the API"
        assert result.get('goal') == "Document the API"  # Goal preserved


class TestOntosignore:
    """Test .ontosignore functionality."""
    
    def test_load_ontosignore_empty(self):
        """Test loading when file doesn't exist."""
        patterns = load_ontosignore(Path("/nonexistent"))
        assert patterns == []
    
    def test_should_ignore_match(self):
        """Test pattern matching."""
        patterns = ["vendor/", "*.generated.md"]
        assert should_ignore(Path("vendor/package.md"), patterns)
        assert should_ignore(Path("docs/api.generated.md"), patterns)
    
    def test_should_not_ignore_mismatch(self):
        """Test non-matching pattern."""
        patterns = ["vendor/"]
        assert not should_ignore(Path("docs/feature.md"), patterns)


class TestLevelMarker:
    """Test level marker display."""
    
    def test_marker_format(self):
        """Test marker string format."""
        assert level_marker(CurationLevel.SCAFFOLD) == "[L0]"
        assert level_marker(CurationLevel.STUB) == "[L1]"
        assert level_marker(CurationLevel.FULL) == "[L2]"


class TestGetCurationInfo:
    """Test comprehensive curation info."""
    
    def test_returns_curation_info_object(self):
        """Test get_curation_info returns CurationInfo."""
        fm = {"id": "test", "type": "atom", "curation_level": 1, "status": "draft"}
        info = get_curation_info(fm)
        assert isinstance(info, CurationInfo)
        assert info.level == CurationLevel.STUB
        assert info.explicit is True
