#!/usr/bin/env python3
"""
Golden Master Comparison Script

Compares current Ontos output against captured baselines.
Used in CI to detect behavior regressions during v3.0 refactoring.

Usage:
    python compare_golden_master.py [--fixture small|medium|large|all]

Exit codes:
    0 - All comparisons pass
    1 - One or more comparisons failed (or configuration error)
"""

import argparse
import difflib
import json
import shutil
import subprocess
import sys
from pathlib import Path

# Constants
SCRIPT_DIR = Path(__file__).parent
FIXTURES_DIR = SCRIPT_DIR / "fixtures"
BASELINES_DIR = SCRIPT_DIR / "baselines"
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# Import normalization functions from capture script
from capture_golden_master import (
    normalize_output,
    normalize_context_map,
    normalize_session_log,
    setup_fixture,
)


class ComparisonResult:
    """Result of comparing actual vs expected output."""

    def __init__(self, name: str):
        self.name = name
        self.passed = True
        self.differences: list[str] = []

    def add_difference(self, diff: str):
        self.passed = False
        self.differences.append(diff)

    def __str__(self):
        if self.passed:
            return f"  {self.name}: PASS"
        return f"  {self.name}: FAIL\n" + "\n".join(
            f"    {line}" for line in self.differences[:20]  # Limit output
        )


def compare_text(expected: str, actual: str, name: str) -> ComparisonResult:
    """Compare two text strings and return detailed differences."""
    result = ComparisonResult(name)

    if expected == actual:
        return result

    # Generate unified diff
    expected_lines = expected.splitlines(keepends=True)
    actual_lines = actual.splitlines(keepends=True)

    diff = list(difflib.unified_diff(
        expected_lines,
        actual_lines,
        fromfile="expected",
        tofile="actual",
        lineterm=""
    ))

    if diff:
        result.add_difference(f"Text differs ({len(diff)} diff lines)")
        for line in diff[:10]:  # Show first 10 diff lines
            result.add_difference(line.rstrip())
        if len(diff) > 10:
            result.add_difference(f"... and {len(diff) - 10} more lines")

    return result


def compare_exit_code(expected: int, actual: int, name: str) -> ComparisonResult:
    """Compare exit codes."""
    result = ComparisonResult(name)

    if expected != actual:
        result.add_difference(f"Exit code: expected {expected}, got {actual}")

    return result


def run_map_command(fixture_path: Path) -> dict:
    """Run map command and return normalized results."""
    # Copy ontos.py and .ontos/ to fixture
    shutil.copy(PROJECT_ROOT / "ontos.py", fixture_path / "ontos.py")
    if (fixture_path / ".ontos").exists():
        shutil.rmtree(fixture_path / ".ontos")
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


def run_log_command(fixture_path: Path) -> dict:
    """Run log command and return normalized results."""
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
         "commit", "-m", "Test change"],
        cwd=fixture_path,
        capture_output=True,
        check=True
    )

    try:
        result = subprocess.run(
            [
                sys.executable, "ontos.py", "log",
                "-e", "chore",
                "-s", "Golden Master Compare",
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

    logs_dir = fixture_path / ".ontos-internal" / "logs"
    session_log_content = ""
    if logs_dir.exists():
        log_files = sorted(logs_dir.glob("*.md"), reverse=True)
        if log_files:
            session_log_content = log_files[0].read_text(encoding="utf-8", errors="replace")

    return {
        "stdout": normalize_output(result.stdout, fixture_path),
        "stderr": normalize_output(result.stderr, fixture_path),
        "exit_code": result.returncode,
        "session_log": normalize_session_log(session_log_content, fixture_path),
    }


def load_baseline(fixture_name: str, command: str) -> dict:
    """Load saved baseline data."""
    baseline_dir = BASELINES_DIR / fixture_name

    if not baseline_dir.exists():
        raise FileNotFoundError(f"Baseline not found: {baseline_dir}")

    data = {
        "stdout": (baseline_dir / f"{command}_stdout.txt").read_text(encoding="utf-8", errors="replace"),
        "stderr": (baseline_dir / f"{command}_stderr.txt").read_text(encoding="utf-8", errors="replace"),
        "exit_code": int((baseline_dir / f"{command}_exit_code.txt")
                         .read_text(encoding="utf-8", errors="replace")
                         .strip()),
    }

    # Load generated files if present
    context_map_file = baseline_dir / "context_map.md"
    if context_map_file.exists():
        data["context_map"] = context_map_file.read_text(encoding="utf-8", errors="replace")

    session_log_file = baseline_dir / "session_log.md"
    if session_log_file.exists():
        data["session_log"] = session_log_file.read_text(encoding="utf-8", errors="replace")

    return data


def compare_fixture(fixture_name: str) -> bool:
    """
    Compare all commands for a single fixture.
    Returns True if all comparisons pass.
    """
    print(f"\n{'='*60}")
    print(f"Comparing: {fixture_name}")
    print(f"{'='*60}")

    all_passed = True
    fixture_path = setup_fixture(fixture_name)

    try:
        # Compare map command
        print("\n  Testing 'ontos map'...")
        expected_map = load_baseline(fixture_name, "map")
        actual_map = run_map_command(fixture_path)

        results = [
            compare_exit_code(
                expected_map["exit_code"],
                actual_map["exit_code"],
                "map exit_code"
            ),
            compare_text(
                expected_map["stdout"],
                actual_map["stdout"],
                "map stdout"
            ),
            # v1.1: Add stderr comparison
            compare_text(
                expected_map["stderr"],
                actual_map["stderr"],
                "map stderr"
            ),
            compare_text(
                expected_map.get("context_map", ""),
                actual_map.get("context_map", ""),
                "context_map.md"
            ),
        ]

        for r in results:
            print(r)
            if not r.passed:
                all_passed = False

        # Reset fixture for log command
        shutil.rmtree(fixture_path)
        fixture_path = setup_fixture(fixture_name)

        # Copy ontos again for log command
        shutil.copy(PROJECT_ROOT / "ontos.py", fixture_path / "ontos.py")
        shutil.copytree(
            PROJECT_ROOT / ".ontos",
            fixture_path / ".ontos",
            dirs_exist_ok=True
        )

        # Compare log command
        print("\n  Testing 'ontos log'...")
        expected_log = load_baseline(fixture_name, "log")
        actual_log = run_log_command(fixture_path)

        results = [
            compare_exit_code(
                expected_log["exit_code"],
                actual_log["exit_code"],
                "log exit_code"
            ),
            compare_text(
                expected_log["stdout"],
                actual_log["stdout"],
                "log stdout"
            ),
            # v1.1: Add stderr comparison
            compare_text(
                expected_log["stderr"],
                actual_log["stderr"],
                "log stderr"
            ),
            # v1.1: Add session_log comparison
            compare_text(
                expected_log.get("session_log", ""),
                actual_log.get("session_log", ""),
                "session_log.md"
            ),
        ]

        for r in results:
            print(r)
            if not r.passed:
                all_passed = False

    finally:
        shutil.rmtree(fixture_path, ignore_errors=True)

    return all_passed


def main():
    parser = argparse.ArgumentParser(
        description="Compare Ontos output against Golden Master baselines"
    )
    parser.add_argument(
        "--fixture",
        choices=["small", "medium", "large", "all"],
        default="all",
        help="Which fixture to compare (default: all)"
    )
    args = parser.parse_args()

    fixtures = ["small", "medium"] if args.fixture == "all" else [args.fixture]

    print("Golden Master Comparison Script")
    print(f"Project root: {PROJECT_ROOT}")

    all_passed = True
    for fixture in fixtures:
        if not compare_fixture(fixture):
            all_passed = False

    print("\n" + "="*60)
    if all_passed:
        print("All comparisons PASSED")
        print("="*60)
        sys.exit(0)
    else:
        print("Some comparisons FAILED")
        print("="*60)
        sys.exit(1)


if __name__ == "__main__":
    main()
