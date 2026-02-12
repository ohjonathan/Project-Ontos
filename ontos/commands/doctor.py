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

from ontos.core.paths import resolve_project_root
from ontos.ui.output import OutputHandler


@dataclass
class CheckResult:
    """Result of a single health check."""
    name: str
    status: str  # "success", "failed", "warning"
    message: str
    details: Optional[str] = None


@dataclass
class DoctorOptions:
    """Configuration for doctor command."""
    verbose: bool = False
    json_output: bool = False
    scope: Optional[str] = None


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
            return "failed"
        elif self.warnings > 0:
            return "warning"
        return "success"


def check_configuration(repo_root: Optional[Path] = None) -> CheckResult:
    """Check 1: .ontos.toml exists and is valid."""
    try:
        root = resolve_project_root(repo_root=repo_root)
    except FileNotFoundError as exc:
        return CheckResult(
            name="configuration",
            status="failed",
            message="Could not resolve Ontos project root",
            details=str(exc),
        )
    config_path = root / ".ontos.toml"

    if not config_path.exists():
        return CheckResult(
            name="configuration",
            status="failed",
            message=".ontos.toml not found",
            details="Run 'ontos init' to create configuration"
        )

    try:
        from ontos.io.config import load_project_config
        load_project_config(repo_root=root)
        return CheckResult(
            name="configuration",
            status="success",
            message=".ontos.toml valid"
        )
    except Exception as e:
        return CheckResult(
            name="configuration",
            status="failed",
            message=".ontos.toml malformed",
            details=str(e)
        )


def check_git_hooks(repo_root: Optional[Path] = None) -> CheckResult:
    """Check 2: Git hooks installed and point to ontos."""
    try:
        root = resolve_project_root(repo_root=repo_root)
    except FileNotFoundError as exc:
        return CheckResult(
            name="git_hooks",
            status="warning",
            message="Not an Ontos project",
            details=str(exc),
        )

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
                status="failed",
                message="Git not working properly",
                details=result.stderr
            )
    except FileNotFoundError:
        return CheckResult(
            name="git_hooks",
            status="failed",
            message="Git executable not found",
            details="Install git to enable hook functionality"
        )
    except subprocess.TimeoutExpired:
        return CheckResult(
            name="git_hooks",
            status="warning",
            message="Git check timed out"
        )

    # Check if in a git repo
    git_dir = root / ".git"
    if not git_dir.is_dir():
        return CheckResult(
            name="git_hooks",
            status="warning",
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
            status="warning",
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
            status="warning",
            message=f"Non-Ontos hooks: {', '.join(non_ontos)}",
            details="These hooks are not managed by Ontos"
        )

    return CheckResult(
        name="git_hooks",
        status="success",
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
            status="success",
            message=f"{version_str} (>=3.9 required)"
        )
    else:
        return CheckResult(
            name="python_version",
            status="failed",
            message=f"{version_str} (>=3.9 required)",
            details="Upgrade Python to 3.9 or later"
        )


def check_docs_directory(scope: Optional[str] = None, repo_root: Optional[Path] = None) -> CheckResult:
    """Check 4: Docs directory exists and contains .md files."""
    try:
        from ontos.io.config import load_project_config
        from ontos.io.scan_scope import ScanScope, collect_scoped_documents, resolve_scan_scope

        root = resolve_project_root(repo_root=repo_root)
        config = load_project_config(repo_root=root)
        effective_scope = resolve_scan_scope(scope, config.scanning.default_scope)
        docs_dir = root / config.paths.docs_dir

        if effective_scope == ScanScope.DOCS and not docs_dir.exists():
            return CheckResult(
                name="docs_directory",
                status="failed",
                message=f"Docs directory not found: {docs_dir}",
                details="Create the docs directory or update .ontos.toml"
            )

        md_files = collect_scoped_documents(
            root,
            config,
            effective_scope,
            base_skip_patterns=config.scanning.skip_patterns,
        )
    except Exception as e:
        return CheckResult(
            name="docs_directory",
            status="warning",
            message="Docs directory check failed",
            details=str(e),
        )

    if not md_files:
        return CheckResult(
            name="docs_directory",
            status="warning",
            message=f"No .md files in selected scope ({scope or 'docs'})",
            details="Add documentation files to track"
        )

    return CheckResult(
        name="docs_directory",
        status="success",
        message=f"{len(md_files)} documents in {docs_dir.name}/"
    )


def check_context_map(repo_root: Optional[Path] = None) -> CheckResult:
    """Check 5: Context map exists and has valid frontmatter."""
    try:
        from ontos.io.config import load_project_config
        root = resolve_project_root(repo_root=repo_root)
        config = load_project_config(repo_root=root)
        context_map = root / config.paths.context_map
    except Exception:
        try:
            root = resolve_project_root(repo_root=repo_root)
            context_map = root / "Ontos_Context_Map.md"
        except Exception as e:
            return CheckResult(
                name="context_map",
                status="warning",
                message="Context map check failed",
                details=str(e),
            )

    if not context_map.exists():
        return CheckResult(
            name="context_map",
            status="failed",
            message="Context map not found",
            details=f"Expected at {context_map}. Run 'ontos map' to generate."
        )

    try:
        content = context_map.read_text()
        if not content.startswith("---"):
            return CheckResult(
                name="context_map",
                status="warning",
                message="Context map missing frontmatter",
                details="Run 'ontos map' to regenerate"
            )

        return CheckResult(
            name="context_map",
            status="success",
            message="Context map valid"
        )
    except Exception as e:
        return CheckResult(
            name="context_map",
            status="failed",
            message="Could not read context map",
            details=str(e)
        )


def check_validation(scope: Optional[str] = None, repo_root: Optional[Path] = None) -> CheckResult:
    """Check 6: No validation errors in current documents."""
    try:
        from ontos.io.config import load_project_config
        from ontos.io.scan_scope import ScanScope, collect_scoped_documents, resolve_scan_scope

        root = resolve_project_root(repo_root=repo_root)
        config = load_project_config(repo_root=root)
        effective_scope = resolve_scan_scope(scope, config.scanning.default_scope)
        docs_dir = root / config.paths.docs_dir

        if effective_scope == ScanScope.DOCS and not docs_dir.exists():
            return CheckResult(
                name="validation",
                status="warning",
                message="Cannot validate (no docs directory)"
            )

        md_files = collect_scoped_documents(
            root,
            config,
            effective_scope,
            base_skip_patterns=config.scanning.skip_patterns,
        )
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
                status="warning",
                message=f"{issues} potential issues found",
                details="Run 'ontos map --strict' for full validation"
            )

        return CheckResult(
            name="validation",
            status="success",
            message="No obvious issues"
        )

    except Exception as e:
        return CheckResult(
            name="validation",
            status="warning",
            message="Validation check skipped",
            details=str(e)
        )


def check_cli_availability() -> CheckResult:
    """Check 7: ontos CLI accessible in PATH."""
    ontos_path = shutil.which("ontos")

    if ontos_path:
        return CheckResult(
            name="cli_availability",
            status="success",
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
                status="success",
                message="ontos available via 'python -m ontos'"
            )
    except Exception:
        pass

    return CheckResult(
        name="cli_availability",
        status="warning",
        message="ontos not in PATH",
        details="Install with 'pip install ontos' or use 'python -m ontos'"
    )


def check_agents_staleness(repo_root: Optional[Path] = None) -> CheckResult:
    """Check 8: AGENTS.md is not stale relative to source files."""
    try:
        root = resolve_project_root(repo_root=repo_root)
    except Exception as e:
        return CheckResult(
            name="agents_staleness",
            status="warning",
            message="Cannot determine AGENTS.md staleness",
            details=str(e),
        )
    
    agents_path = root / "AGENTS.md"
    
    if not agents_path.exists():
        return CheckResult(
            name="agents_staleness",
            status="warning",
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
            config = load_project_config(repo_root=root)
            context_map = root / config.paths.context_map
            logs_dir = root / config.paths.logs_dir
        except Exception:
            context_map = root / "Ontos_Context_Map.md"
            logs_dir = root / ".ontos-internal" / "logs"
        
        config_path = root / ".ontos.toml"
        
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
                status="warning",
                message="Cannot determine AGENTS.md staleness - no source files found"
            )
        
        max_source_mtime = max(source_mtimes)
        
        if agents_mtime < max_source_mtime:
            return CheckResult(
                name="agents_staleness",
                status="warning",
                message="AGENTS.md may be stale. Run 'ontos agents' to regenerate."
            )
        
        return CheckResult(
            name="agents_staleness",
            status="success",
            message="AGENTS.md up to date"
        )
    
    except Exception as e:
        return CheckResult(
            name="agents_staleness",
            status="warning",
            message="Could not check AGENTS.md staleness",
            details=str(e)
        )


def check_environment_manifests(repo_root: Optional[Path] = None) -> CheckResult:
    """Check 9: Detect project environment manifests (v3.2)."""
    from ontos.commands.env import detect_manifests
    
    try:
        root = resolve_project_root(repo_root=repo_root)
        manifests, warnings = detect_manifests(root)
        
        if warnings:
            # Surface parse warnings (v3.2)
            warning_msg = f"Detected {len(manifests)} manifests with {len(warnings)} parse warnings"
            return CheckResult(
                name="environment",
                status="warning",
                message=warning_msg,
                details="\n".join(warnings)
            )

        if not manifests:
            return CheckResult(
                name="environment",
                status="warning",
                message="No environment manifests detected",
                details="Run 'ontos env' to see supported project types"
            )
            
        manifest_names = [m.path.name for m in manifests]
        return CheckResult(
            name="environment",
            status="success",
            message=f"Detected: {', '.join(manifest_names)}"
        )
    except Exception as e:
        return CheckResult(
            name="environment",
            status="warning",
            message="Environment check failed",
            details=str(e)
        )


def _get_config_path(repo_root: Optional[Path] = None) -> Optional[Path]:
    """Get config path if it exists."""
    root = resolve_project_root(repo_root=repo_root)
    config_path = root / ".ontos.toml"
    if config_path.exists():
        return config_path
    return None


def _format_verbose_config(repo_root: Optional[Path] = None) -> str:
    """Build resolved configuration details for verbose output."""
    from ontos.io.config import load_project_config

    try:
        project_root = resolve_project_root(repo_root=repo_root)
        config = load_project_config(repo_root=project_root)

        lines = [
            "Configuration:",
            f"  repo_root:    {project_root}",
            f"  config_path:  {_get_config_path(project_root) or 'default'}",
            f"  docs_dir:     {project_root / config.paths.docs_dir}",
            f"  context_map:  {project_root / config.paths.context_map}",
            "",
        ]
        return "\n".join(lines)
    except Exception as e:
        return f"Configuration: Unable to load ({e})\n"


def _run_doctor_command(options: DoctorOptions) -> Tuple[int, DoctorResult]:
    """
    Run health checks and return results.

    Returns:
        Tuple of (exit_code, DoctorResult)
        Exit code 0 if all pass, 1 if any fail
    """
    try:
        repo_root = resolve_project_root()
    except FileNotFoundError as exc:
        result = DoctorResult(
            checks=[
                CheckResult(
                    name="project_root",
                    status="failed",
                    message="Could not resolve Ontos project root",
                    details=str(exc),
                )
            ],
            passed=0,
            failed=1,
            warnings=0,
        )
        return 1, result

    result = DoctorResult()

    checks = [
        lambda: check_configuration(repo_root),
        lambda: check_git_hooks(repo_root),
        check_python_version,
        lambda: check_docs_directory(options.scope, repo_root),
        lambda: check_context_map(repo_root),
        lambda: check_validation(options.scope, repo_root),
        check_cli_availability,
        lambda: check_agents_staleness(repo_root),
        lambda: check_environment_manifests(repo_root),
    ]

    for check_fn in checks:
        check_result = check_fn()
        result.checks.append(check_result)

        if check_result.status == "success":
            result.passed += 1
        elif check_result.status == "failed":
            result.failed += 1
        else:
            result.warnings += 1

    exit_code = 1 if result.failed > 0 else 0
    return exit_code, result


def doctor_command(options: DoctorOptions) -> int:
    """Run health checks and return exit code only."""
    exit_code, _ = _run_doctor_command(options)
    return exit_code


def format_doctor_output(result: DoctorResult, verbose: bool = False) -> str:
    """Format doctor results for human-readable output."""
    lines = []

    for check in result.checks:
        if check.status == "success":
            icon = "OK"
        elif check.status == "failed":
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


def emit_verbose_config(options: DoctorOptions, output: OutputHandler, repo_root: Optional[Path] = None) -> None:
    """Emit verbose configuration details via OutputHandler."""
    if not options.verbose:
        return
    output.plain(_format_verbose_config(repo_root=repo_root))
