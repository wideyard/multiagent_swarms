#!/usr/bin/env python3
"""
Fly drones to goals loaded from a JSON file
Usage: python fly_to_goals.py <path_to_goals_json>
"""

import sys
import json
import os
import time
import numpy as np
from pathlib import Path

# Add repo root to path
repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root))

from src.integrated_controller import LLMAirSimSwarmController


def load_goals(json_path: str) -> dict:
    """
    Load goals from JSON file
    
    Args:
        json_path: Path to goals JSON file
        
    Returns:
        Dictionary with goals data
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


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


def assign_nearest_unique(drone_positions: dict, goals_ned: np.ndarray) -> dict:
    """
    Assign each drone to the nearest unique goal position.
    
    Args:
        drone_positions: Dict mapping drone_name -> position (3,)
        goals_ned: Array of shape (N, 3) with goal positions
        
    Returns:
        Dict mapping drone_name -> goal_index
    """
    drone_names = sorted(drone_positions.keys(), key=lambda x: int(x.replace('Drone', '')))
    n_drones = len(drone_names)
    n_goals = goals_ned.shape[0]
    
    # Get drone positions as array
    drone_pos_array = np.array([drone_positions[name] for name in drone_names])
    
    # Compute distance matrix (drones x goals) using XY plane distances
    dists = np.linalg.norm(drone_pos_array[:, None, :2] - goals_ned[None, :, :2], axis=2)
    
    assignments = {}
    assigned_goals = set()
    
    # Order drones by descending minimal distance (farther drones pick first)
    min_dists = dists.min(axis=1)
    drone_order = np.argsort(-min_dists)
    
    allow_duplicates = n_goals < n_drones
    if allow_duplicates:
        print(f"⚠ Warning: fewer goal points ({n_goals}) than drones ({n_drones}); some will share targets")
    
    for di in drone_order:
        drone_name = drone_names[di]
        # Find nearest unassigned goal
        choices = list(range(n_goals))
        sorted_goals = sorted(choices, key=lambda g: float(dists[di, g]))
        
        pick = None
        if allow_duplicates:
            pick = sorted_goals[0]
        else:
            for g in sorted_goals:
                if g not in assigned_goals:
                    pick = g
                    break
            if pick is None:
                pick = sorted_goals[0]
        
        assigned_goals.add(pick)
        assignments[drone_name] = int(pick)
    
    return assignments


def main():
    # Parse arguments
    if len(sys.argv) < 2:
        print("Usage: python fly_to_goals.py <path_to_goals_json>")
        print("Example: python fly_to_goals.py outputs/goals_5_20260112_004712.json")
        sys.exit(1)
    
    json_path = sys.argv[1]
    
    # Verify file exists
    if not os.path.exists(json_path):
        print(f"Error: File not found: {json_path}")
        sys.exit(1)
    
    # Load goals
    print(f"Loading goals from {json_path}...")
    try:
        goals_data = load_goals(json_path)
    except Exception as e:
        print(f"Error loading goals: {e}")
        sys.exit(1)
    
    # Load drone initial positions
    print(f"Loading drone initial positions from settings.json...")
    try:
        drone_positions = load_drone_initial_positions("settings.json")
    except Exception as e:
        print(f"Error loading settings: {e}")
        sys.exit(1)
    
    # Extract info
    description = goals_data.get("description", "Unknown shape")
    goals_ned = np.array(goals_data.get("goals_ned", []))
    scale = goals_data.get("scale", 1.0)
    altitude = goals_data.get("flight_altitude", 5.0)
    
    # Force 10 drones
    num_points = 5
    
    # If fewer than 10 goal points, repeat them cyclically
    if len(goals_ned) < num_points:
        repeat_count = (num_points // len(goals_ned)) + 1
        goals_ned = np.vstack([goals_ned] * repeat_count)[:num_points]
    elif len(goals_ned) > num_points:
        goals_ned = goals_ned[:num_points]
    
    print(f"Description: {description}")
    print(f"Number of drones: {num_points}")
    print(f"Scale: {scale}x, Altitude: {altitude}m")
    print(f"Goals shape: {goals_ned.shape}")
    print(f"Goals NED coordinates:\n{goals_ned}")
    
    # Create drone names
    drone_names = [f"Drone{i+1}" for i in range(num_points)]
    print(f"Drone names: {drone_names}")
    
    # Initialize controller
    print("\nInitializing AirSim controller...")
    try:
        controller = LLMAirSimSwarmController(
            drone_names=drone_names,
            airsim_ip="127.0.0.1",
            verbose=True
        )
    except Exception as e:
        print(f"Error initializing controller: {e}")
        sys.exit(1)
    
    # Set goal positions directly (bypass shape generation)
    print("\nSetting goal positions...")
    controller.goal_positions = goals_ned
    
    # Run mission: ALL DRONES IN AIR WITH FORMATION (APF control)
    print("\n" + "="*60)
    print("Starting formation flight mission (all drones simultaneous)...")
    print("="*60 + "\n")
    
    try:
        drone_list = list(controller.swarm.drones.keys())
        n_drones = len(drone_list)
        
        # Step 1: Arm all drones
        print("Step 1: Arming all drones...")
        controller.swarm.arm_all()
        print("✓ All drones armed")
        time.sleep(1.0)
        
        # Step 2: Takeoff all drones simultaneously
        print("\nStep 2: Taking off all drones (simultaneous)...")
        controller.swarm.takeoff_all(5.0)
        print("✓ All drones launched to altitude")
        time.sleep(2.0)
        
        # Step 3: APF-based formation flight to goals
        print("\nStep 3: Computing optimal goal assignments (based on initial positions)...")
        
        # Compute assignments using nearest unique algorithm
        assignments = assign_nearest_unique(drone_positions, goals_ned)
        
        # Build ordered assigned goals array matching swarm drone order
        assigned_goals = np.zeros((n_drones, 3), dtype=float)
        
        print(f"Task assignments:")
        for i, drone_name in enumerate(drone_list):
            goal_idx = assignments.get(drone_name, i)
            assigned_goals[i] = goals_ned[int(goal_idx)]
            goal = assigned_goals[i]
            init_pos = drone_positions.get(drone_name, [0, 0, 0])
            dist = np.linalg.norm(goal[:2] - init_pos[:2])
            print(f"  {drone_name} (init={tuple(init_pos[:2].round(2))}) -> Goal[{goal_idx}] (pos={tuple(goal[:2].round(2))}) distance={dist:.2f}m")
        
        # Configure APF controller
        controller.apf_controller.goals = assigned_goals
        controller.apf_controller.min_dist = 2.0  # 2m separation
        controller.apf_controller.max_vel = 2.0
        
        # Control loop
        arrival_thresh = 0.5  # meters
        dt = 0.5
        max_time = 120.0
        t_start = time.time()
        
        iteration = 0
        while True:
            iteration += 1
            
            # Update current positions
            current_positions = controller.swarm.get_positions()
            if current_positions.shape[0] != n_drones:
                padded = np.zeros((n_drones, 3), dtype=float)
                padded[: current_positions.shape[0], :] = current_positions
                current_positions = padded
            
            # Compute APF control
            controller.apf_controller.goals = assigned_goals
            vels = controller.apf_controller.get_control(current_positions)
            
            # Clip velocities
            speeds = np.linalg.norm(vels, axis=1)
            too_fast = speeds > controller.apf_controller.max_vel
            if np.any(too_fast):
                vels[too_fast] = (
                    vels[too_fast] / speeds[too_fast, None] * controller.apf_controller.max_vel
                )
            
            # Send velocity commands
            controller.swarm.set_velocities(vels, duration=dt)
            
            # Check arrival
            dists = np.linalg.norm(current_positions - assigned_goals, axis=1)
            arrived = np.sum(dists <= arrival_thresh)
            
            if iteration % 10 == 0:  # Log every 5 seconds
                print(f"  Iter {iteration}: {arrived}/{n_drones} drones within range, avg dist: {dists.mean():.2f}m")
                # Detailed position vs goal tracking
                for i, drone_name in enumerate(drone_list):
                    pos = current_positions[i]
                    goal = assigned_goals[i]
                    dist_to_goal = dists[i]
                    print(f"    {drone_name}: pos=({pos[0]:6.2f},{pos[1]:6.2f}) -> goal=({goal[0]:6.2f},{goal[1]:6.2f}) dist={dist_to_goal:.2f}m")
            
            if np.all(dists <= arrival_thresh):
                print(f"✓ All drones within arrival threshold!")
                break
            
            if time.time() - t_start > max_time:
                print(f"⚠ Timeout: moving to finalization after {max_time}s")
                break
            
            time.sleep(dt)
        
        # Step 4: Hovering at target points
        print("\nStep 4: All drones hovering at target positions...")
        print("Press Enter to begin landing sequence...")
        try:
            input()
        except (EOFError, KeyboardInterrupt):
            print("Starting landing sequence...")
        
        # Step 5: Final positioning
        print("\nStep 5: Final positioning...")
        controller.swarm.set_velocities(np.zeros_like(assigned_goals), duration=0.5)
        time.sleep(1.0)
        
        # Step 6: Land all drones simultaneously
        print("\nStep 6: Landing all drones (simultaneous)...")
        controller.swarm.land_all()
        print("✓ All drones landed")
        time.sleep(1.0)
        
        # Step 7: Disarm all
        print("\nStep 7: Disarming all drones...")
        controller.swarm.disarm_all()
        print("✓ All drones disarmed")
        
        print("\n" + "="*60)
        print("✓ FORMATION FLIGHT MISSION COMPLETED SUCCESSFULLY!")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ Error during mission: {e}")
        import traceback
        traceback.print_exc()
        
        # Emergency landing
        print("\nAttempting emergency landing for all drones...")
        try:
            controller.swarm.land_all()
            time.sleep(2.0)
            controller.swarm.disarm_all()
        except Exception as e2:
            print(f"Warning: Error during emergency landing: {e2}")
    
    print("\nMission complete!")


if __name__ == "__main__":
    main()
