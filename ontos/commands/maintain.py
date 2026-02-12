"""Composable weekly maintenance runner.

Implements the `ontos maintain` command using a task registry so maintenance
steps can be extended without rewriting command orchestration.
"""

from __future__ import annotations

import json
import os
import re
import time
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Literal, Optional, Sequence, Tuple, cast

import ontos
from ontos.core.config import OntosConfig
from ontos.core.curation import CurationLevel, detect_curation_level
from ontos.core.link_diagnostics import run_link_diagnostics
from ontos.io.config import load_project_config
from ontos.io.files import find_project_root
from ontos.io.scan_scope import build_scope_roots, collect_scoped_documents, resolve_scan_scope
from ontos.ui.output import OutputHandler

STATUS_SUCCESS = "success"
STATUS_FAILED = "failed"
STATUS_SKIPPED = "skipped"
TaskStatus = Literal["success", "failed", "skipped"]


@dataclass
class MaintainOptions:
    """Configuration for maintain command."""

    verbose: bool = False
    dry_run: bool = False
    skip: List[str] = field(default_factory=list)
    quiet: bool = False
    json_output: bool = False
    scope: Optional[str] = None


@dataclass
class TaskResult:
    """Result returned by each task."""

    status: TaskStatus
    message: str
    details: List[str] = field(default_factory=list)
    metrics: Dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class MaintainTask:
    """Maintenance task definition."""

    name: str
    order: int
    description: str
    run: Callable[["MaintainContext"], TaskResult]
    condition: Optional[Callable[["MaintainContext"], Tuple[bool, str]]] = None


@dataclass
class TaskExecution:
    """Execution record for one task."""

    name: str
    status: TaskStatus
    message: str
    details: List[str] = field(default_factory=list)
    metrics: Dict[str, int] = field(default_factory=dict)
    duration_ms: int = 0


@dataclass
class MaintainContext:
    """Shared execution context for all maintenance tasks."""

    repo_root: Path
    config: OntosConfig
    options: MaintainOptions
    output: OutputHandler


class MaintainTaskRegistry:
    """Registry for maintain tasks."""

    def __init__(self) -> None:
        self._tasks: Dict[str, MaintainTask] = {}

    def register(self, task: MaintainTask) -> None:
        """Register one task by name."""
        if task.name in self._tasks:
            raise ValueError(f"Task '{task.name}' is already registered")
        self._tasks[task.name] = task

    def ordered_tasks(self) -> List[MaintainTask]:
        """Return tasks in deterministic execution order."""
        return sorted(self._tasks.values(), key=lambda t: t.order)

    def names(self) -> List[str]:
        """Return all registered task names in execution order."""
        return [task.name for task in self.ordered_tasks()]


# NOTE: This registry is intentionally scoped to `ontos maintain` only.
# It is not yet a project-wide orchestration precedent for other commands.
DEFAULT_TASK_REGISTRY = MaintainTaskRegistry()


def register_maintain_task(
    name: str,
    order: int,
    description: str,
    condition: Optional[Callable[[MaintainContext], Tuple[bool, str]]] = None,
) -> Callable[[Callable[[MaintainContext], TaskResult]], Callable[[MaintainContext], TaskResult]]:
    """Decorator for registry-backed maintenance tasks."""

    def decorator(func: Callable[[MaintainContext], TaskResult]) -> Callable[[MaintainContext], TaskResult]:
        DEFAULT_TASK_REGISTRY.register(
            MaintainTask(
                name=name,
                order=order,
                description=description,
                run=func,
                condition=condition,
            )
        )
        return func

    return decorator


def list_registered_tasks(registry: Optional[MaintainTaskRegistry] = None) -> List[str]:
    """List task names for active registry."""
    active_registry = registry or DEFAULT_TASK_REGISTRY
    return active_registry.names()


def _ok(message: str, details: Optional[List[str]] = None, metrics: Optional[Dict[str, int]] = None) -> TaskResult:
    return TaskResult(
        status=STATUS_SUCCESS,
        message=message,
        details=details or [],
        metrics=metrics or {},
    )


def _fail(message: str, details: Optional[List[str]] = None, metrics: Optional[Dict[str, int]] = None) -> TaskResult:
    return TaskResult(
        status=STATUS_FAILED,
        message=message,
        details=details or [],
        metrics=metrics or {},
    )


def _parse_bool(value: object, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default

    normalized = str(value).strip().lower()
    accepted = "'1', 'true', 'yes', 'on', '0', 'false', 'no', 'off'"
    if normalized == "":
        warnings.warn(
            f"Unrecognized boolean value {value!r}; using default={default}. Accepted values: {accepted}.",
            RuntimeWarning,
            stacklevel=2,
        )
        return default

    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    warnings.warn(
        f"Unrecognized boolean value {value!r}; using default={default}. Accepted values: {accepted}.",
        RuntimeWarning,
        stacklevel=2,
    )
    return default


def _normalize_task_status(status: object) -> Tuple[TaskStatus, Optional[str]]:
    """Normalize runtime status values to the TaskStatus contract."""
    if status in {STATUS_SUCCESS, STATUS_FAILED, STATUS_SKIPPED}:
        return cast(TaskStatus, status), None
    return (
        STATUS_FAILED,
        f"invalid task status {status!r}; expected one of "
        f"{STATUS_SUCCESS!r}, {STATUS_FAILED!r}, {STATUS_SKIPPED!r}",
    )


def _auto_consolidate_enabled() -> bool:
    """Resolve AUTO_CONSOLIDATE with env override and legacy fallback."""
    if "AUTO_CONSOLIDATE" in os.environ:
        return _parse_bool(os.environ.get("AUTO_CONSOLIDATE"), default=True)

    try:
        from ontos.core.paths import resolve_config

        legacy_value = resolve_config("AUTO_CONSOLIDATE", None, warn_legacy=False)
        if legacy_value is not None:
            return _parse_bool(legacy_value, default=True)
    except Exception:
        pass

    return True


def _condition_auto_consolidate(_ctx: MaintainContext) -> Tuple[bool, str]:
    enabled = _auto_consolidate_enabled()
    if enabled:
        return True, ""
    return False, "AUTO_CONSOLIDATE is disabled"


def _condition_agents_stale(ctx: MaintainContext) -> Tuple[bool, str]:
    """Check AGENTS.md staleness using the same repo root as maintain."""
    agents_path = ctx.repo_root / "AGENTS.md"
    if not agents_path.exists():
        return False, "AGENTS.md not found"

    try:
        agents_mtime = agents_path.stat().st_mtime
    except OSError:
        return False, "Could not read AGENTS.md metadata"

    source_mtimes: List[float] = []

    context_map = ctx.repo_root / ctx.config.paths.context_map
    if context_map.exists():
        source_mtimes.append(context_map.stat().st_mtime)

    config_path = ctx.repo_root / ".ontos.toml"
    if config_path.exists():
        source_mtimes.append(config_path.stat().st_mtime)

    logs_dir = ctx.repo_root / ctx.config.paths.logs_dir
    if logs_dir.exists():
        log_files = list(logs_dir.glob("*.md"))
        if log_files:
            source_mtimes.append(max(path.stat().st_mtime for path in log_files))

    if not source_mtimes:
        return False, "Cannot determine AGENTS.md staleness"

    if agents_mtime < max(source_mtimes):
        return True, "AGENTS.md may be stale"

    return False, "AGENTS.md is up to date"


def _scan_dirs(ctx: MaintainContext) -> List[Path]:
    scope = resolve_scan_scope(ctx.options.scope, ctx.config.scanning.default_scope)
    return build_scope_roots(ctx.repo_root, ctx.config, scope)


def _scan_docs(ctx: MaintainContext) -> List[Path]:
    context_map = (ctx.repo_root / ctx.config.paths.context_map).resolve()
    scope = resolve_scan_scope(ctx.options.scope, ctx.config.scanning.default_scope)
    return collect_scoped_documents(
        ctx.repo_root,
        ctx.config,
        scope,
        base_skip_patterns=list(ctx.config.scanning.skip_patterns),
        extra_skip_patterns=[str(context_map)],
    )


def _load_docs_for_graph(ctx: MaintainContext) -> "DocumentLoadResult":
    from ontos.io.files import load_documents
    from ontos.io.yaml import parse_frontmatter_content

    return load_documents(_scan_docs(ctx), parse_frontmatter_content)


@register_maintain_task(
    name="migrate_untagged",
    order=10,
    description="Migrate untagged markdown files",
)
def _task_migrate_untagged(ctx: MaintainContext) -> TaskResult:
    from ontos.commands.scaffold import (
        ScaffoldOptions,
        _run_scaffold_command,
        find_untagged_files,
    )

    if ctx.options.dry_run:
        return _ok("Would migrate untagged markdown files.")

    untagged = find_untagged_files(paths=_scan_dirs(ctx), root=ctx.repo_root)
    count = len(untagged)

    if count == 0:
        return _ok("No untagged markdown files found.", metrics={"untagged_files": 0})

    details = []
    for path in untagged[:5]:
        try:
            details.append(str(path.relative_to(ctx.repo_root)))
        except ValueError:
            details.append(str(path))
    if count > 5:
        details.append(f"... and {count - 5} more")

    exit_code, message = _run_scaffold_command(
        ScaffoldOptions(
            paths=untagged,
            apply=True,
            dry_run=False,
            quiet=True,
            json_output=False,
        )
    )
    if exit_code == 0:
        return _ok(
            f"Scaffolded {count} untagged file(s).",
            details=details,
            metrics={"untagged_files": count},
        )

    return _fail(
        f"Failed to migrate untagged files: {message}",
        details=details,
        metrics={"untagged_files": count},
    )


@register_maintain_task(
    name="regenerate_map",
    order=20,
    description="Regenerate Ontos context map",
)
def _task_regenerate_map(ctx: MaintainContext) -> TaskResult:
    if ctx.options.dry_run:
        return _ok("Would run `ontos map`.")

    from ontos.commands.map import MapOptions, map_command

    exit_code = map_command(
        MapOptions(
            quiet=True,
            json_output=False,
            scope=ctx.options.scope,
        )
    )
    if exit_code == 0:
        return _ok("Regenerated context map.")
    return _fail(f"Context map regeneration failed (exit code {exit_code}).")


@register_maintain_task(
    name="health_check",
    order=30,
    description="Run health checks",
)
def _task_health_check(ctx: MaintainContext) -> TaskResult:
    if ctx.options.dry_run:
        return _ok("Would run `ontos doctor`.")

    from ontos.commands.doctor import DoctorOptions, _run_doctor_command

    exit_code, result = _run_doctor_command(
        DoctorOptions(
            verbose=ctx.options.verbose,
            json_output=False,
            scope=ctx.options.scope,
        )
    )

    message = f"{result.passed} passed, {result.failed} failed, {result.warnings} warnings"
    details = []
    if ctx.options.verbose:
        for check in result.checks:
            details.append(f"{check.name}: {check.status} - {check.message}")

    metrics = {
        "passed": result.passed,
        "failed": result.failed,
        "warnings": result.warnings,
    }

    if exit_code == 0:
        return _ok(message, details=details, metrics=metrics)
    return _fail(message, details=details, metrics=metrics)


@register_maintain_task(
    name="curation_stats",
    order=40,
    description="Report curation levels (L0/L1/L2)",
)
def _task_curation_stats(ctx: MaintainContext) -> TaskResult:
    if ctx.options.dry_run:
        return _ok("Would report curation stats (L0/L1/L2).")

    counts = {
        CurationLevel.SCAFFOLD: 0,
        CurationLevel.STUB: 0,
        CurationLevel.FULL: 0,
    }

    from ontos.io.files import load_documents
    from ontos.io.yaml import parse_frontmatter_content
    
    load_result = load_documents(_scan_docs(ctx), parse_frontmatter_content)

    for doc in load_result.documents.values():
        level = detect_curation_level(doc.frontmatter)
        counts[level] += 1

    total = sum(counts.values())
    l0 = counts[CurationLevel.SCAFFOLD]
    l1 = counts[CurationLevel.STUB]
    l2 = counts[CurationLevel.FULL]
    message = f"L0={l0}, L1={l1}, L2={l2}, total={total}"

    return _ok(
        message,
        details=[
            f"[L0] Scaffold: {l0}",
            f"[L1] Stub: {l1}",
            f"[L2] Full: {l2}",
        ],
        metrics={
            "l0": l0,
            "l1": l1,
            "l2": l2,
            "total": total,
        },
    )


@register_maintain_task(
    name="consolidate_logs",
    order=50,
    description="Consolidate logs when AUTO_CONSOLIDATE is enabled",
    condition=_condition_auto_consolidate,
)
def _task_consolidate_logs(ctx: MaintainContext) -> TaskResult:
    retention_count = max(1, int(ctx.config.workflow.log_retention_count))

    if ctx.options.dry_run:
        return _ok(
            f"Would run `ontos consolidate --all --count {retention_count}`.",
            metrics={"retention_count": retention_count},
        )

    from ontos.commands.consolidate import (
        ConsolidateOptions,
        _run_consolidate_command,
    )

    exit_code, message = _run_consolidate_command(
        ConsolidateOptions(
            count=retention_count,
            by_age=False,
            days=30,
            dry_run=False,
            quiet=True,
            all=True,
            json_output=False,
        )
    )
    if exit_code == 0:
        return _ok(message or "Consolidation complete.", metrics={"retention_count": retention_count})
    return _fail(message or "Consolidation failed.", metrics={"retention_count": retention_count})


@dataclass
class DraftProposal:
    """Draft proposal candidate for graduation review."""

    id: str
    path: Path
    age_days: int
    version: Optional[str]
    version_match: bool


def _find_draft_proposals(ctx: MaintainContext) -> List[DraftProposal]:
    from ontos.io.files import load_documents
    from ontos.io.yaml import parse_frontmatter_content

    proposal_dirs: List[Path] = []
    
    # ... Same directory detection logic ...
    contributor_dir = ctx.repo_root / ".ontos-internal" / "strategy" / "proposals"
    if contributor_dir.exists():
        proposal_dirs.append(contributor_dir)

    docs_dir = ctx.repo_root / ctx.config.paths.docs_dir / "strategy" / "proposals"
    if docs_dir.exists() and docs_dir not in proposal_dirs:
        proposal_dirs.append(docs_dir)

    if not proposal_dirs:
        return []

    # Use canonical loader (#1)
    all_files: List[Path] = []
    for d in proposal_dirs:
        all_files.extend(d.rglob("*.md"))
    
    load_result = load_documents(all_files, parse_frontmatter_content)
    
    proposals: List[DraftProposal] = []
    version_pattern = re.compile(r"v?(\d+)[._-](\d+)")

    for doc in load_result.documents.values():
        if doc.frontmatter.get("status") != "draft":
            continue

        version_match = version_pattern.search(str(doc.filepath)) or version_pattern.search(doc.id)
        version = None
        if version_match:
            version = f"{version_match.group(1)}.{version_match.group(2)}"

        current_version = ontos.__version__ or ""
        matches_current = bool(version and current_version.startswith(version))
        age_days = int(max(0, (time.time() - doc.filepath.stat().st_mtime) / 86400))

        proposals.append(
            DraftProposal(
                id=doc.id,
                path=doc.filepath,
                age_days=age_days,
                version=version,
                version_match=matches_current,
            )
        )

    proposals.sort(key=lambda p: (not p.version_match, -p.age_days, p.id))
    return proposals


@register_maintain_task(
    name="review_proposals",
    order=60,
    description="Review draft proposals for graduation",
)
def _task_review_proposals(ctx: MaintainContext) -> TaskResult:
    proposals = _find_draft_proposals(ctx)
    count = len(proposals)

    if count == 0:
        return _ok("No draft proposals to review.", metrics={"draft_proposals": 0})

    details = []
    for proposal in proposals[:5]:
        version_note = f" (v{proposal.version})" if proposal.version else ""
        stale_note = " [matches current version]" if proposal.version_match else ""
        details.append(f"{proposal.id}{version_note} - {proposal.age_days} days old{stale_note}")
    if count > 5:
        details.append(f"... and {count - 5} more")

    if ctx.options.dry_run:
        return _ok(
            f"Would review {count} draft proposal(s).",
            details=details,
            metrics={"draft_proposals": count},
        )

    return _ok(
        (
            f"Found {count} draft proposal(s). "
            "Review manually and graduate by moving approved proposals out of proposals/."
        ),
        details=details,
        metrics={"draft_proposals": count},
    )


@register_maintain_task(
    name="check_links",
    order=70,
    description="Validate internal dependency links",
)
def _task_check_links(ctx: MaintainContext) -> TaskResult:
    if ctx.options.dry_run:
        return _ok("Would validate dependency links.")

    scope = resolve_scan_scope(ctx.options.scope, ctx.config.scanning.default_scope)
    doc_paths = _scan_docs(ctx)
    from ontos.io.files import load_documents
    from ontos.io.yaml import parse_frontmatter_content

    load_result = load_documents(doc_paths, parse_frontmatter_content)

    diagnostics = run_link_diagnostics(
        repo_root=ctx.repo_root,
        config=ctx.config,
        doc_paths=doc_paths,
        scope=scope,
        include_body=False,
        include_external_scope_resolution=True,
        include_suggestions=True,
        load_result=load_result,
    )

    details: List[str] = []
    for issue in diagnostics.load_warnings[:10]:
        details.append(f"LOAD {issue.code.upper()}: {issue.message}")
    if len(diagnostics.load_warnings) > 10:
        details.append(f"... and {len(diagnostics.load_warnings) - 10} more load warnings")

    for finding in diagnostics.broken_references[:10]:
        details.append(f"❌ {finding.source_doc_id} [{finding.field}] -> {finding.value}")
    if len(diagnostics.broken_references) > 10:
        details.append(f"... and {len(diagnostics.broken_references) - 10} more broken references")

    for duplicate_id, paths in list(sorted(diagnostics.duplicates.items()))[:5]:
        details.append(f"❌ duplicate_id {duplicate_id}: {', '.join(str(path) for path in paths)}")
    if len(diagnostics.duplicates) > 5:
        details.append(f"... and {len(diagnostics.duplicates) - 5} more duplicate IDs")

    metrics = {
        "broken_links": diagnostics.summary.broken_references,
        "orphans": diagnostics.summary.orphans,
        "external_refs": diagnostics.summary.external_references,
        "duplicates": diagnostics.summary.duplicate_ids,
        "load_issues": diagnostics.summary.load_warnings,
    }

    if diagnostics.exit_code == 1:
        return _fail(
            (
                "Found broken references or duplicate IDs "
                f"(broken={diagnostics.summary.broken_references}, duplicates={diagnostics.summary.duplicate_ids})."
            ),
            details=details,
            metrics=metrics,
        )

    if diagnostics.exit_code == 2:
        details.extend(
            [f"⚠️ orphan {orphan.doc_id} ({orphan.doc_type})" for orphan in diagnostics.orphans[:10]]
        )
        if len(diagnostics.orphans) > 10:
            details.append(f"... and {len(diagnostics.orphans) - 10} more orphans")
        return _ok(
            (
                f"No broken references or duplicates. Found {diagnostics.summary.orphans} "
                "scope-relative orphan(s)."
            ),
            details=details,
            metrics=metrics,
        )

    return _ok(
        "No broken references, duplicates, or scope-relative orphans.",
        details=details,
        metrics=metrics,
    )


@register_maintain_task(
    name="sync_agents",
    order=80,
    description="Regenerate AGENTS.md when stale",
    condition=_condition_agents_stale,
)
def _task_sync_agents(ctx: MaintainContext) -> TaskResult:
    if ctx.options.dry_run:
        return _ok("Would run `ontos agents --force`.")

    from ontos.commands.agents import AgentsOptions, _run_agents_command

    exit_code, message = _run_agents_command(AgentsOptions(force=True))
    if exit_code == 0:
        return _ok(message or "AGENTS.md synchronized.")
    return _fail(message or "AGENTS.md synchronization failed.")


def _normalize_skip(skip_args: Sequence[str]) -> List[str]:
    names: List[str] = []
    for raw in skip_args:
        for token in str(raw).split(","):
            task_name = token.strip()
            if task_name:
                names.append(task_name)
    return names


def _emit_task_line(ctx: MaintainContext, execution: TaskExecution) -> None:
    label = execution.name
    line = f"{label}: {execution.message}"

    if execution.status == STATUS_SUCCESS:
        ctx.output.success(line)
    elif execution.status == STATUS_SKIPPED:
        ctx.output.info(f"{label}: skipped ({execution.message})")
    else:
        ctx.output.error(line)

    if ctx.options.verbose:
        for detail in execution.details:
            ctx.output.detail(detail)
        if execution.duration_ms > 0:
            ctx.output.detail(f"duration: {execution.duration_ms}ms")


def _json_summary(executions: List[TaskExecution], unknown_skips: List[str], dry_run: bool) -> str:
    status = STATUS_FAILED if any(e.status == STATUS_FAILED for e in executions) else STATUS_SUCCESS
    payload = {
        "status": status,
        "dry_run": dry_run,
        "tasks": [
            {
                "name": e.name,
                "status": e.status,
                "message": e.message,
                "details": e.details,
                "metrics": e.metrics,
                "duration_ms": e.duration_ms,
            }
            for e in executions
        ],
        "unknown_skips": unknown_skips,
        "summary": {
            STATUS_SUCCESS: sum(1 for e in executions if e.status == STATUS_SUCCESS),
            STATUS_FAILED: sum(1 for e in executions if e.status == STATUS_FAILED),
            STATUS_SKIPPED: sum(1 for e in executions if e.status == STATUS_SKIPPED),
        },
    }
    return json.dumps(payload)


def maintain_command(options: MaintainOptions, registry: Optional[MaintainTaskRegistry] = None) -> int:
    """Execute `ontos maintain` with registry-based task orchestration."""
    active_registry = registry or DEFAULT_TASK_REGISTRY
    quiet = options.quiet or options.json_output
    output = OutputHandler(quiet=quiet)

    try:
        repo_root = find_project_root()
    except FileNotFoundError as exc:
        if options.json_output:
            print(json.dumps({"status": STATUS_FAILED, "message": str(exc)}))
        elif not options.quiet:
            output.error(str(exc))
        return 1

    try:
        config = load_project_config(repo_root=repo_root)
    except Exception as exc:
        if options.json_output:
            print(json.dumps({"status": STATUS_FAILED, "message": f"Config error: {exc}"}))
        elif not options.quiet:
            output.error(f"Config error: {exc}")
        return 1

    context = MaintainContext(
        repo_root=repo_root,
        config=config,
        options=options,
        output=output,
    )

    skip_names = set(_normalize_skip(options.skip))
    known_names = set(active_registry.names())
    unknown_skips = sorted(skip_names - known_names)

    executions: List[TaskExecution] = []

    if not quiet:
        mode_label = "dry-run" if options.dry_run else "live"
        output.info(f"Running Ontos maintenance ({mode_label})...")

    if unknown_skips and not quiet:
        output.warning(f"Ignoring unknown task(s): {', '.join(unknown_skips)}")

    for task in active_registry.ordered_tasks():
        start = time.perf_counter()

        if task.name in skip_names:
            execution = TaskExecution(
                name=task.name,
                status=STATUS_SKIPPED,
                message="skipped by --skip",
            )
            executions.append(execution)
            _emit_task_line(context, execution)
            continue

        if task.condition is not None:
            try:
                should_run, reason = task.condition(context)
            except Exception as exc:
                execution = TaskExecution(
                    name=task.name,
                    status=STATUS_FAILED,
                    message=f"condition check failed: {exc}",
                )
                execution.duration_ms = int((time.perf_counter() - start) * 1000)
                executions.append(execution)
                _emit_task_line(context, execution)
                continue

            if not should_run:
                execution = TaskExecution(
                    name=task.name,
                    status=STATUS_SKIPPED,
                    message=reason or "condition not met",
                )
                execution.duration_ms = int((time.perf_counter() - start) * 1000)
                executions.append(execution)
                _emit_task_line(context, execution)
                continue

        try:
            result = task.run(context)
            status, status_error = _normalize_task_status(result.status)
            details = list(result.details)
            if status_error:
                details.insert(0, status_error)
            execution = TaskExecution(
                name=task.name,
                status=status,
                message=result.message,
                details=details,
                metrics=result.metrics,
            )
        except Exception as exc:
            execution = TaskExecution(
                name=task.name,
                status=STATUS_FAILED,
                message=f"task raised exception: {exc}",
            )

        execution.duration_ms = int((time.perf_counter() - start) * 1000)
        executions.append(execution)
        _emit_task_line(context, execution)

    success_count = sum(1 for execution in executions if execution.status == STATUS_SUCCESS)
    failure_count = sum(1 for execution in executions if execution.status == STATUS_FAILED)
    skipped_count = sum(1 for execution in executions if execution.status == STATUS_SKIPPED)

    if options.json_output:
        print(_json_summary(executions, unknown_skips, options.dry_run))
    elif not options.quiet:
        output.plain("")
        summary = f"Maintenance summary: {success_count} succeeded, {failure_count} failed, {skipped_count} skipped"
        if failure_count > 0:
            output.warning(summary)
        else:
            output.success(summary)

    return 1 if failure_count > 0 else 0
