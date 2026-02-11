"""Pytest configuration and shared fixtures."""

import os
import sys
import shutil
import subprocess
import warnings
import pytest

# Add bundled scripts directory to path for legacy imports
# (Tests import directly from script names like ontos_generate_context_map)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), '.ontos', 'scripts'))


# v2.9.2: Configure warning filters for deprecation warnings
def pytest_configure(config):
    """Configure pytest warning filters."""
    # Show FutureWarnings from ontos modules
    warnings.filterwarnings(
        "always",
        category=FutureWarning,
        module=r"ontos.*"
    )
    
    # Suppress the ontos_lib deprecation warning in tests
    # (tests may intentionally import from ontos_lib to test the shim)
    warnings.filterwarnings(
        "ignore",
        message="Importing from 'ontos_lib' is deprecated",
        category=FutureWarning,
    )


# =============================================================================
# DUAL-MODE TESTING INFRASTRUCTURE (v2.5.2+)
# =============================================================================


def pytest_addoption(parser):
    """Add --mode option to pytest CLI."""
    parser.addoption(
        "--mode",
        action="store",
        default="contributor",
        choices=["contributor", "user"],
        help="Run tests in 'contributor' or 'user' mode"
    )


@pytest.fixture
def project_mode(request):
    """Get the current test mode."""
    return request.config.getoption("--mode")


@pytest.fixture
def mode_aware_project(request, tmp_path):
    """
    Create a project fixture based on the current mode.
    - contributor: Uses .ontos-internal/ structure
    - user: Uses docs/ structure (simulates user installation)
    """
    mode = request.config.getoption("--mode")
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if mode == "contributor":
        # Contributor mode: copy full project structure
        shutil.copytree(
            os.path.join(project_root, '.ontos-internal'),
            tmp_path / '.ontos-internal'
        )
        shutil.copytree(
            os.path.join(project_root, '.ontos'),
            tmp_path / '.ontos'
        )
    else:
        # User mode: simulate fresh installation
        shutil.copytree(
            os.path.join(project_root, '.ontos'),
            tmp_path / '.ontos'
        )
        shutil.copy(
            os.path.join(project_root, 'ontos_init.py'),
            tmp_path
        )
        # Run init to create user structure
        result = subprocess.run(
            [sys.executable, 'ontos_init.py', '--non-interactive'],
            cwd=tmp_path,
            check=True,
            capture_output=True
        )
        
        # Explicit assertions on ALL expected directories (per Codex review)
        assert (tmp_path / 'docs' / 'logs').exists(), "Missing docs/logs/"
        assert (tmp_path / 'docs' / 'strategy').exists(), "Missing docs/strategy/"
        assert (tmp_path / 'docs' / 'strategy' / 'proposals').exists(), "Missing docs/strategy/proposals/"
        assert (tmp_path / 'docs' / 'archive').exists(), "Missing docs/archive/"
        assert (tmp_path / 'docs' / 'archive' / 'logs').exists(), "Missing docs/archive/logs/"
        assert (tmp_path / 'docs' / 'archive' / 'proposals').exists(), "Missing docs/archive/proposals/"
        assert (tmp_path / 'docs' / 'reference').exists(), "Missing docs/reference/"
        
        # Assert starter files
        assert (tmp_path / 'docs' / 'strategy' / 'decision_history.md').exists(), "Missing decision_history.md"
        assert (tmp_path / 'docs' / 'reference' / 'Common_Concepts.md').exists(), "Missing Common_Concepts.md"

    return tmp_path


@pytest.fixture
def docs_dir(project_mode):
    """Get the docs directory based on mode."""
    if project_mode == "contributor":
        return ".ontos-internal"
    return "docs"


@pytest.fixture
def temp_docs_dir(tmp_path):
    """Create a temporary docs directory."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    return docs_dir


@pytest.fixture
def valid_kernel_doc(temp_docs_dir):
    """Create a valid kernel document."""
    doc = temp_docs_dir / "mission.md"
    doc.write_text("""---
id: mission
type: kernel
status: active
depends_on: []
---
# Mission Statement

Our mission is to build great software.
""")
    return doc


@pytest.fixture
def valid_atom_doc(temp_docs_dir):
    """Create a valid atom document."""
    doc = temp_docs_dir / "api_spec.md"
    doc.write_text("""---
id: api_spec
type: atom
status: active
depends_on: [mission]
---
# API Specification

Technical details here.
""")
    return doc


@pytest.fixture
def doc_without_frontmatter(temp_docs_dir):
    """Create a document without frontmatter."""
    doc = temp_docs_dir / "no_frontmatter.md"
    doc.write_text("""# Just a Title

No YAML frontmatter here.
""")
    return doc


@pytest.fixture
def circular_docs(temp_docs_dir):
    """Create documents with circular dependencies."""
    doc_a = temp_docs_dir / "doc_a.md"
    doc_a.write_text("""---
id: doc_a
type: atom
depends_on: [doc_b]
---
# Document A
""")

    doc_b = temp_docs_dir / "doc_b.md"
    doc_b.write_text("""---
id: doc_b
type: atom
depends_on: [doc_a]
---
# Document B
""")
    return doc_a, doc_b


@pytest.fixture
def broken_link_doc(temp_docs_dir):
    """Create a document with a broken link."""
    doc = temp_docs_dir / "broken.md"
    doc.write_text("""---
id: broken
type: atom
depends_on: [nonexistent_doc]
---
# Broken Link Document
""")
    return doc


@pytest.fixture
def architecture_violation_docs(temp_docs_dir):
    """Create documents with architectural violation."""
    # Kernel depending on atom (violation)
    kernel = temp_docs_dir / "bad_kernel.md"
    kernel.write_text("""---
id: bad_kernel
type: kernel
depends_on: [some_atom]
---
# Bad Kernel
""")

    atom = temp_docs_dir / "some_atom.md"
    atom.write_text("""---
id: some_atom
type: atom
depends_on: []
---
# Some Atom
""")
    return kernel, atom


@pytest.fixture
def template_doc(temp_docs_dir):
    """Create a template document (should be skipped)."""
    doc = temp_docs_dir / "_template.md"
    doc.write_text("""---
id: _template
type: atom
---
# Template
""")
    return doc


@pytest.fixture
def log_doc(temp_docs_dir):
    """Create a log document in logs directory."""
    logs_dir = temp_docs_dir / "logs"
    logs_dir.mkdir()
    doc = logs_dir / "2025-01-01_session.md"
    doc.write_text("""---
id: log_20250101_session
type: log
status: active
depends_on: []
---
# Session Log
""")
    return doc
