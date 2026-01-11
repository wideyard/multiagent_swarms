"""
AirSim Communication Interface for Swarm Control
Handles communication with AirSim drones
"""

import airsim
import numpy as np
from typing import List, Tuple, Dict
import time


class AirSimDroneController:
    """Controller for individual drones in AirSim"""
    
    def __init__(self, drone_name: str = "Drone1", verbose: bool = False):
        """
        Initialize drone controller
        
        Args:
            drone_name: Name of the drone in AirSim
            verbose: Enable verbose output
        """
        self.drone_name = drone_name
        self.verbose = verbose
        self.client = None
        self.position = np.array([0.0, 0.0, 0.0])
        self.velocity = np.array([0.0, 0.0, 0.0])
        self.goal = np.array([0.0, 0.0, 0.0])
        
    def connect(self, ip: str = "127.0.0.1"):
        """
        Connect to AirSim
        
        Args:
            ip: AirSim server IP address
        """
        try:
            self.client = airsim.MultirotorClient(ip=ip)
            self.client.confirmConnection()
            self.log(f"Connected to AirSim at {ip}")
        except Exception as e:
            self.log(f"Failed to connect: {e}")
            raise
    
    def log(self, message: str):
        """Log message if verbose is enabled"""
        if self.verbose:
            print(f"[{self.drone_name}] {message}")
    
    def arm(self):
        """Arm the drone"""
        if self.client:
            self.client.enableApiControl(True, self.drone_name)
            self.client.armDisarm(True, self.drone_name)
            self.log("Armed")
    
    def disarm(self):
        """Disarm the drone"""
        if self.client:
            self.client.armDisarm(False, self.drone_name)
            self.client.enableApiControl(False, self.drone_name)
            self.log("Disarmed")
    
    def takeoff(self, duration: float = 5.0):
        """
        Takeoff the drone
        
        Args:
            duration: Duration of takeoff in seconds
        """
        if self.client:
            self.client.takeoffAsync(vehicle_name=self.drone_name).join()
            self.log("Takeoff complete")
    
    def land(self):
        """Land the drone"""
        if self.client:
            self.client.landAsync(vehicle_name=self.drone_name).join()
            self.log("Landing complete")
    
    def update_position(self):
        """Update current position from AirSim"""
        if self.client:
            state = self.client.getMultirotorState(self.drone_name)
            pos = state.kinematics_estimated.position
            self.position = np.array([pos.x_val, pos.y_val, pos.z_val])
    
    def set_velocity(self, velocity: np.ndarray, duration: float = 0.1):
        """
        Set velocity command
        
        Args:
            velocity: Velocity vector [vx, vy, vz]
            duration: Duration to apply velocity in seconds
        """
        if self.client:
            self.client.moveByVelocityAsync(
                velocity.x if hasattr(velocity, 'x') else velocity[0],
                velocity.y if hasattr(velocity, 'y') else velocity[1],
                velocity.z if hasattr(velocity, 'z') else velocity[2],
                duration,
                vehicle_name=self.drone_name
            )
    
    def set_position(self, position: np.ndarray, velocity: float = 1.0):
        """
        Move to absolute position
        
        Args:
            position: Target position [x, y, z]
            velocity: Maximum velocity during movement
        """
        if self.client:
            self.client.moveToPositionAsync(
                position[0], position[1], position[2],
                velocity,
                vehicle_name=self.drone_name
            ).join()
            self.update_position()


class AirSimSwarmController:
    """Manages swarm of drones in AirSim"""
    
    def __init__(self, drone_names: List[str] = None, verbose: bool = False):
        """
        Initialize swarm controller
        
        Args:
            drone_names: List of drone names in AirSim
            verbose: Enable verbose output
        """
        self.verbose = verbose
        self.drones: Dict[str, AirSimDroneController] = {}
        
        if drone_names:
            for name in drone_names:
                self.drones[name] = AirSimDroneController(name, verbose)
        
    def connect_all(self, ip: str = "127.0.0.1"):
        """
        Connect all drones to AirSim
        
        Args:
            ip: AirSim server IP address
        """
        for drone in self.drones.values():
            drone.connect(ip)
        self.log(f"Connected {len(self.drones)} drones")
    
    def add_drone(self, drone_name: str):
        """
        Add a drone to the swarm
        
        Args:
            drone_name: Name of the drone
        """
        if drone_name not in self.drones:
            self.drones[drone_name] = AirSimDroneController(drone_name, self.verbose)
    
    def log(self, message: str):
        """Log message if verbose is enabled"""
        if self.verbose:
            print(f"[Swarm] {message}")
    
    def arm_all(self):
        """Arm all drones"""
        for drone in self.drones.values():
            drone.arm()
        self.log("All drones armed")
    
    def disarm_all(self):
        """Disarm all drones"""
        for drone in self.drones.values():
            drone.disarm()
        self.log("All drones disarmed")
    
    def takeoff_all(self, duration: float = 5.0):
        """
        Takeoff all drones
        
        Args:
            duration: Duration of takeoff in seconds
        """
        for drone in self.drones.values():
            drone.takeoff(duration)
        self.log("All drones launched")
    
    def land_all(self):
        """Land all drones"""
        for drone in self.drones.values():
            drone.land()
        self.log("All drones landed")
    
    def get_positions(self) -> np.ndarray:
        """
        Get positions of all drones
        
        Returns:
            Array of shape (N, 3) with drone positions
        """
        positions = []
        for drone in self.drones.values():
            drone.update_position()
            positions.append(drone.position)
        return np.array(positions)
    
    def set_velocities(self, velocities: np.ndarray, duration: float = 0.1):
        """
        Set velocities for all drones
        
        Args:
            velocities: Array of shape (N, 3) with velocities
            duration: Duration to apply velocities in seconds
        """
        drone_list = list(self.drones.values())
        for i, drone in enumerate(drone_list):
            if i < len(velocities):
                drone.set_velocity(velocities[i], duration)
    
    def set_positions(self, positions: np.ndarray, velocity: float = 1.0):
        """
        Set target positions for all drones
        
        Args:
            positions: Array of shape (N, 3) with target positions
            velocity: Maximum velocity during movement
        """
        drone_list = list(self.drones.values())
        for i, drone in enumerate(drone_list):
            if i < len(positions):
                drone.set_position(positions[i], velocity)
    
    def get_drone_count(self) -> int:
        """Get number of drones in swarm"""
        return len(self.drones)
    
    def __getitem__(self, drone_name: str) -> AirSimDroneController:
        """Get drone by name"""
        return self.drones[drone_name]


# Example usage
if __name__ == "__main__":
    # Create swarm controller with 4 drones
    swarm = AirSimSwarmController(["Drone1", "Drone2", "Drone3", "Drone4"], verbose=True)
    
    try:
        # Connect to AirSim
        swarm.connect_all("127.0.0.1")
        
        # Arm all drones
        swarm.arm_all()
        
        # Takeoff
        swarm.takeoff_all(5.0)
        
        # Get current positions
        positions = swarm.get_positions()
        print("Current positions shape:", positions.shape)
        
        # Create goal positions (move forward)
        goal_positions = positions + np.array([[1, 0, 0], [0, 1, 0], [-1, 0, 0], [0, -1, 0]])
        
        # Move to goal positions
        swarm.set_positions(goal_positions, velocity=1.0)
        
        # Land all drones
        swarm.land_all()
        
        # Disarm all drones
        swarm.disarm_all()
        
    except Exception as e:
        print(f"Error: {e}")
        swarm.disarm_all()
