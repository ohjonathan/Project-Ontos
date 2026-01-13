"""Pre-push hook logic for Ontos.

v2.4: Added auto-archive mode, hook timeout, context map regeneration.

This script is called by the bash pre-push hook. It checks whether
a session has been archived and provides contextual feedback based
on the size and nature of changes.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Tuple, List

# Add scripts dir to path

from ontos_config import PROJECT_ROOT

MARKER_FILE = os.path.join(PROJECT_ROOT, '.ontos', 'session_archived')

# Import config with fallbacks
# v2.4: Use resolve_config for mode-aware settings
try:
    from ontos.core.paths import resolve_config
    ENFORCE_ARCHIVE_BEFORE_PUSH = resolve_config('ENFORCE_ARCHIVE_BEFORE_PUSH', True)
    AUTO_ARCHIVE_ON_PUSH = resolve_config('AUTO_ARCHIVE_ON_PUSH', False)
    SMALL_CHANGE_THRESHOLD = resolve_config('SMALL_CHANGE_THRESHOLD', 20)
except ImportError:
    # Fallback if resolve_config not available
    try:
        from ontos_config import ENFORCE_ARCHIVE_BEFORE_PUSH
    except ImportError:
        ENFORCE_ARCHIVE_BEFORE_PUSH = True
    try:
        from ontos_config import SMALL_CHANGE_THRESHOLD
    except ImportError:
        SMALL_CHANGE_THRESHOLD = 20
    AUTO_ARCHIVE_ON_PUSH = False

try:
    from ontos_config_defaults import HOOK_TIMEOUT_SECONDS
except ImportError:
    HOOK_TIMEOUT_SECONDS = 10

try:
    from ontos_config_defaults import LOG_WARNING_THRESHOLD
except ImportError:
    LOG_WARNING_THRESHOLD = 20


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


def count_active_logs() -> int:
    """Count active log files in the logs directory.
    
    Returns:
        Number of log files.
    """
    try:
        from ontos_config import LOGS_DIR
    except ImportError:
        LOGS_DIR = 'docs/logs'
    
    if not os.path.exists(LOGS_DIR):
        return 0
    
    count = 0
    for filename in os.listdir(LOGS_DIR):
        if filename.endswith('.md') and not filename.startswith('_'):
            count += 1
    return count


def regenerate_context_map() -> None:
    """Regenerate context map to ensure it's current.
    
    v2.4: Auto-regeneration prevents stale context maps.
    """
    try:
        bundled_map = Path(__file__).resolve().parent / "ontos_generate_context_map.py"
        result = subprocess.run(
            [sys.executable, str(bundled_map)],
            capture_output=True, text=True, timeout=HOOK_TIMEOUT_SECONDS,
            cwd=PROJECT_ROOT
        )
        
        if result.returncode != 0:
            print("⚠️  Context map generation failed. Proceeding anyway.")
            return
        
        # Check if context map changed
        diff_result = subprocess.run(
            ['git', 'diff', '--name-only', 'Ontos_Context_Map.md'],
            capture_output=True, text=True, cwd=PROJECT_ROOT
        )
        
        if diff_result.stdout.strip():
            print("📝 Context map updated (will be in next commit)")
    except subprocess.TimeoutExpired:
        print("⚠️  Context map generation timed out. Proceeding anyway.")
    except (FileNotFoundError, OSError):
        pass


def run_auto_archive() -> bool:
    """Run auto-archive via ontos_end_session.py --auto.
    
    Returns:
        True if auto-archive succeeded, False otherwise.
    """
    try:
        bundled_end = Path(__file__).resolve().parent / "ontos_end_session.py"
        result = subprocess.run(
            [sys.executable, str(bundled_end), '--auto'],
            timeout=HOOK_TIMEOUT_SECONDS,
            cwd=PROJECT_ROOT
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("⚠️  Auto-archive timed out. Proceeding with push.")
        print("    Run 'Maintain Ontos' to check status.")
        return True  # Don't block on timeout
    except (FileNotFoundError, OSError):
        return False


def check_dirty_git() -> bool:
    """Check if there are uncommitted changes.
    
    Returns:
        True if there are uncommitted changes.
    """
    try:
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True, text=True, timeout=5
        )
        return bool(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


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


def check_version_reminder() -> list:
    """Remind contributors to update changelog when shipping new versions.
    
    v2.6 improvements:
    - Uses origin tracking ref to catch multi-commit pushes (Codex)
    - Includes Dual_Mode_Matrix.md reminder (Gemini)
    
    Returns:
        List of reminder strings to print.
    """
    from ontos_config_defaults import is_ontos_repo
    
    if not is_ontos_repo():
        return []  # Skip for users
    
    # Get current branch
    branch_result = subprocess.run(
        ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
        capture_output=True, text=True
    )
    if branch_result.returncode != 0:
        return []
    
    branch = branch_result.stdout.strip()
    
    # Get files changed since upstream (catches multi-commit pushes)
    # Falls back to HEAD~1 if no upstream exists
    result = subprocess.run(
        ['git', 'diff', '--name-only', f'origin/{branch}..HEAD'],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        # Fallback for new branches without upstream
        result = subprocess.run(
            ['git', 'diff', '--name-only', 'HEAD~1..HEAD'],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return []
    
    changed_files = [f for f in result.stdout.strip().split('\n') if f]
    scripts_changed = any(f.startswith('.ontos/scripts/') for f in changed_files)
    matrix_changed = '.ontos-internal/reference/Dual_Mode_Matrix.md' in changed_files
    
    reminders = []
    
    if scripts_changed:
        reminder = (
            "⚠️  CONTRIBUTOR REMINDER: .ontos/scripts/ modified\n"
            "   If shipping a new version, remember to update:\n"
            "   1. ONTOS_VERSION in ontos_config_defaults.py\n"
            "   2. Ontos_CHANGELOG.md with release notes\n"
        )
        # Also remind about Dual_Mode_Matrix if script behavior changed
        if not matrix_changed:
            reminder += "   3. reference/Dual_Mode_Matrix.md if behavior changed\n"
        reminders.append(reminder)
    
    return reminders

def main() -> int:
    """Main hook logic.
    
    Returns:
        Exit code (0 = allow push, 1 = block push)
    """
    # v2.4: Regenerate context map first
    regenerate_context_map()
    
    # v2.4+: Check log count and warn (v2.6.2: uses LOG_WARNING_THRESHOLD)
    log_count = count_active_logs()
    if log_count > LOG_WARNING_THRESHOLD:
        print(f"⚠️  {log_count} logs exceed threshold ({LOG_WARNING_THRESHOLD}). Run 'Maintain Ontos' to consolidate.")
    
    # v2.6: Version release reminder for contributors
    version_reminders = check_version_reminder()
    for reminder in version_reminders:
        print(reminder)
    
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
    
    # v2.4: Auto-archive mode
    if AUTO_ARCHIVE_ON_PUSH:
        # Check for dirty git
        if check_dirty_git():
            print()
            print("⚠️  Uncommitted changes detected. Skipping auto-archive.")
            print("    Commit your changes first, or run 'Archive Ontos' manually.")
            print()
            # Still proceed with push in auto mode
            return 0
        
        # Run auto-archive
        run_auto_archive()
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
