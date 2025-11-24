import os
import json
import sys
import argparse

DEFAULT_DOCS_DIR = 'docs'
PROMPT_FILE = 'migration_prompt.txt'
RESPONSE_FILE = 'migration_response.json'

def has_frontmatter(filepath):
    """Checks if a file already has YAML frontmatter."""
    try:
        with open(filepath, 'r') as f:
            line = f.readline()
            return line.strip() == '---'
    except:
        return False

def scan_for_untagged_files(root_dir):
    """Finds all markdown files without frontmatter."""
    untagged = []
    for subdir, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.md'):
                filepath = os.path.join(subdir, file)
                if not has_frontmatter(filepath):
                    untagged.append(filepath)
    return untagged

def generate_prompt(files):
    """Generates a prompt containing the content of untagged files."""
    prompt = """You are the Ontos Librarian. I have a list of documentation files that need YAML frontmatter.
For each file, analyze its content and generate the appropriate YAML metadata.

Output ONLY a valid JSON object where the keys are the filepaths and the values are the YAML frontmatter fields (id, type, status, depends_on).
Do NOT output markdown code blocks. Just the raw JSON.

Rules:
1. 'id': Generate a unique, snake_case slug based on the filename and content.
2. 'type': Choose one of [kernel, strategy, product, atom].
   - kernel: Mission, values, high-level principles.
   - strategy: Business goals, monetization, target audience.
   - product: User journeys, features, requirements.
   - atom: Technical specs, specific implementation details.
3. 'status': Default to 'active'.
4. 'depends_on': A list of IDs this doc relates to (leave empty if unknown).

Files to process:
"""
    
    file_data = {}
    for filepath in files:
        with open(filepath, 'r') as f:
            content = f.read(2000) # Read first 2000 chars for context
            file_data[filepath] = content
            
    prompt += json.dumps(file_data, indent=2)
    
    with open(PROMPT_FILE, 'w') as f:
        f.write(prompt)
    
    print(f"✅ Generated {PROMPT_FILE}")
    print(f"👉 Action: Copy the content of {PROMPT_FILE} into ChatGPT/Claude.")
    print(f"👉 Action: Save the LLM's JSON response to {RESPONSE_FILE} and run this script again with --apply")

def apply_frontmatter(response_file):
    """Reads the JSON response and applies frontmatter to files."""
    try:
        with open(response_file, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: {response_file} not found.")
        return
    except json.JSONDecodeError:
        print(f"❌ Error: {response_file} contains invalid JSON.")
        return

    success_count = 0
    for filepath, meta in data.items():
        if not os.path.exists(filepath):
            print(f"⚠️ Skipping {filepath} (File not found)")
            continue
            
        # Construct YAML
        yaml_block = "---\n"
        yaml_block += f"id: {meta.get('id', 'unknown')}\n"
        yaml_block += f"type: {meta.get('type', 'atom')}\n"
        yaml_block += f"status: {meta.get('status', 'active')}\n"
        deps = json.dumps(meta.get('depends_on', []))
        yaml_block += f"depends_on: {deps}\n"
        yaml_block += "---\n\n"
        
        # Read original content
        with open(filepath, 'r') as f:
            original_content = f.read()
            
        # Write new content
        with open(filepath, 'w') as f:
            f.write(yaml_block + original_content)
            
        print(f"✅ Updated {filepath} (ID: {meta.get('id')})")
        success_count += 1
        
    print(f"\n🎉 Successfully updated {success_count} files!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Ontos Frontmatter Migration Tool')
    parser.add_argument('--dir', type=str, default=DEFAULT_DOCS_DIR, help='Directory to scan for documentation (default: docs)')
    parser.add_argument('--apply', action='store_true', help='Apply changes from migration_response.json')
    
    args = parser.parse_args()

    if args.apply:
        apply_frontmatter(RESPONSE_FILE)
    else:
        files = scan_for_untagged_files(args.dir)
        if not files:
            print(f"No untagged files found in {args.dir}!")
        else:
            print(f"Found {len(files)} untagged files in {args.dir}.")
            generate_prompt(files)
