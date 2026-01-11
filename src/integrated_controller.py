"""
Integrated LLM + AirSim Swarm Controller
Combines LLM-based shape generation with AirSim drone control
"""

import numpy as np
import time
import os
import json
import datetime
from typing import List, Optional
import threading

from .llm_client import LLMClient, SDFGenerator
from .airsim_controller import AirSimSwarmController
from .swarm_controller import PointDistributor, APFSwarmController
from .sdf_executor import SDFExecutor
from .svg_utils import parse_and_sample


class LLMAirSimSwarmController:
    """
    Main controller that integrates:
    1. LLM for shape description -> SDF code
    2. SDF executor to generate SDF function
    3. Point distributor to generate waypoints
    4. APF controller for swarm movement
    5. AirSim interface for drone control
    """
    
    def __init__(self, 
                 drone_names: List[str],
                 airsim_ip: str = "127.0.0.1",
                 llm_api_key: str = None,
                 llm_base_url: str = None,
                 llm_model: str = None,
                 verbose: bool = True):
        """
        Initialize integrated controller
        
        Args:
            drone_names: List of drone names in AirSim
            airsim_ip: AirSim server IP
            llm_api_key: LLM API key
            llm_base_url: LLM API base URL
            llm_model: LLM model name
            verbose: Enable verbose output
        """
        self.verbose = verbose
        self.drone_names = drone_names
        
        # Initialize components
        self.llm_client = LLMClient(llm_api_key, llm_base_url, llm_model)
        self.sdf_generator = SDFGenerator(self.llm_client)
        self.edge_generator = None
        try:
            # EdgePointGenerator is optional; import lazily to avoid circular issues
            from .llm_client import EdgePointGenerator
            self.edge_generator = EdgePointGenerator(self.llm_client)
        except Exception:
            self.edge_generator = None
        self.svg_generator = None
        try:
            from .llm_client import SVGGenerator
            self.svg_generator = SVGGenerator(self.llm_client)
        except Exception:
            self.svg_generator = None
        self.sdf_executor = SDFExecutor()
        
        self.swarm = AirSimSwarmController(drone_names, verbose)
        self.apf_controller = APFSwarmController()
        self.point_distributor = None
        
        # State variables
        self.current_sdf_code = None
        self.current_shape_description = None
        self.goal_positions = None
        self.is_running = False
        self.control_thread = None
        
        # Parameters
        self.control_rate = 10  # Hz
        self.control_dt = 1.0 / self.control_rate
        
        # Shape transformation parameters for AirSim (NED coordinate system)
        self.shape_scale = 5.0  # Scale factor for generated shapes (meters)
        self.flight_altitude = 5.0  # Center altitude for shapes (meters, positive value)
        # Output directory for saved artifacts (SDF code, goal coordinates)
        self.output_dir = os.path.normpath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs")
        )
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Try to connect to AirSim
        try:
            self.swarm.connect_all(airsim_ip)
            self.log("Connected to AirSim")
        except Exception as e:
            self.log(f"Warning: Could not connect to AirSim: {e}")
    
    def log(self, message: str):
        """Log message if verbose is enabled"""
        if self.verbose:
            print(f"[LLMAirSimSwarm] {message}")
    
    def set_shape_parameters(self, scale: float = None, altitude: float = None):
        """
        Set shape transformation parameters
        
        Args:
            scale: Scale factor for shapes (meters per unit)
            altitude: Center altitude for shapes (meters, positive value)
        """
        if scale is not None:
            self.shape_scale = scale
            self.log(f"Shape scale set to {scale}x")
        
        if altitude is not None:
            self.flight_altitude = altitude
            self.log(f"Flight altitude set to {altitude}m")
    
    def describe_shape(self, description: str) -> bool:
        """
        Generate SDF code from shape description
        
        Args:
            description: Natural language description of shape
            
        Returns:
            True if successful
        """
        try:
            self.log(f"Generating SDF code for: {description}")
            self.current_shape_description = description
            
            # Generate SDF code
            self.current_sdf_code = self.sdf_generator.generate_sdf_code(description)
            
            if not self.current_sdf_code:
                self.log("Failed to generate SDF code")
                return False
            
            self.log("SDF code generated successfully")
            self.log(f"Code preview: {self.current_sdf_code[:100]}...")
            try:
                # Save generated SDF code to outputs directory with timestamp
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_desc = "_".join(description.split())[:40]
                fname = f"sdf_code_{safe_desc}_{ts}.txt"
                path = os.path.join(self.output_dir, fname)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(self.current_sdf_code)
                self.log(f"Saved SDF code to {path}")
            except Exception as e:
                self.log(f"Warning: could not save SDF code: {e}")
            
            return True
            
        except Exception as e:
            self.log(f"Error generating shape: {e}")
            return False
    
    def generate_waypoints(self, num_points: int = None) -> bool:
        """
        Generate waypoints from current SDF
        
        Args:
            num_points: Number of waypoints (defaults to number of drones)
            
        Returns:
            True if successful
        """
        if num_points is None:
            num_points = len(self.drone_names)
        
        try:
            if self.current_shape_description is None:
                self.log("No shape description available. Call describe_shape() first.")
                return False

            # Detect simple shapes we can generate directly (bypass SDF)
            desc = self.current_shape_description.lower()
            is_circle = any(k in desc for k in ("圆", "圆形", "圆盘", "circle", "disk"))
            is_edge_shape = is_circle or any(k in desc for k in ("square", "方", "方形", "rectangle", "矩形", "字", "文字", "letter", "text"))
            is_svg_shape = any(k in desc for k in ("字","文字","letter","text","svg","glyph"))

            if is_circle:
                self.log(f"Detected circle description, generating {num_points} circular waypoints directly...")
                # Default unit radius = 1.0 (will be scaled by self.shape_scale)
                # Try to parse an explicit radius in the description (e.g., 'radius 2' or '半径2')
                radius = 1.0
                try:
                    import re
                    m = re.search(r"(半径|radius)\s*[:=：]?\s*(\d+(?:\.\d+)?)", self.current_shape_description, flags=re.IGNORECASE)
                    if m:
                        radius = float(m.group(2))
                except Exception:
                    pass

                waypoints_relative = self._generate_circle_points(num_points, radius=radius)
                generated_directly = True
            else:
                # For edge-like shapes try multiple direct generation strategies in order:
                # 1) EdgePointGenerator -> 2) SVGGenerator -> 3) fallback to SDF
                waypoints_relative = None
                generated_directly = False

                # Attempt EdgePointGenerator first (if available)
                if is_edge_shape and self.edge_generator is not None:
                    try:
                        self.log(f"Requesting edge points from LLM for: {self.current_shape_description}")
                        pts = self.edge_generator.generate_edge_points(self.current_shape_description, num_points=num_points)
                        if pts and len(pts) >= num_points:
                            waypoints_relative = np.array(pts[:num_points], dtype=float)
                            generated_directly = True
                        else:
                            self.log("LLM edge generation returned too few points or empty")
                    except Exception as e:
                        self.log(f"Edge generation error: {e}")

                # If edge attempt failed, try SVGGenerator (if description suggests SVG/text)
                if waypoints_relative is None and is_svg_shape and self.svg_generator is not None:
                    try:
                        self.log(f"Requesting SVG from LLM for: {self.current_shape_description}")
                        svg = self.svg_generator.generate_svg(self.current_shape_description)
                        if svg:
                            # save raw svg for debugging
                            try:
                                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                                raw_path = os.path.join(self.output_dir, f"llm_svg_{ts}.svg")
                                with open(raw_path, "w", encoding="utf-8") as f:
                                    f.write(svg)
                                self.log(f"Saved raw SVG to {raw_path}")
                            except Exception:
                                pass

                            pts = parse_and_sample(svg, num_points)
                            if pts.size and pts.shape[0] >= num_points:
                                waypoints_relative = pts[:num_points]
                                generated_directly = True
                            else:
                                self.log("SVG parsing/sampling failed or returned too few points")
                        else:
                            self.log("LLM did not return SVG text")
                    except Exception as e:
                        self.log(f"SVG generation/parsing error: {e}")

                # If still no direct generation, fallback to SDF
                if waypoints_relative is None:
                    self.log(f"Generating {num_points} waypoints from SDF (fallback)...")
                    if self.current_sdf_code is None:
                        self.log("No SDF code available. Call describe_shape() first.")
                        return False

                    # Execute SDF code
                    sdf_func = self.sdf_executor.create_sdf_function(self.current_sdf_code)
                    if sdf_func is None:
                        self.log(f"Error: {self.sdf_executor.get_error_message()}")
                        return False

                    # Create point distributor
                    self.point_distributor = PointDistributor(sdf_func)

                    # Generate waypoints (relative coordinates)
                    waypoints_relative = self.point_distributor.generate_points(num_points)
                    generated_directly = False

            # If LLM edge attempt set waypoints_relative to None, perform SDF fallback
            if waypoints_relative is None:
                if self.current_sdf_code is None:
                    self.log("No SDF code available for fallback. Call describe_shape() first.")
                    return False
                sdf_func = self.sdf_executor.create_sdf_function(self.current_sdf_code)
                if sdf_func is None:
                    self.log(f"Error: {self.sdf_executor.get_error_message()}")
                    return False
                self.point_distributor = PointDistributor(sdf_func)
                waypoints_relative = self.point_distributor.generate_points(num_points)
                generated_directly = False
                generated_directly = False
            
            # Transform waypoints to AirSim coordinates
            # AirSim uses NED (North-East-Down): Z negative is up
            # Scale and offset the shape to a suitable flight altitude
            self.goal_positions = waypoints_relative * self.shape_scale
            # In NED: z=-10 means 10 meters altitude
            self.goal_positions[:, 2] = self.goal_positions[:, 2] - self.flight_altitude
            
            self.log(f"Generated waypoints shape: {self.goal_positions.shape}")
            if generated_directly:
                self.log(f"Generated waypoints (relative, unit scale):\n{waypoints_relative}")
            else:
                self.log(f"SDF-generated waypoints (relative, unit scale):\n{waypoints_relative}")
            self.log(f"Transformed waypoints (AirSim NED coordinates):\n{self.goal_positions}")
            self.log(f"  Scale: {self.shape_scale}x, Center altitude: {self.flight_altitude}m")
            try:
                # Save goal positions (as JSON list) with timestamp
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                fname = f"goals_{num_points}_{ts}.json"
                path = os.path.join(self.output_dir, fname)
                data = {
                    "description": self.current_shape_description,
                    "num_points": int(num_points),
                    "scale": float(self.shape_scale),
                    "flight_altitude": float(self.flight_altitude),
                    "generated_directly": bool(generated_directly),
                    "goals_ned": self.goal_positions.tolist(),
                }
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                self.log(f"Saved goal positions to {path}")
            except Exception as e:
                self.log(f"Warning: could not save goal positions: {e}")
            
            return True
            
        except Exception as e:
            self.log(f"Error generating waypoints: {e}")
            return False
    
    def prepare_mission(self, shape_description: str, num_points: int = None) -> bool:
        """
        Complete preparation pipeline: shape description -> SDF -> waypoints
        
        Args:
            shape_description: Natural language shape description
            num_points: Number of waypoints
            
        Returns:
            True if successful
        """
        if not self.describe_shape(shape_description):
            return False
        
        if not self.generate_waypoints(num_points):
            return False
        
        self.log("Mission prepared successfully!")
        return True

    def _generate_circle_points(self, num_points: int, radius: float = 1.0) -> np.ndarray:
        """
        Generate evenly spaced points on a horizontal circle in the XY plane.

        Args:
            num_points: number of points on the circle
            radius: radius in unit shape coordinates (will be scaled later)

        Returns:
            np.ndarray of shape (num_points, 3)
        """
        angles = np.linspace(0, 2 * np.pi, num_points, endpoint=False)
        x = radius * np.cos(angles)
        y = radius * np.sin(angles)
        z = np.zeros_like(x)
        return np.stack([x, y, z], axis=1)

    def _assign_nearest_unique(self, goal_positions: np.ndarray) -> dict:
        """
        Assign each drone the nearest unique goal position.

        Returns a dict mapping drone_name -> goal_index
        """
        drone_names = list(self.drone_names)
        n_drones = len(drone_names)
        n_goals = goal_positions.shape[0]

        # Get current drone positions
        current_positions = self.swarm.get_positions()
        if current_positions.shape[0] != n_drones:
            # If mismatch, assume order of drone_names and query individually
            current_positions = []
            for name in drone_names:
                try:
                    pos = self.swarm[name].position
                except Exception:
                    pos = np.array([0.0, 0.0, 0.0])
                current_positions.append(pos)
            current_positions = np.array(current_positions)

        # Compute distance matrix (drones x goals) using XY plane distances
        # shape current_positions: (n_drones, 3) -> (n_drones, 1, 2)
        # shape goal_positions: (n_goals, 3) -> (1, n_goals, 2)
        dists = np.linalg.norm(current_positions[:, None, :2] - goal_positions[None, :, :2], axis=2)

        assignments = {}
        assigned_goals = set()

        # Order drones by descending minimal distance so far (give far drones first pick)
        min_dists = dists.min(axis=1)
        drone_order = np.argsort(-min_dists)

        allow_duplicates = n_goals < n_drones
        if allow_duplicates:
            self.log("Warning: fewer goal points than drones; duplicates will be assigned")

        for di in drone_order:
            # find nearest unassigned goal (or nearest overall if duplicates allowed)
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
                    # fallback: pick nearest even if already assigned
                    pick = sorted_goals[0]

            assigned_goals.add(pick)
            assignments[drone_names[di]] = int(pick)

        return assignments
    
    def start_mission(self):
        """Start the swarm control mission"""
        try:
            if self.goal_positions is None:
                self.log("No goal positions set. Call prepare_mission() first.")
                return False
            
            self.log("Starting mission...")
            
            # Arm all drones first
            self.log("Arming all drones...")
            self.swarm.arm_all()
            self.log("✓ All drones armed")

            # Takeoff drones staggered (one by one) to reduce collision risk at start
            self.log("Taking off drones staggered (sequentially)...")
            drone_list = list(self.swarm.drones.keys())
            for i, drone_name in enumerate(drone_list):
                self.log(f"Launching {drone_name} ({i+1}/{len(drone_list)})...")
                try:
                    drone = self.swarm[drone_name]
                    task = drone.takeoff(5.0)
                    if task:
                        task.join()
                    time.sleep(0.5)  # Stagger launches
                except Exception as e:
                    self.log(f"Warning: takeoff error for {drone_name}: {e}")
            
            self.log("✓ All drones launched to altitude")

            # Wait a moment for stabilization
            time.sleep(1.0)

            # Assign unique nearest waypoints to each drone
            self.log("Assigning nearest unique waypoints to drones...")
            assignments = self._assign_nearest_unique(self.goal_positions)
            self.log(f"Assignments: {assignments}")
            # save assignments for debugging/audit
            try:
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                assign_fname = f"assignments_{ts}.json"
                assign_path = os.path.join(self.output_dir, assign_fname)
                with open(assign_path, "w", encoding="utf-8") as af:
                    json.dump({"assignments": assignments}, af, indent=2, ensure_ascii=False)
                self.log(f"Saved assignments to {assign_path}")
            except Exception:
                pass

            # Online APF-based movement with separation to avoid collisions
            self.log("Starting online APF control for collision-avoiding movement...")

            # Build ordered assigned goals array matching swarm drone order
            drone_list = list(self.swarm.drones.keys())
            n = len(drone_list)
            assigned_goals = np.zeros((n, 3), dtype=float)
            for i, name in enumerate(drone_list):
                goal_idx = assignments.get(name, 0)
                assigned_goals[i] = self.goal_positions[int(goal_idx)]

            # Configure APF controller goals
            try:
                self.apf_controller.goals = assigned_goals
                self.apf_controller.min_dist = 1.0  # meters separation
                self.apf_controller.max_vel = 2.0
            except Exception:
                pass

            # Control loop: run until all drones reach their assigned goals or timeout
            arrival_thresh = 0.5  # meters
            dt = 0.5
            max_time = 120.0
            t_start = time.time()

            while True:
                # Update current positions
                current_positions = self.swarm.get_positions()
                if current_positions.shape[0] != n:
                    # fill missing with zeros
                    padded = np.zeros((n, 3), dtype=float)
                    padded[: current_positions.shape[0], :] = current_positions
                    current_positions = padded

                # Update APF target goals (keeps assignment fixed)
                self.apf_controller.goals = assigned_goals

                # Compute control velocities
                vels = self.apf_controller.get_control(current_positions)


                # Clip velocities to max
                speeds = np.linalg.norm(vels, axis=1)
                too_fast = speeds > self.apf_controller.max_vel
                if np.any(too_fast):
                    vels[too_fast] = (
                        vels[too_fast] / speeds[too_fast, None] * self.apf_controller.max_vel
                    )

                # Predictive collision check: scale down velocities if predicted positions conflict
                pred_pos = current_positions + vels * dt
                # pairwise distances
                pp_dists = np.linalg.norm(pred_pos[:, None, :2] - pred_pos[None, :, :2], axis=2)
                conflict_mask = pp_dists < max(0.5, self.apf_controller.min_dist)
                # zero diagonal
                np.fill_diagonal(conflict_mask, False)
                if np.any(conflict_mask):
                    # For each conflicting pair, reduce both velocities by half (conservative)
                    pairs = np.argwhere(conflict_mask)
                    affected = set()
                    for i, j in pairs:
                        affected.add(i)
                        affected.add(j)
                    for idx in affected:
                        vels[idx] = 0.5 * vels[idx]

                self.swarm.set_velocities(vels, duration=dt)

                # Check arrival
                dists = np.linalg.norm(current_positions - assigned_goals, axis=1)
                if np.all(dists <= arrival_thresh):
                    self.log("All drones within arrival threshold")
                    break

                if time.time() - t_start > max_time:
                    self.log("Warning: APF control timed out before all drones reached goals")
                    break

                time.sleep(dt)

            # Stop all drones (zero velocity) and snap to final positions
            self.swarm.set_velocities(np.zeros_like(assigned_goals), duration=0.5)
            # Optionally call set_positions once to ensure final placement
            try:
                self.swarm.set_positions(assigned_goals, velocity=1.0)
            except Exception:
                pass

            self.log("✓ APF-based movement complete")
            
            # Start the hovering control loop to maintain positions
            self.is_running = True
            self.control_thread = threading.Thread(target=self._hovering_control_loop, daemon=True)
            self.control_thread.start()
            
            self.log("Mission started! Drones are now holding position at goal points.")
            return True
            
        except Exception as e:
            self.log(f"Error starting mission: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _hovering_control_loop(self):
        """Control loop that keeps drones hovering at goal positions"""
        try:
            hover_timeout = 0
            while self.is_running:
                # Periodically check and maintain positions
                positions = self.swarm.get_positions()
                
                if positions.shape[0] > 0 and self.goal_positions is not None:
                    # Check if drones are close to their goal positions
                    distances = np.linalg.norm(positions - self.goal_positions[:positions.shape[0]], axis=1)
                    max_distance = np.max(distances)
                    
                    # If drones have drifted, send them back to goal
                    if max_distance > 0.5:  # threshold of 0.5 units
                        self.swarm.set_positions(self.goal_positions, velocity=0.5)
                    
                    # Log status periodically (every 5 seconds)
                    hover_timeout += 1
                    if hover_timeout >= 50:  # 50 * 0.1s = 5s
                        avg_distance = np.mean(distances)
                        self.log(f"Hovering: avg distance to goal = {avg_distance:.2f}m, max = {max_distance:.2f}m")
                        hover_timeout = 0
                
                # Sleep
                time.sleep(self.control_dt)
                
        except Exception as e:
            self.log(f"Error in hovering control loop: {e}")
            self.stop_mission()
    
    def stop_mission(self):
        """Stop the mission and land drones"""
        try:
            self.log("Stopping mission...")
            self.is_running = False
            
            if self.control_thread:
                self.control_thread.join(timeout=5.0)
            
            # Land and disarm
            self.swarm.land_all()
            self.swarm.disarm_all()
            
            self.log("Mission stopped")
            
        except Exception as e:
            self.log(f"Error stopping mission: {e}")
    
    def interactive_mode(self):
        """Run interactive command prompt"""
        self.log("Entering interactive mode. Commands:")
        self.log("  shape <description> - Generate shape and waypoints")
        self.log("  start - Start the mission")
        self.log("  stop - Stop the mission")
        self.log("  status - Show current status")
        self.log("  set scale <value> - Set shape scale (default: 5)")
        self.log("  set altitude <value> - Set flight altitude in meters (default: 5)")
        self.log("  quit - Exit")
        
        while True:
            try:
                command = input("\n> ").strip().lower()
                
                if command.startswith("shape "):
                    description = command[6:].strip()
                    if self.prepare_mission(description):
                        self.log("Ready to execute. Type 'start' to begin.")
                
                elif command == "start":
                    if self.goal_positions is not None:
                        self.start_mission()
                    else:
                        self.log("No mission prepared. Use 'shape <description>' first.")
                
                elif command == "stop":
                    self.stop_mission()
                
                elif command.startswith("set scale "):
                    try:
                        scale = float(command[10:].strip())
                        self.set_shape_parameters(scale=scale)
                    except ValueError:
                        self.log("Invalid scale value. Use: set scale <number>")
                
                elif command.startswith("set altitude "):
                    try:
                        altitude = float(command[13:].strip())
                        self.set_shape_parameters(altitude=altitude)
                    except ValueError:
                        self.log("Invalid altitude value. Use: set altitude <number>")
                
                elif command == "status":
                    self.log(f"Running: {self.is_running}")
                    self.log(f"Current shape: {self.current_shape_description}")
                    self.log(f"Shape scale: {self.shape_scale}x")
                    self.log(f"Flight altitude: {self.flight_altitude}m")
                    if self.goal_positions is not None:
                        self.log(f"Goal positions: {self.goal_positions.shape}")
                        positions = self.swarm.get_positions()
                        self.log(f"Current positions: {positions.shape}")
                
                elif command == "quit":
                    if self.is_running:
                        self.stop_mission()
                    self.log("Exiting...")
                    break
                
                else:
                    self.log("Unknown command")
                    
            except KeyboardInterrupt:
                self.log("\nInterrupted")
                break
            except Exception as e:
                self.log(f"Error: {e}")


# Example usage
if __name__ == "__main__":
    import sys
    
    # Configure drones
    DRONE_NAMES = ["Drone1", "Drone2", "Drone3", "Drone4"]
    
    try:
        # Create controller
        controller = LLMAirSimSwarmController(
            drone_names=DRONE_NAMES,
            airsim_ip="127.0.0.1",
            verbose=True
        )
        
        # Test with simple shape
        print("\n" + "="*60)
        print("Testing shape generation and waypoint planning...")
        print("="*60 + "\n")
        
        if controller.prepare_mission("cube with 1 unit side length", num_points=4):
            print("\nWaypoints generated successfully!")
            print("In production, call controller.start_mission() to begin")
            # controller.start_mission()
            # time.sleep(30)
            # controller.stop_mission()
        else:
            print("Failed to prepare mission")
        
        # Uncomment below for interactive mode:
        # print("\n" + "="*60)
        # print("Starting interactive mode...")
        # print("="*60)
        # controller.interactive_mode()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
