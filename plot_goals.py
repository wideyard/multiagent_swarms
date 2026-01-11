#!/usr/bin/env python3
"""
Plot goal positions in 2D (XY plane)
"""

import sys
import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


def load_goals(json_path: str) -> tuple:
    """
    Load goals from JSON file
    
    Args:
        json_path: Path to goals JSON file
        
    Returns:
        Tuple of (description, goals_array)
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    description = data.get("description", "Unknown shape")
    goals_ned = np.array(data.get("goals_ned", []))
    
    return description, goals_ned


def plot_goals(goals_ned: np.ndarray, description: str, output_path: str = None):
    """
    Plot goal positions in 2D (XY plane)
    
    Args:
        goals_ned: Array of shape (N, 3) with NED coordinates
        description: Description of the shape
        output_path: Optional path to save the plot
    """
    # Extract X and Y coordinates (ignore Z)
    x = goals_ned[:, 0]
    y = goals_ned[:, 1]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Plot points
    ax.scatter(x, y, s=200, c='red', marker='o', zorder=3, label='Drone Goals')
    
    # Plot line connecting points (to show shape)
    # Close the loop by adding first point at the end
    x_loop = np.append(x, x[0])
    y_loop = np.append(y, y[0])
    ax.plot(x_loop, y_loop, 'b--', linewidth=2, alpha=0.5, label='Shape outline')
    
    # Annotate points with index
    for i, (xi, yi) in enumerate(zip(x, y)):
        ax.annotate(
            f'Drone{i+1}\n({xi:.2f}, {yi:.2f})',
            xy=(xi, yi),
            xytext=(10, 10),
            textcoords='offset points',
            fontsize=10,
            bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.7),
            arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0')
        )
    
    # Set labels and title
    ax.set_xlabel('X (East)', fontsize=12)
    ax.set_ylabel('Y (North)', fontsize=12)
    ax.set_title(f'Drone Goal Positions - {description}', fontsize=14, fontweight='bold')
    
    # Add grid
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')
    
    # Add legend
    ax.legend(loc='upper right', fontsize=10)
    
    # Calculate and display statistics
    center_x = np.mean(x)
    center_y = np.mean(y)
    distances = np.linalg.norm(goals_ned[:, :2] - np.array([center_x, center_y]), axis=1)
    
    stats_text = f"Center: ({center_x:.2f}, {center_y:.2f})\n"
    stats_text += f"Radius range: [{distances.min():.2f}, {distances.max():.2f}]\n"
    stats_text += f"Num points: {len(x)}"
    
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    # Adjust layout
    plt.tight_layout()
    
    # Save if output path provided
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Plot saved to {output_path}")
    
    # Show plot
    plt.show()


def main():
    # Default path
    json_path = "outputs/goals_5_20260112_004712.json"
    
    # Check command line args
    if len(sys.argv) > 1:
        json_path = sys.argv[1]
    
    print(f"Loading goals from {json_path}...")
    
    try:
        description, goals_ned = load_goals(json_path)
    except Exception as e:
        print(f"Error loading goals: {e}")
        sys.exit(1)
    
    print(f"Description: {description}")
    print(f"Goals shape: {goals_ned.shape}")
    print(f"Goals (X, Y, Z):\n{goals_ned}")
    
    # Generate output path
    output_path = json_path.replace('.json', '_plot.png')
    
    # Plot
    print(f"\nGenerating plot...")
    plot_goals(goals_ned, description, output_path)


if __name__ == "__main__":
    main()
