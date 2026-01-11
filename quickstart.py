#!/usr/bin/env python3
"""
Quick start script for LLM AirSim Swarm Controller
Run this script to get started quickly
"""

import os
import sys
import argparse
from pathlib import Path


def setup_environment():
    """Setup Python path and environment"""
    # Add current directory and src package to path
    current_dir = Path(__file__).parent
    src_dir = current_dir / "src"
    sys.path.insert(0, str(current_dir))
    if src_dir.exists():
        sys.path.insert(0, str(src_dir))
    
    print(f"Working directory: {current_dir}")


def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        "numpy",
        "scipy",
        "sklearn",
        "openai",
        "airsim",
    ]
    
    print("\nChecking dependencies...")
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} (NOT INSTALLED)")
            missing.append(package)
    
    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        print("Install with: pip install -r requirements.txt")
        return False
    
    print("\n✓ All dependencies satisfied")
    return True


def check_api_keys():
    """Check if API keys are configured"""
    print("\nChecking API configuration...")
    
    api_key = os.getenv("OPENAI_API_KEY", "")
    if api_key:
        print(f"  ✓ OPENAI_API_KEY configured")
    else:
        print(f"  ⚠ OPENAI_API_KEY not set")
        print("    Set it with: export OPENAI_API_KEY='your-key'")
        return False
    
    return True


def test_llm_connection():
    """Test connection to LLM API"""
    print("\nTesting LLM API connection...")
    
    try:
        from src.llm_client import LLMClient
        
        client = LLMClient()
        print("  Testing API call...")
        
        response = client.chat_completion([
            {"role": "user", "content": "Say 'Hello' in one word"}
        ])
        
        if response:
            print(f"  ✓ LLM API working")
            print(f"    Response: {response}")
            return True
        else:
            print(f"  ✗ No response from LLM")
            return False
            
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_airsim_connection():
    """Test connection to AirSim"""
    print("\nTesting AirSim connection...")
    
    try:
        import airsim
        import time
        
        print("  Trying to connect to AirSim at 127.0.0.1...")
        client = airsim.MultirotorClient(ip="127.0.0.1", timeout_value=5)
        
        print("  Confirming connection...")
        client.confirmConnection()
        
        print("  ✓ Connected to AirSim")
        
        # Try to ping a drone
        print("  Checking for drones...")
        try:
            client.enableApiControl(True, "Drone1")
            print("  ✓ Can communicate with Drone1")
        except:
            print("  ⚠ Could not enable API control (this is normal)")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Could not connect to AirSim: {e}")
        print("    Possible issues:")
        print("    - AirSim may not be running")
        print("    - AirSim may be frozen (try restarting)")
        print("    - settings.json may not be loaded properly")
        print("\n    Try: Restart AirSim and press Play in the simulation")
        return False


def run_interactive():
    """Run in interactive mode"""
    print("\n" + "="*70)
    print("Starting LLM AirSim Swarm Controller - Interactive Mode")
    print("="*70 + "\n")
    
    try:
        from src.integrated_controller import LLMAirSimSwarmController
        
        # Create list of 10 drone names
        drone_names = [f"Drone{i}" for i in range(1, 11)]
        
        print("Initializing controller...")
        controller = LLMAirSimSwarmController(
            drone_names=drone_names,
            verbose=True
        )
        
        # Explicitly test AirSim connection
        print("\nTesting AirSim connection...")
        try:
            positions = controller.swarm.get_positions()
            print(f"✓ Successfully connected to AirSim with {len(positions)} drones")
            print(f"  Drones: {', '.join(drone_names[:3])}...")
        except Exception as e:
            print(f"⚠ Warning: Could not verify AirSim connection: {e}")
            print("  Make sure AirSim is running with 10 drones configured")
        
        controller.interactive_mode()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


def run_example(example_num):
    """Run a specific example"""
    print("\n" + "="*70)
    print(f"Running Example {example_num}")
    print("="*70 + "\n")
    
    try:
        from examples import (
            example_basic_usage,
            example_multiple_shapes,
            example_custom_parameters,
            example_shape_descriptions,
            example_error_handling,
        )
        
        examples = {
            1: ("Basic Usage", example_basic_usage),
            2: ("Multiple Shapes", example_multiple_shapes),
            3: ("Custom Parameters", example_custom_parameters),
            4: ("Shape Descriptions", example_shape_descriptions),
            5: ("Error Handling", example_error_handling),
        }
        
        if example_num in examples:
            name, func = examples[example_num]
            func()
        else:
            print(f"Example {example_num} not found")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="LLM AirSim Swarm Controller Quick Start"
    )
    
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check dependencies and configuration"
    )
    
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test LLM and AirSim connections"
    )
    
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Run in interactive mode"
    )
    
    parser.add_argument(
        "--example",
        "-e",
        type=int,
        help="Run a specific example (1-5)"
    )
    
    args = parser.parse_args()
    
    # Setup
    setup_environment()
    
    # Check dependencies
    if args.check or (not args.test and not args.interactive and not args.example):
        if not check_dependencies():
            sys.exit(1)
        
        check_api_keys()
        
        if not args.check and not args.test and not args.interactive and not args.example:
            print("\nRun with --help to see available options")
            print("\nQuick start options:")
            print("  python quickstart.py --test      - Test connections")
            print("  python quickstart.py -i          - Interactive mode")
            print("  python quickstart.py -e 1        - Run example 1")
            sys.exit(0)
    
    # Test connections
    if args.test:
        if check_dependencies():
            test_llm_connection()
            test_airsim_connection()
        sys.exit(0)
    
    # Interactive mode
    if args.interactive:
        if check_dependencies():
            run_interactive()
        sys.exit(0)
    
    # Run example
    if args.example:
        if check_dependencies():
            run_example(args.example)
        sys.exit(0)


if __name__ == "__main__":
    main()
