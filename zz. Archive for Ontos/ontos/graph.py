import os
import yaml
import networkx as nx

def build_graph(directory):
    """Builds a NetworkX graph from the directory."""
    G = nx.DiGraph()
    
    # 1. Add nodes
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        # Parse frontmatter manually or use safe_load_all
                        content = f.read()
                        if content.startswith("---"):
                            parts = content.split("---", 2)
                            if len(parts) >= 3:
                                metadata = yaml.safe_load(parts[1])
                                if metadata:
                                    node_id = metadata.get('id', os.path.basename(file))
                                    G.add_node(node_id, **metadata, filepath=file_path)
                except Exception as e:
                    print(f"Error parsing {file}: {e}")

    # 2. Add edges (Heuristic for MVP: Kernel -> Strategy -> Product -> Atom)
    # In a real version, we'd parse 'depends_on' from frontmatter or links.
    # For MVP, we'll just link based on types if no explicit links exist.
    
    nodes_by_type = {
        "kernel": [],
        "strategy": [],
        "product": [],
        "atom": []
    }
    
    for node, data in G.nodes(data=True):
        node_type = data.get('type', 'atom')
        if node_type in nodes_by_type:
            nodes_by_type[node_type].append(node)
            
    # Simple hierarchy: Kernel -> Strategy -> Product -> Atom
    # Connect every kernel to every strategy, etc. (This is a simplification for MVP visualization)
    # A better approach for MVP might be just to show them grouped by type in the tree
    # or try to infer parentage from directory structure if nested.
    # For now, let's create a "Root" node and connect Kernels to it.
    
    G.add_node("ROOT", type="root")
    
    for kernel in nodes_by_type["kernel"]:
        G.add_edge("ROOT", kernel)
        
    for strategy in nodes_by_type["strategy"]:
        # Connect to first kernel if exists, else ROOT
        parents = nodes_by_type["kernel"]
        if parents:
            for p in parents: G.add_edge(p, strategy)
        else:
            G.add_edge("ROOT", strategy)
            
    for product in nodes_by_type["product"]:
        parents = nodes_by_type["strategy"]
        if parents:
             for p in parents: G.add_edge(p, product)
        else:
            G.add_edge("ROOT", product)
            
    for atom in nodes_by_type["atom"]:
        parents = nodes_by_type["product"]
        if parents:
             for p in parents: G.add_edge(p, atom)
        else:
            G.add_edge("ROOT", atom)
            
    return G

def visualize_graph(G):
    """Generates an ASCII tree from the graph."""
    # Since it's a DAG, we can print it recursively or use networkx's bfs_tree
    # But we want a pretty print.
    
    def print_tree(node, prefix="", is_last=True):
        if node != "ROOT":
            connector = "└── " if is_last else "├── "
            print(f"{prefix}{connector}{node} ({G.nodes[node].get('type', 'unknown')})")
            prefix += "    " if is_last else "│   "
        
        children = list(G.successors(node))
        for i, child in enumerate(children):
            print_tree(child, prefix, i == len(children) - 1)

    print("Ontology Graph:")
    print_tree("ROOT")
