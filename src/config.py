"""
Configuration module for LLM AirSim Swarm
"""

import os
from typing import Dict, Any

# ============ LLM Configuration ============
LLM_CONFIG = {
    # API Configuration - can be overridden by environment variables
    "api_key": os.getenv("OPENAI_API_KEY", ""),
    "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
    "model": os.getenv("LLM_MODEL", "gpt-3.5-turbo"),
    
    # Generation parameters
    "temperature": 0.7,
    "max_tokens": 1000,
}

# ============ AirSim Configuration ============
AIRSIM_CONFIG = {
    # Connection settings
    "ip": os.getenv("AIRSIM_IP", "127.0.0.1"),
    "port": 41451,  # Default AirSim port
    
    # Drone configuration
    "drones": {
        "Drone1": {"start_pos": [0, 0, 0]},
        "Drone2": {"start_pos": [1, 0, 0]},
        "Drone3": {"start_pos": [0, 1, 0]},
        "Drone4": {"start_pos": [-1, 0, 0]},
    },
    
    # Control parameters
    "takeoff_duration": 5.0,
    "control_rate_hz": 10,
    "max_velocity": 1.0,
}

# ============ Swarm Control Configuration ============
SWARM_CONTROL_CONFIG = {
    # APF parameters
    "p_cohesion": 1.0,
    "p_separation": 1.0,
    "p_alignment": 1.0,
    "max_vel": 1.0,
    "min_dist": 0.5,
    
    # Point distribution parameters
    "num_waypoints": 4,
    "num_samples": 1000,
    "distribution_method": "l-bfgs-b",
}

# ============ Logging Configuration ============
LOGGING_CONFIG = {
    "verbose": True,
    "log_file": "airsim_swarm_llm.log",
    "log_level": "INFO",
}


def get_config(section: str) -> Dict[str, Any]:
    """
    Get configuration section
    
    Args:
        section: Configuration section name
        
    Returns:
        Configuration dictionary
    """
    configs = {
        "llm": LLM_CONFIG,
        "airsim": AIRSIM_CONFIG,
        "swarm": SWARM_CONTROL_CONFIG,
        "logging": LOGGING_CONFIG,
    }
    
    return configs.get(section, {})


def update_config(section: str, key: str, value: Any):
    """
    Update configuration value
    
    Args:
        section: Configuration section name
        key: Configuration key
        value: New value
    """
    config = get_config(section)
    if config:
        config[key] = value


# Example: Load configuration
if __name__ == "__main__":
    print("LLM Config:", get_config("llm"))
    print("AirSim Config:", get_config("airsim"))
    print("Swarm Control Config:", get_config("swarm"))
