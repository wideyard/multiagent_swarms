#!/usr/bin/env python3
"""
Test SDF sampling and point distribution
"""

import numpy as np
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sdf_executor import SDFExecutor
from swarm_controller import PointDistributor


def test_cube_sampling():
    """Test sampling points on a cube"""
    print("="*70)
    print("Testing Cube Sampling")
    print("="*70)
    
    # Create a simple cube SDF
    code = """
from sdf import *

f = box(1)
"""
    
    print("\nSDF Code:")
    print(code)
    
    # Execute SDF
    executor = SDFExecutor()
    sdf_func = executor.create_sdf_function(code)
    
    if sdf_func is None:
        print("Failed to create SDF function")
        return
    
    print("✓ SDF function created")
    
    # Test some points
    test_points = np.array([
        [0, 0, 0],      # Center
        [0.5, 0.5, 0.5], # Corner
        [0, 0, 0.5],    # Face center
        [2, 2, 2],      # Outside
    ])
    
    print("\nTesting SDF values:")
    for i, point in enumerate(test_points):
        sdf_val = sdf_func(point.reshape(1, 3))
        sdf_scalar = float(sdf_val.flat[0])  # Use flat[0] to avoid deprecation warning
        status = "inside" if sdf_scalar < 0 else ("surface" if abs(sdf_scalar) < 0.01 else "outside")
        print(f"  Point {point}: SDF = {sdf_scalar:.4f} ({status})")
    
    # Generate points
    print("\nGenerating 10 waypoints...")
    distributor = PointDistributor(sdf_func)
    waypoints = distributor.generate_points(10)
    
    print(f"\nGenerated waypoints (shape: {waypoints.shape}):")
    for i, wp in enumerate(waypoints):
        sdf_val = sdf_func(wp.reshape(1, 3))
        print(f"  Waypoint {i+1}: [{wp[0]:6.3f}, {wp[1]:6.3f}, {wp[2]:6.3f}], SDF = {float(sdf_val.flat[0]):6.3f}")
    
    # Check uniqueness
    unique_waypoints = np.unique(waypoints, axis=0)
    print(f"\nUnique waypoints: {len(unique_waypoints)} / {len(waypoints)}")
    
    # Check distribution
    from scipy.spatial.distance import pdist
    if len(waypoints) > 1:
        distances = pdist(waypoints)
        print(f"Distance statistics:")
        print(f"  Min: {distances.min():.3f}")
        print(f"  Max: {distances.max():.3f}")
        print(f"  Mean: {distances.mean():.3f}")
        print(f"  Std: {distances.std():.3f}")


def test_sphere_sampling():
    """Test sampling points on a sphere"""
    print("\n" + "="*70)
    print("Testing Sphere Sampling")
    print("="*70)
    
    # Create a simple sphere SDF
    code = """
from sdf import *

f = sphere(2)
"""
    
    print("\nSDF Code:")
    print(code)
    
    # Execute SDF
    executor = SDFExecutor()
    sdf_func = executor.create_sdf_function(code)
    
    if sdf_func is None:
        print("Failed to create SDF function")
        return
    
    print("✓ SDF function created")
    
    # Generate points
    print("\nGenerating 10 waypoints...")
    distributor = PointDistributor(sdf_func)
    waypoints = distributor.generate_points(10)
    
    print(f"\nGenerated waypoints (shape: {waypoints.shape}):")
    for i, wp in enumerate(waypoints):
        sdf_val = sdf_func(wp.reshape(1, 3))
        distance = np.linalg.norm(wp)
        print(f"  Waypoint {i+1}: [{wp[0]:6.3f}, {wp[1]:6.3f}, {wp[2]:6.3f}], SDF = {float(sdf_val.flat[0]):6.3f}, dist = {distance:.3f}")
    
    # Check uniqueness
    unique_waypoints = np.unique(waypoints, axis=0)
    print(f"\nUnique waypoints: {len(unique_waypoints)} / {len(waypoints)}")


def test_complex_shape():
    """Test sampling points on a complex shape"""
    print("\n" + "="*70)
    print("Testing Complex Shape (Torus)")
    print("="*70)
    
    # Create a torus SDF
    code = """
from sdf import *

f = torus(2, 0.5)
"""
    
    print("\nSDF Code:")
    print(code)
    
    # Execute SDF
    executor = SDFExecutor()
    sdf_func = executor.create_sdf_function(code)
    
    if sdf_func is None:
        print("Failed to create SDF function")
        return
    
    print("✓ SDF function created")
    
    # Generate points
    print("\nGenerating 10 waypoints...")
    distributor = PointDistributor(sdf_func)
    waypoints = distributor.generate_points(10)
    
    print(f"\nGenerated waypoints (shape: {waypoints.shape}):")
    for i, wp in enumerate(waypoints):
        sdf_val = sdf_func(wp.reshape(1, 3))
        print(f"  Waypoint {i+1}: [{wp[0]:6.3f}, {wp[1]:6.3f}, {wp[2]:6.3f}], SDF = {float(sdf_val.flat[0]):6.3f}")
    
    # Check uniqueness
    unique_waypoints = np.unique(waypoints, axis=0)
    print(f"\nUnique waypoints: {len(unique_waypoints)} / {len(waypoints)}")


if __name__ == "__main__":
    try:
        test_cube_sampling()
        test_sphere_sampling()
        test_complex_shape()
        
        print("\n" + "="*70)
        print("All tests completed!")
        print("="*70)
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
