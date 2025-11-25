import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
import matplotlib.patches as patches

# Create figure
fig, ax = plt.subplots(1, 1, figsize=(16, 12))
ax.set_xlim(0, 16)
ax.set_ylim(0, 12)
ax.axis('off')

# Define colors
process_color = '#4A90E2'
data_store_color = '#50C878'
entity_color = '#FF6B6B'
flow_color = '#2C3E50'

# External Entities (Rectangles with shadow)
entities = [
    ('User', 1, 9),
    ('Admin', 15, 9),
]

# Processes (Rounded rectangles)
processes = [
    ('Login\nProcess', 3, 9),
    ('Signup\nProcess', 3, 6),
    ('Prediction\nProcess', 8, 9),
    ('Admin\nDashboard', 12, 9),
    ('ML Model\nPrediction', 8, 6),
]

# Data Stores (Open rectangles)
data_stores = [
    ('Users\nDatabase', 3, 3),
    ('Sessions\nDatabase', 6, 3),
    ('Predictions\nDatabase', 9, 3),
]

# Draw External Entities
for name, x, y in entities:
    rect = FancyBboxPatch((x-0.8, y-0.6), 1.6, 1.2,
                         boxstyle="round,pad=0.1", 
                         edgecolor=entity_color, 
                         facecolor='white',
                         linewidth=2)
    ax.add_patch(rect)
    ax.text(x, y, name, ha='center', va='center', 
            fontsize=10, fontweight='bold', color=entity_color)

# Draw Processes
for name, x, y in processes:
    rect = FancyBboxPatch((x-1, y-0.7), 2, 1.4,
                         boxstyle="round,pad=0.1", 
                         edgecolor=process_color, 
                         facecolor=process_color,
                         linewidth=2,
                         alpha=0.3)
    ax.add_patch(rect)
    # Process number circle
    circle = Circle((x-1.2, y+0.5), 0.25, 
                   color=process_color, 
                   fill=True, 
                   edgecolor='white',
                   linewidth=2)
    ax.add_patch(circle)
    ax.text(x-1.2, y+0.5, str(processes.index((name, x, y)) + 1), 
           ha='center', va='center', 
           fontsize=8, fontweight='bold', color='white')
    ax.text(x, y, name, ha='center', va='center', 
           fontsize=9, fontweight='bold', color=process_color)

# Draw Data Stores
for name, x, y in data_stores:
    # Open rectangle (two parallel lines)
    left_line = plt.Line2D([x-1, x-1], [y-0.6, y+0.6], 
                          color=data_store_color, linewidth=3)
    right_line = plt.Line2D([x+1, x+1], [y-0.6, y+0.6], 
                           color=data_store_color, linewidth=3)
    top_line = plt.Line2D([x-1, x+1], [y+0.6, y+0.6], 
                          color=data_store_color, linewidth=2)
    bottom_line = plt.Line2D([x-1, x+1], [y-0.6, y-0.6], 
                            color=data_store_color, linewidth=2)
    ax.add_line(left_line)
    ax.add_line(right_line)
    ax.add_line(top_line)
    ax.add_line(bottom_line)
    ax.text(x, y, name, ha='center', va='center', 
           fontsize=9, fontweight='bold', color=data_store_color)

# Draw Data Flows with labels
flows = [
    # User flows
    ((1, 9), (2.2, 9), 'Login\nCredentials', '→'),
    ((3.8, 9), (7.2, 9), 'Validated\nUser', '→'),
    ((1, 9), (2.2, 6), 'Signup\nData', '→'),
    ((3.8, 6), (3, 3.6), 'User\nData', '→'),
    ((3, 2.4), (3.8, 6), 'User\nInfo', '→'),
    
    # Prediction flows
    ((8.8, 9), (8.8, 6.7), 'Input\nParameters', '→'),
    ((8.8, 5.3), (8.8, 3.6), 'Save\nPrediction', '→'),
    ((9, 2.4), (8.8, 5.3), 'Historical\nData', '→'),
    ((7.2, 6), (8.8, 6), 'ML\nPrediction', '→'),
    
    # Admin flows
    ((15, 9), (13.2, 9), 'Admin\nRequest', '→'),
    ((11.2, 9), (10, 3.6), 'Query\nData', '→'),
    ((9, 2.4), (11.2, 9), 'Reports\n& Stats', '→'),
    ((6, 2.4), (11.2, 9), 'Session\nData', '→'),
    
    # Session flows
    ((3.8, 9), (5.2, 3.6), 'Login\nSession', '→'),
    ((6, 2.4), (3.8, 9), 'Session\nStatus', '→'),
]

# Draw arrows
for (start, end, label, direction) in flows:
    x1, y1 = start
    x2, y2 = end
    
    # Calculate arrow position
    if direction == '→':
        # Adjust start/end points to avoid overlapping with shapes
        if x1 < x2:  # Right arrow
            x1 += 0.8
            x2 -= 0.8
        elif x1 > x2:  # Left arrow
            x1 -= 0.8
            x2 += 0.8
        if y1 < y2:  # Down arrow
            y1 += 0.6
            y2 -= 0.6
        elif y1 > y2:  # Up arrow
            y1 -= 0.6
            y2 += 0.6
    
    arrow = FancyArrowPatch((x1, y1), (x2, y2),
                           arrowstyle='->', 
                           mutation_scale=20,
                           color=flow_color,
                           linewidth=1.5,
                           alpha=0.7)
    ax.add_patch(arrow)
    
    # Add label
    mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
    # Offset label position
    if abs(x2 - x1) > abs(y2 - y1):  # Horizontal flow
        label_y = mid_y + 0.3
    else:  # Vertical flow
        label_x = mid_x + 0.3
        label_y = mid_y
    
    if abs(x2 - x1) > abs(y2 - y1):  # Horizontal
        ax.text(mid_x, label_y, label, ha='center', va='bottom',
               fontsize=7, color=flow_color, 
               bbox=dict(boxstyle='round,pad=0.3', 
                        facecolor='white', 
                        edgecolor=flow_color,
                        alpha=0.8))
    else:  # Vertical
        ax.text(mid_x + 0.3, mid_y, label, ha='left', va='center',
               fontsize=7, color=flow_color,
               bbox=dict(boxstyle='round,pad=0.3', 
                        facecolor='white', 
                        edgecolor=flow_color,
                        alpha=0.8))

# Add title
ax.text(8, 11.5, 'Data Flow Diagram (DFD) - Crop Production Prediction System', 
       ha='center', va='center', 
       fontsize=16, fontweight='bold', color='#2C3E50')

# Add legend
legend_elements = [
    mpatches.Patch(color=entity_color, label='External Entity'),
    mpatches.Patch(color=process_color, label='Process', alpha=0.3),
    mpatches.Patch(color=data_store_color, label='Data Store'),
    mpatches.Patch(color=flow_color, label='Data Flow', alpha=0.7)
]
ax.legend(handles=legend_elements, loc='lower left', fontsize=9, framealpha=0.9)

# Add level indicator
ax.text(0.5, 0.5, 'Level 0 - Context Diagram', 
       ha='left', va='bottom', 
       fontsize=10, style='italic', color='gray')

plt.tight_layout()
plt.savefig('static/dfd_diagram.png', dpi=300, bbox_inches='tight', facecolor='white')
print("DFD diagram saved to static/dfd_diagram.png")
plt.close()

