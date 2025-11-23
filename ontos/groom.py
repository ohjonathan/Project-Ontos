def check_file_size(file_path, limit=1000):
    """
    Checks if a file exceeds the line limit.
    Returns a warning message if it does, None otherwise.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if len(lines) > limit:
                return f"File has {len(lines)} lines (limit: {limit}). Consider splitting."
    except Exception as e:
        return f"Error reading file: {str(e)}"
    return None

def check_headers(file_path):
    """
    Checks if a file has at least one H1 (# ) or H2 (## ) header.
    Returns a warning message if missing, None otherwise.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Simple check for headers at start of line
            has_h1 = False
            has_h2 = False
            
            for line in content.splitlines():
                if line.strip().startswith("# "):
                    has_h1 = True
                if line.strip().startswith("## "):
                    has_h2 = True
            
            if not (has_h1 or has_h2):
                return "Missing standard headers (H1 or H2). Ontology builder may fail to parse."
    except Exception as e:
        return f"Error reading file: {str(e)}"
    return None
