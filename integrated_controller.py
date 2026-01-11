"""
Integrated LLM + AirSim Swarm Controller
Combines LLM-based shape generation with AirSim drone control
"""

import numpy as np
import time
from typing import List, Optional
import threading

from llm_client import LLMClient, SDFGenerator
from airsim_controller import AirSimSwarmController
from swarm_controller import PointDistributor, APFSwarmController
from sdf_executor import SDFExecutor


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
            if self.current_sdf_code is None:
                self.log("No SDF code available. Call describe_shape() first.")
                return False
            
            self.log(f"Generating {num_points} waypoints from SDF...")
            
            # Execute SDF code
            sdf_func = self.sdf_executor.create_sdf_function(self.current_sdf_code)
            if sdf_func is None:
                self.log(f"Error: {self.sdf_executor.get_error_message()}")
                return False
            
            # Create point distributor
            self.point_distributor = PointDistributor(sdf_func)
            
            # Generate waypoints
            self.goal_positions = self.point_distributor.generate_points(num_points)
            
            self.log(f"Generated waypoints shape: {self.goal_positions.shape}")
            self.log(f"Waypoints:\n{self.goal_positions}")
            
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
    
    def start_mission(self):
        """Start the swarm control mission"""
        try:
            if self.goal_positions is None:
                self.log("No goal positions set. Call prepare_mission() first.")
                return False
            
            self.log("Starting mission...")
            
            # Arm and takeoff
            self.swarm.arm_all()
            self.swarm.takeoff_all(5.0)
            
            # Move all drones to their goal positions and hold them there
            self.log("Moving drones to goal positions...")
            self.swarm.set_positions(self.goal_positions, velocity=2.0)
            
            # Keep drones at goal positions indefinitely
            self.is_running = True
            self.control_thread = threading.Thread(target=self._hovering_control_loop, daemon=True)
            self.control_thread.start()
            
            self.log("Mission started! Drones are now holding position at goal points.")
            return True
            
        except Exception as e:
            self.log(f"Error starting mission: {e}")
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
                
                elif command == "status":
                    self.log(f"Running: {self.is_running}")
                    self.log(f"Current shape: {self.current_shape_description}")
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
