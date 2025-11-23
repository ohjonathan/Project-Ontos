import os
import networkx as nx
import time

def check_drift(G):
    """
    Checks for drift (Parent modified after Child).
    Returns a list of issues.
    """
    issues = []
    
    for node in G.nodes():
        if node == "ROOT": continue
        
        child_path = G.nodes[node].get('filepath')
        if not child_path: continue
        
        child_mtime = os.path.getmtime(child_path)
        
        # Check all parents
        parents = list(G.predecessors(node))
        for parent in parents:
            if parent == "ROOT": continue
            
            parent_path = G.nodes[parent].get('filepath')
            if not parent_path: continue
            
            parent_mtime = os.path.getmtime(parent_path)
            
            # If Parent is newer than Child -> Drift
            if parent_mtime > child_mtime:
                diff_seconds = parent_mtime - child_mtime
                diff_hours = diff_seconds / 3600
                issues.append({
                    "child": node,
                    "parent": parent,
                    "diff_hours": diff_hours
                })
                
    return issues
