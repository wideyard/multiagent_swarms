#!/usr/bin/env python3
"""
Simple launcher for LLM AirSim Swarm Controller
Just import this module and you're ready to go!

Usage:
    from launcher import controller, examples
    
    # Quick start
    controller.LLMAirSimSwarmController(["Drone1", "Drone2"])
    
    # Or run examples
    examples.example_basic_usage()
"""

__version__ = "1.0.0"

# Import main components
from integrated_controller import LLMAirSimSwarmController
from llm_client import LLMClient, SDFGenerator
from airsim_controller import AirSimDroneController, AirSimSwarmController
from swarm_controller import PointDistributor, APFSwarmController
from sdf_executor import SDFExecutor
from config import get_config, update_config
import examples
import diagnose
import quickstart

# Convenience functions
def create_controller(drone_names, verbose=True):
    """Quick way to create a controller"""
    return LLMAirSimSwarmController(
        drone_names=drone_names,
        verbose=verbose
    )


def run_diagnostic():
    """Run diagnostic tool"""
    diagnose.main()


def show_examples():
    """Show available examples"""
    import inspect
    
    print("Available examples:")
    for name, obj in inspect.getmembers(examples):
        if name.startswith("example_"):
            print(f"  - {name}")


def run_example(example_num):
    """Run a specific example"""
    quickstart.run_example(example_num)


# Command-line interface
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "diagnose":
            run_diagnostic()
        elif command == "examples":
            show_examples()
        elif command.startswith("example"):
            try:
                num = int(sys.argv[2])
                run_example(num)
            except:
                print("Usage: python launcher.py example <number>")
        else:
            print(f"Unknown command: {command}")
    else:
        print(__doc__)
