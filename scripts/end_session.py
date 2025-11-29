import os
import datetime
import subprocess
import argparse
import sys

from config import __version__, LOGS_DIR

def get_daily_git_log():
    """Gets the git log for the current day."""
    try:
        # Get commits since midnight
        result = subprocess.run(
            ['git', 'log', '--since=midnight', '--pretty=format:%h - %s'], 
            capture_output=True, 
            text=True
        )
        if result.returncode != 0:
            return "Error getting git log."
        
        logs = result.stdout.strip()
        if not logs:
            return "No commits found for today."
        return logs
    except Exception as e:
        return f"Error running git: {e}"

def create_log_file(topic_slug, quiet=False):
    """Creates a new session log file with a template."""
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)
        if not quiet:
            print(f"Created directory: {LOGS_DIR}")

    today = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"{today}_{topic_slug}.md"
    filepath = os.path.join(LOGS_DIR, filename)

    if os.path.exists(filepath):
        if not quiet:
            print(f"⚠️  Log file already exists: {filepath}")
        return filepath

    daily_log = get_daily_git_log()

    content = f"""---
id: log_{today.replace('-', '')}_{topic_slug.replace('-', '_')}
type: atom
status: active
depends_on: []
---

# Session Log: {topic_slug.replace('-', ' ').title()}
Date: {today}

## 1. Goal
<!-- [AGENT: Fill this in. What was the primary objective of this session?] -->

## 2. Key Decisions
<!-- [AGENT: Fill this in. What architectural or design choices were made?] -->
- 

## 3. Changes Made
<!-- [AGENT: Fill this in. Summary of file changes.] -->
- 

## 4. Next Steps
<!-- [AGENT: Fill this in. What should the next agent work on?] -->
- 

---
## Raw Session History
```text
{daily_log}
```
"""

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    if not quiet:
        print(f"✅ Created session log: {filepath}")
    return filepath

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scaffold a new session log file.')
    parser.add_argument('--version', '-V', action='version', version=f'%(prog)s {__version__}')
    parser.add_argument('topic', type=str, nargs='?', help='Short slug describing the session (e.g. auth-refactor)')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress non-error output')
    args = parser.parse_args()

    if not args.topic:
        parser.print_help()
        sys.exit(1)

    create_log_file(args.topic, args.quiet)
