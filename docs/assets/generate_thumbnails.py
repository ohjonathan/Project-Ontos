from pathlib import Path
import random

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

OUTPUT_DIR = Path(__file__).resolve().parent

def setup_canvas():
    """Sets up a 1280x640 canvas (GitHub Social Preview size)"""
    fig, ax = plt.subplots(figsize=(12.8, 6.4), dpi=100)
    ax.set_xlim(0, 1280)
    ax.set_ylim(0, 640)
    ax.axis('off')
    return fig, ax

def save_plot(filename):
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    output_path = OUTPUT_DIR / filename
    plt.savefig(output_path, dpi=100)
    plt.close()
    print(f"Generated: {output_path}")

# --- DESIGN 1: THE CONTEXT GRAPH (Dark Mode) ---
def create_graph_design():
    fig, ax = setup_canvas()
    
    # Background: Dark Grey/Black
    bg_color = '#0d1117' # GitHub Dark Dimmed
    rect = patches.Rectangle((0, 0), 1280, 640, color=bg_color)
    ax.add_patch(rect)
    
    # Draw abstract graph nodes
    # We create a small cluster on the right side
    nodes = [
        (900, 320), (1050, 450), (1050, 190), 
        (1150, 320), (800, 200), (950, 500)
    ]
    
    # Draw edges
    for i, start in enumerate(nodes):
        for j, end in enumerate(nodes):
            if i < j and random.random() > 0.4: # Random connections
                ax.plot([start[0], end[0]], [start[1], end[1]], 
                        color='#30363d', linewidth=1.5, zorder=1)

    # Draw nodes
    for x, y in nodes:
        circle = patches.Circle((x, y), radius=12, color='#58a6ff', zorder=2) # GitHub Blue
        ax.add_patch(circle)
        # Halo effect
        halo = patches.Circle((x, y), radius=30, color='#58a6ff', alpha=0.1, zorder=1)
        ax.add_patch(halo)

    # Typography (Left aligned)
    ax.text(120, 360, "PROJECT ONTOS", fontsize=48, color='white', 
            fontname='sans-serif', weight='bold',  ha='left')
    
    ax.text(120, 290, "Portable context for the agentic era.", fontsize=24, color='#8b949e', 
            fontname='sans-serif', ha='left')

    # Accent Line
    ax.plot([120, 220], [430, 430], color='#58a6ff', linewidth=3)

    save_plot('ontos_graph.png')

# --- DESIGN 2: THE STACK (Light/Structural) ---
def create_stack_design():
    fig, ax = setup_canvas()
    
    # Background: White/Clean
    bg_color = '#ffffff'
    rect = patches.Rectangle((0, 0), 1280, 640, color=bg_color)
    ax.add_patch(rect)
    
    # The Hierarchy Stack (Visualizing Kernel -> Strategy -> Product)
    stack_x = 800
    stack_width = 300
    base_y = 150
    height = 80
    gap = 20
    
    colors = ['#24292f', '#424a53', '#6e7781', '#afb8c1'] # Gradient of greys
    labels = ["KERNEL", "STRATEGY", "PRODUCT", "ATOM"]
    
    for i, label in enumerate(labels):
        y_pos = base_y + (i * (height + gap))
        # Draw box
        box = patches.FancyBboxPatch((stack_x, y_pos), stack_width, height, 
                                     boxstyle="round,pad=0,rounding_size=10", 
                                     color=colors[3-i]) # Darker at bottom
        ax.add_patch(box)
        
        # Label inside box
        ax.text(stack_x + stack_width/2, y_pos + height/2, label, 
                color='white', fontsize=14, ha='center', va='center', weight='bold')

    # Main Title (Left)
    ax.text(120, 380, "ONTOS", fontsize=80, color='#24292f', 
            fontname='sans-serif', weight='bold')
    
    ax.text(125, 330, "Context is a glass box.", fontsize=26, color='#57606a', 
            fontname='sans-serif')

    save_plot('ontos_stack.png')

# --- DESIGN 3: THE TERMINAL (Dev/Vibe Coding) ---
def create_terminal_design():
    fig, ax = setup_canvas()
    
    # Background: Deep Terminal Black
    bg_color = '#0d1117'
    rect = patches.Rectangle((0, 0), 1280, 640, color=bg_color)
    ax.add_patch(rect)
    
    font_family = 'monospace'
    font_size = 22
    
    # Each line is a list of (text, color) segments
    punctuation = '#6e7681'   # Grey for delimiters
    key_color   = '#79c0ff'   # Blue for YAML keys
    value_color = '#a5d6ff'   # Light blue for string values
    bracket_color = '#d2a8ff' # Purple for brackets
    green       = '#3fb950'   # Green for status line
    white       = '#e6edf3'   # White for plain text
    
    lines = [
        [("---", punctuation)],
        [("id",    key_color), (": ",   punctuation), ("project_ontos",             value_color)],
        [("type",  key_color), (": ",   punctuation), ("AI-context-management",     value_color)],
        [("depends_on", key_color), (": ", punctuation), 
         ("intention, decision, mission", value_color)],
        [("status", key_color), (": ",  punctuation), ("activate",                  value_color)],
        [("---",   punctuation)],
        [],
        [("# context loaded", green)],
    ]
    
    start_y = 530
    line_height = 45
    start_x = 140
    
    for i, segments in enumerate(lines):
        x = start_x
        y = start_y - (i * line_height)
        for text, color in segments:
            t = ax.text(x, y, text, fontsize=font_size, color=color,
                        fontname=font_family, ha='left', va='top')
            # Get rendered width to position next segment
            fig.canvas.draw()
            bbox = t.get_window_extent(renderer=fig.canvas.get_renderer())
            bbox_data = bbox.transformed(ax.transData.inverted())
            x = bbox_data.x1  # advance cursor to end of this segment

    # Tagline
    ax.text(140, start_y - (9 * line_height), "Never explain twice. Own your context.", 
            fontsize=18, color='#8b949e', fontname='sans-serif', fontstyle='italic', ha='left')

    # Brand stamp bottom right
    ax.text(1150, start_y - (9 * line_height), "ONTOS", fontsize=30, color='#30363d', 
            fontname=font_family, ha='right', weight='bold')

    save_plot('ontos_terminal.png')

if __name__ == "__main__":
    random.seed(42)
    create_graph_design()
    create_stack_design()
    create_terminal_design()
