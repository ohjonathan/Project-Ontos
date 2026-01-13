"""
CLI entry point for Phase 1.

This module provides the main entry point for the `ontos` command.
It delegates to bundled legacy scripts to maintain exact v2.9.x behavior.

v1.1 Changes:
- Uses bundled scripts from ontos/_scripts/ (works for PyPI installs)
- Adds project root discovery (works from subdirectories)
- Passes through stdin/stdout/stderr (preserves TTY)

v1.2 Changes:
- Exempts `ontos init` from project root discovery (allows initialization in fresh directories)
"""

import sys
import subprocess
from pathlib import Path
from typing import Optional


def find_project_root() -> Optional[Path]:
    """
    Find the Ontos project root by walking up the directory tree.

    Looks for directories containing `.ontos/` or `.ontos-internal/`.
    Returns None if no project root is found.
    """
    current = Path.cwd().resolve()

    while current != current.parent:
        if (current / ".ontos-internal").exists() or (current / ".ontos").exists():
            return current
        current = current.parent

    # Check root as well
    if (current / ".ontos-internal").exists() or (current / ".ontos").exists():
        return current

    return None


def get_bundled_script(script_name: str) -> Path:
    """
    Get path to a bundled script in ontos/_scripts/.
    """
    return Path(__file__).parent / "_scripts" / script_name


def main():
    """
    Main CLI entry point.

    Delegates to bundled legacy scripts to maintain exact v2.9.x behavior.
    Phase 4 will implement full CLI directly in this module.
    """
    import ontos

    # Handle --version flag
    if len(sys.argv) > 1 and sys.argv[1] in ("--version", "-V"):
        print(f"ontos {ontos.__version__}")
        sys.exit(0)

    # Handle --help with no subcommand
    if len(sys.argv) == 1 or (len(sys.argv) > 1 and sys.argv[1] in ("--help", "-h")):
        print(f"ontos {ontos.__version__}")
        print()
        print("Usage: ontos <command> [options]")
        print()
        print("Commands:")
        print("  map         Generate context map")
        print("  log         Create session log")
        print("  init        Initialize project")
        print("  verify      Verify documentation")
        print("  query       Query documents")
        print("  promote     Promote document curation level")
        print()
        print("Use 'ontos <command> --help' for command-specific help.")
        sys.exit(0)

    # Handle init specially - it doesn't need project root (v1.2 fix)
    # Phase 3: Handle init natively to avoid module shadowing (B1 fix)
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        from ontos.commands.init import init_command, InitOptions
        options = InitOptions(
            path=Path.cwd(),
            force='--force' in sys.argv or '-f' in sys.argv,
            interactive=False,  # Reserved for v3.1
            skip_hooks='--skip-hooks' in sys.argv,
        )
        code, msg = init_command(options)
        print(msg)
        sys.exit(code)

    # Find project root (v1.1: support running from subdirectories)
    project_root = find_project_root()
    if project_root is None:
        print("Error: Not in an Ontos-enabled project.", file=sys.stderr)
        print("Run 'ontos init' to initialize a project, or navigate to a project directory.", file=sys.stderr)
        sys.exit(1)

    # Use bundled unified dispatcher (v1.1: works for PyPI installs)
    unified_cli = get_bundled_script("ontos.py")

    if not unified_cli.exists():
        # This should never happen if package is installed correctly
        print(f"Error: Bundled scripts not found at {unified_cli}", file=sys.stderr)
        print("This indicates a broken installation. Try reinstalling: pip install --force-reinstall ontos", file=sys.stderr)
        sys.exit(1)

    # v3.0: Pass project root via env var for non-editable installs
    # (bundled scripts can't reliably compute PROJECT_ROOT from __file__)
    import os
    env = os.environ.copy()
    env["ONTOS_PROJECT_ROOT"] = str(project_root)

    # Execute the unified dispatcher with the same arguments
    # v1.1: Pass through streams to preserve TTY and signals
    result = subprocess.run(
        [sys.executable, str(unified_cli)] + sys.argv[1:],
        cwd=project_root,  # Run from project root
        env=env,  # v3.0: Include project root env var
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
