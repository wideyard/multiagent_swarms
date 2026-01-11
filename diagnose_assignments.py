#!/usr/bin/env python3
"""
Diagnose drone-to-goal assignments and visualize trajectories
"""

import sys
import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


def load_goals(json_path: str) -> tuple:
    """Load goals from JSON file"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    goals_ned = np.array(data.get("goals_ned", []))
    return goals_ned


def load_drone_initial_positions(settings_path: str = "settings.json") -> dict:
    """Load drone initial positions from AirSim settings.json"""
    with open(settings_path, 'r', encoding='utf-8') as f:
        settings = json.load(f)
    
    vehicles = settings.get("Vehicles", {})
    positions = {}
    
    for drone_name, config in vehicles.items():
        x = config.get("X", 0)
        y = config.get("Y", 0)
        z = config.get("Z", 0)
        positions[drone_name] = np.array([float(x), float(y), float(z)])
    
    return positions


def plot_assignments(goals_ned: np.ndarray, drone_positions: dict, output_path: str = None):
    """
    Plot goal positions and actual drone initial positions
    Show which drone should fly to which goal based on nearest assignment
    """
    # Get drone names and positions in order
    drone_names = sorted(drone_positions.keys(), key=lambda x: int(x.replace('Drone', '')))
    n_drones = len(drone_names)
    
    # Extract X and Y for drones and goals
    drones_xy = np.array([drone_positions[name][:2] for name in drone_names])
    goals_xy = goals_ned[:, :2]
    
    # Compute distances from each drone to each goal
    print("\n" + "="*80)
    print("DISTANCE MATRIX: DRONE INITIAL POSITIONS TO GOALS")
    print("="*80)
    print(f"{'Drone':<10}", end='')
    for i in range(goals_xy.shape[0]):
        print(f"Goal{i}      ", end='')
    print()
    print("-" * 80)
    
    distances = np.zeros((n_drones, goals_xy.shape[0]))
    for d, name in enumerate(drone_names):
        print(f"{name:<10}", end='')
        for g in range(goals_xy.shape[0]):
            dist = np.linalg.norm(drones_xy[d] - goals_xy[g])
            distances[d, g] = dist
            print(f"{dist:7.3f}  ", end='')
        print()
    
    print("\n" + "="*80)
    print("GREEDY NEAREST UNIQUE ASSIGNMENT")
    print("="*80 + "\n")
    
    # Simulate assignment algorithm
    assigned_goals = set()
    assignments = {}
    
    # Order drones by descending minimal distance (farther drones pick first)
    min_dists = distances.min(axis=1)
    drone_order = np.argsort(-min_dists)
    
    for di in drone_order:
        drone_name = drone_names[di]
        # Find nearest unassigned goal
        sorted_goals = np.argsort(distances[di])
        
        pick = None
        for g in sorted_goals:
            if g not in assigned_goals:
                pick = g
                break
        
        if pick is None:
            pick = sorted_goals[0]
        
        assigned_goals.add(pick)
        assignments[di] = pick
        
        drone_pos = drones_xy[di]
        goal_pos = goals_xy[pick]
        dist = distances[di, pick]
        
        print(f"{drone_name} (pos={drone_pos}) -> Goal{pick} (pos={goal_pos}), distance={dist:.3f}m")
    
    # Create visualization
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Plot drones (initial positions)
    ax.scatter(drones_xy[:, 0], drones_xy[:, 1], s=400, c='blue', marker='s',
              zorder=4, label='Drone Initial Positions', edgecolors='darkblue', linewidth=2)
    for i, name in enumerate(drone_names):
        ax.annotate(name, xy=(drones_xy[i, 0], drones_xy[i, 1]),
                   xytext=(5, 5), textcoords='offset points', fontsize=11, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.4', fc='lightblue', ec='darkblue', linewidth=1.5))
    
    # Plot goals
    ax.scatter(goals_xy[:, 0], goals_xy[:, 1], s=400, c='red', marker='o',
              zorder=3, label='Goal Positions', edgecolors='darkred', linewidth=2)
    for i, goal in enumerate(goals_xy):
        ax.annotate(f'Goal{i}', xy=(goal[0], goal[1]),
                   xytext=(5, -20), textcoords='offset points', fontsize=11, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.4', fc='lightyellow', ec='darkred', linewidth=1.5))
    
    # Draw assignment arrows with colors
    colors = plt.cm.tab10(np.arange(n_drones))
    for d in range(n_drones):
        g = assignments[d]
        ax.arrow(drones_xy[d, 0], drones_xy[d, 1],
                goals_xy[g, 0] - drones_xy[d, 0],
                goals_xy[g, 1] - drones_xy[d, 1],
                head_width=0.2, head_length=0.15, fc=colors[d], ec=colors[d],
                alpha=0.7, linewidth=2.5, zorder=2)
        
        # Add text label on arrow
        mid_x = (drones_xy[d, 0] + goals_xy[g, 0]) / 2
        mid_y = (drones_xy[d, 1] + goals_xy[g, 1]) / 2
        ax.text(mid_x, mid_y, f'{drone_names[d]}->{g}', fontsize=9,
               bbox=dict(boxstyle='round,pad=0.2', fc='white', alpha=0.8))
    
    ax.set_xlabel('X (East) [m]', fontsize=13, fontweight='bold')
    ax.set_ylabel('Y (North) [m]', fontsize=13, fontweight='bold')
    ax.set_title('Actual Drone Initial Positions → Goal Assignments\n(Based on Nearest Unique Assignment)',
                fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_aspect('equal')
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"\nPlot saved to {output_path}")
    
    plt.show()


def main():
    json_path = "outputs/goals_5_20260112_004712.json"
    settings_path = "settings.json"
    
    if len(sys.argv) > 1:
        json_path = sys.argv[1]
    
    print(f"Diagnosing assignments from {json_path}...")
    print(f"Using drone initial positions from {settings_path}...\n")
    
    try:
        goals_ned = load_goals(json_path)
        drone_positions = load_drone_initial_positions(settings_path)
    except Exception as e:
        print(f"✗ Error loading data: {e}")
        sys.exit(1)
    
    print(f"Goal points: {goals_ned.shape[0]}")
    print(f"Goals (X, Y, Z):")
    for i, goal in enumerate(goals_ned):
        print(f"  [Goal {i}] X={goal[0]:7.3f}, Y={goal[1]:7.3f}, Z={goal[2]:7.3f}")
    
    print(f"\nDrone initial positions:")
    for name in sorted(drone_positions.keys(), key=lambda x: int(x.replace('Drone', ''))):
        pos = drone_positions[name]
        print(f"  {name}: X={pos[0]:7.3f}, Y={pos[1]:7.3f}, Z={pos[2]:7.3f}")
    
    # Generate output path
    output_path = json_path.replace('.json', '_assignments.png')
    
    # Plot
    print(f"\nGenerating assignment visualization...")
    plot_assignments(goals_ned, drone_positions, output_path)


if __name__ == "__main__":
    main()
