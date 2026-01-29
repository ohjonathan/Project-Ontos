"""Environment manifest detection command."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
import re
from datetime import datetime, timezone

# Python 3.11+ has tomllib in stdlib; fall back to tomli for 3.9/3.10
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        # If tomli is also missing, we can't parse TOML on older Python versions
        tomllib = None


class AmbiguityError(ValueError):
    """Raised when multiple conflicting configurations are found."""
    pass


# =============================================================================
# Data Structures
# =============================================================================

@dataclass
class ManifestInfo:
    """Information about a detected environment manifest."""
    path: Path
    manifest_type: str  # python_deps, system_deps, runtime_versions, npm_deps
    package_manager: Optional[str] = None
    lock_file: Optional[Path] = None
    lock_present: bool = False
    dependency_count: Dict[str, int] = field(default_factory=dict)
    details: Dict = field(default_factory=dict)
    bootstrap_command: str = ""


@dataclass
class EnvResult:
    """Result of environment detection."""
    manifests: List[ManifestInfo] = field(default_factory=list)
    not_detected: List[Dict] = field(default_factory=list)
    onboarding_steps: List[str] = field(default_factory=list)
    parse_warnings: List[str] = field(default_factory=list)  # v1.1: Surface parse failures
    generated_at: str = ""


@dataclass
class EnvOptions:
    """Configuration for env command."""
    path: Path = field(default_factory=Path.cwd)
    write: bool = False
    force: bool = False  # v1.1: Required to overwrite existing environment.md
    format: str = "text"  # text, json
    quiet: bool = False


# =============================================================================
# Manifest Detection
# =============================================================================

MANIFEST_PATTERNS = {
    "pyproject.toml": {
        "type": "python_deps",
        "lock_files": ["poetry.lock", "pdm.lock", "uv.lock"],
        "bootstrap": "poetry install",  # Default, refined during parse
    },
    "requirements.txt": {
        "type": "python_deps",
        "lock_files": [],
        "bootstrap": "pip install -r requirements.txt",
    },
    "Brewfile": {
        "type": "system_deps",
        "lock_files": ["Brewfile.lock.json"],
        "bootstrap": "brew bundle",
    },
    ".tool-versions": {
        "type": "runtime_versions",
        "lock_files": [],
        "bootstrap": "asdf install",
    },
    "package.json": {
        "type": "npm_deps",
        "lock_files": ["package-lock.json", "yarn.lock", "pnpm-lock.yaml"],
        "bootstrap": "npm install",  # Refined based on lock file
    },
    ".nvmrc": {
        "type": "runtime_versions",
        "lock_files": [],
        "bootstrap": "nvm install",
    },
    ".python-version": {
        "type": "runtime_versions",
        "lock_files": [],
        "bootstrap": "pyenv install",
    },
}


def detect_manifests(workspace: Path) -> Tuple[List[ManifestInfo], List[str]]:
    """Scan workspace for known manifest files.

    Returns:
        Tuple of (manifests, parse_warnings)
    """
    manifests = []
    warnings = []

    # Note: Lock file priority order is poetry > pdm > uv (first match wins)
    for filename, spec in MANIFEST_PATTERNS.items():
        manifest_path = workspace / filename
        if manifest_path.exists():
            info = ManifestInfo(
                path=manifest_path,
                manifest_type=spec["type"],
                bootstrap_command=spec["bootstrap"],
            )

            # Check for lock files
            for lock_name in spec["lock_files"]:
                lock_path = workspace / lock_name
                if lock_path.exists():
                    info.lock_file = lock_path
                    info.lock_present = True
                    # Refine bootstrap command based on lock file
                    if lock_name == "yarn.lock":
                        info.bootstrap_command = "yarn install"
                        info.package_manager = "yarn"
                    elif lock_name == "pnpm-lock.yaml":
                        info.bootstrap_command = "pnpm install"
                        info.package_manager = "pnpm"
                    break

            # Parse manifest for details; collect any warnings
            warning = _parse_manifest(info)
            if warning:
                warnings.append(warning)
            manifests.append(info)

    return manifests, warnings


def _parse_manifest(info: ManifestInfo) -> Optional[str]:
    """Parse manifest file to extract details.

    Returns:
        Warning message if parsing failed, None on success.
    """
    try:
        if info.path.name == "pyproject.toml":
            _parse_pyproject(info)
        elif info.path.name == "Brewfile":
            _parse_brewfile(info)
        elif info.path.name == ".tool-versions":
            _parse_tool_versions(info)
        elif info.path.name == "package.json":
            _parse_package_json(info)
        elif info.path.name in (".nvmrc", ".python-version"):
            _parse_single_version(info)
        elif info.path.name == "requirements.txt":
            _parse_requirements(info)
        return None
    except (
        FileNotFoundError,
        PermissionError,
        UnicodeDecodeError,
    ) as e:
        return f"{info.path.name}: parse failed ({type(e).__name__})"
    except Exception as e:
        # Check for TOML/JSON errors specifically if tomllib/json are used
        if tomllib and isinstance(e, getattr(tomllib, "TOMLDecodeError", type(None))):
             return f"{info.path.name}: parse failed (TOMLDecodeError)"
        if isinstance(e, json.JSONDecodeError):
             return f"{info.path.name}: parse failed (JSONDecodeError)"
        
        if isinstance(e, ValueError) and "empty" in str(e):
             return f"{info.path.name}: parse failed (empty file)"
        
        if isinstance(e, AmbiguityError):
             return f"{info.path.name}: {str(e)}"
        
        # Catch-all for unexpected errors
        return f"{info.path.name}: parse failed ({type(e).__name__})"


def _parse_pyproject(info: ManifestInfo) -> None:
    """Parse pyproject.toml for dependency info."""
    if tomllib is None:
        raise ImportError("tomllib or tomli is required to parse pyproject.toml")
        
    content = info.path.read_text().strip()
    if not content:
        # NB4: Empty file warning
        raise ValueError("file is empty")
        
    data = tomllib.loads(content)

    # Detect package manager
    pm_detected = False
    if "tool" in data:
        if "poetry" in data["tool"]:
            info.package_manager = "poetry"
            info.bootstrap_command = "poetry install"
            pm_detected = True
            deps = data["tool"]["poetry"].get("dependencies", {})
            dev_deps = data["tool"]["poetry"].get("dev-dependencies", {})
            # Exclude python itself from count
            runtime = len([k for k in deps if k != "python"])
            info.dependency_count = {"runtime": runtime, "dev": len(dev_deps)}
        elif "pdm" in data["tool"]:
            info.package_manager = "pdm"
            info.bootstrap_command = "pdm install"
            pm_detected = True
        elif "uv" in data["tool"]:
            info.package_manager = "uv"
            info.bootstrap_command = "uv sync"
            pm_detected = True

    # Fallback to lock file inference if no tool section (v3.2)
    if not pm_detected:
        parent = info.path.parent
        found_locks = []
        if (parent / "poetry.lock").exists(): found_locks.append("poetry.lock")
        if (parent / "pdm.lock").exists(): found_locks.append("pdm.lock")
        if (parent / "uv.lock").exists(): found_locks.append("uv.lock")

        if len(found_locks) > 1:
            # X-H1: Ambiguity warning
            info.bootstrap_command = "pip install ."
            raise AmbiguityError(f"multiple lock files detected ({', '.join(found_locks)}); cannot infer package manager")
        elif "poetry.lock" in found_locks:
            info.package_manager = "poetry"
            info.bootstrap_command = "poetry install"
        elif "pdm.lock" in found_locks:
            info.package_manager = "pdm"
            info.bootstrap_command = "pdm install"
        elif "uv.lock" in found_locks:
            info.package_manager = "uv"
            info.bootstrap_command = "uv sync"
        elif (parent / "requirements.txt").exists():
            info.bootstrap_command = "pip install -r requirements.txt"
        else:
            # Generic PEP 621 without obvious tool
            info.bootstrap_command = "pip install ."

    # PEP 621 dependencies
    if "project" in data:
        deps = data["project"].get("dependencies", [])
        optional = data["project"].get("optional-dependencies", {})
        dev_count = len(optional.get("dev", []))
        info.dependency_count = {"runtime": len(deps), "dev": dev_count}


def _parse_brewfile(info: ManifestInfo) -> None:
    """Parse Brewfile for formulae and casks."""
    content = info.path.read_text()
    formulae = re.findall(r'^brew\s+["\']([^"\']+)', content, re.MULTILINE)
    casks = re.findall(r'^cask\s+["\']([^"\']+)', content, re.MULTILINE)
    mas_apps = re.findall(r'^mas\s+["\']([^"\']+)', content, re.MULTILINE)

    info.details = {
        "formulae": formulae,
        "casks": casks,
        "mas_apps": mas_apps,
    }
    info.dependency_count = {
        "formulae": len(formulae),
        "casks": len(casks),
        "mas_apps": len(mas_apps),
    }


def _parse_tool_versions(info: ManifestInfo) -> None:
    """Parse .tool-versions for runtime versions."""
    content = info.path.read_text()
    runtimes = {}
    for line in content.strip().split("\n"):
        line = line.strip()
        if line and not line.startswith("#"):
            parts = line.split()
            if len(parts) >= 2:
                runtimes[parts[0]] = parts[1]
    info.details = {"runtimes": runtimes}


def _parse_package_json(info: ManifestInfo) -> None:
    """Parse package.json for dependency info."""
    content = info.path.read_text()
    data = json.loads(content)

    deps = data.get("dependencies", {})
    dev_deps = data.get("devDependencies", {})
    info.dependency_count = {"runtime": len(deps), "dev": len(dev_deps)}

    # Detect package manager from packageManager field
    if "packageManager" in data:
        pm = data["packageManager"].split("@")[0]
        info.package_manager = pm
        info.bootstrap_command = f"{pm} install"


def _parse_single_version(info: ManifestInfo) -> None:
    """Parse single-version files (.nvmrc, .python-version)."""
    version = info.path.read_text().strip()
    info.details = {"version": version}


def _parse_requirements(info: ManifestInfo) -> None:
    """Parse requirements.txt for line count."""
    content = info.path.read_text()
    lines = [l for l in content.split("\n") if l.strip() and not l.startswith("#")]
    info.dependency_count = {"packages": len(lines)}


# =============================================================================
# Onboarding Step Generation
# =============================================================================

# Bootstrap command priority order
BOOTSTRAP_ORDER = [
    "system_deps",      # Install system tools first (Brewfile)
    "runtime_versions", # Then language runtimes (.tool-versions)
    "python_deps",      # Then Python deps
    "npm_deps",         # Then npm deps
]


def generate_onboarding(manifests: List[ManifestInfo]) -> List[str]:
    """Generate ordered bootstrap commands."""
    by_type = {}
    for m in manifests:
        by_type.setdefault(m.manifest_type, []).append(m)

    steps = []
    for manifest_type in BOOTSTRAP_ORDER:
        for m in by_type.get(manifest_type, []):
            if m.bootstrap_command:
                steps.append(m.bootstrap_command)

    return steps


# =============================================================================
# Output Formatting
# =============================================================================

def format_text_output(result: EnvResult) -> str:
    """Format result as human-readable text."""
    lines = ["Environment Manifest Detection", ""]

    if result.manifests:
        lines.append("Detected Manifests:")
        for i, m in enumerate(result.manifests):
            prefix = "├──" if i < len(result.manifests) - 1 else "└──"
            type_label = _type_label(m.manifest_type)
            lines.append(f"  {prefix} {m.path.name} ({type_label})")

            # Details line
            detail_parts = []
            if m.dependency_count:
                counts = ", ".join(f"{v} {k}" for k, v in m.dependency_count.items())
                detail_parts.append(counts)
            if m.lock_present:
                detail_parts.append(f"{m.lock_file.name} present")
            if m.details.get("runtimes"):
                rt = m.details["runtimes"]
                detail_parts.append(", ".join(f"{k} {v}" for k, v in rt.items()))

            if detail_parts:
                detail_prefix = "│   └──" if i < len(result.manifests) - 1 else "    └──"
                lines.append(f"  {detail_prefix} {'; '.join(detail_parts)}")
    else:
        lines.append("No environment manifests detected.")

    if result.not_detected:
        lines.append("")
        lines.append("Not Detected:")
        for nd in result.not_detected:
            lines.append(f"  └── {nd['expected_file']} ({nd.get('reason', 'not found')})")

    if result.onboarding_steps:
        lines.append("")
        lines.append("Onboarding Steps:")
        for i, step in enumerate(result.onboarding_steps, 1):
            lines.append(f"  {i}. {step}")

    # v1.1: Display parse warnings so users know when detection is incomplete
    if result.parse_warnings:
        lines.append("")
        lines.append("Parse Warnings:")
        for warning in result.parse_warnings:
            lines.append(f"  - {warning}")

    lines.append("")
    lines.append("Run 'ontos env --write' to save to .ontos/environment.md")

    return "\n".join(lines)


def _type_label(manifest_type: str) -> str:
    """Convert manifest type to human label."""
    labels = {
        "python_deps": "Python dependencies",
        "system_deps": "System dependencies",
        "runtime_versions": "Runtime versions",
        "npm_deps": "npm dependencies",
    }
    return labels.get(manifest_type, manifest_type)


def format_json_output(result: EnvResult) -> Dict:
    """Format result as JSON-serializable dict."""
    return {
        "$schema": "ontos-env-v1",
        "generated_at": result.generated_at,
        "manifests": [
            {
                "path": str(m.path.name),
                "type": m.manifest_type,
                "package_manager": m.package_manager,
                "lock_file": str(m.lock_file.name) if m.lock_file else None,
                "lock_present": m.lock_present,
                "dependency_count": m.dependency_count,
                "details": m.details,
                "bootstrap_command": m.bootstrap_command,
            }
            for m in result.manifests
        ],
        "not_detected": result.not_detected,
        "onboarding_steps": result.onboarding_steps,
        "parse_warnings": result.parse_warnings,  # v1.1: Include warnings in JSON
    }


def generate_environment_md(result: EnvResult, workspace: Path) -> str:
    """Generate .ontos/environment.md content."""
    lines = [
        "# Environment Setup",
        "",
        "> Auto-generated by `ontos env`. Do not edit manually.",
        f"> Regenerate with: `ontos env --write`",
        f"> Last updated: {result.generated_at}",
        "",
        "---",
        "",
        "## Detected Manifests",
        "",
        "| Manifest | Type | Purpose | Bootstrap Command |",
        "|----------|------|---------|-------------------|",
    ]

    for m in result.manifests:
        rel_path = f"../{m.path.name}"
        lines.append(
            f"| [{m.path.name}]({rel_path}) | {_type_label(m.manifest_type)} | "
            f"{m.package_manager or 'N/A'} | `{m.bootstrap_command}` |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## Quick Start",
        "",
        "New contributors should run these commands in order:",
        "",
        "```bash",
    ])

    for i, step in enumerate(result.onboarding_steps, 1):
        lines.append(f"# {i}. {_step_comment(step)}")
        lines.append(step)
        lines.append("")

    lines.extend([
        "```",
        "",
        "---",
        "",
        "## Manifest Details",
        "",
    ])

    for m in result.manifests:
        lines.append(f"### {m.path.name}")
        lines.append("")
        lines.append(f"**Location:** `{m.path.name}`")
        if m.package_manager:
            lines.append(f"**Package Manager:** {m.package_manager}")
        if m.dependency_count:
            counts = ", ".join(f"{v} {k}" for k, v in m.dependency_count.items())
            lines.append(f"**Dependencies:** {counts}")
        if m.lock_present:
            lines.append(f"**Lock File:** Present ({m.lock_file.name})")
        if m.details.get("runtimes"):
            lines.append("**Runtimes:**")
            for rt, ver in m.details["runtimes"].items():
                lines.append(f"- {rt}: {ver}")
        if m.details.get("formulae"):
            lines.append(f"**Formulae:** {', '.join(m.details['formulae'])}")
        if m.details.get("casks"):
            lines.append(f"**Casks:** {', '.join(m.details['casks'])}")
        lines.append("")

    return "\n".join(lines)


def _step_comment(step: str) -> str:
    """Generate comment for bootstrap step."""
    if "brew" in step:
        return "System dependencies (macOS)"
    elif "asdf" in step or "nvm" in step:
        return "Runtime versions"
    elif "poetry" in step or "pip" in step or "pdm" in step or "uv" in step:
        return "Python dependencies"
    elif "npm" in step or "yarn" in step or "pnpm" in step:
        return "Node.js dependencies"
    return step


# =============================================================================
# Main Command
# =============================================================================

def env_command(options: EnvOptions) -> Tuple[int, str]:
    """
    Detect environment manifests and generate documentation.

    Returns:
        Tuple of (exit_code, output_message)
    """
    workspace = options.path

    # X-M3: Validate workspace path
    if not workspace.exists():
        return 1, f"Error: workspace path does not exist: {workspace}"
    if not workspace.is_dir():
        return 1, f"Error: workspace path is not a directory: {workspace}"

    # Detect manifests (v1.1: now returns tuple with warnings)
    manifests, parse_warnings = detect_manifests(workspace)

    # Generate onboarding steps
    onboarding = generate_onboarding(manifests)

    # Build result
    result = EnvResult(
        manifests=manifests,
        onboarding_steps=onboarding,
        parse_warnings=parse_warnings,  # v1.1: Include warnings
        generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )

    # Check for potential missing manifests
    has_node = any(m.details.get("runtimes", {}).get("node") for m in manifests)
    has_package_json = any(m.path.name == "package.json" for m in manifests)
    if has_node and not has_package_json:
        result.not_detected.append({
            "type": "npm_deps",
            "expected_file": "package.json",
            "reason": "node in .tool-versions but no package.json found",
        })

    # Handle --write flag
    if options.write:
        ontos_dir = workspace / ".ontos"
        ontos_dir.mkdir(exist_ok=True)
        env_md = ontos_dir / "environment.md"

        # v1.1: Safety check - require --force to overwrite existing file
        if env_md.exists() and not options.force:
            return 1, f"Error: {env_md} already exists. Use --force to overwrite."

        env_md.write_text(generate_environment_md(result, workspace))
        if not options.quiet:
            return 0, f"Environment documentation written to {env_md}"
        return 0, ""

    # Format output
    if options.format == "json":
        import json as json_module
        return 0, json_module.dumps(format_json_output(result), indent=2)

    return 0, format_text_output(result)
