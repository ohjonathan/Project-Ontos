import networkx as nx
import pyperclip
import os

def retrieve_context(query, G):
    """
    Retrieves context based on the query.
    Returns a formatted string of the context.
    """
    # 1. Find Active Task Node (Keyword Match)
    active_nodes = []
    query_terms = query.lower().split()
    
    for node, data in G.nodes(data=True):
        if node == "ROOT": continue
        
        # Check ID and content (if we had it indexed, for now just ID/filename)
        node_id = str(node).lower()
        if any(term in node_id for term in query_terms):
            active_nodes.append(node)
            
    if not active_nodes:
        return "No relevant context found for query."

    # 2. Pruning Algorithm
    # Layer 1: Kernel (All Kernel nodes)
    kernel_nodes = [n for n, d in G.nodes(data=True) if d.get('type') == 'kernel']
    
    # Layer 2: Focus (The Active Nodes)
    focus_nodes = active_nodes
    
    # Layer 3: Graph (Parents of Active Nodes)
    graph_nodes = set()
    for node in active_nodes:
        # Get predecessors (parents)
        parents = list(G.predecessors(node))
        for p in parents:
            if p != "ROOT":
                graph_nodes.add(p)
                
    # Assemble Context
    context_parts = []
    
    # Helper to get content
    def get_content(node, full=True):
        filepath = G.nodes[node].get('filepath')
        if not filepath: return ""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                # Strip frontmatter for clean context
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        content = parts[2].strip()
                
                if full:
                    return f"--- DOCUMENT: {node} ---\n{content}\n"
                else:
                    # First 2 paragraphs for Graph Layer
                    paragraphs = content.split("\n\n")
                    snippet = "\n\n".join(paragraphs[:2])
                    return f"--- CONTEXT: {node} ---\n{snippet}\n...\n"
        except:
            return ""

    # Add Kernel (Full)
    if kernel_nodes:
        context_parts.append("=== KERNEL CONTEXT ===")
        for node in kernel_nodes:
            context_parts.append(get_content(node, full=True))
            
    # Add Graph (Snippet)
    if graph_nodes:
        context_parts.append("=== STRATEGIC CONTEXT ===")
        for node in graph_nodes:
            # Don't duplicate if it's also a focus node
            if node not in focus_nodes:
                context_parts.append(get_content(node, full=False))
                
    # Add Focus (Full)
    context_parts.append("=== ACTIVE TASK CONTEXT ===")
    for node in focus_nodes:
        context_parts.append(get_content(node, full=True))
        
    return "\n".join(context_parts)

def copy_to_clipboard(text):
    try:
        pyperclip.copy(text)
        return True
    except Exception as e:
        print(f"Clipboard error: {e}")
        return False
