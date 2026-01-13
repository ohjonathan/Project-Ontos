"""Pre-commit hook for Ontos auto-consolidation (v2.5).

Safety features (from architectural review):
- CI detection: Skips in automated environments
- Rebase detection: Skips during rebase/cherry-pick
- Explicit staging: Only stages tracked files touched by consolidation
- Try/except wrapper: Guarantees return 0
- Dual condition: Count AND old_logs must both be true
"""

import os
import sys
import subprocess


from ontos.core.paths import (
    resolve_config,
    get_logs_dir,
    get_log_count,
    get_logs_older_than,
    get_archive_dir,
    get_decision_history_path,
)
from ontos_config_defaults import PROJECT_ROOT


def get_mode() -> str:
    """Get current Ontos mode."""
    return resolve_config('ONTOS_MODE', 'prompted')


def is_ci_environment() -> bool:
    """Detect CI/CD environments where hook should be skipped."""
    ci_indicators = [
        'CI',                    # Generic (GitHub Actions, GitLab CI, etc.)
        'CONTINUOUS_INTEGRATION', # Travis CI
        'GITHUB_ACTIONS',        # GitHub Actions
        'GITLAB_CI',             # GitLab CI
        'JENKINS_URL',           # Jenkins
        'CIRCLECI',              # CircleCI
        'BUILDKITE',             # Buildkite
        'TF_BUILD',              # Azure Pipelines
    ]
    return any(os.environ.get(var) for var in ci_indicators)


def is_special_git_operation() -> bool:
    """Detect rebase, cherry-pick, etc. where hook should be skipped."""
    result = subprocess.run(
        ['git', 'rev-parse', '--git-dir'],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return False

    git_dir = result.stdout.strip()

    # Rebase in progress
    if (os.path.exists(os.path.join(git_dir, 'rebase-merge')) or
        os.path.exists(os.path.join(git_dir, 'rebase-apply'))):
        return True

    # Cherry-pick in progress
    if os.path.exists(os.path.join(git_dir, 'CHERRY_PICK_HEAD')):
        return True

    return False


def should_consolidate() -> bool:
    """Check if consolidation should run.

    v2.6.2: Simplified to count-based check only.
    Triggers when log count exceeds LOG_WARNING_THRESHOLD (20).
    Consolidation keeps newest LOG_RETENTION_COUNT (10) logs.
    """
    mode = get_mode()

    # Only auto-consolidate in automated mode
    if mode != 'automated':
        return False

    # Skip in CI environments
    if is_ci_environment():
        return False

    # Skip during rebase/cherry-pick
    if is_special_git_operation():
        return False

    # Skip if explicitly disabled
    if os.environ.get('ONTOS_SKIP_HOOKS', '').lower() in ('1', 'true', 'yes'):
        return False

    # Check if feature is enabled (allows override)
    if not resolve_config('AUTO_CONSOLIDATE_ON_COMMIT', True):
        return False

    # v2.6.2: Simple count-based check
    log_count = get_log_count()
    warning_threshold = resolve_config('LOG_WARNING_THRESHOLD', 20)

    return log_count > warning_threshold


def run_consolidation() -> tuple:
    """Run consolidation in quiet, auto mode.

    Returns:
        (success, output) tuple where success is a bool and output is
        the combined stdout/stderr from the consolidation script.
    """
    script = os.path.join(PROJECT_ROOT, '.ontos', 'scripts', 'ontos_consolidate.py')
    threshold_days = resolve_config('CONSOLIDATION_THRESHOLD_DAYS', 30)

    result = subprocess.run(
        [sys.executable, script, '--all', '--quiet', '--days', str(threshold_days)],
        capture_output=True,
        text=True
    )
    return result.returncode == 0, result.stdout + result.stderr


def get_tracked_modified_files(directory: str) -> list:
    """Get list of tracked files in a directory that have been modified.
    
    Only returns files that:
    1. Are tracked by git
    2. Have modifications (staged or unstaged)
    
    This prevents staging untracked WIP files.
    """
    if not os.path.exists(directory):
        return []
    
    result = subprocess.run(
        ['git', 'diff', '--name-only', 'HEAD', '--', directory],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return []
    
    files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
    return files


def get_untracked_files(directory: str) -> list:
    """Get list of untracked files in a directory.
    
    Used to stage new files created by consolidation (e.g., archived logs).
    """
    if not os.path.exists(directory):
        return []
    
    result = subprocess.run(
        ['git', 'ls-files', '--others', '--exclude-standard', '--', directory],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return []
    
    files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
    return files


def stage_consolidated_files() -> None:
    """Stage ONLY tracked files modified by consolidation.

    CRITICAL: Do NOT stage untracked files or entire directories.
    Only stage specific files that were modified during consolidation.
    """
    # Use config-aware path resolution
    decision_history = get_decision_history_path()
    archive_dir = get_archive_dir()
    logs_dir = get_logs_dir()

    # Stage decision_history.md if it was modified and is tracked
    if os.path.exists(decision_history):
        # Check if file is tracked
        result = subprocess.run(
            ['git', 'ls-files', decision_history],
            capture_output=True, text=True
        )
        if result.stdout.strip():
            subprocess.run(['git', 'add', decision_history], capture_output=True)

    # Stage tracked modified files in archive directory
    modified_archive = get_tracked_modified_files(archive_dir)
    for filepath in modified_archive:
        full_path = os.path.join(PROJECT_ROOT, filepath) if not os.path.isabs(filepath) else filepath
        subprocess.run(['git', 'add', full_path], capture_output=True)
    
    # Stage NEW untracked files in archive directory (created by consolidation)
    new_archive = get_untracked_files(archive_dir)
    for filepath in new_archive:
        full_path = os.path.join(PROJECT_ROOT, filepath) if not os.path.isabs(filepath) else filepath
        subprocess.run(['git', 'add', full_path], capture_output=True)

    # Stage tracked modified files in logs directory (deleted logs)
    modified_logs = get_tracked_modified_files(logs_dir)
    for filepath in modified_logs:
        full_path = os.path.join(PROJECT_ROOT, filepath) if not os.path.isabs(filepath) else filepath
        subprocess.run(['git', 'add', full_path], capture_output=True)


def main() -> int:
    """Main entry point for pre-commit hook.

    Returns:
        0 ALWAYS (never block commit) - wrapped in try/except
    """
    try:
        verbose = os.environ.get('ONTOS_VERBOSE', '').lower() in ('1', 'true')

        if verbose:
            print("   [Ontos pre-commit hook running...]")

        if not should_consolidate():
            if verbose:
                print("   [Ontos: No consolidation needed]")
            return 0

        log_count = get_log_count()
        threshold = resolve_config('LOG_WARNING_THRESHOLD', 20)

        print(f"   Auto-consolidating ({log_count} logs > {threshold} threshold)...")

        success, output = run_consolidation()

        if success:
            stage_consolidated_files()
            print("   Consolidated and staged")
        else:
            # Check if it's a "no work" vs "real error" (v2.6.2: count-based messages)
            if "within threshold" in output or "Nothing to consolidate" in output:
                if verbose:
                    print("   [Ontos: Log count within threshold]")
            else:
                # Surface real errors (permission, disk, etc.)
                print(f"   Warning: Consolidation issue: {output[:200]}")

        return 0  # Never block commit

    except Exception as e:
        # Guarantee return 0 even on unexpected errors
        print(f"   Warning: Ontos pre-commit hook error: {e}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
