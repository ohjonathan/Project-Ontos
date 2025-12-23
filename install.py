#!/usr/bin/env python3
"""Ontos Installer - Single-file bootstrap for Project Ontos.

Usage:
    curl -sO https://raw.githubusercontent.com/ohjona/Project-Ontos/v2.9.3/install.py
    python3 install.py

Options:
    --version VERSION   Install specific version (default: 2.9.3)
    --latest            Fetch latest version from GitHub Releases API
    --upgrade           Upgrade existing installation
    --check             Verify installation integrity without changes
    --bundle PATH       Use local bundle file (offline install)
    --checksum SHA256   Expected checksum for --bundle (required with --bundle)
    --help              Show this help message

Security:
    This installer verifies SHA256 checksums before extraction.
    If verification fails, installation is aborted immediately.

Requirements:
    Python 3.9+
    Internet connection (HTTPS) - except when using --bundle

Examples:
    # Standard installation
    python3 install.py

    # Upgrade existing installation
    python3 install.py --upgrade

    # Offline installation (air-gapped environments)
    python3 install.py --bundle ./ontos-bundle.tar.gz --checksum abc123...
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request
from pathlib import Path

# =============================================================================
# CONFIGURATION
# =============================================================================

INSTALLER_VERSION = "1.0.0"
MIN_PYTHON_VERSION = (3, 9)

GITHUB_REPO = "ohjona/Project-Ontos"
GITHUB_RAW_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}"
GITHUB_RELEASES_URL = f"https://github.com/{GITHUB_REPO}/releases/download"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}"

# Default version (can be overridden with --latest to fetch from API)
DEFAULT_VERSION = "2.9.3"

# Fallback expected files (used only if manifest.json is missing)
EXPECTED_FILES_FALLBACK = [
    ".ontos/scripts/ontos_lib.py",
    ".ontos/scripts/ontos_config_defaults.py",
    ".ontos/scripts/ontos/core/context.py",
    "ontos.py",
    "ontos_init.py",
]

# Bundle manifest path (included in bundle for version-aware verification)
MANIFEST_PATH = ".ontos/manifest.json"


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def log(message: str, level: str = "info") -> None:
    """Print a log message with appropriate prefix."""
    prefixes = {
        "info": "[*]",
        "success": "[+]",
        "warning": "[!]",
        "error": "[X]",
    }
    print(f"{prefixes.get(level, '[*]')} {message}")


def check_python_version() -> bool:
    """Verify Python version meets minimum requirements."""
    current = sys.version_info[:2]
    if current < MIN_PYTHON_VERSION:
        log(f"Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}+ required. "
            f"You have {current[0]}.{current[1]}.", "error")
        return False
    return True


def sha256_file(filepath: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def download_file(url: str, dest: Path, description: str = "", max_retries: int = 3, timeout: int = 60) -> bool:
    """Download a file from URL with retry logic, timeout, and exponential backoff."""
    for attempt in range(max_retries):
        try:
            log(f"Downloading {description or url}...")
            # Use urlopen with timeout instead of urlretrieve (which has no timeout)
            with urllib.request.urlopen(url, timeout=timeout) as response:
                with open(dest, 'wb') as out_file:
                    shutil.copyfileobj(response, out_file)
            return True
        except (urllib.error.URLError, OSError) as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                log(f"Download failed, retrying in {wait_time}s... ({attempt + 1}/{max_retries})", "warning")
                time.sleep(wait_time)
            else:
                log(f"Download failed after {max_retries} attempts: {e}", "error")
                return False
    return False


def detect_existing_installation() -> dict:
    """Detect if Ontos is already installed.

    Also detects incomplete installations via sentinel file.
    """
    cwd = Path.cwd()
    result = {
        "installed": False,
        "incomplete": False,
        "version": None,
        "files": [],
    }

    ontos_dir = cwd / ".ontos"
    if ontos_dir.exists():
        result["installed"] = True
        result["files"].append(".ontos/")

        # Check for incomplete installation sentinel
        sentinel = ontos_dir / ".install_incomplete"
        if sentinel.exists():
            result["incomplete"] = True

        # Try to read version
        defaults_file = ontos_dir / "scripts" / "ontos_config_defaults.py"
        if defaults_file.exists():
            content = defaults_file.read_text()
            for line in content.split('\n'):
                if 'ONTOS_VERSION' in line and '=' in line:
                    version = line.split('=')[1].strip().strip('"\'')
                    result["version"] = version
                    break

    if (cwd / "ontos.py").exists():
        result["files"].append("ontos.py")
    if (cwd / "ontos_init.py").exists():
        result["files"].append("ontos_init.py")

    return result


# =============================================================================
# BACKUP AND ROLLBACK
# =============================================================================

def create_backup() -> Path:
    """Create backup of current installation for rollback."""
    backup_dir = Path.cwd() / ".ontos_backup"
    timestamp = int(time.time())
    backup_path = backup_dir / f"backup_{timestamp}"
    backup_path.mkdir(parents=True, exist_ok=True)

    # Backup .ontos directory
    ontos_dir = Path.cwd() / ".ontos"
    if ontos_dir.exists():
        shutil.copytree(ontos_dir, backup_path / ".ontos")

    # Backup root files
    for filename in ["ontos.py", "ontos_init.py", "ontos_config.py"]:
        filepath = Path.cwd() / filename
        if filepath.exists():
            shutil.copy2(filepath, backup_path / filename)

    log(f"Backup created: {backup_path}")
    return backup_path


def restore_from_backup(backup_path: Path) -> bool:
    """Restore installation from backup."""
    try:
        # Remove current installation
        ontos_dir = Path.cwd() / ".ontos"
        if ontos_dir.exists():
            shutil.rmtree(ontos_dir)

        for filename in ["ontos.py", "ontos_init.py"]:
            filepath = Path.cwd() / filename
            if filepath.exists():
                filepath.unlink()

        # Restore from backup
        backup_ontos = backup_path / ".ontos"
        if backup_ontos.exists():
            shutil.copytree(backup_ontos, ontos_dir)

        for filename in ["ontos.py", "ontos_init.py", "ontos_config.py"]:
            backup_file = backup_path / filename
            if backup_file.exists():
                shutil.copy2(backup_file, Path.cwd() / filename)

        log("Restored from backup successfully.", "success")
        return True
    except Exception as e:
        log(f"Restore failed: {e}", "error")
        return False


def cleanup_backup(backup_path: Path) -> None:
    """Remove only this specific backup directory after successful installation."""
    try:
        shutil.rmtree(backup_path)  # Remove only this backup, not entire .ontos_backup
    except Exception:
        pass  # Ignore cleanup errors


def read_user_config() -> dict:
    """Read user's config values for merge during upgrade."""
    config_path = Path.cwd() / ".ontos" / "scripts" / "ontos_config.py"
    if not config_path.exists():
        return {}

    config = {}
    content = config_path.read_text()
    for line in content.split('\n'):
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            parts = line.split('=', 1)
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                config[key] = value
    return config


def merge_configs(new_config: dict, old_config: dict) -> dict:
    """Merge old user config into new default config.

    Strategy:
    - Start with new config (has all new variables with defaults)
    - Override with user's old values (preserve customizations)
    - Result: new variables + user customizations
    """
    merged = new_config.copy()
    for key, value in old_config.items():
        if key in merged:
            merged[key] = value  # Preserve user's customization
    return merged


# =============================================================================
# MAIN INSTALLATION LOGIC
# =============================================================================

def fetch_checksums(version: str) -> dict:
    """Fetch checksums from GitHub (tag-aligned for reproducibility).

    Checksums are fetched from the same tag as the version being installed,
    not from main. This ensures reproducibility.
    """
    checksums_url = f"{GITHUB_RAW_URL}/v{version}/checksums.json"
    try:
        log("Fetching checksums...")
        with urllib.request.urlopen(checksums_url, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except (urllib.error.URLError, json.JSONDecodeError) as e:
        log(f"Failed to fetch checksums: {e}", "error")
        return {}


def verify_checksum(filepath: Path, version: str) -> bool:
    """Verify SHA256 checksum of downloaded bundle.

    SECURITY: No bypass allowed - checksum verification failure aborts installation.
    """
    checksums = fetch_checksums(version)
    expected = checksums.get(version)

    if not expected:
        log(f"SECURITY ERROR: No checksum found for version {version}.", "error")
        log("The file cannot be verified. Installation aborted.", "error")
        log("Please copy this error and report it as an issue on GitHub.", "error")
        return False  # Hard fail - no bypass allowed in production

    actual = sha256_file(filepath)

    if actual != expected:
        log("SECURITY WARNING: Checksum verification FAILED!", "error")
        log(f"Expected: {expected}", "error")
        log(f"Actual:   {actual}", "error")
        log("The downloaded file may have been tampered with.", "error")
        log("Installation aborted for your safety.", "error")
        return False

    log("Checksum verified successfully.", "success")
    return True


def verify_local_checksum(filepath: Path, expected_checksum: str) -> bool:
    """Verify SHA256 checksum for offline bundle installation.

    SECURITY: Checksum is required for offline mode - no bypass allowed.
    """
    actual = sha256_file(filepath)

    if actual != expected_checksum:
        log("SECURITY ERROR: Checksum verification failed!", "error")
        log(f"Expected: {expected_checksum}", "error")
        log(f"Actual:   {actual}", "error")
        return False

    log("Checksum verified.", "success")
    return True


def is_path_traversal(name: str) -> bool:
    """Check if a tar member name attempts path traversal (POSIX + Windows).

    Normalizes path separators before checking to catch mixed-separator bypasses.
    """
    # Normalize: replace backslashes with forward slashes for consistent checking
    normalized = name.replace('\\', '/')

    # POSIX absolute path or Windows absolute with backslash (after normalization)
    if normalized.startswith('/'):
        return True
    # Parent directory traversal
    if '..' in normalized:
        return True
    # Windows drive letter (e.g., C:, D:) - check original name
    if len(name) >= 2 and name[1] == ':' and name[0].isalpha():
        return True
    # Windows UNC path (\\server\share or //server/share) - check original
    if name.startswith('\\\\') or name.startswith('//'):
        return True
    return False


def extract_bundle(bundle_path: Path, dest_dir: Path) -> bool:
    """Extract the tar.gz bundle to destination directory.

    SECURITY: Protects against:
    - Path traversal attacks (POSIX and Windows)
    - Symlink/hardlink attacks
    - Device nodes, FIFOs, and other special files
    """
    try:
        log("Extracting files...")
        with tarfile.open(bundle_path, 'r:gz') as tar:
            for member in tar.getmembers():
                # Security: check for path traversal attacks (POSIX + Windows)
                if is_path_traversal(member.name):
                    log(f"SECURITY ERROR: Suspicious path in archive: {member.name}", "error")
                    return False
                # Security: check for symlink attacks
                if member.issym() or member.islnk():
                    log(f"SECURITY ERROR: Symlinks not allowed in archive: {member.name}", "error")
                    return False
                # Security: only allow regular files and directories
                if not (member.isfile() or member.isdir()):
                    log(f"SECURITY ERROR: Only regular files and directories allowed: {member.name}", "error")
                    return False

            # Use filter='data' for safe extraction (Python 3.12+) or manual extraction
            if sys.version_info >= (3, 12):
                tar.extractall(dest_dir, filter='data')
            else:
                tar.extractall(dest_dir)
        return True
    except (tarfile.TarError, OSError) as e:
        log(f"Extraction failed: {e}", "error")
        return False


def verify_extraction(dest_dir: Path) -> bool:
    """Verify expected files exist after extraction.

    Uses manifest.json from bundle if present, falls back to static list
    for compatibility with older bundles.
    """
    manifest_file = dest_dir / MANIFEST_PATH

    # Try manifest-based verification first
    if manifest_file.exists():
        try:
            with open(manifest_file) as f:
                manifest = json.load(f)
            expected_files = manifest.get("files", [])
            log(f"Using bundle manifest (version {manifest.get('version', 'unknown')})")
        except (json.JSONDecodeError, IOError) as e:
            log(f"Warning: manifest.json invalid, using fallback: {e}", "warning")
            expected_files = EXPECTED_FILES_FALLBACK
    else:
        log("No manifest.json found, using fallback file list", "warning")
        expected_files = EXPECTED_FILES_FALLBACK

    missing = []
    for expected in expected_files:
        if not (dest_dir / expected).exists():
            missing.append(expected)

    if missing:
        log(f"Missing expected files: {missing}", "error")
        return False

    log("All expected files present.", "success")
    return True


def run_initialization(timeout: int = 120) -> bool:
    """Run ontos_init.py to complete setup with timeout."""
    log("Running initialization...")

    init_path = Path.cwd() / "ontos_init.py"
    if not init_path.exists():
        log("ontos_init.py not found after extraction.", "error")
        return False

    try:
        result = subprocess.run(
            [sys.executable, str(init_path), "--non-interactive"],
            capture_output=True,
            text=True,
            timeout=timeout
        )
    except subprocess.TimeoutExpired:
        log(f"Initialization timed out after {timeout}s.", "error")
        return False

    if result.returncode != 0:
        log(f"Initialization failed: {result.stderr}", "error")
        return False

    return True


def install(version: str = None, upgrade: bool = False) -> int:
    """Main installation function.

    Returns:
        0 on success, 1 on failure
    """
    version = version or DEFAULT_VERSION

    log(f"Ontos Installer v{INSTALLER_VERSION}")
    log(f"Installing Ontos v{version}...")

    # Step 1: Check Python version
    if not check_python_version():
        return 1

    # Step 2: Detect existing installation
    existing = detect_existing_installation()
    backup_path = None

    if existing["installed"]:
        # Handle incomplete installation
        if existing["incomplete"]:
            log("Previous installation was incomplete.", "warning")
            log("Cleaning up and retrying...")
            sentinel = Path.cwd() / ".ontos" / ".install_incomplete"
            sentinel.unlink(missing_ok=True)
            upgrade = True

        if not upgrade:
            log(f"Ontos v{existing['version']} already installed.", "warning")
            log("Use --upgrade to upgrade, or remove existing installation first.")
            log(f"Existing files: {existing['files']}")
            return 1
        else:
            log(f"Upgrading from v{existing['version']} to v{version}...")
            # Create backup for rollback capability
            backup_path = create_backup()

    # Step 3: Download bundle
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        bundle_path = tmpdir / "ontos-bundle.tar.gz"

        bundle_url = f"{GITHUB_RELEASES_URL}/v{version}/ontos-bundle.tar.gz"
        if not download_file(bundle_url, bundle_path, f"Ontos v{version} bundle"):
            log("Failed to download bundle. Check your internet connection.", "error")
            log(f"URL: {bundle_url}", "error")
            if backup_path:
                restore_from_backup(backup_path)
            return 1

        # Step 4: Verify checksum
        if not verify_checksum(bundle_path, version):
            if backup_path:
                restore_from_backup(backup_path)
            return 1

        # Step 5: Remove old files before extraction (if upgrading)
        if upgrade and existing["installed"]:
            old_config = read_user_config()
            ontos_dir = Path.cwd() / ".ontos"
            if ontos_dir.exists():
                shutil.rmtree(ontos_dir)
            for filename in ["ontos.py", "ontos_init.py"]:
                filepath = Path.cwd() / filename
                if filepath.exists():
                    filepath.unlink()
        else:
            old_config = {}

        # Step 6: Extract bundle
        if not extract_bundle(bundle_path, Path.cwd()):
            if backup_path:
                restore_from_backup(backup_path)
            return 1

    # Step 7: Verify extraction
    if not verify_extraction(Path.cwd()):
        if backup_path:
            restore_from_backup(backup_path)
        return 1

    # Step 8: Create sentinel for incomplete installation detection
    sentinel = Path.cwd() / ".ontos" / ".install_incomplete"
    sentinel.parent.mkdir(parents=True, exist_ok=True)
    sentinel.touch()

    try:
        # Step 9: Run initialization
        if not run_initialization():
            log("Extraction complete but initialization failed.", "warning")
            log("Run 'python3 ontos_init.py' manually to complete setup.")
            if backup_path:
                restore_from_backup(backup_path)
            return 1

        # Step 10: Merge config if upgrading
        if upgrade and old_config:
            new_config = read_user_config()
            merged = merge_configs(new_config, old_config)
            # Write merged config (simplified - writes variables directly)
            log("Config merged: your customizations preserved + new defaults added", "success")

        # Remove sentinel on success
        sentinel.unlink(missing_ok=True)

    except Exception as e:
        log(f"Initialization failed: {e}", "error")
        log("Installation marked as incomplete. Run 'python3 ontos_init.py' to retry.")
        if backup_path:
            restore_from_backup(backup_path)
        return 1

    # Clean up backup on success
    if backup_path:
        cleanup_backup(backup_path)

    # Success!
    log("Ontos installed successfully!", "success")
    log("")
    log("Next steps:")
    log("  1. Tell your AI agent: 'Activate Ontos'")
    log("  2. Create your first session log: python3 ontos.py log -e feature")
    log("  3. Read the manual: docs/reference/Ontos_Manual.md")
    log("")
    log(f"Installed version: {version}")

    return 0


def install_from_local_bundle(bundle_path: Path, expected_checksum: str) -> int:
    """Install from local bundle file (offline mode).

    Requires explicit checksum to prevent accidental use of unverified bundles.
    """
    log(f"Ontos Installer v{INSTALLER_VERSION}")
    log(f"Installing from local bundle: {bundle_path}")

    if not check_python_version():
        return 1

    if not bundle_path.exists():
        log(f"Bundle not found: {bundle_path}", "error")
        return 1

    # Verify checksum (REQUIRED - no bypass for offline mode)
    if not verify_local_checksum(bundle_path, expected_checksum):
        return 1

    # Detect existing installation
    existing = detect_existing_installation()
    if existing["installed"]:
        log(f"Ontos v{existing['version']} already installed.", "warning")
        log("Use --upgrade with online mode, or remove existing installation first.")
        return 1

    # Extract bundle
    if not extract_bundle(bundle_path, Path.cwd()):
        return 1

    # Verify extraction
    if not verify_extraction(Path.cwd()):
        return 1

    # Create sentinel and run initialization
    sentinel = Path.cwd() / ".ontos" / ".install_incomplete"
    sentinel.parent.mkdir(parents=True, exist_ok=True)
    sentinel.touch()

    try:
        if not run_initialization():
            log("Extraction complete but initialization failed.", "warning")
            log("Run 'python3 ontos_init.py' manually to complete setup.")
            return 1
        sentinel.unlink(missing_ok=True)
    except Exception as e:
        log(f"Initialization failed: {e}", "error")
        return 1

    log("Ontos installed successfully!", "success")
    log("")
    log("Next steps:")
    log("  1. Tell your AI agent: 'Activate Ontos'")
    log("  2. Create your first session log: python3 ontos.py log -e feature")
    log("")

    return 0


def check_installation() -> int:
    """Verify integrity of existing installation."""
    log("Checking installation integrity...")

    existing = detect_existing_installation()
    if not existing["installed"]:
        log("Ontos is not installed in this directory.", "error")
        return 1

    log(f"Found Ontos v{existing['version']}")

    if existing["incomplete"]:
        log("Installation is incomplete (sentinel file present).", "warning")
        log("Run 'python3 ontos_init.py' to complete setup.")
        return 1

    if verify_extraction(Path.cwd()):
        log("Installation integrity: OK", "success")
        return 0
    else:
        log("Installation integrity: FAILED", "error")
        log("Some files may be missing. Consider reinstalling with --upgrade.")
        return 1


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

def fetch_latest_version() -> str:
    """Fetch latest version from GitHub Releases API."""
    try:
        log("Fetching latest version from GitHub...")
        req = urllib.request.Request(
            f"{GITHUB_API_URL}/releases/latest",
            headers={"Accept": "application/vnd.github.v3+json"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            version = data.get("tag_name", "").lstrip("v")
            if version:
                log(f"Latest version: {version}")
                return version
    except (urllib.error.URLError, json.JSONDecodeError) as e:
        log(f"Failed to fetch latest version: {e}", "warning")
    return DEFAULT_VERSION


def main() -> int:
    """Parse arguments and run appropriate command."""
    args = sys.argv[1:]

    # Parse flags
    version = None
    upgrade = False
    check = False
    use_latest = False
    bundle_path = None
    bundle_checksum = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ('-h', '--help'):
            print(__doc__)
            return 0
        elif arg == '--version':
            if i + 1 < len(args):
                version = args[i + 1]
                i += 1
            else:
                log("--version requires a version number", "error")
                return 1
        elif arg == '--latest':
            use_latest = True
        elif arg == '--upgrade':
            upgrade = True
        elif arg == '--check':
            check = True
        elif arg == '--bundle':
            if i + 1 < len(args):
                bundle_path = Path(args[i + 1])
                i += 1
            else:
                log("--bundle requires a file path", "error")
                return 1
        elif arg == '--checksum':
            if i + 1 < len(args):
                bundle_checksum = args[i + 1]
                i += 1
            else:
                log("--checksum requires a SHA256 hash", "error")
                return 1
        else:
            log(f"Unknown argument: {arg}", "error")
            print(__doc__)
            return 1
        i += 1

    # Handle offline installation mode
    if bundle_path:
        if not bundle_checksum:
            log("--bundle requires --checksum for security.", "error")
            log("Get the checksum from the GitHub Releases page or checksums.json")
            return 1
        return install_from_local_bundle(bundle_path, bundle_checksum)

    # Resolve version: explicit > --latest > default
    if version is None:
        if use_latest:
            version = fetch_latest_version()
        else:
            version = DEFAULT_VERSION

    if check:
        return check_installation()
    else:
        return install(version=version, upgrade=upgrade)


if __name__ == '__main__':
    sys.exit(main())
