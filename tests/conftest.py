"""Pytest configuration and shared fixtures."""

import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import warnings

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
_existing_pythonpath = os.environ.get("PYTHONPATH")
os.environ["PYTHONPATH"] = (
    str(REPO_ROOT)
    if not _existing_pythonpath
    else f"{REPO_ROOT}{os.pathsep}{_existing_pythonpath}"
)


def _repository_status() -> str:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout if result.returncode == 0 else "<git-status-unavailable>"


_SESSION_STARTED_CLEAN = _repository_status() == ""


_ALIASED_VALUE_OPTION = re.compile(
    r"^(?P<indent>\s+)(?P<first>--?[A-Za-z0-9][\w-]*)"
    r"(?: (?P<first_metavar>[A-Z][A-Z0-9_-]*))?, "
    r"(?P<second>--?[A-Za-z0-9][\w-]*) "
    r"(?P<metavar>[A-Z][A-Z0-9_-]*)"
    r"(?P<spacing>\s{2,})(?P<description>.*)$"
)


def _canonicalize_argparse_help(output: str) -> str:
    """Normalize presentation-only argparse drift across supported Python versions."""
    lines = output.replace("\r\n", "\n").replace("\r", "\n").split("\n")

    # Python versions wrap mutually-exclusive usage groups differently.
    if lines and lines[0].startswith("usage: "):
        usage_end = 1
        while (
            usage_end < len(lines)
            and lines[usage_end].strip()
            and lines[usage_end][:1].isspace()
        ):
            usage_end += 1
        lines[:usage_end] = [" ".join(line.strip() for line in lines[:usage_end])]

    for index, line in enumerate(lines):
        # Python 3.9 uses the older section label.
        if line == "optional arguments:":
            lines[index] = "options:"
            continue

        # Python <=3.12 repeats a metavar for every alias; 3.13+ prints it once.
        match = _ALIASED_VALUE_OPTION.match(line)
        if match and match.group("first_metavar") in (None, match.group("metavar")):
            lines[index] = (
                f"{match.group('indent')}{match.group('first')}, "
                f"{match.group('second')} {match.group('metavar')}"
                f"  {match.group('description')}"
            )

    return "\n".join(lines)


@pytest.fixture
def assert_help_parity():
    """Compare CLI help while preserving all non-stdlib-controlled content."""
    def _assert_help_parity(actual: str, golden: str) -> None:
        assert _canonicalize_argparse_help(actual) == _canonicalize_argparse_help(golden)

    return _assert_help_parity


def pytest_sessionfinish(session, exitstatus):
    """Turn a clean-clone test run dirtying the checkout into a test failure."""
    if not _SESSION_STARTED_CLEAN:
        return
    status = _repository_status()
    if status:
        reporter = session.config.pluginmanager.get_plugin("terminalreporter")
        if reporter is not None:
            reporter.write_sep("=", "tests modified the repository checkout", red=True)
            reporter.write(status)
        session.exitstatus = pytest.ExitCode.TESTS_FAILED


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
