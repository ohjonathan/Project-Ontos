"""Migration script for Ontos v1.x logs to v2.0 schema."""

import os
import re
import argparse
import sys
from typing import Optional

from ontos_config import LOGS_DIR

def migrate_file(filepath: str, dry_run: bool = False) -> bool:
    """Migrate a single file to v2.0 schema.
    
    Changes:
    - type: atom -> type: log
    - Adds event_type: chore (if missing)
    - Adds impacts: [] (if missing)
    - Moves depends_on content to impacts (if logic permits, otherwise just adds impacts)
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except (IOError, OSError) as e:
        print(f"Error reading {filepath}: {e}")
        return False
        
    if not content.startswith('---'):
        return False
        
    parts = content.split('---', 2)
    if len(parts) < 3:
        return False
        
    frontmatter = parts[1]
    body = parts[2]
    
    # Check if migration is needed
    if 'type: log' in frontmatter and 'event_type:' in frontmatter:
        # Already v2
        return False
        
    if 'type: atom' not in frontmatter and 'type: log' not in frontmatter:
        # Not a target file
        return False

    new_frontmatter = frontmatter
    
    # 1. Update type
    new_frontmatter = re.sub(r'type:\s*atom', 'type: log', new_frontmatter)
    
    # 2. Add event_type if missing
    if 'event_type:' not in new_frontmatter:
        if 'status:' in new_frontmatter:
            new_frontmatter = re.sub(r'(status:.*)', r'\1\nevent_type: chore', new_frontmatter)
        else:
            new_frontmatter += "\nevent_type: chore"
            
    # 3. Handle depends_on -> impacts
    # If depends_on exists, we might want to move it to impacts or just add impacts
    depends_on_match = re.search(r'depends_on:\s*(\[.*?\])', new_frontmatter, re.DOTALL)
    if 'impacts:' not in new_frontmatter:
        if depends_on_match:
            deps = depends_on_match.group(1)
            if deps != '[]':
                # Move depends_on to impacts
                new_frontmatter = new_frontmatter.replace(deps, '[]') # Clear depends_on
                new_frontmatter += f"\nimpacts: {deps}"
            else:
                new_frontmatter += "\nimpacts: []"
        else:
            new_frontmatter += "\nimpacts: []"
            
    # 4. Remove empty depends_on if we want to clean up, or keep it (log schema warns but allows)
    # Let's keep it minimal
    
    if new_frontmatter == frontmatter:
        return False
        
    if dry_run:
        print(f"[DRY RUN] Would migrate {filepath}")
        return True
        
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"---{new_frontmatter}---{body}")
        print(f"Migrated {filepath}")
        return True
    except (IOError, OSError) as e:
        print(f"Error writing {filepath}: {e}")
        return False

def main() -> None:
    parser = argparse.ArgumentParser(description='Migrate Ontos v1.x logs to v2.0 schema.')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without modifying files')
    parser.add_argument('--dir', type=str, default=LOGS_DIR, help=f'Directory to scan (default: {LOGS_DIR})')
    args = parser.parse_args()
    
    if not os.path.isdir(args.dir):
        print(f"Directory not found: {args.dir}")
        sys.exit(1)
        
    print(f"Scanning {args.dir} for v1 logs...")
    
    count = 0
    migrated = 0
    
    for filename in os.listdir(args.dir):
        if not filename.endswith('.md'):
            continue
            
        # Only migrate files that look like logs (start with date)
        if not re.match(r'^\d{4}-\d{2}-\d{2}', filename):
            continue
            
        filepath = os.path.join(args.dir, filename)
        if migrate_file(filepath, dry_run=args.dry_run):
            migrated += 1
        count += 1
            
    print(f"Scanned {count} files.")
    if args.dry_run:
        print(f"Would migrate {migrated} files.")
    else:
        print(f"Migrated {migrated} files.")

if __name__ == "__main__":
    main()
