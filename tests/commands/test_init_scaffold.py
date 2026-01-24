"""Tests for scaffold integration in ontos init (v3.1.1)."""
import pytest
from pathlib import Path
import subprocess

from ontos.commands.init import init_command, InitOptions
from ontos.commands.scaffold import DEFAULT_IGNORES


@pytest.fixture
def git_repo(tmp_path):
    """Create a temporary git repository."""
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
    return tmp_path


class TestInitDirectories:
    """Tests for full type hierarchy directory creation."""

    def test_init_creates_kernel_dir(self, git_repo):
        """Init creates docs/kernel/ directory."""
        options = InitOptions(path=git_repo, skip_hooks=True, no_scaffold=True)
        init_command(options)
        assert (git_repo / "docs" / "kernel").is_dir()

    def test_init_creates_product_dir(self, git_repo):
        """Init creates docs/product/ directory."""
        options = InitOptions(path=git_repo, skip_hooks=True, no_scaffold=True)
        init_command(options)
        assert (git_repo / "docs" / "product").is_dir()

    def test_init_creates_atom_dir(self, git_repo):
        """Init creates docs/atom/ directory."""
        options = InitOptions(path=git_repo, skip_hooks=True, no_scaffold=True)
        init_command(options)
        assert (git_repo / "docs" / "atom").is_dir()

    def test_init_creates_all_type_hierarchy_dirs(self, git_repo):
        """Init creates complete type hierarchy."""
        options = InitOptions(path=git_repo, skip_hooks=True, no_scaffold=True)
        init_command(options)
        for subdir in ['kernel', 'strategy', 'product', 'atom', 'logs', 'reference', 'archive']:
            assert (git_repo / "docs" / subdir).is_dir(), f"Missing docs/{subdir}/"


class TestScaffoldFlags:
    """Tests for --scaffold / --no-scaffold flags."""

    def test_no_scaffold_flag_skips(self, git_repo, monkeypatch):
        """--no-scaffold suppresses scaffold entirely."""
        (git_repo / "docs").mkdir()
        (git_repo / "docs" / "test.md").write_text("# Test\nContent.")

        monkeypatch.setattr('sys.stdin.isatty', lambda: True)
        options = InitOptions(path=git_repo, skip_hooks=True, no_scaffold=True)
        code, _ = init_command(options)

        assert code in (0, 3)
        # File should NOT have frontmatter
        content = (git_repo / "docs" / "test.md").read_text()
        assert "id:" not in content

    def test_scaffold_flag_forces(self, git_repo, monkeypatch):
        """--scaffold runs scaffold without prompting."""
        docs = git_repo / "docs"
        docs.mkdir()
        (docs / "test.md").write_text("# Test\nContent here.")

        monkeypatch.setattr('sys.stdin.isatty', lambda: True)
        options = InitOptions(path=git_repo, skip_hooks=True, scaffold=True)
        code, _ = init_command(options)

        assert code in (0, 3)
        content = (docs / "test.md").read_text()
        assert "id:" in content

    def test_non_tty_skips_scaffold(self, git_repo, monkeypatch):
        """Non-TTY mode skips scaffold silently."""
        docs = git_repo / "docs"
        docs.mkdir()
        (docs / "test.md").write_text("# Test\nContent.")

        monkeypatch.setattr('sys.stdin.isatty', lambda: False)
        options = InitOptions(path=git_repo, skip_hooks=True)
        code, _ = init_command(options)

        assert code in (0, 3)
        content = (docs / "test.md").read_text()
        assert "id:" not in content


class TestScaffoldPrompt:
    """Tests for interactive scaffold prompt flow."""

    def test_no_untagged_skips_prompt(self, git_repo, monkeypatch):
        """No prompt when no untagged files exist."""
        docs = git_repo / "docs"
        docs.mkdir()
        (docs / "tagged.md").write_text("---\nid: tagged\ntype: atom\n---\n# Tagged")

        input_called = []
        def mock_input(prompt):
            input_called.append(prompt)
            return 'n'
        monkeypatch.setattr('builtins.input', mock_input)
        monkeypatch.setattr('sys.stdin.isatty', lambda: True)

        options = InitOptions(path=git_repo, skip_hooks=True)
        code, _ = init_command(options)
        assert code in (0, 3)
        # Scaffold-related prompt should NOT have been called
        assert not any('scaffold' in p.lower() for p in input_called)

    def test_prompt_decline(self, git_repo, monkeypatch):
        """User declining scaffold prompt skips scaffold."""
        docs = git_repo / "docs"
        docs.mkdir()
        (docs / "test.md").write_text("# Test\nContent.")

        inputs = iter(['n'])
        monkeypatch.setattr('builtins.input', lambda prompt: next(inputs))
        monkeypatch.setattr('sys.stdin.isatty', lambda: True)

        options = InitOptions(path=git_repo, skip_hooks=True)
        code, _ = init_command(options)
        assert code in (0, 3)
        content = (docs / "test.md").read_text()
        assert "id:" not in content

    def test_prompt_accept_docs_scope(self, git_repo, monkeypatch):
        """User accepts scaffold with docs/ scope."""
        docs = git_repo / "docs"
        docs.mkdir()
        (docs / "test.md").write_text("# Test\nContent.")

        inputs = iter(['y', '1'])
        monkeypatch.setattr('builtins.input', lambda prompt: next(inputs))
        monkeypatch.setattr('sys.stdin.isatty', lambda: True)

        options = InitOptions(path=git_repo, skip_hooks=True)
        code, _ = init_command(options)
        assert code in (0, 3)
        content = (docs / "test.md").read_text()
        assert "id:" in content

    def test_prompt_accept_repo_scope(self, git_repo, monkeypatch):
        """User accepts scaffold with entire repo scope."""
        docs = git_repo / "docs"
        docs.mkdir()
        (docs / "test.md").write_text("# Test\nContent.")
        # Also create a file outside docs/
        (git_repo / "notes.md").write_text("# Notes\nSome notes.")

        inputs = iter(['y', '2'])
        monkeypatch.setattr('builtins.input', lambda prompt: next(inputs))
        monkeypatch.setattr('sys.stdin.isatty', lambda: True)

        options = InitOptions(path=git_repo, skip_hooks=True)
        code, _ = init_command(options)
        assert code in (0, 3)

    def test_eof_skips_gracefully(self, git_repo, monkeypatch):
        """EOFError during scaffold prompt skips gracefully."""
        docs = git_repo / "docs"
        docs.mkdir()
        (docs / "test.md").write_text("# Test\nContent.")

        def mock_input(prompt):
            raise EOFError()
        monkeypatch.setattr('builtins.input', mock_input)
        monkeypatch.setattr('sys.stdin.isatty', lambda: True)

        options = InitOptions(path=git_repo, skip_hooks=True)
        code, _ = init_command(options)
        assert code in (0, 3)  # Init still succeeds

    def test_keyboard_interrupt_skips(self, git_repo, monkeypatch):
        """KeyboardInterrupt during scaffold prompt skips (does not abort init)."""
        docs = git_repo / "docs"
        docs.mkdir()
        (docs / "test.md").write_text("# Test\nContent.")

        call_count = [0]
        def mock_input(prompt):
            call_count[0] += 1
            if 'scaffold' in prompt.lower() or 'y/N' in prompt:
                raise KeyboardInterrupt()
            return 'n'
        monkeypatch.setattr('builtins.input', mock_input)
        monkeypatch.setattr('sys.stdin.isatty', lambda: True)

        options = InitOptions(path=git_repo, skip_hooks=True)
        code, _ = init_command(options)
        # Init should still succeed (scaffold skipped, not aborted)
        assert code in (0, 3)

    def test_prompt_shows_when_docs_empty_but_repo_has_files(self, git_repo, monkeypatch, capsys):
        """Prompt appears when untagged files exist outside docs/."""
        # Setup: empty docs/, untagged file in notes/
        docs = git_repo / "docs"
        docs.mkdir()
        notes = git_repo / "notes"
        notes.mkdir()
        (notes / "readme.md").write_text("# Notes")
        
        input_prompts = []
        def mock_input(prompt):
            input_prompts.append(prompt)
            return 'n'
            
        monkeypatch.setattr('builtins.input', mock_input)
        monkeypatch.setattr('sys.stdin.isatty', lambda: True)
        
        options = InitOptions(path=git_repo, skip_hooks=True)
        init_command(options)
        
        captured = capsys.readouterr()
        # Should see prompt (not skip silently)
        assert "untagged markdown file" in captured.out

    def test_warning_count_matches_selected_scope(self, git_repo, monkeypatch, capsys):
        """The >50 warning reflects the selected scope, not just docs/."""
        # Setup: 10 files in docs/, 60 files in notes/
        docs = git_repo / "docs"
        docs.mkdir()
        notes = git_repo / "notes"
        notes.mkdir()
        for i in range(10):
            (docs / f"doc{i}.md").write_text(f"# Doc {i}")
        for i in range(60):
            (notes / f"note{i}.md").write_text(f"# Note {i}")
        
        # Accept, then select Choice 2 (entire repo) which has 70 files (>50)
        inputs = iter(['y', '2'])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))
        monkeypatch.setattr('sys.stdin.isatty', lambda: True)
        
        init_command(InitOptions(path=git_repo, skip_hooks=True))
        
        captured = capsys.readouterr()
        # Should see count of 70 and the "may take a moment" warning
        assert "70" in captured.out or "70" in captured.err
        assert "This may take a moment" in captured.out or "This may take a moment" in captured.err


class TestScaffoldSafety:
    """Tests for scaffold safety guards."""

    def test_default_ignores_node_modules(self, git_repo, monkeypatch):
        """node_modules/ files are NOT scaffolded even with repo-wide scan."""
        docs = git_repo / "docs"
        docs.mkdir()
        (docs / "legit.md").write_text("# Legit\nContent.")

        nm = git_repo / "node_modules"
        nm.mkdir()
        (nm / "README.md").write_text("# Some Package\nDo not scaffold me.")

        inputs = iter(['y', '2'])  # Accept, entire repo
        monkeypatch.setattr('builtins.input', lambda prompt: next(inputs))
        monkeypatch.setattr('sys.stdin.isatty', lambda: True)

        options = InitOptions(path=git_repo, skip_hooks=True)
        init_command(options)

        # node_modules file should NOT have frontmatter
        nm_content = (nm / "README.md").read_text()
        assert "id:" not in nm_content

    def test_default_ignores_venv(self, git_repo, monkeypatch):
        """Files in .venv/ are NOT scaffolded."""
        docs = git_repo / "docs"
        docs.mkdir()
        (docs / "legit.md").write_text("# Legit\nContent.")

        venv = git_repo / ".venv" / "lib"
        venv.mkdir(parents=True)
        (venv / "guide.md").write_text("# Venv Doc\nShould be ignored.")

        inputs = iter(['y', '2'])
        monkeypatch.setattr('builtins.input', lambda prompt: next(inputs))
        monkeypatch.setattr('sys.stdin.isatty', lambda: True)

        options = InitOptions(path=git_repo, skip_hooks=True)
        init_command(options)

        venv_content = (venv / "guide.md").read_text()
        assert "id:" not in venv_content

    def test_custom_path_escape_rejected(self, git_repo, monkeypatch):
        """Path escaping project root is rejected."""
        docs = git_repo / "docs"
        docs.mkdir()
        (docs / "test.md").write_text("# Test\nContent.")

        inputs = iter(['y', '3', '../outside'])
        monkeypatch.setattr('builtins.input', lambda prompt: next(inputs))
        monkeypatch.setattr('sys.stdin.isatty', lambda: True)

        options = InitOptions(path=git_repo, skip_hooks=True)
        code, _ = init_command(options)
        # Init succeeds but scaffold is skipped
        assert code in (0, 3)
        content = (docs / "test.md").read_text()
        assert "id:" not in content

    def test_custom_path_absolute_rejected(self, git_repo, monkeypatch):
        """Absolute path outside project is rejected."""
        docs = git_repo / "docs"
        docs.mkdir()
        (docs / "test.md").write_text("# Test\nContent.")

        inputs = iter(['y', '3', '/tmp/other'])
        monkeypatch.setattr('builtins.input', lambda prompt: next(inputs))
        monkeypatch.setattr('sys.stdin.isatty', lambda: True)

        options = InitOptions(path=git_repo, skip_hooks=True)
        code, _ = init_command(options)
        assert code in (0, 3)
        content = (docs / "test.md").read_text()
        assert "id:" not in content

    def test_invalid_scope_defaults_to_docs(self, git_repo, monkeypatch):
        """Invalid scope input defaults to docs/ with message."""
        docs = git_repo / "docs"
        docs.mkdir()
        (docs / "test.md").write_text("# Test\nContent.")

        inputs = iter(['y', '5'])  # Invalid scope
        monkeypatch.setattr('builtins.input', lambda prompt: next(inputs))
        monkeypatch.setattr('sys.stdin.isatty', lambda: True)

        options = InitOptions(path=git_repo, skip_hooks=True)
        code, _ = init_command(options)
        assert code in (0, 3)
        # Should still scaffold (defaulted to docs/)
        content = (docs / "test.md").read_text()
        assert "id:" in content

    def test_scaffold_failure_nonfatal(self, git_repo, monkeypatch):
        """scaffold_command failure doesn't abort init."""
        docs = git_repo / "docs"
        docs.mkdir()
        (docs / "test.md").write_text("# Test\nContent.")

        # Mock scaffold_command to raise
        def mock_scaffold_cmd(options):
            raise RuntimeError("Simulated failure")

        monkeypatch.setattr(
            'ontos.commands.scaffold.scaffold_command',
            mock_scaffold_cmd
        )

        options = InitOptions(path=git_repo, skip_hooks=True, scaffold=True)
        code, _ = init_command(options)
        # Init should still succeed despite scaffold failure
        assert code in (0, 3)
        assert (git_repo / ".ontos.toml").exists()


class TestDefaultIgnoresConstant:
    """Tests for the DEFAULT_IGNORES constant itself."""

    def test_default_ignores_contains_node_modules(self):
        """DEFAULT_IGNORES includes node_modules."""
        assert 'node_modules' in DEFAULT_IGNORES

    def test_default_ignores_contains_venv(self):
        """DEFAULT_IGNORES includes .venv."""
        assert '.venv' in DEFAULT_IGNORES

    def test_default_ignores_contains_vendor(self):
        """DEFAULT_IGNORES includes vendor."""
        assert 'vendor' in DEFAULT_IGNORES

    def test_default_ignores_minimum_count(self):
        """DEFAULT_IGNORES has at least 8 patterns."""
        assert len(DEFAULT_IGNORES) >= 8
