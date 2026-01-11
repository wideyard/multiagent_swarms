"""
Example usage of the LLM AirSim Swarm Controller
Demonstrates the complete pipeline: shape description -> waypoint generation -> swarm control
"""

import time
from src.integrated_controller import LLMAirSimSwarmController


def example_basic_usage():
    """Basic example: single shape and mission"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Usage - Simple Shape")
    print("="*70 + "\n")
    
    # Configure drones
    drone_names = ["Drone1", "Drone2", "Drone3", "Drone4"]
    
    # Create controller
    controller = LLMAirSimSwarmController(
        drone_names=drone_names,
        airsim_ip="127.0.0.1",
        verbose=True
    )
    
    # Prepare mission: describe shape -> generate waypoints
    shape_description = "A sphere with radius 2"
    print(f"\nPreparing mission for shape: '{shape_description}'")
    
    if controller.prepare_mission(shape_description, num_points=len(drone_names)):
        print("\n✓ Mission prepared successfully!")
        print("Waypoints generated and ready for execution")
        
        # In actual scenario, you would call:
        # controller.start_mission()
        # time.sleep(60)  # Let mission run
        # controller.stop_mission()
        
    else:
        print("✗ Failed to prepare mission")


def example_interactive_mode():
    """Interactive example: user-guided mission planning"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Interactive Mode - User-Guided Control")
    print("="*70 + "\n")
    
    drone_names = ["Drone1", "Drone2", "Drone3", "Drone4"]
    
    controller = LLMAirSimSwarmController(
        drone_names=drone_names,
        verbose=True
    )
    
    print("\nStarting interactive mode...")
    print("You can:")
    print("  - Describe shapes in natural language")
    print("  - Generate waypoints automatically")
    print("  - Control drone swarm movement")
    print("  - Monitor mission status\n")
    
    # Run interactive prompt
    controller.interactive_mode()


def example_multiple_shapes():
    """Advanced example: multiple sequential shapes"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Sequential Shapes - Building Complex Paths")
    print("="*70 + "\n")
    
    drone_names = ["Drone1", "Drone2", "Drone3", "Drone4"]
    
    controller = LLMAirSimSwarmController(
        drone_names=drone_names,
        verbose=True
    )
    
    # Define sequence of shapes
    shapes = [
        ("A cube", 4),
        ("A cylinder", 4),
        ("A pyramid", 3),
    ]
    
    for i, (shape_desc, num_waypoints) in enumerate(shapes):
        print(f"\n--- Shape {i+1}/{len(shapes)}: {shape_desc} ---")
        
        if controller.prepare_mission(shape_desc, num_points=num_waypoints):
            print(f"✓ Generated waypoints for: {shape_desc}")
            # In production:
            # controller.start_mission()
            # time.sleep(30)
            # controller.stop_mission()
        else:
            print(f"✗ Failed to generate waypoints for: {shape_desc}")


def example_custom_parameters():
    """Example with custom swarm parameters"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Custom Swarm Parameters")
    print("="*70 + "\n")
    
    drone_names = ["Drone1", "Drone2", "Drone3", "Drone4"]
    
    # Create controller with custom settings
    controller = LLMAirSimSwarmController(
        drone_names=drone_names,
        airsim_ip="127.0.0.1",
        verbose=True
    )
    
    # Customize APF parameters for slower, more cohesive movement
    controller.apf_controller.p_cohesion = 0.5  # Lower cohesion
    controller.apf_controller.p_separation = 2.0  # Higher separation
    controller.apf_controller.max_vel = 0.5  # Lower max velocity
    controller.apf_controller.min_dist = 1.0  # Larger minimum distance
    
    print("APF Controller customized:")
    print(f"  - Cohesion gain: {controller.apf_controller.p_cohesion}")
    print(f"  - Separation gain: {controller.apf_controller.p_separation}")
    print(f"  - Max velocity: {controller.apf_controller.max_vel}")
    print(f"  - Min distance: {controller.apf_controller.min_dist}")
    
    # Prepare and execute mission
    if controller.prepare_mission("A torus shape", num_points=len(drone_names)):
        print("\n✓ Mission prepared with custom parameters")
        # controller.start_mission()


def example_shape_descriptions():
    """Example with various shape descriptions"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Various Shape Descriptions")
    print("="*70 + "\n")
    
    drone_names = ["Drone1", "Drone2", "Drone3", "Drone4", "Drone5", "Drone6"]
    
    controller = LLMAirSimSwarmController(
        drone_names=drone_names,
        verbose=False  # Less verbose for this example
    )
    
    # Various shape descriptions
    descriptions = [
        "A sphere with radius 1.5",
        "A rounded box 2x2x2 with 0.25 radius corners",
        "A torus with major radius 2 and minor radius 0.5",
        "A pyramid shape",
        "A capsule shape 2 units tall with 0.5 radius",
    ]
    
    print("Testing shape generation with various descriptions:\n")
    
    for desc in descriptions:
        print(f"Shape: {desc}")
        if controller.describe_shape(desc):
            print("  ✓ SDF code generated")
            if controller.generate_waypoints(len(drone_names)):
                print(f"  ✓ Waypoints generated")
        else:
            print("  ✗ Failed")
        print()


def example_error_handling():
    """Example demonstrating error handling"""
    print("\n" + "="*70)
    print("EXAMPLE 6: Error Handling and Recovery")
    print("="*70 + "\n")
    
    drone_names = ["Drone1", "Drone2"]
    
    controller = LLMAirSimSwarmController(
        drone_names=drone_names,
        verbose=True
    )
    
    # Test 1: Generate waypoints without preparing mission (should fail gracefully)
    print("Test 1: Generate waypoints without shape")
    if controller.generate_waypoints(2):
        print("✗ Should have failed!")
    else:
        print("✓ Correctly handled missing SDF")
    
    print()
    
    # Test 2: Successful mission preparation
    print("Test 2: Proper mission preparation")
    if controller.prepare_mission("A cube", num_points=2):
        print("✓ Mission prepared successfully")
    
    print()
    
    # Test 3: Start mission with valid waypoints
    print("Test 3: Mission execution (simulated)")
    if controller.goal_positions is not None:
        print("✓ Ready to start mission")
        # Would call controller.start_mission() here


if __name__ == "__main__":
    import sys
    
    # Show all examples
    print("\n" + "="*70)
    print("LLM AirSim Swarm Controller - Usage Examples")
    print("="*70)
    
    examples = [
        ("1", "Basic Usage", example_basic_usage),
        ("2", "Interactive Mode", example_interactive_mode),
        ("3", "Sequential Shapes", example_multiple_shapes),
        ("4", "Custom Parameters", example_custom_parameters),
        ("5", "Shape Descriptions", example_shape_descriptions),
        ("6", "Error Handling", example_error_handling),
    ]
    
    print("\nAvailable examples:")
    for idx, name, _ in examples:
        print(f"  {idx}. {name}")
    print("  0. Run all examples")
    print("  q. Quit")
    
    choice = input("\nSelect example to run (or press Enter for all): ").strip().lower()
    
    if choice == "q":
        print("Exiting...")
    elif choice == "" or choice == "0":
        print("\nRunning all examples...\n")
        for idx, name, func in examples:
            try:
                func()
                time.sleep(1)
            except Exception as e:
                print(f"Error in {name}: {e}")
                import traceback
                traceback.print_exc()
    else:
        for idx, name, func in examples:
            if idx == choice:
                try:
                    func()
                except Exception as e:
                    print(f"Error: {e}")
                    import traceback
                    traceback.print_exc()
                break
