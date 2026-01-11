"""
Generate sampled edge points (via LLM SVG or local generators) and send them to AirSim.

Usage:
    python scripts/run_mission_from_svg.py "描述文字或英文" --num 10 [--scale 5] [--alt 5] [--dry-run]

Options:
    --desc / positional: shape description (if omitted, default demo used)
    --num: number of drones/points
    --scale: shape_scale (meters per unit)
    --alt: flight altitude (meters)
    --dry-run: generate & save points but don't arm/takeoff/move

Notes:
 - This script sets controller.current_shape_description directly to avoid SDF generation when possible.
 - If LLM SVG/edge generation fails, it will fall back to SDF-based sampling.
"""
import argparse
import time
import os
import sys

# Ensure repo root is on sys.path so `import src...` works when running this script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.integrated_controller import LLMAirSimSwarmController


def main():
    p = argparse.ArgumentParser()
    p.add_argument('description', nargs='?', default='Generate SVG outline for letter A')
    p.add_argument('--num', type=int, default=10)
    p.add_argument('--scale', type=float, default=5.0)
    p.add_argument('--alt', type=float, default=5.0)
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--airsim-ip', default='127.0.0.1')
    args = p.parse_args()

    desc = args.description
    num = args.num

    # Create controller for N drones (names Drone1..DroneN)
    drone_names = [f"Drone{i+1}" for i in range(num)]
    controller = LLMAirSimSwarmController(drone_names=drone_names, airsim_ip=args.airsim_ip, verbose=True)

    # Configure scale/alt
    controller.set_shape_parameters(scale=args.scale, altitude=args.alt)

    # Set description directly (avoid SDF step) and generate waypoints
    controller.current_shape_description = desc
    ok = controller.generate_waypoints(num_points=num)
    if not ok:
        print("Failed to generate waypoints")
        return 1

    # Points saved to outputs by generate_waypoints; print path suggestion
    print("Generated goal positions (saved in outputs).\nSample of goals:")
    print(controller.goal_positions)

    if args.dry_run:
        print("Dry run: not sending to AirSim")
        return 0

    # Start mission (arm, takeoff, move, hover loop)
    started = controller.start_mission()
    if not started:
        print("Failed to start mission")
        return 1

    try:
        # Let the mission run for some time (user can Ctrl-C)
        runtime = max(10, num * 2)
        print(f"Mission running for {runtime}s... press Ctrl-C to stop earlier")
        time.sleep(runtime)
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        controller.stop_mission()

    return 0

if __name__ == '__main__':
    main()
