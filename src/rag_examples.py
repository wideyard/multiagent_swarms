#!/usr/bin/env python3
"""
Examples of using RAG system for drone swarm control
Demonstrates how RAG enhances task understanding and execution
"""

import os
from rag_system import QwenEmbedding, KnowledgeBase, RAGLLMClient
from rag_integration import RAGEnhancedLLMClient, create_rag_enhanced_controller


def example_1_basic_rag():
    """Example 1: Basic RAG with knowledge retrieval"""
    print("\n" + "="*70)
    print("Example 1: Basic RAG Knowledge Retrieval")
    print("="*70)
    
    try:
        # Initialize embedding model
        embedding = QwenEmbedding()
        
        # Create knowledge base
        kb = KnowledgeBase(embedding, "drone_kb_example1")
        
        # Add domain knowledge
        kb.add_document("""
        Drone swarm formations:
        - Grid formation: Drones arranged in rows and columns, uniform spacing
        - Circle formation: Drones arranged around a center point
        - V-formation: Drones arranged in V shape, energy efficient
        - Cube formation: 3D arrangement of drones
        """, {"type": "formation"})
        
        kb.add_document("""
        Safe drone spacing:
        - Minimum distance: 0.5 meters
        - Recommended distance: 2-3 meters
        - Maximum drones in 10x10m area: 20-30 drones
        """, {"type": "safety"})
        
        kb.add_document("""
        Collision avoidance methods:
        - Artificial Potential Field (APF): Repulsive forces between drones
        - Velocity Obstacles: Predict and avoid future collisions
        - Distributed Control: Each drone makes local decisions
        """, {"type": "algorithms"})
        
        # Test retrieval
        print("\nKnowledge Base Statistics:")
        stats = kb.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print("\nTesting retrieval for query: 'How should drones maintain safe distance?'")
        results = kb.search("How should drones maintain safe distance?", top_k=2)
        
        print(f"\nFound {len(results)} relevant documents:")
        for i, (doc, score, meta) in enumerate(results, 1):
            print(f"\n  Document {i} (similarity: {score:.3f})")
            if meta and 'type' in meta:
                print(f"    Type: {meta['type']}")
            print(f"    Content: {doc[:100]}...")
        
        print("\n✓ Example 1 completed successfully")
        
    except ValueError as e:
        print(f"⚠ Skipping example: {e}")


def example_2_rag_enhanced_llm():
    """Example 2: RAG-enhanced LLM for task understanding"""
    print("\n" + "="*70)
    print("Example 2: RAG-Enhanced LLM Task Understanding")
    print("="*70)
    
    try:
        # Create RAG-enhanced LLM client
        rag_llm = RAGEnhancedLLMClient(use_rag=True)
        
        # Build knowledge base
        print("\nBuilding knowledge base...")
        
        # Test LLM response with knowledge enhancement
        test_prompt = """
        I want to create a drone swarm that forms a sphere shape.
        The sphere should have 10 drones. What should I consider for this task?
        """
        
        print(f"\nUser query: {test_prompt.strip()}")
        print("\nGenerating response with RAG enhancement...")
        
        response = rag_llm.chat_completion([
            {"role": "user", "content": test_prompt}
        ])
        
        print(f"\nLLM Response:\n{response}")
        print("\n✓ Example 2 completed successfully")
        
    except ValueError as e:
        print(f"⚠ Skipping example: {e}")


def example_3_rag_sdf_generation():
    """Example 3: RAG-enhanced SDF code generation"""
    print("\n" + "="*70)
    print("Example 3: RAG-Enhanced SDF Code Generation")
    print("="*70)
    
    try:
        # Create RAG-enhanced LLM client
        rag_llm = RAGEnhancedLLMClient(use_rag=True)
        
        print("\nGenerating SDF code for: 'A cube with 2 unit side length'")
        print("(Using RAG to enhance code quality)...\n")
        
        sdf_code = rag_llm.generate_sdf_code("A cube with 2 unit side length")
        
        if sdf_code:
            print("Generated SDF Code:")
            print("-" * 70)
            print(sdf_code)
            print("-" * 70)
            print("\n✓ SDF code generated with RAG enhancement")
        else:
            print("⚠ No code generated")
        
        print("\n✓ Example 3 completed successfully")
        
    except ValueError as e:
        print(f"⚠ Skipping example: {e}")


def example_4_rag_controller():
    """Example 4: RAG-enhanced swarm controller"""
    print("\n" + "="*70)
    print("Example 4: RAG-Enhanced Swarm Controller")
    print("="*70)
    
    try:
        drone_names = [f"Drone{i}" for i in range(1, 6)]
        
        print(f"\nCreating RAG-enhanced controller with {len(drone_names)} drones...")
        controller = create_rag_enhanced_controller(drone_names, use_rag=True)
        
        print("✓ Controller created successfully")
        print(f"  Drones: {', '.join(drone_names)}")
        print("  RAG Enhancement: Enabled")
        print("  LLM Client: RAG-Enhanced")
        
        # Test shape understanding
        print("\nTesting task understanding...")
        task = "Create a pyramid formation with the drones"
        
        print(f"Task: {task}")
        print("Preparing mission...")
        
        success = controller.prepare_mission(task, num_points=len(drone_names))
        
        if success:
            print("✓ Mission prepared successfully")
            print(f"  Generated {controller.goal_positions.shape[0]} waypoints")
            print(f"  First waypoint: {controller.goal_positions[0]}")
        else:
            print("⚠ Mission preparation had issues (this is normal in test mode)")
        
        print("\n✓ Example 4 completed successfully")
        
    except Exception as e:
        print(f"⚠ Example 4 note: {e}")


def example_5_load_custom_knowledge():
    """Example 5: Load custom knowledge from file"""
    print("\n" + "="*70)
    print("Example 5: Loading Custom Knowledge Base")
    print("="*70)
    
    try:
        # Create a sample knowledge file
        sample_file = "sample_knowledge.txt"
        
        knowledge_content = """
        Drone Battery Management:
        A typical drone battery has:
        - Capacity: 1000-5000 mAh
        - Voltage: 7.4-14.8V
        - Flight time: 10-30 minutes
        - Charge time: 30-120 minutes
        
        Optimal battery level: 80-95% for long missions
        
        Waypoint Navigation:
        Drones can be programmed to:
        1. Follow GPS waypoints
        2. Use visual odometry
        3. Follow predefined paths
        4. Adapt paths dynamically
        
        Each waypoint includes:
        - Position (x, y, z)
        - Orientation (yaw angle)
        - Speed
        - Action (stop, rotate, etc)
        
        Drone Communication:
        - Ground station: High bandwidth, limited range
        - Inter-drone: Low bandwidth, mesh network
        - GPS: Position only, low bandwidth
        - Video stream: High bandwidth, limited drones
        """
        
        # Write sample file
        with open(sample_file, 'w') as f:
            f.write(knowledge_content)
        
        print(f"Created sample knowledge file: {sample_file}\n")
        
        # Load knowledge
        embedding = QwenEmbedding()
        kb = KnowledgeBase(embedding, "custom_kb")
        
        print("Loading knowledge from file...")
        kb.add_documents_from_file(sample_file, chunk_size=300)
        
        kb.save_to_cache()
        
        # Test retrieval
        print("\nTesting retrieval: 'How long can a drone fly?'")
        results = kb.search("How long can a drone fly?", top_k=1)
        
        if results:
            doc, score, meta = results[0]
            print(f"Found match (score: {score:.3f}):")
            print(f"  {doc[:150]}...")
        
        print("\n✓ Example 5 completed successfully")
        
        # Clean up
        import os
        if os.path.exists(sample_file):
            os.remove(sample_file)
            print(f"Cleaned up {sample_file}")
        
    except ValueError as e:
        print(f"⚠ Skipping example: {e}")
    except Exception as e:
        print(f"⚠ Example 5 note: {e}")


def main():
    """Run all examples"""
    print("\n" + "="*70)
    print("RAG System Examples for Drone Swarm Control")
    print("="*70)
    print("\nThese examples demonstrate how to use the RAG system to enhance")
    print("LLM understanding of drone swarm tasks and improve task execution.")
    
    # Check environment
    print("\nEnvironment Check:")
    if os.getenv("DASHSCOPE_API_KEY"):
        print("  ✓ DASHSCOPE_API_KEY configured")
    else:
        print("  ⚠ DASHSCOPE_API_KEY not configured (needed for embedding)")
    
    if os.getenv("OPENAI_API_KEY"):
        print("  ✓ OPENAI_API_KEY configured")
    else:
        print("  ⚠ OPENAI_API_KEY not configured (needed for LLM)")
    
    # Run examples
    example_1_basic_rag()
    example_2_rag_enhanced_llm()
    example_3_rag_sdf_generation()
    example_4_rag_controller()
    example_5_load_custom_knowledge()
    
    print("\n" + "="*70)
    print("All examples completed!")
    print("="*70)


if __name__ == "__main__":
    main()
