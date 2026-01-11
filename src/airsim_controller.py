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
        self.connected = False
        self.connected_ip = None
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
            self.connected = True
            self.connected_ip = ip
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
        if not self._ensure_connected():
            self.log("Cannot arm: no connection to AirSim")
            return

        try:
            self.client.enableApiControl(True, self.drone_name)
            self.client.armDisarm(True, self.drone_name)
            self.log("Armed")
        except Exception as e:
            self.log(f"Failed to arm: {e}")
    
    def disarm(self):
        """Disarm the drone"""
        if not self._ensure_connected():
            self.log("Cannot disarm: no connection to AirSim")
            return

        try:
            self.client.armDisarm(False, self.drone_name)
            self.client.enableApiControl(False, self.drone_name)
            self.log("Disarmed")
        except Exception as e:
            self.log(f"Failed to disarm: {e}")
    
    def takeoff(self, duration: float = 5.0):
        """
        Takeoff the drone
        
        Args:
            duration: Duration of takeoff in seconds
        """
        if not self._ensure_connected():
            self.log("Cannot takeoff: no connection to AirSim")
            return None

        try:
            return self.client.takeoffAsync(vehicle_name=self.drone_name)
        except Exception as e:
            self.log(f"Takeoff failed: {e}")
            return None
    
    def land(self):
        """Land the drone"""
        if not self._ensure_connected():
            self.log("Cannot land: no connection to AirSim")
            return None

        try:
            return self.client.landAsync(vehicle_name=self.drone_name)
        except Exception as e:
            self.log(f"Land failed: {e}")
            return None
    
    def update_position(self):
        """Update current position from AirSim"""
        if not self._ensure_connected():
            # keep previous position
            return

        try:
            state = self.client.getMultirotorState(self.drone_name)
            pos = state.kinematics_estimated.position
            self.position = np.array([pos.x_val, pos.y_val, pos.z_val])
        except Exception:
            # ignore errors updating position
            return
    
    def set_velocity(self, velocity: np.ndarray, duration: float = 0.1):
        """
        Set velocity command
        
        Args:
            velocity: Velocity vector [vx, vy, vz]
            duration: Duration to apply velocity in seconds
        """
        if not self._ensure_connected():
            self.log("Cannot set velocity: no connection to AirSim")
            return

        try:
            self.client.moveByVelocityAsync(
                velocity.x if hasattr(velocity, 'x') else velocity[0],
                velocity.y if hasattr(velocity, 'y') else velocity[1],
                velocity.z if hasattr(velocity, 'z') else velocity[2],
                duration,
                vehicle_name=self.drone_name
            )
        except Exception as e:
            self.log(f"moveByVelocityAsync failed: {e}")
    
    def set_position(self, position: np.ndarray, velocity: float = 1.0):
        """
        Move to absolute position (async, non-blocking)
        
        Args:
            position: Target position [x, y, z]
            velocity: Maximum velocity during movement
        """
        if not self._ensure_connected():
            self.log("Cannot set position: no connection to AirSim")
            return None

        try:
            return self.client.moveToPositionAsync(
                position[0], position[1], position[2],
                velocity,
                vehicle_name=self.drone_name
            )
        except Exception as e:
            self.log(f"moveToPositionAsync failed: {e}")
            return None

    def _ensure_connected(self) -> bool:
        """Ensure the underlying AirSim client is available and usable."""
        if not self.client:
            return False

        try:
            # Try a lightweight call to verify transport is alive
            # getMultirotorState will raise if session/transport is invalid
            _ = self.client.getMultirotorState(self.drone_name)
            return True
        except Exception:
            # Attempt to reconnect if we have an IP saved
            if self.connected_ip:
                try:
                    self.connect(self.connected_ip)
                    return True
                except Exception:
                    return False
            return False


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
        Takeoff all drones simultaneously
        
        Args:
            duration: Duration of takeoff in seconds
        """
        # Collect all async objects
        tasks = []
        for drone in self.drones.values():
            task = drone.takeoff(duration)
            if task:
                tasks.append(task)
        
        # Wait for all to complete
        for task in tasks:
            task.join()
        
        self.log("All drones launched")
    
    def land_all(self):
        """Land all drones simultaneously"""
        # Collect all async objects
        tasks = []
        for drone in self.drones.values():
            task = drone.land()
            if task:
                tasks.append(task)
        
        # Wait for all to complete
        for task in tasks:
            task.join()
        
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
        Set target positions for all drones simultaneously
        
        Args:
            positions: Array of shape (N, 3) with target positions
            velocity: Maximum velocity during movement
        """
        # Collect all async objects without blocking
        tasks = []
        drone_list = list(self.drones.values())
        for i, drone in enumerate(drone_list):
            if i < len(positions):
                task = drone.set_position(positions[i], velocity)
                if task:
                    tasks.append((drone.drone_name, task))
        
        # Wait for all movements to complete
        for drone_name, task in tasks:
            task.join()
        
        # Update positions after all drones have moved
        for drone in drone_list:
            drone.update_position()
    
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
