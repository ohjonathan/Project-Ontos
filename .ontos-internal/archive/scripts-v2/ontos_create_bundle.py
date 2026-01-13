#!/usr/bin/env python3
"""Create release bundle for Ontos distribution.

Usage:
    python3 .ontos/scripts/ontos_create_bundle.py --version 2.9.3

Creates:
    - dist/ontos-bundle.tar.gz (for GitHub Releases)
    - Updates checksums.json with the bundle's SHA256

Options:
    --version VERSION   Version number for the bundle (required)
    --output DIR        Output directory (default: dist)
    --dry-run           Preview what would be bundled without creating

Examples:
    # Create release bundle
    python3 .ontos/scripts/ontos_create_bundle.py --version 2.9.3

    # Preview bundle contents
    python3 .ontos/scripts/ontos_create_bundle.py --version 2.9.3 --dry-run
"""

import argparse
import datetime
import hashlib
import io
import json
import os
import sys
import tarfile
from pathlib import Path

# Files and directories to include in the bundle
BUNDLE_ITEMS = [
    ".ontos/",
    "ontos.py",
    "ontos_init.py",
    "docs/reference/Ontos_Agent_Instructions.md",
    "docs/reference/Ontos_Manual.md",
    "docs/reference/Common_Concepts.md",
]

# Patterns to exclude from the bundle
EXCLUDE_PATTERNS = [
    "__pycache__",
    ".pytest_cache",
    "*.pyc",
    ".DS_Store",
    ".install_incomplete",
    ".ontos_backup",
]


def should_exclude(path: str) -> bool:
    """Check if path should be excluded from bundle."""
    for pattern in EXCLUDE_PATTERNS:
        if pattern.startswith("*"):
            if path.endswith(pattern[1:]):
                return True
        elif pattern in path:
            return True
    return False


def collect_files(bundle_items: list, project_root: Path) -> list:
    """Collect all files to be included in the bundle."""
    files = []
    
    for item in bundle_items:
        item_path = project_root / item
        
        if not item_path.exists():
            print(f"Warning: {item} not found, skipping")
            continue
        
        if item_path.is_dir():
            for root, dirs, filenames in os.walk(item_path):
                # Filter excluded directories
                dirs[:] = [d for d in dirs if not should_exclude(d)]
                
                for filename in filenames:
                    if not should_exclude(filename):
                        filepath = Path(root) / filename
                        relative = filepath.relative_to(project_root)
                        files.append(str(relative))
        else:
            relative = item_path.relative_to(project_root)
            files.append(str(relative))
    
    return sorted(files)


def create_manifest(version: str, files: list) -> dict:
    """Create manifest.json for version-aware verification."""
    return {
        "version": version,
        "created": datetime.datetime.utcnow().isoformat() + "Z",
        "file_count": len(files),
        "files": files,
    }


def create_bundle(version: str, output_dir: Path, project_root: Path, dry_run: bool = False) -> Path:
    """Create the release bundle with manifest.json."""
    # Collect files
    files = collect_files(BUNDLE_ITEMS, project_root)
    
    if dry_run:
        print(f"Would bundle {len(files)} files:")
        for f in files[:20]:
            print(f"  {f}")
        if len(files) > 20:
            print(f"  ... and {len(files) - 20} more")
        return None
    
    bundle_name = "ontos-bundle.tar.gz"
    bundle_path = output_dir / bundle_name
    
    print(f"Creating bundle: {bundle_path}")
    print(f"Version: {version}")
    print(f"Files: {len(files)}")
    
    with tarfile.open(bundle_path, "w:gz") as tar:
        for filepath in files:
            full_path = project_root / filepath
            tar.add(full_path, arcname=filepath)
        
        # Add manifest.json to bundle
        manifest = create_manifest(version, files)
        manifest_content = json.dumps(manifest, indent=2).encode('utf-8')
        
        manifest_info = tarfile.TarInfo(name=".ontos/manifest.json")
        manifest_info.size = len(manifest_content)
        manifest_info.mtime = int(datetime.datetime.utcnow().timestamp())
        tar.addfile(manifest_info, io.BytesIO(manifest_content))
        
        print(f"Added manifest.json with {len(files)} files")
    
    print(f"Created: {bundle_path}")
    return bundle_path


def calculate_checksum(filepath: Path) -> str:
    """Calculate SHA256 checksum of file."""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def update_checksums(checksums_path: Path, version: str, checksum: str) -> None:
    """Update checksums.json with new version checksum."""
    checksums = {}
    if checksums_path.exists():
        content = checksums_path.read_text()
        checksums = json.loads(content)
    
    # Remove comment field if present
    checksums.pop("_comment", None)
    
    # Add new version
    checksums[version] = checksum
    
    checksums_path.write_text(json.dumps(checksums, indent=2) + "\n")
    print(f"Updated: {checksums_path}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create Ontos release bundle",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--version", "-v",
        required=True,
        help="Version number (e.g., 2.9.3)"
    )
    parser.add_argument(
        "--output", "-o",
        default="dist",
        help="Output directory (default: dist)"
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Preview what would be bundled"
    )
    
    args = parser.parse_args()
    
    # Determine project root (script is in .ontos/scripts/)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    
    output_dir = Path(args.output)
    if not args.dry_run:
        output_dir.mkdir(exist_ok=True)
    
    # Create bundle
    bundle_path = create_bundle(args.version, output_dir, project_root, args.dry_run)
    
    if args.dry_run:
        return 0
    
    # Calculate checksum
    checksum = calculate_checksum(bundle_path)
    print(f"SHA256: {checksum}")
    
    # Update checksums.json in project root
    checksums_path = project_root / "checksums.json"
    update_checksums(checksums_path, args.version, checksum)
    
    # Print release instructions
    print("\n" + "=" * 60)
    print("RELEASE INSTRUCTIONS:")
    print("=" * 60)
    print(f"1. Commit checksums.json update")
    print(f"2. Create GitHub Release v{args.version}")
    print(f"3. Upload {bundle_path} to the release")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
