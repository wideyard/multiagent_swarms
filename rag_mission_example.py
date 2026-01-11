#!/usr/bin/env python3
"""
Practical RAG Example: Use RAG to plan and execute drone swarm missions

This script demonstrates:
1. Building a domain knowledge base for drone operations
2. Using RAG to generate mission-specific waypoints
3. Executing the mission with RAG-informed parameters

Usage:
    python rag_mission_example.py <shape_description>
    
Example:
    python rag_mission_example.py "pentagon formation with 10 drones"
"""

import sys
import json
import os
from pathlib import Path

repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root))

from src.rag_system import QwenEmbedding, KnowledgeBase


def build_drone_knowledge_base(embedding_model):
    """Build a comprehensive knowledge base for drone operations"""
    
    print("Building drone operations knowledge base...")
    kb = KnowledgeBase(embedding_model, "drone_operations_kb")
    
    # Clear existing documents for fresh start
    kb.documents = []
    kb.embeddings = []
    kb.metadata = []
    
    knowledge_documents = [
        {
            "text": """
FORMATION SPECIFICATIONS FOR 10 DRONES:
- Circle: radius 5-10m, all drones at same altitude 5-10m
  * Advantages: Easy to monitor, good for surveillance
  * Minimum spacing: 2m
  * Control: APF with cohesion=2.0, separation=1.0
  
- Pentagon: 10 drones arranged in 2 rings (5+5)
  * Outer ring: 5 drones in circle, radius 8m
  * Inner ring: 5 drones in circle, radius 4m
  * All at 5m altitude
  * Best for balanced visibility
  
- Square Grid: 10 drones in 3x3+1 grid
  * Spacing: 3-4 meters between drones
  * Altitude: 5-10 meters
  * Best for area coverage
  
- 3D Sphere: 10 drones distributed on sphere surface
  * Radius: 6-8 meters
  * Center altitude: 5-10 meters
  * Requires altitude variation 2-8 meters
""",
            "metadata": {"topic": "formation_planning", "priority": 5}
        },
        {
            "text": """
SAFETY PARAMETERS FOR 10-DRONE SWARMS:
- Minimum separation distance: 2.0 meters (critical)
- Recommended separation: 3.0 meters (optimal)
- Maximum velocity: 2.0 m/s (safe operation)
- Maximum acceleration: 1.0 m/s²
- Arrival threshold: 0.5 meters
- Control update frequency: 2 Hz (dt=0.5s)
- Separation force scaling: inverse-distance weighted
  * Applied within 2-meter radius
  * Scales to 0.2 (20%) near goal (< 1m)
  * Ensures smooth final approach
""",
            "metadata": {"topic": "safety_parameters", "priority": 5}
        },
        {
            "text": """
COLLISION AVOIDANCE FOR SIMULTANEOUS FLIGHT:
- Artificial Potential Field (APF) Method:
  * Cohesion force: attracts drone toward goal (weight: 2.0)
  * Separation force: repels from neighbors (weight: 1.0)
  * Combined: V_total = 2.0*V_cohesion + 1.0*V_separation
  
- Predictive Collision Detection:
  * Check pairwise distances at current + 1 step
  * If distance < 1.5m, scale velocities down by 20-30%
  * Prevents close approaches before they happen
  
- Dynamic Separation Scaling:
  * Near goal (< 1m distance): reduce separation by 80%
  * Medium range (1-3m): full separation force
  * Far from goal (> 3m): normal forces
  
- Recommended Parameters:
  * p_cohesion = 2.0, p_separation = 1.0
  * min_dist = 2.0 meters
  * max_vel = 2.0 m/s
  * arrival_thresh = 0.5 m
""",
            "metadata": {"topic": "collision_avoidance", "priority": 5}
        },
        {
            "text": """
LLM CODE GENERATION FOR FORMATIONS:
- SDF (Signed Distance Function) method:
  * Generate Python code defining formation geometry
  * Sample points from SDF to get waypoints
  * Works for: circles, spheres, cubes, custom shapes
  
- Edge Point Method:
  * Ask LLM to generate formation edge points directly
  * Return as JSON array of [x, y, z] coordinates
  * Faster than SDF, no code execution needed
  
- SVG Method:
  * LLM generates SVG drawing of formation
  * Parse SVG path to extract contour points
  * Uniformly resample for even spacing
  * Best for planar formations
  
- Recommended approach for 10 drones:
  * Try Edge method first (fastest)
  * Fallback to SVG method
  * Final fallback to SDF method
""",
            "metadata": {"topic": "waypoint_generation", "priority": 4}
        },
        {
            "text": """
APF CONTROLLER PARAMETERS FOR DIFFERENT SCENARIOS:
- Sparse formations (large spacing):
  * p_cohesion: 2.0-3.0 (strong goal attraction)
  * p_separation: 0.5-1.0 (light repulsion)
  * min_dist: 3.0-5.0 meters
  
- Dense formations (tight spacing):
  * p_cohesion: 1.5-2.0
  * p_separation: 1.5-2.0 (strong repulsion)
  * min_dist: 2.0-3.0 meters
  
- Dynamic adjustments:
  * Increase p_cohesion if drones lag behind
  * Increase p_separation if collisions occur
  * Reduce max_vel if unstable
  
- Tuning tips:
  * Start conservative, gradually increase speed
  * Monitor distance between drones
  * Watch for oscillations around goal
  * Adjust arrival_thresh based on mission tolerance
""",
            "metadata": {"topic": "apf_tuning", "priority": 3}
        },
        {
            "text": """
MISSION EXECUTION WORKFLOW:
1. Load drone initial positions from settings.json
   - Each drone starts at specific [x, y, z] position
   - AirSim uses NED coordinate system
   
2. Generate formation waypoints
   - Use LLM/SDF/SVG to create goal positions
   - Transform to NED coordinates
   - Ensure altitude is set (usually 5-10m)
   
3. Assign drones to goals (nearest-unique algorithm)
   - Compute distances from each drone to each goal
   - Sort drones by descending min_distance
   - Greedily assign nearest unassigned goal
   - Prevents long-distance assignments
   
4. Arm and takeoff all drones simultaneously
   - Call arm_all() on swarm controller
   - Call takeoff_all(altitude) to launch
   - Wait 2-3 seconds for stabilization
   
5. Run APF control loop
   - Update positions via get_positions()
   - Compute control velocities via apf_controller.get_control()
   - Send velocity commands via set_velocities()
   - Check arrival conditions
   - Continue until all drones within 0.5m of goal
   
6. Hover at goal positions
   - Send zero velocity commands
   - Wait for user input to begin landing
   - Allows time for observation/photos
   
7. Land and disarm
   - Call land_all() for simultaneous landing
   - Call disarm_all() when all landed
   - Mission complete
""",
            "metadata": {"topic": "mission_workflow", "priority": 5}
        },
    ]
    
    for doc in knowledge_documents:
        kb.add_document(doc["text"], doc["metadata"])
    
    print(f"✓ Knowledge base built with {len(kb.documents)} documents")
    return kb


def query_knowledge_base(kb, query: str, top_k: int = 3):
    """Query the knowledge base and return results"""
    print(f"\nQuerying: \"{query}\"")
    print("-" * 70)
    
    try:
        results = kb.search(query, top_k=top_k)
        
        if not results:
            print("No relevant knowledge found.")
            return []
        
        print(f"Found {len(results)} relevant documents:\n")
        for i, (text, score, metadata) in enumerate(results, 1):
            print(f"Match {i} (relevance: {score:.3f}) [{metadata.get('topic', 'general')}]:")
            print(text[:300] + "...\n")
        
        return results
    except Exception as e:
        print(f"✗ Error querying knowledge base: {e}")
        return []


def main():
    print("\n" + "="*70)
    print("  RAG-ASSISTED DRONE SWARM MISSION PLANNING")
    print("="*70)
    
    # Initialize RAG system
    print("\n1. Initializing RAG system...")
    try:
        embedding_model = QwenEmbedding()
        print("   ✓ Embedding model initialized")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        print("   Please set DASHSCOPE_API_KEY environment variable")
        return
    
    # Build knowledge base
    print("\n2. Building knowledge base...")
    kb = build_drone_knowledge_base(embedding_model)
    
    # Example mission planning queries
    print("\n3. Demonstrating RAG-assisted mission planning...")
    
    queries = [
        "How should I configure APF controller for 10 drones in a circle formation?",
        "What safety parameters should I use for simultaneous drone flight?",
        "How does the assignment algorithm work for matching drones to goal positions?",
        "What is the complete mission execution workflow?",
    ]
    
    all_results = {}
    for query in queries:
        results = query_knowledge_base(kb, query, top_k=2)
        all_results[query] = results
    
    # Generate mission summary
    print("\n4. Mission Planning Summary")
    print("="*70)
    
    summary = """
RECOMMENDED MISSION CONFIGURATION FOR 10 DRONES:

Formation: Circle with 5m radius at 5m altitude

Safety Parameters:
  • Min separation distance: 2.0 meters
  • Max velocity: 2.0 m/s
  • Arrival threshold: 0.5 meters
  • Control update rate: 2 Hz

APF Controller Settings:
  • p_cohesion: 2.0 (goal attraction strength)
  • p_separation: 1.0 (obstacle/neighbor repulsion)
  • min_dist: 2.0 meters (separation zone radius)

Workflow:
  1. Load drone positions from settings.json
  2. Generate circle waypoints (10 points around circumference)
  3. Assign drones using nearest-unique algorithm
  4. Arm all drones simultaneously
  5. Takeoff to 5m altitude
  6. Run APF control loop until arrival
  7. Hover at positions (await user input)
  8. Land and disarm

Expected Behavior:
  ✓ All drones launch together
  ✓ Move toward assigned goals while maintaining separation
  ✓ Avoid collisions via APF repulsion forces
  ✓ Arrive at formation positions within 60 seconds
  ✓ Hover stably at goals
  ✓ Descend together for landing

To Run This Mission:
  python fly_to_goals.py <path_to_goals_json>
"""
    
    print(summary)
    
    # Save configuration
    config_file = "rag_mission_config.json"
    config = {
        "mission_type": "circle_formation_10_drones",
        "formation": {
            "name": "circle",
            "radius": 5.0,
            "altitude": 5.0,
            "num_drones": 10,
        },
        "safety_parameters": {
            "min_separation": 2.0,
            "max_velocity": 2.0,
            "arrival_threshold": 0.5,
            "control_update_hz": 2.0,
        },
        "apf_controller": {
            "p_cohesion": 2.0,
            "p_separation": 1.0,
            "min_dist": 2.0,
        },
        "knowledge_base": f"Using {len(kb.documents)} domain documents for guidance",
    }
    
    print(f"\n5. Saving configuration to {config_file}...")
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"   ✓ Saved: {config_file}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n" + "="*70)
    print("✓ RAG-Assisted Mission Planning Complete!")
    print("="*70)
    print("""
Next steps:
1. Generate waypoints: python rag_quickstart.py
2. Execute mission: python fly_to_goals.py outputs/goals_<timestamp>.json
3. Monitor drone positions and adjust parameters if needed

For more information:
- See docs/RAG_README.md for detailed documentation
- Check src/rag_system.py for implementation details
- Review fly_to_goals.py for actual execution code
    """)


if __name__ == "__main__":
    main()
