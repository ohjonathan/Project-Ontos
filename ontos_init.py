"""Unified initialization script for Project Ontos.

Prerequisites:
- Copy the `.ontos/` folder to your project root BEFORE running this script
- Copy this file (ontos_init.py) to your project root

This script will:
1. Verify .ontos/ exists (required)
2. Create optional directories (.ontos-internal, docs)
3. Install git hooks
4. Generate the initial context map
"""

import os
import sys
import shutil
import subprocess

# Define paths relative to the script logic (assuming script runs from root or is copied to root)
# If this script lives in repo root, fine. If in .ontos/scripts, user might call it differently.
# Typically user wget/curls this to root and runs it.

def main():
    print("Welcome to Project Ontos v2.0 Setup")
    print("===================================")
    
    # 1. Ensure .ontos directory exists and is populated
    # In a real install, this might involve cloning or copying from a package
    # For now, assuming we are in the repo where .ontos exists or we are initializing a fresh repo
    
    if not os.path.exists('.ontos/scripts'):
        print("Error: .ontos/scripts not found. Please ensure you have cloned Project Ontos correctly.")
        print("If you are installing into a new project, copy the .ontos directory first.")
        sys.exit(1)
        
    print("\n1. Setting up directories...")
    dirs = [
        '.ontos-internal',
        '.ontos-internal/kernel',
        '.ontos-internal/strategy',
        '.ontos-internal/atom',
        'docs',
        'docs/reference',
        'docs/logs'
    ]
    
    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d)
            print(f"  Created {d}/")
        else:
            print(f"  {d}/ already exists")
            
    print("\n2. Creating configuration...")
    if not os.path.exists('ontos_config.py'):
        try:
            # Copy template or simple defaults
            with open('ontos_config.py', 'w') as f:
                f.write("# Ontos Configuration\n")
                f.write("# Override defaults from .ontos/scripts/ontos_config_defaults.py here\n\n")
                f.write("from typing import Any\n\n")
                f.write("# DOCS_DIR = 'docs'\n")
            print("  Created ontos_config.py")
        except Exception as e:
            print(f"  Error creating config: {e}")
    else:
        print("  ontos_config.py already exists")

    print("\n3. Installing git hooks...")
    try:
        subprocess.run([sys.executable, '.ontos/scripts/ontos_install_hooks.py'], check=True)
    except subprocess.CalledProcessError:
        print("  Warning: Failed to install hooks. You can try manually running .ontos/scripts/ontos_install_hooks.py")
        
    print("\n4. Generating initial Context Map...")
    try:
        subprocess.run([sys.executable, '.ontos/scripts/ontos_generate_context_map.py'], check=True)
    except subprocess.CalledProcessError:
        print("  Warning: Context map generation failed.")
        
    print("\n✅ Ontos initialized successfully!")
    print("Next steps:")
    print("1. Edit .ontos-internal/kernel/mission.md to define your project")
    print("2. Run 'python3 .ontos/scripts/ontos_end_session.py init' to log this setup")

if __name__ == "__main__":
    main()
