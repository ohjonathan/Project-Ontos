"""Pytest configuration and shared fixtures."""

import os
import sys
import pytest

# Add scripts directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '.ontos', 'scripts'))


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
type: atom
depends_on: []
---
# Session Log
""")
    return doc
