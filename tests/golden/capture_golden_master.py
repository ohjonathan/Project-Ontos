#!/usr/bin/env python3
"""
Golden Master Capture Script

Captures v2.9.x behavior for regression testing during v3.0 refactoring.
Run this ONCE on v2.9.x to establish baselines, then compare against v3.0.

Usage:
    python capture_golden_master.py [--fixture small|medium|large|all]
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Constants
SCRIPT_DIR = Path(__file__).parent
FIXTURES_DIR = SCRIPT_DIR / "fixtures"
BASELINES_DIR = SCRIPT_DIR / "baselines"
PROJECT_ROOT = SCRIPT_DIR.parent.parent  # tests/golden/ -> project root


def normalize_output(text: str, fixture_path: Path) -> str:
    """
    Normalize non-deterministic elements in captured output.

    Handles:
    - Timestamps (various formats)
    - Absolute paths
    - Version strings
    - Document counts (keep as-is, fixture-specific)
    """
    # Normalize timestamps
    # Format: "2026-01-12 03:21:47 UTC" or "2026-01-12 22:21:47"
    text = re.sub(
        r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}( UTC)?',
        '<TIMESTAMP>',
        text
    )

    # Format: "Date: 2026-01-12 03:21 EST"
    text = re.sub(
        r'Date: \d{4}-\d{2}-\d{2} \d{2}:\d{2} \w+',
        'Date: <TIMESTAMP>',
        text
    )

    # Format: ISO dates like "2026-01-12"
    text = re.sub(
        r'Generated: \d{4}-\d{2}-\d{2}',
        'Generated: <DATE>',
        text
    )

    # Normalize absolute paths to fixture root
    fixture_str = str(fixture_path.resolve())
    text = text.replace(fixture_str, '<FIXTURE_ROOT>')

    # Normalize any remaining absolute paths containing .ontos-internal
    text = re.sub(
        r'/[^\s]+/\.ontos-internal',
        '<FIXTURE_ROOT>/.ontos-internal',
        text
    )

    # Normalize home directory paths
    home = str(Path.home())
    text = text.replace(home, '<HOME>')

    return text


def normalize_context_map(content: str, fixture_path: Path) -> str:
    """
    Normalize the generated Ontos_Context_Map.md file.

    Additional normalizations specific to context map:
    - Provenance header timestamps
    - Mode indicator (Contributor/User)
    - Scanned directory path
    - decision_history.md references (v1.1)
    """
    content = normalize_output(content, fixture_path)

    # Normalize provenance header
    content = re.sub(
        r'Generated: <TIMESTAMP> by Ontos v[\d.]+',
        'Generated: <TIMESTAMP> by Ontos v<VERSION>',
        content
    )

    # Normalize mode (fixture always runs in contributor mode)
    content = re.sub(
        r'Mode: (Contributor|User)',
        'Mode: <MODE>',
        content
    )

    # v1.1: Normalize decision_history.md generation timestamp
    content = re.sub(
        r'decision_history\.md \(generated <TIMESTAMP>\)',
        'decision_history.md (generated <TIMESTAMP>)',
        content
    )

    return content


def normalize_session_log(content: str, fixture_path: Path) -> str:
    """
    Normalize the generated session log file.

    Additional normalizations:
    - Log ID with date
    - Date in frontmatter
    """
    content = normalize_output(content, fixture_path)

    # Normalize log ID (contains date)
    content = re.sub(
        r'id: log_\d{8}_',
        'id: log_<DATE>_',
        content
    )

    # Normalize date field in frontmatter
    content = re.sub(
        r'^date: \d{4}-\d{2}-\d{2}',
        'date: <DATE>',
        content,
        flags=re.MULTILINE
    )

    return content


def setup_fixture(fixture_name: str) -> Path:
    """
    Copy fixture to a temp location for isolated testing.
    Returns path to the temporary fixture directory.
    """
    fixture_src = FIXTURES_DIR / fixture_name
    if not fixture_src.exists():
        raise FileNotFoundError(f"Fixture not found: {fixture_src}")

    # Create temp directory
    import tempfile
    temp_dir = Path(tempfile.mkdtemp(prefix=f"golden_{fixture_name}_"))

    # Copy fixture contents
    shutil.copytree(fixture_src, temp_dir, dirs_exist_ok=True)

    # Initialize git repo (required for some commands)
    # v1.1: Configure git user to prevent CI failures
    subprocess.run(
        ["git", "init"],
        cwd=temp_dir,
        capture_output=True,
        check=True
    )
    subprocess.run(
        ["git", "-c", "user.name=Golden Master", "-c", "user.email=test@example.com", "add", "."],
        cwd=temp_dir,
        capture_output=True,
        check=True
    )
    subprocess.run(
        ["git", "-c", "user.name=Golden Master", "-c", "user.email=test@example.com",
         "commit", "-m", "Initial commit"],
        cwd=temp_dir,
        capture_output=True,
        check=True
    )

    return temp_dir


def capture_map_command(fixture_path: Path) -> dict:
    """
    Capture output of `python3 ontos.py map` command.

    Returns dict with:
    - stdout: normalized stdout
    - stderr: normalized stderr
    - exit_code: int
    - context_map: normalized content of generated file
    """
    # Copy ontos.py and .ontos/ to fixture (simulates installed state)
    shutil.copy(PROJECT_ROOT / "ontos.py", fixture_path / "ontos.py")
    shutil.copytree(
        PROJECT_ROOT / ".ontos",
        fixture_path / ".ontos",
        dirs_exist_ok=True
    )

    try:
        result = subprocess.run(
            [sys.executable, "ontos.py", "map"],
            cwd=fixture_path,
            capture_output=True,
            text=True,
            timeout=60,
            errors="replace"
        )
    except subprocess.TimeoutExpired:
        print("    ERROR: Command timed out after 60 seconds")
        return {
            "stdout": "",
            "stderr": "TIMEOUT: Command did not complete within 60 seconds",
            "exit_code": -1,
            "context_map": "",
        }

    # Read generated context map
    context_map_path = fixture_path / "Ontos_Context_Map.md"
    context_map_content = ""
    if context_map_path.exists():
        context_map_content = context_map_path.read_text(encoding="utf-8", errors="replace")

    return {
        "stdout": normalize_output(result.stdout, fixture_path),
        "stderr": normalize_output(result.stderr, fixture_path),
        "exit_code": result.returncode,
        "context_map": normalize_context_map(context_map_content, fixture_path),
    }


def capture_log_command(fixture_path: Path, event_type: str = "chore") -> dict:
    """
    Capture output of `python3 ontos.py log` command.

    Note: Uses --auto flag to avoid interactive prompts.

    Returns dict with:
    - stdout: normalized stdout
    - stderr: normalized stderr
    - exit_code: int
    - session_log: normalized content of generated log file (if any)
    """
    # Make a change to trigger log creation
    test_file = fixture_path / ".ontos-internal" / "test_change.md"
    test_file.write_text("# Test Change\nThis triggers log creation.\n")

    subprocess.run(
        ["git", "-c", "user.name=Golden Master", "-c", "user.email=test@example.com", "add", "."],
        cwd=fixture_path,
        capture_output=True,
        check=True
    )
    subprocess.run(
        ["git", "-c", "user.name=Golden Master", "-c", "user.email=test@example.com",
         "commit", "-m", "Test change for log capture"],
        cwd=fixture_path,
        capture_output=True,
        check=True
    )

    try:
        result = subprocess.run(
            [
                sys.executable, "ontos.py", "log",
                "-e", event_type,
                "-s", "Golden Master Capture",
                "--auto"
            ],
            cwd=fixture_path,
            capture_output=True,
            text=True,
            timeout=60,
            errors="replace"
        )
    except subprocess.TimeoutExpired:
        print("    ERROR: Command timed out after 60 seconds")
        return {
            "stdout": "",
            "stderr": "TIMEOUT: Command did not complete within 60 seconds",
            "exit_code": -1,
            "session_log": "",
        }

    # Find generated session log
    logs_dir = fixture_path / ".ontos-internal" / "logs"
    session_log_content = ""
    if logs_dir.exists():
        # Find most recent log (by filename)
        log_files = sorted(logs_dir.glob("*.md"), reverse=True)
        if log_files:
            newest_log = log_files[0]
            session_log_content = newest_log.read_text(encoding="utf-8", errors="replace")

    return {
        "stdout": normalize_output(result.stdout, fixture_path),
        "stderr": normalize_output(result.stderr, fixture_path),
        "exit_code": result.returncode,
        "session_log": normalize_session_log(session_log_content, fixture_path),
    }


def save_baseline(fixture_name: str, command: str, data: dict) -> None:
    """Save captured data as baseline files."""
    baseline_dir = BASELINES_DIR / fixture_name
    baseline_dir.mkdir(parents=True, exist_ok=True)

    # Save individual files
    (baseline_dir / f"{command}_stdout.txt").write_text(data["stdout"])
    (baseline_dir / f"{command}_stderr.txt").write_text(data["stderr"])
    (baseline_dir / f"{command}_exit_code.txt").write_text(str(data["exit_code"]))

    # Save generated files
    if "context_map" in data and data["context_map"]:
        (baseline_dir / "context_map.md").write_text(data["context_map"])
    if "session_log" in data and data["session_log"]:
        (baseline_dir / "session_log.md").write_text(data["session_log"])

    # Save metadata
    metadata = {
        "captured_at": datetime.now().isoformat(),
        "python_version": sys.version,
        "fixture": fixture_name,
        "command": command,
    }
    (baseline_dir / f"{command}_metadata.json").write_text(
        json.dumps(metadata, indent=2)
    )


def capture_fixture(fixture_name: str) -> None:
    """Capture all baselines for a single fixture."""
    print(f"\n{'='*60}")
    print(f"Capturing baseline for: {fixture_name}")
    print(f"{'='*60}")

    # Setup isolated fixture
    fixture_path = setup_fixture(fixture_name)
    print(f"  Fixture path: {fixture_path}")

    try:
        # Capture map command
        print("  Capturing 'ontos map'...")
        map_data = capture_map_command(fixture_path)
        save_baseline(fixture_name, "map", map_data)
        print(f"    Exit code: {map_data['exit_code']}")
        print(f"    Context map: {len(map_data['context_map'])} chars")

        # Capture log command
        print("  Capturing 'ontos log'...")
        log_data = capture_log_command(fixture_path)
        save_baseline(fixture_name, "log", log_data)
        print(f"    Exit code: {log_data['exit_code']}")
        print(f"    Session log: {len(log_data['session_log'])} chars")

        print(f"  Baseline saved to: {BASELINES_DIR / fixture_name}")

    finally:
        # Cleanup temp directory
        shutil.rmtree(fixture_path, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(
        description="Capture Golden Master baselines for Ontos commands"
    )
    parser.add_argument(
        "--fixture",
        choices=["small", "medium", "large", "all"],
        default="all",
        help="Which fixture to capture (default: all)"
    )
    args = parser.parse_args()

    fixtures = ["small", "medium", "large"] if args.fixture == "all" else [args.fixture]

    print("Golden Master Capture Script")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Fixtures dir: {FIXTURES_DIR}")
    print(f"Baselines dir: {BASELINES_DIR}")

    for fixture in fixtures:
        capture_fixture(fixture)

    print("\n" + "="*60)
    print("Capture complete!")
    print("="*60)


if __name__ == "__main__":
    main()
