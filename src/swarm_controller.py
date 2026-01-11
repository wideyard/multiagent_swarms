"""
Point Distribution and APF Swarm Control
Adapted from flock_gpt/scripts/
"""

import numpy as np
from scipy.optimize import minimize
from scipy.spatial.distance import cdist
from scipy.spatial import ConvexHull, QhullError
from sklearn.cluster import KMeans
from typing import Callable, Tuple


class PointDistributor:
    """
    Distributes points within an SDF boundary
    Adapted from flock_gpt/scripts/point_distributor.py
    """
    
    def __init__(self, sdf_func: Callable, epsilon: float = 1e-6):
        """
        Initialize point distributor
        
        Args:
            sdf_func: SDF function that takes (N, 3) array of points
            epsilon: Numerical gradient epsilon
        """
        self.sdf_func = sdf_func
        self.epsilon = epsilon
        
        # Estimate bounds from SDF
        self.bounds_min, self.bounds_max = self._estimate_bounds()
    
    def _estimate_bounds(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Estimate bounding box for SDF
        
        Returns:
            Tuple of (min_bounds, max_bounds)
        """
        # Test points along axes to find bounds
        test_range = np.linspace(-10, 10, 21)
        valid_points = []
        
        for x in test_range:
            for y in test_range:
                for z in test_range:
                    point = np.array([[x, y, z]])
                    try:
                        sdf_val = self.sdf_func(point)
                        if sdf_val[0] <= 0:  # Inside or on boundary
                            valid_points.append([x, y, z])
                    except:
                        pass
        
        if valid_points:
            valid_points = np.array(valid_points)
            bounds_min = valid_points.min(axis=0)
            bounds_max = valid_points.max(axis=0)
        else:
            # Default bounds
            bounds_min = np.array([-5, -5, -5])
            bounds_max = np.array([5, 5, 5])
        
        return bounds_min, bounds_max
    
    def get_cost_sdf(self, x: np.ndarray) -> float:
        """
        Calculate cost based on SDF distance
        
        Args:
            x: Flattened point array
            
        Returns:
            SDF cost
        """
        points = x.reshape(-1, 3)
        try:
            sdf_cost = np.sum(np.abs(self.sdf_func(points)))
            return float(sdf_cost)
        except:
            return 1e6
    
    def distrib_cost(self, x: np.ndarray) -> float:
        """
        Calculate distribution cost (SDF + coverage)
        
        Args:
            x: Flattened point array
            
        Returns:
            Total cost
        """
        x = x.reshape(-1, 3)
        
        sdf_cost = 0
        dist_cost = 0
        volume = 0
        
        if x.shape[0] > 1:
            # Distance-based cost
            dists = cdist(x, x)
            min_dists = []
            for i, dist in enumerate(dists):
                dist_nonzero = dist[dist > 0]
                if len(dist_nonzero) > 0:
                    min_dists.append(np.min(dist_nonzero))
            
            if min_dists:
                min_dists = np.array(min_dists)
                dist_cost = np.sum(min_dists)
            
            # Volume cost
            try:
                volume = ConvexHull(x).volume
            except QhullError:
                volume = 0
        
        # SDF cost
        try:
            sdf_cost = np.sum(np.abs(self.sdf_func(x)))
        except:
            sdf_cost = 1e6
        
        total_cost = 100 * sdf_cost - 0.5 * dist_cost - 0.5 * volume
        return float(total_cost)
    
    def generate_points(self, num_points: int, num_samples: int = 1000) -> np.ndarray:
        """
        Generate optimized point distribution
        
        Args:
            num_points: Number of output points
            num_samples: Number of initial samples
            
        Returns:
            Array of shape (num_points, 3) with optimized positions
        """
        # Generate initial random points
        points = np.random.uniform(
            low=self.bounds_min, 
            high=self.bounds_max, 
            size=(num_samples, 3)
        )
        
        # Optimize for SDF
        init_shape = points.shape
        points_flat = points.flatten()
        res = minimize(
            self.get_cost_sdf, 
            points_flat, 
            method="L-BFGS-B",
            options={"maxiter": 1000}
        )
        points = res.x.reshape(init_shape[0], 3)
        
        # Cluster points
        kmeans = KMeans(n_clusters=num_points, random_state=0, n_init=10)
        kmeans.fit(points)
        out_points = kmeans.cluster_centers_
        
        # Fine-tune distribution
        out_points_flat = out_points.flatten()
        res = minimize(
            self.distrib_cost,
            out_points_flat,
            method="L-BFGS-B",
            options={"maxiter": 100}
        )
        out_points = res.x.reshape(-1, 3)
        
        return out_points


class APFSwarmController:
    """
    Artificial Potential Field controller for drone swarms
    Adapted from flock_gpt/scripts/apf_controller.py
    """
    
    def __init__(self, 
                 p_cohesion: float = 1.0,
                 p_separation: float = 1.0,
                 p_alignment: float = 1.0,
                 max_vel: float = 1.0,
                 min_dist: float = 0.5):
        """
        Initialize APF controller
        
        Args:
            p_cohesion: Cohesion gain
            p_separation: Separation gain
            p_alignment: Alignment gain
            max_vel: Maximum velocity magnitude
            min_dist: Minimum distance between drones
        """
        self.p_cohesion = p_cohesion
        self.p_separation = p_separation
        self.p_alignment = p_alignment
        self.max_vel = max_vel
        self.min_dist = min_dist
        
        self.goals = None
        self.velocities = None
    
    def distribute_goals(self, current_poses: np.ndarray, goal_poses: np.ndarray) -> np.ndarray:
        """
        Distribute goals to drones (optimal assignment)
        
        Args:
            current_poses: Array of shape (N, 3) with current positions
            goal_poses: Array of shape (M, 3) with goal positions
            
        Returns:
            Array of shape (N, 3) with assigned goals
        """
        if goal_poses.shape[0] == 0:
            return np.zeros_like(current_poses)
        
        # Compute distance matrix
        dist_arr = cdist(current_poses, goal_poses)
        out_goals = np.zeros_like(current_poses)
        
        # Greedy assignment
        for i in range(current_poses.shape[0]):
            if np.any(dist_arr[i] < np.inf):
                ind = np.argmin(dist_arr[i])
                out_goals[i] = goal_poses[ind]
                dist_arr[i, :] = np.inf
                dist_arr[:, ind] = np.inf
            else:
                out_goals[i] = current_poses[i]  # Stay in place
        
        self.goals = out_goals
        return out_goals
    
    def get_control(self, poses: np.ndarray) -> np.ndarray:
        """
        Calculate control velocities for swarm
        
        Args:
            poses: Array of shape (N, 3) with current positions
            
        Returns:
            Array of shape (N, 3) with velocity commands
        """
        if self.goals is None or self.goals.shape[0] == 0:
            return np.zeros_like(poses)
        
        if self.velocities is None:
            self.velocities = np.zeros_like(poses)
        
        # Cohesion: move toward goals
        vel_cohesion = self.p_cohesion * (self.goals - poses)
        
        # Limit cohesion velocity
        for j in range(len(vel_cohesion)):
            vel_mag = np.linalg.norm(vel_cohesion[j])
            if vel_mag > self.max_vel:
                vel_cohesion[j] = self.max_vel * vel_cohesion[j] / vel_mag
        
        # Separation: avoid other drones
        vel_separation = np.zeros_like(vel_cohesion)
        for i, pose in enumerate(poses):
            # Find nearest neighbors
            distances = np.linalg.norm(poses - pose, axis=1)
            too_close = distances < self.min_dist
            too_close[i] = False  # Exclude self
            
            # Repulsion from neighbors
            v = np.zeros(3)
            for j in np.where(too_close)[0]:
                v -= (poses[j] - pose)
            
            # Only apply horizontal separation
            v[2] = 0
            vel_separation[i] = v
        
        # Combine forces
        control_vels = vel_cohesion + vel_separation
        
        return control_vels


# Example usage
if __name__ == "__main__":
    # Simple SDF: sphere
    def sphere_sdf(points: np.ndarray) -> np.ndarray:
        """Simple sphere SDF with radius 2"""
        r = np.linalg.norm(points, axis=1)
        return r - 2.0
    
    # Create point distributor
    distributor = PointDistributor(sphere_sdf)
    points = distributor.generate_points(8)
    print("Generated points shape:", points.shape)
    print("Points:\n", points)
    
    # Test APF controller
    current_poses = np.array([
        [0, 0, 0],
        [1, 0, 0],
        [0, 1, 0],
        [-1, 0, 0]
    ])
    
    goal_poses = np.array([
        [2, 0, 0],
        [0, 2, 0],
        [-2, 0, 0],
        [0, -2, 0]
    ])
    
    controller = APFSwarmController(max_vel=1.0)
    assigned_goals = controller.distribute_goals(current_poses, goal_poses)
    print("\nAssigned goals shape:", assigned_goals.shape)
    
    velocities = controller.get_control(current_poses)
    print("Control velocities shape:", velocities.shape)
    print("Velocities:\n", velocities)
