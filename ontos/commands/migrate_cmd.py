"""
Migrate convenience command — runs export data + migration-report.

Note: Named migrate_cmd.py to avoid conflict with existing migrate.py (schema migration).
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from ontos.commands.export_data import export_data_command, ExportDataOptions
from ontos.commands.migration_report import migration_report_command, MigrationReportOptions
from ontos.io.files import find_project_root


@dataclass
class MigrateOptions:
    """Options for migrate convenience command."""
    out_dir: Path = Path("./migration/")
    force: bool = False
    quiet: bool = False
    json_output: bool = False


def migrate_convenience_command(options: MigrateOptions) -> Tuple[int, str]:
    """
    Run export data + migration-report together.

    Creates:
    - {out_dir}/snapshot.json
    - {out_dir}/analysis.md

    Returns:
        Tuple of (exit_code, message)
    """
    try:
        root = find_project_root()
    except Exception as e:
        return 1, f"Error: {e}"

    # Create output directory
    out_dir = options.out_dir
    if not out_dir.is_absolute():
        out_dir = root / out_dir

    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return 1, f"Error creating output directory: {e}"

    # Run export data
    export_options = ExportDataOptions(
        output_path=out_dir / "snapshot.json",
        force=options.force,
        quiet=True,
    )
    export_code, export_msg = export_data_command(export_options)
    if export_code != 0:
        return export_code, f"Export failed: {export_msg}"

    # Run migration report
    report_options = MigrationReportOptions(
        output_path=out_dir / "analysis.md",
        format="md",
        force=options.force,
        quiet=True,
    )
    report_code, report_msg = migration_report_command(report_options)
    if report_code != 0:
        return report_code, f"Report failed: {report_msg}"

    return 0, f"Migration artifacts created in {out_dir}/\n  - snapshot.json\n  - analysis.md"
