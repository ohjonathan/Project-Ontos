# ontos/commands/doctor.py
"""
Health check and diagnostics command.

Implements the CLI health checks with graceful error handling.
"""

import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional, Tuple

from ontos.core.errors import OntosUserError
from ontos.core.paths import resolve_project_root
from ontos.ui.json_output import ExitCode
from ontos.ui.output import OutputHandler


@dataclass
class CheckResult:
    """Result of a single health check."""
    name: str
    status: str  # "success", "failed", "warning"
    message: str
    details: Optional[str] = None
    # (#133) Structured counts + count_basis labels so doctor's numbers can
    # be reconciled with the surface they came from (e.g. activate).
    data: Optional[dict] = None


@dataclass
class DoctorOptions:
    """Configuration for doctor command."""
    verbose: bool = False
    json_output: bool = False
    scope: Optional[str] = None
    frontmatter: bool = False


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
        import ontos
        from ontos.core.config import required_version_incompatibility
        from ontos.io.config import load_project_config
        config = load_project_config(repo_root=root)
        version_issue = required_version_incompatibility(
            config.ontos.required_version,
            ontos.__version__,
        )
        if version_issue:
            return CheckResult(
                name="configuration",
                status="failed",
                message="Running Ontos version is incompatible with project config",
                details=version_issue,
            )
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

    # Check if in a git repo. Use git itself so linked worktrees with a
    # .git file are recognized correctly.
    inside = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=5,
    )
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        return CheckResult(
            name="git_hooks",
            status="warning",
            message="Not a git repository",
            details="Hooks are not applicable outside a git repository"
        )

    # Check for hook files
    hook_path_result = subprocess.run(
        ["git", "rev-parse", "--git-path", "hooks"],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=5,
    )
    hooks_raw = hook_path_result.stdout.strip() if hook_path_result.returncode == 0 else ".git/hooks"
    hooks_dir = Path(hooks_raw)
    if not hooks_dir.is_absolute():
        hooks_dir = root / hooks_dir
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

        # (#136) Verify generator provenance against the installed CLI so a
        # map produced by an older install is surfaced instead of silently
        # passing as "valid".
        import ontos
        from ontos.io.yaml import parse_frontmatter_content

        frontmatter, _ = parse_frontmatter_content(content)
        generator_version = (frontmatter or {}).get("generator_version")
        if not generator_version:
            return CheckResult(
                name="context_map",
                status="warning",
                message="Context map predates generator metadata",
                details="Run 'ontos map' to regenerate with provenance info",
            )
        if str(generator_version) != ontos.__version__:
            return CheckResult(
                name="context_map",
                status="warning",
                message=(
                    f"Context map generated by Ontos {generator_version}, "
                    f"installed {ontos.__version__}"
                ),
                details="Run 'ontos map' to refresh",
            )

        return CheckResult(
            name="context_map",
            status="success",
            message=f"Context map valid (generator {generator_version})"
        )
    except Exception as e:
        return CheckResult(
            name="context_map",
            status="failed",
            message="Could not read context map",
            details=str(e)
        )


def check_activation_health(
    scope: Optional[str] = None,
    repo_root: Optional[Path] = None,
) -> CheckResult:
    """(#117/#133) Align doctor counts with `ontos activate` by construction.

    Delegates to the SAME activation pipeline (`run_activation` with
    write_map=False — read-only) instead of running a parallel snapshot
    validation, so doctor's warning/error counts can never drift from what
    `ontos activate` reports. Hard errors → `failed`; warnings alone stay
    `warning`; clean is `success`.
    """
    try:
        from ontos.commands.activate import run_activation

        root = resolve_project_root(repo_root=repo_root)
        code, payload = run_activation(scope, write_map=False, root=root)
    except Exception as exc:
        return CheckResult(
            name="activation_health",
            status="warning",
            message="Activation health check skipped",
            details=str(exc),
        )

    summary = payload.get("summary", {})
    error_count = summary.get("validation_errors", 0)
    warning_count = summary.get("validation_warnings", 0)
    load_issue_count = summary.get("load_issues", 0)
    info_count = summary.get("validation_info", 0)
    data = {
        "validation_errors": error_count,
        "validation_warnings": warning_count,
        "validation_info": info_count,
        "load_issues": load_issue_count,
        "scope": payload.get("scope"),
        "count_basis": "activation_pipeline",
    }

    if code in {ExitCode.USAGE, ExitCode.INTERNAL, ExitCode.INTERRUPTED}:
        return CheckResult(
            name="activation_health",
            status="warning",
            message="Activation context unavailable",
            details=payload.get("reason"),
            data=data,
        )

    if error_count:
        error_records = payload.get("validation", {}).get("errors", [])
        details = "; ".join(
            f"[{record.get('rule_id', 'unknown')}] {record.get('message', '')}"
            for record in error_records[:5]
        ) or None
        return CheckResult(
            name="activation_health",
            status="failed",
            message=(
                f"{error_count} activation error(s), "
                f"{warning_count} warning(s) — counts match `ontos activate` "
                "(basis: activation pipeline)"
            ),
            details=details,
            data=data,
        )
    if warning_count or load_issue_count:
        return CheckResult(
            name="activation_health",
            status="warning",
            message=(
                f"{warning_count} activation warning(s); no hard errors — "
                "counts match `ontos activate` (basis: activation pipeline)"
            ),
            data=data,
        )
    return CheckResult(
        name="activation_health",
        status="success",
        message="Activation clean (no errors or warnings)",
        data=data,
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

        # (#133) This is a bounded heuristic, not full validation — label it
        # as such so its count is never read against activation totals.
        data = {
            "count_basis": "frontmatter_quick_scan",
            "files_checked": min(len(md_files), 50),
        }
        if issues > 0:
            return CheckResult(
                name="validation",
                status="warning",
                message=(
                    f"{issues} file(s) missing frontmatter "
                    "(quick scan, first 50 files; full counts in activation_health)"
                ),
                details="Run 'ontos map --strict' for full validation",
                data=data,
            )

        return CheckResult(
            name="validation",
            status="success",
            message="No obvious issues (quick scan, first 50 files)",
            data=data,
        )

    except Exception as e:
        return CheckResult(
            name="validation",
            status="warning",
            message="Validation check skipped",
            details=str(e)
        )


def check_frontmatter_enums(scope: Optional[str] = None, repo_root: Optional[Path] = None) -> CheckResult:
    """Check frontmatter type/status enum diagnostics with exact paths."""
    try:
        from ontos.core.frontmatter_repair import build_enum_repair_plan, enum_issue_summary
        from ontos.io.config import load_project_config
        from ontos.io.scan_scope import collect_scoped_documents, resolve_scan_scope

        root = resolve_project_root(repo_root=repo_root)
        config = load_project_config(repo_root=root)
        effective_scope = resolve_scan_scope(scope, config.scanning.default_scope)
        files = collect_scoped_documents(
            root,
            config,
            effective_scope,
            base_skip_patterns=list(config.scanning.skip_patterns),
        )
        aliases = config.frontmatter.aliases
        plan = build_enum_repair_plan(
            files,
            type_aliases=aliases.get("type"),
            status_aliases=aliases.get("status"),
        )
    except Exception as exc:
        return CheckResult(
            name="frontmatter_enums",
            status="warning",
            message="Frontmatter enum check failed",
            details=str(exc),
        )

    if not plan.diagnostics:
        return CheckResult(
            name="frontmatter_enums",
            status="success",
            message="No invalid type/status enum values",
        )

    details = "\n".join(enum_issue_summary(plan.diagnostics, root=root, limit=10))
    return CheckResult(
        name="frontmatter_enums",
        status="warning",
        message=(
            f"{len(plan.diagnostics)} invalid enum value(s); "
            f"{len(plan.repairable_edits)} repairable"
        ),
        details=details,
    )


_CLI_VERSION_PATTERN = re.compile(
    r"(?:^|\s)(?:ontos\s+)?v?(\d+(?:\.\d+){1,2})(?:\s|$)",
    re.IGNORECASE,
)


def check_cli_availability(repo_root: Optional[Path] = None) -> CheckResult:
    """Check 7: execute the PATH CLI and detect package/version skew."""
    import ontos
    from ontos.core.config import (
        required_version_incompatibility,
        version_satisfies_requirement,
    )

    running_version = ontos.__version__
    required_version: Optional[str] = None
    if repo_root is not None:
        try:
            from ontos.io.config import load_project_config

            required_version = load_project_config(
                repo_root=resolve_project_root(repo_root=repo_root)
            ).ontos.required_version
        except Exception:
            # The dedicated configuration check reports malformed config.
            required_version = None

    ontos_path = shutil.which("ontos")

    if ontos_path:
        try:
            result = subprocess.run(
                [ontos_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
        except FileNotFoundError:
            return CheckResult(
                name="cli_availability",
                status="warning",
                message=f"PATH ontos disappeared before it could be executed: {ontos_path}",
                details=f"Use '{sys.executable} -m ontos' as the fallback.",
            )
        except subprocess.TimeoutExpired:
            return CheckResult(
                name="cli_availability",
                status="warning",
                message=f"PATH ontos timed out: {ontos_path}",
                details=f"Use '{sys.executable} -m ontos' as the fallback.",
            )

        if result.returncode != 0:
            details = (result.stderr or result.stdout).strip() or "No diagnostic output"
            return CheckResult(
                name="cli_availability",
                status="warning",
                message=f"PATH ontos failed its version probe: {ontos_path}",
                details=(
                    f"{details}. Use '{sys.executable} -m ontos' as the fallback."
                ),
            )

        path_version = _extract_cli_version(result.stdout, result.stderr)
        if path_version is None:
            return CheckResult(
                name="cli_availability",
                status="warning",
                message=f"PATH ontos returned an unrecognized version: {ontos_path}",
                details=(result.stdout or result.stderr).strip() or "No version output",
            )

        version_issue = required_version_incompatibility(
            required_version,
            path_version,
        )
        if version_issue:
            return CheckResult(
                name="cli_availability",
                status="failed",
                message=f"PATH ontos {path_version} is incompatible with this project",
                details=(
                    f"{version_issue} The running Python package is {running_version}; "
                    f"retry with '{sys.executable} -m ontos'."
                ),
            )

        if not version_satisfies_requirement(path_version, f"={running_version}"):
            return CheckResult(
                name="cli_availability",
                status="warning",
                message=(
                    f"PATH ontos reports {path_version}, but the running package is "
                    f"{running_version}"
                ),
                details=(
                    f"{ontos_path} shadows the running package. Activation should "
                    f"retry with '{sys.executable} -m ontos'."
                ),
            )

        return CheckResult(
            name="cli_availability",
            status="success",
            message=f"ontos {path_version} available at {ontos_path}",
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
            module_version = _extract_cli_version(result.stdout, result.stderr)
            if module_version is None:
                return CheckResult(
                    name="cli_availability",
                    status="warning",
                    message="'python -m ontos' returned an unrecognized version",
                    details=(result.stdout or result.stderr).strip() or "No version output",
                )
            return CheckResult(
                name="cli_availability",
                status="success",
                message=f"ontos {module_version} available via 'python -m ontos'",
            )
    except Exception:
        pass

    return CheckResult(
        name="cli_availability",
        status="warning",
        message="ontos not in PATH",
        details="Install with 'pip install ontos' or use 'python -m ontos'"
    )


def _extract_cli_version(stdout: str, stderr: str) -> Optional[str]:
    """Extract the version from ``ontos --version`` without shell parsing."""
    match = _CLI_VERSION_PATTERN.search(f"{stdout}\n{stderr}")
    return match.group(1) if match else None


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


def check_antigravity_mcp() -> CheckResult:
    """Check 10: Antigravity native MCP config status."""
    from ontos.core.antigravity_mcp import inspect_antigravity_ontos_config

    try:
        inspection = inspect_antigravity_ontos_config()
    except Exception as exc:
        return CheckResult(
            name="antigravity_mcp",
            status="warning",
            message="Antigravity MCP check failed",
            details=str(exc),
        )

    return CheckResult(
        name="antigravity_mcp",
        status="success" if inspection.ok else "warning",
        message=inspection.message,
        details=inspection.details,
    )


def _cursor_scope_summary(inspection) -> Tuple[str, str]:
    """Normalize Cursor adapter inspection into status/reason for aggregation."""
    if hasattr(inspection, "status") and hasattr(inspection, "reason"):
        return inspection.status, inspection.reason
    if inspection.code in {"invalid_json", "invalid_root", "empty", "unreadable"}:
        return "warning", "malformed config"
    if not inspection.file_present:
        return "skipped", "config not present"
    if not inspection.entry_present:
        return "skipped", "no Ontos entry"
    if inspection.ok:
        return "success", "valid Ontos entry"
    return "warning", inspection.message


def _format_cursor_details(project_status: str, project_reason: str, user_status: str, user_reason: str) -> str:
    """Format scope-level details for Cursor doctor output."""
    return f"project: {project_status} - {project_reason}; user: {user_status} - {user_reason}"


def _inspect_cursor_scope(scope: str, repo_root: Path, *, allow_unmanaged_probe: bool = True) -> Any:
    """Compatibility wrapper around the Cursor adapter inspection entry point."""
    from ontos.core.cursor_mcp import inspect_cursor_ontos_config

    return inspect_cursor_ontos_config(
        scope=scope,
        workspace_root=repo_root,
        allow_unmanaged_probe=allow_unmanaged_probe,
    )


def check_cursor_mcp(repo_root: Optional[Path] = None, *, allow_project_unmanaged_probe: bool = False) -> CheckResult:
    """Check 11: Cursor native MCP config status with project precedence."""
    try:
        root = resolve_project_root(repo_root=repo_root)
    except FileNotFoundError as exc:
        return CheckResult(
            name="cursor_mcp",
            status="warning",
            message="Cursor MCP check failed",
            details=str(exc),
        )

    project = _inspect_cursor_scope(
        "project",
        root,
        allow_unmanaged_probe=allow_project_unmanaged_probe,
    )
    user = _inspect_cursor_scope("user", root)
    project_status, project_reason = _cursor_scope_summary(project)
    user_status, user_reason = _cursor_scope_summary(user)
    details = _format_cursor_details(project_status, project_reason, user_status, user_reason)

    if project_status == "success":
        return CheckResult(
            name="cursor_mcp",
            status="success",
            message="Cursor Ontos MCP entry valid in project scope",
            details=details,
        )
    project_entry_present = getattr(project, "entry_present", getattr(project, "has_ontos_entry", False))
    if project_status == "warning" and project_entry_present:
        return CheckResult(
            name="cursor_mcp",
            status="warning",
            message="Cursor Ontos MCP entry invalid in project scope",
            details=details,
        )
    if project_status == "warning":
        return CheckResult(
            name="cursor_mcp",
            status="warning",
            message="Cursor MCP config malformed in project scope",
            details=details,
        )
    if user_status == "success":
        return CheckResult(
            name="cursor_mcp",
            status="success",
            message="Cursor Ontos MCP entry valid in user scope",
            details=details,
        )
    if user_status == "warning":
        return CheckResult(
            name="cursor_mcp",
            status="warning",
            message="Cursor MCP config malformed in user scope",
            details=details,
        )
    return CheckResult(
        name="cursor_mcp",
        status="success",
        message="Cursor not configured for Ontos; skipping MCP check",
        details=details,
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
        Tuple of (exit_code, DoctorResult) for completed diagnostics.
        Internal diagnostic code 0 if all pass, 1 if any completed check
        fails, and 3 if checks complete with warnings. Public ``doctor``
        command boundaries normalize warning-only code 3 to process exit 0.

    Raises:
        OntosUserError: If the project root or project configuration cannot
            be loaded. These are invocation/input failures, not completed
            diagnostic findings.
    """
    try:
        repo_root = resolve_project_root()
    except FileNotFoundError as exc:
        raise OntosUserError(
            "Could not resolve Ontos project root",
            code="E_WORKSPACE_NOT_FOUND",
            details=str(exc),
        ) from exc

    configuration = check_configuration(repo_root)
    if configuration.status == "failed":
        raise OntosUserError(
            configuration.message,
            code="E_CONFIG_ERROR",
            details=configuration.details,
        )

    result = DoctorResult(checks=[configuration])
    if configuration.status == "success":
        result.passed = 1
    else:
        result.warnings = 1

    checks = [
        lambda: check_git_hooks(repo_root),
        check_python_version,
        lambda: check_docs_directory(options.scope, repo_root),
        lambda: check_context_map(repo_root),
        lambda: check_validation(options.scope, repo_root),
        # (#117) Doctor severity now reflects activation hard-error severity.
        # If `ontos activate` reports any error-severity entry, this check
        # contributes a `failed` status and doctor exits non-zero.
        lambda: check_activation_health(options.scope, repo_root),
        lambda: check_cli_availability(repo_root),
        lambda: check_agents_staleness(repo_root),
        lambda: check_environment_manifests(repo_root),
        check_antigravity_mcp,
        lambda: check_cursor_mcp(repo_root, allow_project_unmanaged_probe=False),
    ]
    if options.frontmatter:
        checks.append(lambda: check_frontmatter_enums(options.scope, repo_root))

    for check_fn in checks:
        check_result = check_fn()
        result.checks.append(check_result)

        if check_result.status == "success":
            result.passed += 1
        elif check_result.status == "failed":
            result.failed += 1
        else:
            result.warnings += 1

    if result.failed > 0:
        exit_code = int(ExitCode.FINDINGS)
    elif result.warnings > 0:
        exit_code = int(ExitCode.WARNINGS)
    else:
        exit_code = int(ExitCode.CLEAN)
    return exit_code, result


def doctor_command(options: DoctorOptions) -> int:
    """Run health checks and return exit code only."""
    try:
        exit_code, _ = _run_doctor_command(options)
        return (
            int(ExitCode.CLEAN)
            if exit_code == ExitCode.WARNINGS
            else exit_code
        )
    except OntosUserError:
        return int(ExitCode.USAGE)


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

        if check.details and (verbose or check.name == "frontmatter_enums"):
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
