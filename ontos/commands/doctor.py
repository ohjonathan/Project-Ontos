# ontos/commands/doctor.py
"""
Health check and diagnostics command.

Implements 7 health checks per Roadmap 6.4 and Spec v1.1 Section 4.2.
Decision: Option B (Standard) - all 7 checks with graceful error handling.
"""

import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple


@dataclass
class CheckResult:
    """Result of a single health check."""
    name: str
    status: str  # "pass", "fail", "warn"
    message: str
    details: Optional[str] = None


@dataclass
class DoctorOptions:
    """Configuration for doctor command."""
    verbose: bool = False
    json_output: bool = False


@dataclass
class DoctorResult:
    """Result of all health checks."""
    checks: List[CheckResult] = field(default_factory=list)
    passed: int = 0
    failed: int = 0
    warnings: int = 0

    @property
    def status(self) -> str:
        """Overall status: pass, fail, or warn."""
        if self.failed > 0:
            return "fail"
        elif self.warnings > 0:
            return "warn"
        return "pass"


def check_configuration() -> CheckResult:
    """Check 1: .ontos.toml exists and is valid."""
    config_path = Path.cwd() / ".ontos.toml"

    if not config_path.exists():
        return CheckResult(
            name="configuration",
            status="fail",
            message=".ontos.toml not found",
            details="Run 'ontos init' to create configuration"
        )

    try:
        from ontos.io.config import load_project_config
        load_project_config()
        return CheckResult(
            name="configuration",
            status="pass",
            message=".ontos.toml valid"
        )
    except Exception as e:
        return CheckResult(
            name="configuration",
            status="fail",
            message=".ontos.toml malformed",
            details=str(e)
        )


def check_git_hooks() -> CheckResult:
    """Check 2: Git hooks installed and point to ontos."""
    # Verify git is available (graceful handling)
    try:
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            return CheckResult(
                name="git_hooks",
                status="fail",
                message="Git not working properly",
                details=result.stderr
            )
    except FileNotFoundError:
        return CheckResult(
            name="git_hooks",
            status="fail",
            message="Git executable not found",
            details="Install git to enable hook functionality"
        )
    except subprocess.TimeoutExpired:
        return CheckResult(
            name="git_hooks",
            status="warn",
            message="Git check timed out"
        )

    # Check if in a git repo
    git_dir = Path.cwd() / ".git"
    if not git_dir.is_dir():
        return CheckResult(
            name="git_hooks",
            status="warn",
            message="Not a git repository",
            details="Hooks are not applicable outside a git repository"
        )

    # Check for hook files
    hooks_dir = git_dir / "hooks"
    pre_push = hooks_dir / "pre-push"
    pre_commit = hooks_dir / "pre-commit"

    missing = []
    if not pre_push.exists():
        missing.append("pre-push")
    if not pre_commit.exists():
        missing.append("pre-commit")

    if missing:
        return CheckResult(
            name="git_hooks",
            status="warn",
            message=f"Hooks missing: {', '.join(missing)}",
            details="Run 'ontos init --force' to install hooks"
        )

    # Check if hooks are Ontos-managed (lenient for reporting)
    non_ontos = []

    for hook_path in [pre_push, pre_commit]:
        if hook_path.exists():
            if not _is_ontos_hook_lenient(hook_path):
                non_ontos.append(hook_path.name)

    if non_ontos:
        return CheckResult(
            name="git_hooks",
            status="warn",
            message=f"Non-Ontos hooks: {', '.join(non_ontos)}",
            details="These hooks are not managed by Ontos"
        )

    return CheckResult(
        name="git_hooks",
        status="pass",
        message="pre-push, pre-commit installed"
    )


def _is_ontos_hook_lenient(hook_path: Path) -> bool:
    """Check if hook is Ontos-managed (heuristic for reporting only).
    
    Uses a lenient heuristic that checks for:
    1. The official marker comment: # ontos-managed-hook
    2. Substring "ontos hook" in content
    3. Python module execution: python3 -m ontos
    
    NOTE: This is for reporting in `ontos doctor` only. The `ontos init`
    command uses strict marker checking for overwrite decisions.
    
    Args:
        hook_path: Path to the git hook file.
        
    Returns:
        True if the hook appears to be Ontos-managed.
    """
    try:
        content = hook_path.read_text()
        return (
            "# ontos-managed-hook" in content or
            "ontos hook" in content.lower() or
            "python3 -m ontos" in content
        )
    except Exception:
        return False


def check_python_version() -> CheckResult:
    """Check 3: Python version >= 3.9."""
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"

    if version >= (3, 9):
        return CheckResult(
            name="python_version",
            status="pass",
            message=f"{version_str} (>=3.9 required)"
        )
    else:
        return CheckResult(
            name="python_version",
            status="fail",
            message=f"{version_str} (>=3.9 required)",
            details="Upgrade Python to 3.9 or later"
        )


def check_docs_directory() -> CheckResult:
    """Check 4: Docs directory exists and contains .md files."""
    try:
        from ontos.io.config import load_project_config
        config = load_project_config()
        docs_dir = Path.cwd() / config.paths.docs_dir
    except Exception:
        docs_dir = Path.cwd() / "docs"

    if not docs_dir.exists():
        return CheckResult(
            name="docs_directory",
            status="fail",
            message=f"Docs directory not found: {docs_dir}",
            details="Create the docs directory or update .ontos.toml"
        )

    md_files = list(docs_dir.rglob("*.md"))
    if not md_files:
        return CheckResult(
            name="docs_directory",
            status="warn",
            message=f"No .md files in {docs_dir}",
            details="Add documentation files to track"
        )

    return CheckResult(
        name="docs_directory",
        status="pass",
        message=f"{len(md_files)} documents in {docs_dir.name}/"
    )


def check_context_map() -> CheckResult:
    """Check 5: Context map exists and has valid frontmatter."""
    try:
        from ontos.io.config import load_project_config
        config = load_project_config()
        context_map = Path.cwd() / config.paths.context_map
    except Exception:
        context_map = Path.cwd() / "Ontos_Context_Map.md"

    if not context_map.exists():
        return CheckResult(
            name="context_map",
            status="fail",
            message="Context map not found",
            details=f"Expected at {context_map}. Run 'ontos map' to generate."
        )

    try:
        content = context_map.read_text()
        if not content.startswith("---"):
            return CheckResult(
                name="context_map",
                status="warn",
                message="Context map missing frontmatter",
                details="Run 'ontos map' to regenerate"
            )

        return CheckResult(
            name="context_map",
            status="pass",
            message="Context map valid"
        )
    except Exception as e:
        return CheckResult(
            name="context_map",
            status="fail",
            message="Could not read context map",
            details=str(e)
        )


def check_validation() -> CheckResult:
    """Check 6: No validation errors in current documents."""
    try:
        from ontos.io.config import load_project_config
        config = load_project_config()
        docs_dir = Path.cwd() / config.paths.docs_dir

        if not docs_dir.exists():
            return CheckResult(
                name="validation",
                status="warn",
                message="Cannot validate (no docs directory)"
            )

        md_files = list(docs_dir.rglob("*.md"))
        issues = 0

        for md_file in md_files[:50]:  # Check first 50 to avoid slowness
            try:
                content = md_file.read_text()
                if content.strip() and not content.startswith("---"):
                    issues += 1
            except Exception:
                issues += 1

        if issues > 0:
            return CheckResult(
                name="validation",
                status="warn",
                message=f"{issues} potential issues found",
                details="Run 'ontos map --strict' for full validation"
            )

        return CheckResult(
            name="validation",
            status="pass",
            message="No obvious issues"
        )

    except Exception as e:
        return CheckResult(
            name="validation",
            status="warn",
            message="Validation check skipped",
            details=str(e)
        )


def check_cli_availability() -> CheckResult:
    """Check 7: ontos CLI accessible in PATH."""
    ontos_path = shutil.which("ontos")

    if ontos_path:
        return CheckResult(
            name="cli_availability",
            status="pass",
            message=f"ontos available at {ontos_path}"
        )

    # Check if python -m ontos works
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ontos", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return CheckResult(
                name="cli_availability",
                status="pass",
                message="ontos available via 'python -m ontos'"
            )
    except Exception:
        pass

    return CheckResult(
        name="cli_availability",
        status="warn",
        message="ontos not in PATH",
        details="Install with 'pip install ontos' or use 'python -m ontos'"
    )


def check_agents_staleness() -> CheckResult:
    """Check 8: AGENTS.md is not stale relative to source files."""
    # Use shared repo-root helper (M2 fix)
    from ontos.commands.agents import find_repo_root
    
    repo_root = find_repo_root()
    if repo_root is None:
        repo_root = Path.cwd()  # Fallback for doctor — still check if possible
    
    agents_path = repo_root / "AGENTS.md"
    
    if not agents_path.exists():
        return CheckResult(
            name="agents_staleness",
            status="warn",
            message="AGENTS.md not found",
            details="Run 'ontos agents' to generate"
        )
    
    try:
        agents_mtime = agents_path.stat().st_mtime
        
        # Get source file paths
        source_paths = []
        
        # Context map
        try:
            from ontos.io.config import load_project_config
            config = load_project_config()
            context_map = repo_root / config.paths.context_map
            logs_dir = repo_root / config.paths.logs_dir
        except Exception:
            context_map = repo_root / "Ontos_Context_Map.md"
            logs_dir = repo_root / ".ontos-internal" / "logs"
        
        config_path = repo_root / ".ontos.toml"
        
        # Collect existing source file mtimes
        source_mtimes = []
        
        if context_map.exists():
            source_mtimes.append(context_map.stat().st_mtime)
            source_paths.append(context_map.name)
        
        if config_path.exists():
            source_mtimes.append(config_path.stat().st_mtime)
            source_paths.append(config_path.name)
        
        if logs_dir.exists():
            # M5 fix: Use max() for O(n) instead of sorted() O(n log n)
            log_files = list(logs_dir.glob("*.md"))
            if log_files:
                max_log_mtime = max(f.stat().st_mtime for f in log_files)
                source_mtimes.append(max_log_mtime)
                source_paths.append(f"{logs_dir.name}/")
        
        if not source_mtimes:
            return CheckResult(
                name="agents_staleness",
                status="warn",
                message="Cannot determine AGENTS.md staleness - no source files found"
            )
        
        max_source_mtime = max(source_mtimes)
        
        if agents_mtime < max_source_mtime:
            return CheckResult(
                name="agents_staleness",
                status="warn",
                message="AGENTS.md may be stale. Run 'ontos agents' to regenerate."
            )
        
        return CheckResult(
            name="agents_staleness",
            status="pass",
            message="AGENTS.md up to date"
        )
    
    except Exception as e:
        return CheckResult(
            name="agents_staleness",
            status="warn",
            message="Could not check AGENTS.md staleness",
            details=str(e)
        )


def check_environment_manifests() -> CheckResult:
    """Check 9: Detect project environment manifests (v3.2)."""
    from ontos.commands.env import detect_manifests
    
    try:
        manifests, warnings = detect_manifests(Path.cwd())
        
        if warnings:
            # Surface parse warnings (v3.2)
            warning_msg = f"Detected {len(manifests)} manifests with {len(warnings)} parse warnings"
            return CheckResult(
                name="environment",
                status="warn",
                message=warning_msg,
                details="\n".join(warnings)
            )

        if not manifests:
            return CheckResult(
                name="environment",
                status="warn",
                message="No environment manifests detected",
                details="Run 'ontos env' to see supported project types"
            )
            
        manifest_names = [m.path.name for m in manifests]
        return CheckResult(
            name="environment",
            status="pass",
            message=f"Detected: {', '.join(manifest_names)}"
        )
    except Exception as e:
        return CheckResult(
            name="environment",
            status="warn",
            message="Environment check failed",
            details=str(e)
        )


def _get_config_path() -> Optional[Path]:
    """Get config path if it exists."""
    config_path = Path.cwd() / ".ontos.toml"
    if config_path.exists():
        return config_path
    return None


def _print_verbose_config(options: DoctorOptions) -> None:
    """Print resolved configuration paths in verbose mode."""
    if not options.verbose:
        return

    from ontos.io.files import find_project_root
    from ontos.io.config import load_project_config

    try:
        project_root = find_project_root()
        config = load_project_config(repo_root=project_root)

        print("Configuration:")
        print(f"  repo_root:    {project_root}")
        print(f"  config_path:  {_get_config_path() or 'default'}")
        print(f"  docs_dir:     {project_root / config.paths.docs_dir}")
        print(f"  context_map:  {project_root / config.paths.context_map}")
        print()
    except Exception as e:
        print(f"Configuration: Unable to load ({e})")
        print()


def doctor_command(options: DoctorOptions) -> Tuple[int, DoctorResult]:
    """
    Run health checks and return results.

    Returns:
        Tuple of (exit_code, DoctorResult)
        Exit code 0 if all pass, 1 if any fail
    """
    # Print verbose config if requested
    _print_verbose_config(options)

    result = DoctorResult()

    checks = [
        check_configuration,
        check_git_hooks,
        check_python_version,
        check_docs_directory,
        check_context_map,
        check_validation,
        check_cli_availability,
        check_agents_staleness,
        check_environment_manifests,
    ]

    for check_fn in checks:
        check_result = check_fn()
        result.checks.append(check_result)

        if check_result.status == "pass":
            result.passed += 1
        elif check_result.status == "fail":
            result.failed += 1
        else:
            result.warnings += 1

    exit_code = 1 if result.failed > 0 else 0
    return exit_code, result


def format_doctor_output(result: DoctorResult, verbose: bool = False) -> str:
    """Format doctor results for human-readable output."""
    lines = []

    for check in result.checks:
        if check.status == "pass":
            icon = "OK"
        elif check.status == "fail":
            icon = "FAIL"
        else:
            icon = "WARN"

        lines.append(f"{icon}: {check.name}: {check.message}")

        if verbose and check.details:
            lines.append(f"     {check.details}")

    lines.append("")
    lines.append(
        f"Health check: {result.passed} passed, "
        f"{result.failed} failed, {result.warnings} warnings"
    )

    return "\n".join(lines)
