"""Pre-push hook logic for Ontos.

This script is called by the bash pre-push hook. It checks whether
a session has been archived and provides contextual feedback based
on the size and nature of changes.
"""

import os
import sys
import subprocess
from typing import Tuple, List

# Add scripts dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ontos_config import PROJECT_ROOT

MARKER_FILE = os.path.join(PROJECT_ROOT, '.ontos', 'session_archived')

# Import config with fallbacks
try:
    from ontos_config import ENFORCE_ARCHIVE_BEFORE_PUSH
except ImportError:
    ENFORCE_ARCHIVE_BEFORE_PUSH = True

try:
    from ontos_config import SMALL_CHANGE_THRESHOLD
except ImportError:
    SMALL_CHANGE_THRESHOLD = 20


def get_change_stats() -> Tuple[int, int, List[str]]:
    """Analyze changes since last archive.
    
    Returns:
        Tuple of (files_changed, lines_changed, list_of_files)
    """
    try:
        # Get diff stats for unpushed commits (local vs upstream)
        # If no upstream, fallback to origin/main
        target = "@{u}..HEAD"
        result = subprocess.run(
            ['git', 'diff', '--stat', target],
            capture_output=True, text=True, timeout=10
        )
        
        # Fallback if @{u} fails (e.g. new branch with no upstream set yet)
        if result.returncode != 0:
            target = "origin/main..HEAD"
            result = subprocess.run(
                ['git', 'diff', '--stat', target],
                capture_output=True, text=True, timeout=10
            )

        if result.returncode != 0:
            # If still fails, maybe no origin/main? Just check HEAD (last commit)
            result = subprocess.run(
                ['git', 'diff', '--stat', 'HEAD~1'],
                capture_output=True, text=True, timeout=10
            )

        lines = result.stdout.strip().split('\n')
        files_changed = 0
        lines_changed = 0
        changed_files = []
        
        for line in lines:
            if ' | ' in line:
                files_changed += 1
                try:
                    filename = line.split(' | ')[0].strip()
                    changed_files.append(filename)
                    
                    # Extract line count
                    parts = line.split(' | ')[1].strip().split()
                    if parts and parts[0].isdigit():
                        lines_changed += int(parts[0])
                except IndexError:
                    continue
        
        return files_changed, lines_changed, changed_files[:10]
        
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return 0, 0, []


def suggest_related_docs(changed_files: List[str]) -> List[str]:
    """Suggest possibly related documentation based on changed files.
    
    Simple heuristic: extract base names from changed files.
    """
    suggestions = []
    for f in changed_files[:5]:
        base = os.path.splitext(os.path.basename(f))[0]
        # Skip common non-doc files
        if base not in ('index', 'main', 'app', '__init__', 'test'):
            suggestions.append(base)
    return suggestions[:3]


def print_small_change_message(lines: int, files: List[str]):
    """Print advisory message for small changes."""
    print()
    print("╔════════════════════════════════════════════════════════════╗")
    print(f"║         📝 SMALL CHANGE DETECTED ({lines} lines)                ║")
    print("╠════════════════════════════════════════════════════════════╣")
    if files:
        print(f"║  Changed: {', '.join(files[:3])}")
    print("║")
    print("║  This looks like a small change. You can:")
    print("║    1. Archive anyway: run 'Archive Ontos'")
    print("║    2. Skip this time: git push --no-verify")
    print("║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()


def print_large_change_message(files_count: int, lines: int, files: List[str], suggestions: List[str]):
    """Print blocking message for large changes."""
    print()
    print("╔════════════════════════════════════════════════════════════╗")
    print("║         ❌ SESSION ARCHIVE REQUIRED                        ║")
    print("╠════════════════════════════════════════════════════════════╣")
    print("║")
    print(f"║  📊 Changes detected: {files_count} files, {lines} lines")
    print("║")
    if files:
        print(f"║  📁 Modified: {', '.join(files[:5])}")
        print("║")
    if suggestions:
        print(f"║  💡 Possibly related docs: {', '.join(suggestions)}")
        print("║")
    print("║  Run: 'Archive Ontos' or:")
    print("║    python3 .ontos/scripts/ontos_end_session.py -e <type>")
    print("║")
    print("║  Emergency bypass: git push --no-verify")
    print("║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()


def print_advisory_message(lines: int):
    """Print non-blocking reminder."""
    print()
    print(f"💡 Reminder: {lines} lines changed. Consider archiving your session.")
    print()


def main() -> int:
    """Main hook logic.
    
    Returns:
        Exit code (0 = allow push, 1 = block push)
    """
    # Check if marker exists (session archived)
    if os.path.exists(MARKER_FILE):
        print()
        print("✅ Session archived. Proceeding with push...")
        print()
        
        # Delete marker (one archive = one push)
        try:
            os.remove(MARKER_FILE)
        except OSError:
            pass
        
        return 0
    
    # Analyze changes
    files_count, lines_count, changed_files = get_change_stats()
    suggestions = suggest_related_docs(changed_files)
    
    # Decide based on config and change size
    if not ENFORCE_ARCHIVE_BEFORE_PUSH:
        # Advisory mode
        print_advisory_message(lines_count)
        return 0
    
    # Blocking mode
    if lines_count < SMALL_CHANGE_THRESHOLD:
        print_small_change_message(lines_count, changed_files)
    else:
        print_large_change_message(files_count, lines_count, changed_files, suggestions)
    
    return 1


if __name__ == "__main__":
    sys.exit(main())
