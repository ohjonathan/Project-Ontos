import os
import yaml
import click

KEYWORDS = {
    "kernel": ["mission", "vision", "value", "principle", "manifesto"],
    "strategy": ["strategy", "persona", "stack", "market", "business", "plan"],
    "product": ["roadmap", "journey", "schema", "design", "prd", "requirement"],
    "atom": ["feature", "spec", "component", "task", "guide", "manual"]
}

def scan_directory(directory):
    """Scans directory for .md files."""
    md_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".md"):
                md_files.append(os.path.join(root, file))
    return md_files

def tag_file(file_path):
    """Heuristically determines the type of the file based on filename and content."""
    filename = os.path.basename(file_path).lower()
    
    # Check filename first
    for type_name, keywords in KEYWORDS.items():
        for keyword in keywords:
            if keyword in filename:
                return type_name
    
    # Fallback: Check content (first 500 chars)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read(500).lower()
            for type_name, keywords in KEYWORDS.items():
                for keyword in keywords:
                    if keyword in content:
                        return type_name
    except:
        pass
        
    return "atom" # Default to atom

def update_frontmatter(file_path, dry_run=False):
    """Injects YAML frontmatter if missing."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if frontmatter already exists
        if content.startswith("---"):
            # Simple check, could be more robust
            return False, "Frontmatter already exists"
            
        file_type = tag_file(file_path)
        filename = os.path.basename(file_path)
        
        metadata = {
            "type": file_type,
            "id": filename.replace(" ", "_").replace(".md", "").lower(),
            "status": "draft"
        }
        
        frontmatter = "---\n" + yaml.dump(metadata, default_flow_style=False) + "---\n\n"
        new_content = frontmatter + content
        
        if not dry_run:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
        
        return True, f"Added frontmatter (type: {file_type})"
        
    except Exception as e:
        return False, f"Error: {str(e)}"
