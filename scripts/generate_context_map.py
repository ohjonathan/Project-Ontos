import os
import sys
import yaml
import datetime
import argparse

DEFAULT_DOCS_DIR = 'docs'
OUTPUT_FILE = 'CONTEXT_MAP.md'

def parse_frontmatter(filepath):
    """Parses YAML frontmatter from a markdown file."""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    if content.startswith('---'):
        try:
            # Split by '---' and take the second element (the frontmatter)
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])
                return frontmatter
        except yaml.YAMLError as e:
            print(f"Error parsing YAML in {filepath}: {e}")
    return None

def scan_docs(root_dir):
    """Scans the docs directory for markdown files and parses their metadata."""
    files_data = {}
    for subdir, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.md'):
                filepath = os.path.join(subdir, file)
                frontmatter = parse_frontmatter(filepath)
                if frontmatter and 'id' in frontmatter:
                    files_data[frontmatter['id']] = {
                        'filepath': filepath,
                        'filename': file,
                        'type': frontmatter.get('type', 'unknown'),
                        'depends_on': frontmatter.get('depends_on', []),
                        'status': frontmatter.get('status', 'unknown')
                    }
    return files_data

def generate_tree(files_data):
    """Generates a hierarchy tree string."""
    tree = []
    
    # Group by type
    by_type = {'kernel': [], 'strategy': [], 'product': [], 'atom': [], 'unknown': []}
    for doc_id, data in files_data.items():
        doc_type = data['type']
        if isinstance(doc_type, list):
            doc_type = doc_type[0] if doc_type else 'unknown'
            # Clean up if it looks like "[option1 | option2]"
            if '|' in str(doc_type): 
                 doc_type = 'unknown'

        if doc_type in by_type:
            by_type[doc_type].append(doc_id)
        else:
            by_type['unknown'].append(doc_id)
            
    order = ['kernel', 'strategy', 'product', 'atom', 'unknown']
    
    for doc_type in order:
        if by_type[doc_type]:
            tree.append(f"### {doc_type.upper()}")
            for doc_id in by_type[doc_type]:
                data = files_data[doc_id]
                deps = ", ".join(data['depends_on']) if data['depends_on'] else "None"
                tree.append(f"- **{doc_id}** ({data['filename']})")
                tree.append(f"  - Status: {data['status']}")
                tree.append(f"  - Depends On: {deps}")
            tree.append("")
            
    return "\n".join(tree)

def validate_dependencies(files_data):
    """Checks for broken links, cycles, orphans, depth, and type violations."""
    issues = []
    existing_ids = set(files_data.keys())
    
    # 1. Build Adjacency List & Reverse Graph
    adj = {doc_id: [] for doc_id in existing_ids}
    rev_adj = {doc_id: [] for doc_id in existing_ids}
    
    for doc_id, data in files_data.items():
        deps = data['depends_on']
        if deps:
            # Handle case where user wrote string instead of list
            if isinstance(deps, str):
                deps = [deps]
            for dep in deps:
                if dep not in existing_ids:
                    issues.append(f"- [BROKEN LINK] **{doc_id}** links to missing ID: `{dep}`")
                else:
                    adj[doc_id].append(dep)
                    rev_adj[dep].append(doc_id)

    # 2. Cycle Detection (DFS)
    visited = set()
    recursion_stack = set()
    
    def detect_cycle(node, path):
        visited.add(node)
        recursion_stack.add(node)
        path.append(node)
        
        for neighbor in adj[node]:
            if neighbor not in visited:
                if detect_cycle(neighbor, path):
                    return True
            elif neighbor in recursion_stack:
                cycle_path = " -> ".join(path[path.index(neighbor):] + [neighbor])
                issues.append(f"- [CYCLE] Circular dependency detected: {cycle_path}")
                return True
        
        recursion_stack.remove(node)
        path.pop()
        return False

    for doc_id in existing_ids:
        if doc_id not in visited:
            detect_cycle(doc_id, [])

    # 3. Orphan Detection
    for doc_id in existing_ids:
        if not rev_adj[doc_id]:
            doc_type = files_data[doc_id]['type']
            filename = files_data[doc_id]['filename']
            
            # Skip expected root types and templates
            if doc_type in ['product', 'strategy', 'kernel']:
                continue
            if 'template' in filename.lower():
                continue
                
            issues.append(f"- [ORPHAN] **{doc_id}** is not depended on by any other document.")

    # 4. Dependency Depth
    # Calculate max depth for each node
    memo_depth = {}
    def get_depth(node):
        if node in memo_depth: return memo_depth[node]
        if not adj[node]: return 0
        
        # Avoid infinite recursion in cycles by temporarily setting a value
        # (Cycles are already reported, so we just need to terminate)
        memo_depth[node] = 0 
        
        max_d = 0
        for neighbor in adj[node]:
            max_d = max(max_d, get_depth(neighbor))
        
        memo_depth[node] = 1 + max_d
        return memo_depth[node]

    for doc_id in existing_ids:
        depth = get_depth(doc_id)
        if depth > 5:
            issues.append(f"- [DEPTH] **{doc_id}** has a dependency depth of {depth} (max recommended: 5).")

    # 5. Type Hierarchy Violations
    # Hierarchy: Kernel (0) < Strategy (1) < Product (2) < Atom (3)
    type_rank = {'kernel': 0, 'strategy': 1, 'product': 2, 'atom': 3, 'unknown': 4}
    
    for doc_id, data in files_data.items():
        my_type = data['type']
        if isinstance(my_type, list): my_type = my_type[0]
        my_rank = type_rank.get(my_type, 4)
        
        for dep in data['depends_on']:
            # Handle case where user wrote string instead of list
            if isinstance(dep, str) and dep not in files_data: 
                 # This check is slightly redundant with loop above but safe. 
                 # Actually, data['depends_on'] is the list. 
                 # We need to handle if data['depends_on'] is a string before iterating?
                 # Wait, the previous fix handles 'deps' variable. 
                 # Here we iterate data['depends_on'] directly.
                 pass

        # Let's fix the iteration logic properly.
        deps = data['depends_on']
        if isinstance(deps, str):
            deps = [deps]
            
        for dep in deps:
            if dep in files_data:
                dep_type = files_data[dep]['type']
                if isinstance(dep_type, list): dep_type = dep_type[0]
                dep_rank = type_rank.get(dep_type, 4)
                
                # Rule: Depend on things 'lower' or 'equal' in the stack.
                # Violation: If I (lower) depend on something (higher).
                # Example: Kernel (0) depends on Atom (3). 0 < 3. Violation.
                # Example: Atom (3) depends on Kernel (0). 3 > 0. False. OK.
                if my_rank < dep_rank:
                     issues.append(f"- [ARCHITECTURE] **{doc_id}** ({my_type}) depends on higher-layer **{dep}** ({dep_type}).")

    return issues

def generate_context_map(target_dir):
    """Main function to generate the CONTEXT_MAP.md file."""
    print(f"Scanning {target_dir}...")
    files_data = scan_docs(target_dir)
    
    print("Generating tree...")
    tree_view = generate_tree(files_data)
    
    print("Validating dependencies...")
    issues = validate_dependencies(files_data)
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    content = f"""# Ontos Context Map
Generated on: {timestamp}
Scanned Directory: `{target_dir}`

## 1. Hierarchy Tree
{tree_view}

## 2. Dependency Audit
{'No issues found.' if not issues else chr(10).join(issues)}

## 3. Index
| ID | Filename | Type |
|---|---|---|
"""
    
    for doc_id, data in files_data.items():
        content += f"| {doc_id} | [{data['filename']}]({data['filepath']}) | {data['type']} |\n"
        
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print(f"Successfully generated {OUTPUT_FILE}")
    print(f"📊 Scanned {len(files_data)} documents, found {len(issues)} issues.")

    # Return issue count for strict mode
    return len(issues)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate Ontos Context Map')
    parser.add_argument('--dir', type=str, default=DEFAULT_DOCS_DIR, help='Directory to scan (default: docs)')
    parser.add_argument('--strict', action='store_true', help='Exit with error code 1 if issues found')
    args = parser.parse_args()
    
    issue_count = generate_context_map(args.dir)
    
    if args.strict and issue_count > 0:
        print(f"\n❌ Strict mode: {issue_count} issues detected. Exiting with error.")
        sys.exit(1)
```
