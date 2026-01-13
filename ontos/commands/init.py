"""Ontos project initialization command."""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple
import subprocess
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
        return 1, "Already initialized. Use --force to reinitialize."

    # 2. Check for git repository (handle worktrees)
    git_check = _check_git_repo(project_root)
    if git_check is not None:
        return git_check

    # 3. Detect legacy .ontos/scripts/
    legacy_path = project_root / ".ontos" / "scripts"
    if legacy_path.exists():
        print("Warning: Legacy .ontos/scripts/ detected. Consider migrating.", file=sys.stderr)

    # 4. Create default config
    config = default_config()
    save_project_config(config, config_path)

    # 5. Create directory structure
    _create_directories(project_root, config)

    # 6. Generate initial context map
    _generate_initial_context_map(project_root, config)

    # 7. Install hooks (with collision safety)
    hooks_status = _install_hooks(project_root, options)

    # 8. Build success message
    msg = f"Initialized Ontos in {project_root}\n"
    msg += f"Created: .ontos.toml, {config.paths.context_map}\n"
    msg += "Tip: Run 'ontos export' for AI assistant integration"

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
        f"{config.paths.docs_dir}/strategy",
        f"{config.paths.docs_dir}/reference",
        f"{config.paths.docs_dir}/archive",
    ]
    for d in dirs:
        (root / d).mkdir(parents=True, exist_ok=True)


def _generate_initial_context_map(root: Path, config) -> None:
    """Generate initial context map by running the map command."""
    try:
        # Use subprocess to call the bundled map script
        # This is the same approach the legacy init uses
        bundled_map = Path(__file__).resolve().parent.parent / "_scripts" / "ontos_generate_context_map.py"
        if bundled_map.exists():
            result = subprocess.run(
                [sys.executable, str(bundled_map)],
                cwd=str(root),
                capture_output=True,
                timeout=30
            )
            if result.returncode == 0:
                print("   ✓ Context map generated", file=sys.stderr)
            else:
                print(f"Warning: Context map generation returned code {result.returncode}", file=sys.stderr)
        else:
            # Fallback: create a minimal context map placeholder
            context_map_path = root / config.paths.context_map
            if not context_map_path.exists():
                context_map_path.write_text(
                    "# Ontos Context Map\n\n"
                    "> Run `ontos map` to generate the full context map.\n"
                )
                print("   ✓ Created placeholder context map", file=sys.stderr)
    except subprocess.TimeoutExpired:
        print("Warning: Context map generation timed out", file=sys.stderr)
    except Exception as e:
        print(f"Warning: Could not generate initial context map: {e}", file=sys.stderr)


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
