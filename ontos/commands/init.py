"""Ontos project initialization command."""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple
import sys

from ontos.core.config import default_config, ConfigError
from ontos.io.config import save_project_config, config_exists

# Explicit marker for hook detection
ONTOS_HOOK_MARKER = "# ontos-managed-hook"


@dataclass
class InitOptions:
    """Configuration for init command."""
    path: Path = None
    force: bool = False
    interactive: bool = False  # Reserved for v3.1
    skip_hooks: bool = False
    yes: bool = False
    scaffold: bool = False      # Force scaffold without prompt
    no_scaffold: bool = False   # Suppress scaffold prompt entirely


def _confirm_hooks(options: InitOptions) -> bool:
    """Confirm hook installation with user in TTY contexts.

    Returns:
        True if hooks should be installed, False otherwise.

    Raises:
        KeyboardInterrupt: If user presses Ctrl+C (aborts entire init)

    Behavioral matrix:
        skip_hooks=True  -> False (user explicitly skipped)
        yes=True         -> True  (non-interactive mode)
        non-TTY          -> True  (CI/scripts proceed)
        TTY              -> prompt user
    """
    if options.skip_hooks:
        return False  # User explicitly skipped
    if options.yes:
        return True   # Non-interactive mode
    if not sys.stdin.isatty():
        return True   # Non-TTY: proceed (CI/scripts)

    # Print preflight message
    print("\nGit hooks to be installed:")
    print("  - pre-commit: Validates documentation before commits")
    print("  - pre-push: Ensures context map exists before push")
    print("\nHooks location: .git/hooks/")
    print("Use --skip-hooks to skip installation.\n")

    try:
        response = input("Install git hooks? [Y/n] ").strip().lower()
        return response in ('', 'y', 'yes')
    except EOFError:
        print("\nSkipping hooks.")
        return False
    except KeyboardInterrupt:
        print("\nAborted.")
        raise  # Re-raise to abort init entirely


def _prompt_scaffold(project_root: Path, config, options: InitOptions):
    """Prompt user to scaffold untagged markdown files during init.

    Returns:
        List[Path] of directories to scaffold, or None to skip.

    Behavioral matrix:
        no_scaffold=True     -> None (skip)
        scaffold=True        -> [docs_dir] (force, docs scope)
        non-TTY              -> None (skip silently)
            Rationale: hooks proceed in non-TTY because they add new files.
            Scaffold modifies existing files, requiring explicit opt-in.
        TTY, 0 untagged      -> None (no prompt)
        TTY, N untagged      -> prompt user for confirmation + scope
    """
    from typing import List

    # Short-circuit on flags
    if options.no_scaffold:
        return None

    docs_path = project_root / config.paths.docs_dir

    if options.scaffold:
        return [docs_path]

    # Non-TTY: skip silently
    if not sys.stdin.isatty():
        return None

    # Detect untagged files in ENTIRE repo (X-H1)
    try:
        from ontos.commands.scaffold import find_untagged_files
        all_untagged = find_untagged_files(root=project_root)
    except Exception:
        return None

    if not all_untagged:
        return None

    total_count = len(all_untagged)

    # Prompt for confirmation with total repo count
    print(f"\nFound {total_count} untagged markdown file(s).")
    print("Scaffold adds YAML headers to identify each file.")
    try:
        response = input("Would you like to scaffold them? [y/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return None

    if response not in ('y', 'yes'):
        return None

    # Prompt for scope
    print(f"\nWhere should we scan?")
    print(f"  (1) {config.paths.docs_dir}/ directory only")
    print("  (2) Entire repository (excludes node_modules, .venv, etc.)")
    print("  (3) Custom path")

    try:
        choice = input("Choice [1]: ").strip()
    except (EOFError, KeyboardInterrupt):
        return None

    selected_paths = []
    if choice == '2':
        selected_paths = [project_root]
    elif choice == '3':
        try:
            custom_input = input("Path (relative to project root): ").strip()
        except (EOFError, KeyboardInterrupt):
            return None

        if not custom_input:
            selected_paths = [docs_path]
        else:
            custom_path = Path(custom_input)
            if not custom_path.is_absolute():
                custom_path = project_root / custom_path
            resolved = custom_path.resolve()

            # Path escape guard (B2)
            if not resolved.is_relative_to(project_root.resolve()):
                print("Error: Path must be within project root.", file=sys.stderr)
                return None

            if not resolved.exists():
                print(f"Error: Path '{custom_input}' does not exist.", file=sys.stderr)
                return None
            selected_paths = [resolved]
    else:  # Choice 1 or empty/invalid
        if choice not in ('1', '', '2', '3'):
            print("Invalid choice, using docs/ directory.", file=sys.stderr)
        selected_paths = [docs_path]

    # Large file count warning (X-H2) - Move to after scope selection
    try:
        scope_untagged = find_untagged_files(paths=selected_paths, root=project_root)
        scope_count = len(scope_untagged)
        if scope_count > 50:
            print(f"\nNote: {scope_count} files will be scaffolded. This may take a moment.", file=sys.stderr)
        elif choice == '2' and scope_count != total_count:
            # Re-count if somehow find_untagged_files(project_root) differ from
            # subsequent call, but generally they should match.
            pass
    except Exception:
        pass

    return selected_paths


def _run_scaffold(project_root: Path, paths) -> None:
    """Run scaffold on given paths during init. Non-fatal on failure.

    Matches the non-fatal pattern of _generate_agents_file().
    Note: Scaffold writes persist even if init is subsequently aborted.
    """
    try:
        from ontos.commands.scaffold import ScaffoldOptions, scaffold_command

        options = ScaffoldOptions(
            paths=paths,
            apply=True,
            dry_run=False,
            quiet=True,
        )
        exit_code, message = scaffold_command(options)

        if exit_code == 0:
            print("   Scaffold complete.", file=sys.stderr)
        else:
            print(f"Warning: Scaffold completed with errors: {message}", file=sys.stderr)
    except Exception as e:
        print(f"Warning: Could not run scaffold: {e}", file=sys.stderr)


def init_command(options: InitOptions) -> Tuple[int, str]:
    """
    Initialize a new Ontos project.

    Returns:
        Tuple of (exit_code, message)

    Exit Codes:
        0: Success
        1: Already initialized (use --force)
        2: Not a git repository
        3: Hooks skipped due to existing non-Ontos hooks
    """
    project_root = options.path or Path.cwd()

    # 1. Check if already initialized
    config_path = project_root / ".ontos.toml"
    if config_path.exists() and not options.force:
        return 0, "Already initialized. Use --force to reinitialize."

    # 2. Check for git repository (handle worktrees)
    git_check = _check_git_repo(project_root)
    if git_check is not None:
        return git_check

    # 3. Detect legacy .ontos/scripts/
    legacy_path = project_root / ".ontos" / "scripts"
    if legacy_path.exists():
        print("Warning: Legacy .ontos/scripts/ detected. Consider migrating.", file=sys.stderr)

    # Track created items for cleanup on abort
    created_paths = []

    try:
        # 4. Create default config
        config = default_config()
        if not config_path.exists():
            created_paths.append(config_path)
        save_project_config(config, config_path)

        # 5. Create directory structure (full type hierarchy)
        dirs = [
            config.paths.docs_dir,
            config.paths.logs_dir,
            f"{config.paths.docs_dir}/kernel",
            f"{config.paths.docs_dir}/strategy",
            f"{config.paths.docs_dir}/product",
            f"{config.paths.docs_dir}/atom",
            f"{config.paths.docs_dir}/reference",
            f"{config.paths.docs_dir}/archive",
        ]
        for d in dirs:
            p = project_root / d
            if not p.exists():
                # Track newly created directories for cleanup
                # We track the deepest nonexistent parent to avoid orphaned folders
                created_paths.append(p)
            p.mkdir(parents=True, exist_ok=True)

        # 5.5 Scaffold integration (optional, interactive)
        scaffold_paths = _prompt_scaffold(project_root, config, options)
        if scaffold_paths is not None:
            _run_scaffold(project_root, scaffold_paths)

        # 6. Generate initial context map
        context_map_path = project_root / config.paths.context_map
        if not context_map_path.exists():
            created_paths.append(context_map_path)
        _generate_initial_context_map(project_root, config)

        # 7. Install hooks (with collision safety and consent)
        if _confirm_hooks(options):
            hooks_status = _install_hooks(project_root, options)
        else:
            hooks_status = 0  # Skipped by user choice

    except KeyboardInterrupt:
        # Cleanup partial initialization on Ctrl+C (reverse order)
        for p in reversed(created_paths):
            try:
                if p.is_file():
                    p.unlink()
                elif p.is_dir():
                    # Only remove if empty to avoid accidental data loss
                    if not any(p.iterdir()):
                        p.rmdir()
            except Exception:
                pass
        print("\nInit aborted. Cleanup complete.")
        return 130, "Aborted by user"  # Standard SIGINT exit code

    # 8. Auto-generate AGENTS.md (non-fatal on failure)
    _generate_agents_file(project_root)

    # 9. Build success message
    msg = f"Initialized Ontos in {project_root}\n"
    msg += f"Created: .ontos.toml, {config.paths.context_map}\n"
    msg += "Tip: Run 'ontos agents' to regenerate instruction files"

    return hooks_status, msg


def _check_git_repo(project_root: Path) -> Optional[Tuple[int, str]]:
    """Check if path is a valid git repository (handles worktrees)."""
    git_path = project_root / ".git"

    if git_path.is_dir():
        return None  # Normal git repo

    if git_path.is_file():
        # Git worktree or submodule - .git is a file pointing to actual repo
        return None  # Still valid

    return 2, "Not a git repository. Run 'git init' first."


def _create_directories(root: Path, config) -> None:
    """Create standard directory structure."""
    dirs = [
        config.paths.docs_dir,
        config.paths.logs_dir,
        f"{config.paths.docs_dir}/kernel",
        f"{config.paths.docs_dir}/strategy",
        f"{config.paths.docs_dir}/product",
        f"{config.paths.docs_dir}/atom",
        f"{config.paths.docs_dir}/reference",
        f"{config.paths.docs_dir}/archive",
    ]
    for d in dirs:
        (root / d).mkdir(parents=True, exist_ok=True)


def _generate_initial_context_map(root: Path, config) -> None:
    """Generate initial context map by running the map command.

    Non-fatal on failure - creates placeholder if native command fails.
    """
    try:
        from ontos.commands.map import map_command, MapOptions

        # Save current working directory and change to project root
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(str(root))

            options = MapOptions(
                output=root / config.paths.context_map,
                strict=False,
                json_output=False,
                quiet=True,  # Suppress verbose output during init
            )
            exit_code = map_command(options)

            if exit_code == 0:
                print("   ✓ Context map generated", file=sys.stderr)
            else:
                print(f"Warning: Context map generation returned code {exit_code}", file=sys.stderr)
        finally:
            os.chdir(original_cwd)

    except Exception as e:
        # Fallback: create a minimal context map placeholder
        print(f"Warning: Could not generate context map: {e}", file=sys.stderr)
        try:
            context_map_path = root / config.paths.context_map
            if not context_map_path.exists():
                context_map_path.write_text(
                    "# Ontos Context Map\n\n"
                    "> Run `ontos map` to generate the full context map.\n"
                )
                print("   ✓ Created placeholder context map", file=sys.stderr)
        except Exception as fallback_error:
            print(f"Warning: Could not create placeholder: {fallback_error}", file=sys.stderr)


def _generate_agents_file(root: Path) -> None:
    """
    Generate AGENTS.md file after init.
    
    Non-fatal on failure per spec v1.1 Section 4.3.1.
    """
    try:
        from ontos.commands.agents import agents_command, AgentsOptions
        
        options = AgentsOptions(
            output_path=root / "AGENTS.md",
            force=False,
            format="agents",
            all_formats=False,
        )
        exit_code, message = agents_command(options)
        
        if exit_code == 0:
            print("   ✓ AGENTS.md generated", file=sys.stderr)
        elif exit_code == 1:
            # File already exists, not an error
            print("   ✓ AGENTS.md exists", file=sys.stderr)
        else:
            print(f"Warning: AGENTS.md generation failed: {message}", file=sys.stderr)
    except Exception as e:
        print(f"Warning: Could not generate AGENTS.md: {e}", file=sys.stderr)


def _get_hooks_dir(root: Path) -> Path:
    """Get the hooks directory for a git repository (handles worktrees)."""
    git_path = root / ".git"

    if git_path.is_file():
        # Worktree: .git is a file containing "gitdir: /path/to/..."
        content = git_path.read_text().strip()
        if content.startswith("gitdir:"):
            actual_git = Path(content[7:].strip())
            if "worktrees" in actual_git.parts:
                main_git = actual_git.parent.parent
                hooks_dir = main_git / "hooks"
            else:
                hooks_dir = actual_git / "hooks"
        else:
            hooks_dir = root / ".git" / "hooks"
    else:
        hooks_dir = root / ".git" / "hooks"

    # Create hooks directory if missing
    hooks_dir.mkdir(parents=True, exist_ok=True)

    return hooks_dir


def _install_hooks(root: Path, options: InitOptions) -> int:
    """Install git hooks with collision safety."""
    if options.skip_hooks:
        return 0

    try:
        hooks_dir = _get_hooks_dir(root)
    except Exception as e:
        print(f"Warning: Could not access hooks directory: {e}", file=sys.stderr)
        return 3

    hooks = ["pre-push", "pre-commit"]
    skipped = []

    for hook in hooks:
        hook_path = hooks_dir / hook
        try:
            if hook_path.exists():
                if _is_ontos_hook(hook_path):
                    _write_shim_hook(hook_path, hook)
                elif options.force:
                    _write_shim_hook(hook_path, hook)
                else:
                    skipped.append(hook)
                    print(f"Warning: Existing {hook} hook detected. Skipping. "
                          f"Use --force to overwrite, or manually integrate.", file=sys.stderr)
            else:
                _write_shim_hook(hook_path, hook)
        except PermissionError as e:
            print(f"Warning: Cannot write {hook} hook (permission denied): {e}", file=sys.stderr)
            skipped.append(hook)
        except Exception as e:
            print(f"Warning: Failed to install {hook} hook: {e}", file=sys.stderr)
            skipped.append(hook)

    return 3 if skipped else 0


def _is_ontos_hook(path: Path) -> bool:
    """Check if hook file is an Ontos shim (uses explicit marker)."""
    try:
        content = path.read_text()
        return ONTOS_HOOK_MARKER in content
    except Exception:
        return False


def _write_shim_hook(path: Path, hook_type: str) -> None:
    """
    Write minimal shim hook with marker.
    
    Per Spec v1.1 Section 4.6: Python-based shim hooks with 3-method fallback:
    1. PATH lookup (preferred)
    2. sys.executable -m ontos
    3. Graceful degradation (allow operation, warn)
    """
    import os
    import stat
    
    shim = f'''#!/usr/bin/env python3
{ONTOS_HOOK_MARKER}
"""Ontos {hook_type} hook. Delegates to ontos CLI."""
import subprocess
import sys

def run_hook():
    """Try multiple methods to invoke ontos hook."""
    args = ["hook", "{hook_type}"] + sys.argv[1:]

    # Method 1: PATH lookup (preferred)
    try:
        return subprocess.call(["ontos"] + args)
    except FileNotFoundError:
        pass

    # Method 2: sys.executable -m ontos
    try:
        return subprocess.call([sys.executable, "-m", "ontos"] + args)
    except Exception:
        pass

    # Method 3: Graceful degradation
    print("Warning: ontos not found. Skipping hook.", file=sys.stderr)
    return 0

if __name__ == "__main__":
    sys.exit(run_hook())
'''
    path.write_text(shim, encoding='utf-8')

    # Set executable permission (no-op on Windows, required on Unix)
    if os.name != 'nt':  # Not Windows
        try:
            current_mode = path.stat().st_mode
            path.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        except OSError:
            pass  # Silently continue if chmod fails
