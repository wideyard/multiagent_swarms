#!/usr/bin/env python3
"""
RAG Workflow Demo - Complete example of Retrieval-Augmented Generation
with drone swarm control

This demo shows:
1. Building a knowledge base with domain knowledge
2. Retrieving relevant knowledge for queries
3. Enhancing LLM responses with retrieved context
4. Using RAG for drone mission planning

Usage:
    python rag_workflow_demo.py
"""

import os
import sys
import json
from pathlib import Path

# Add repo root to path
repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root))

try:
    from src.rag_system import QwenEmbedding, KnowledgeBase
    from src.llm_client import LLMClient
except ImportError as e:
    print(f"Error importing RAG modules: {e}")
    print("Please ensure DASHSCOPE_API_KEY is set in environment variables")
    sys.exit(1)


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def demo_1_initialize_rag():
    """Demo 1: Initialize RAG system with knowledge base"""
    print_section("DEMO 1: Initialize RAG System")
    
    print("\nStep 1: Initialize embedding model (Qwen)...")
    try:
        embedding_model = QwenEmbedding()
        print("  ✓ Embedding model initialized successfully")
    except Exception as e:
        print(f"  ✗ Error: {e}")
        print("    Make sure DASHSCOPE_API_KEY is set")
        return None
    
    print("\nStep 2: Create knowledge base...")
    kb = KnowledgeBase(embedding_model, "drone_swarm_kb")
    print(f"  ✓ Knowledge base created: {kb.name}")
    
    return embedding_model, kb


def demo_2_add_knowledge(kb: KnowledgeBase):
    """Demo 2: Add domain knowledge to the knowledge base"""
    print_section("DEMO 2: Add Domain Knowledge")
    
    # Sample domain knowledge documents
    knowledge_docs = [
        {
            "text": """
Drone Safety Requirements:
- Minimum separation distance between drones: 2.0 meters
- Maximum altitude for indoor flight: 5 meters
- Maximum altitude for outdoor flight: 120 meters
- Recommended separation during formation: 2-3 meters
- Emergency landing: activate when battery < 10%
""",
            "metadata": {"category": "safety", "priority": "high"}
        },
        {
            "text": """
Common Swarm Formations:
1. Circle Formation: Drones arranged in a circular pattern, best for 5-20 drones
2. Square Formation: Drones in rectangular grid, efficient for surveillance
3. Sphere Formation: 3D arrangement, requires altitude variation
4. Line Formation: Single or multiple rows, good for area coverage
5. V-Formation: Aerodynamic arrangement, reduces air resistance
""",
            "metadata": {"category": "formations", "priority": "high"}
        },
        {
            "text": """
Collision Avoidance Strategies:
- Artificial Potential Field (APF): Repulsion forces between drones
- Dynamic Window Approach: Predict future positions
- Velocity Obstacle: Calculate safe velocity ranges
- Master-Slave Formation: Central drone leads, others follow
- Decentralized Control: Each drone manages local avoidance
""",
            "metadata": {"category": "collision_avoidance", "priority": "medium"}
        },
        {
            "text": """
Drone Motor and Battery Information:
- Battery capacity: typically 2200-5000mAh
- Flight time per charge: 15-30 minutes
- Maximum takeoff weight: varies by model (500g-5kg)
- Motor KV rating: 700-1000 KV for typical drones
- Propeller size: 8-18 inches depending on weight class
""",
            "metadata": {"category": "hardware", "priority": "medium"}
        },
        {
            "text": """
Path Planning for Swarm:
- RRT (Rapidly-exploring Random Tree): Good for obstacle avoidance
- Potential Field Method: Smooth paths, computationally efficient
- A* Algorithm: Optimal paths, memory intensive
- Dubins Curve: Smooth curves with curvature limits
- Cooperative planning: Consider all drones simultaneously
""",
            "metadata": {"category": "path_planning", "priority": "medium"}
        },
    ]
    
    print(f"\nAdding {len(knowledge_docs)} domain knowledge documents...")
    for i, doc in enumerate(knowledge_docs, 1):
        try:
            kb.add_document(doc["text"], doc["metadata"])
            print(f"  ✓ Document {i} added: {doc['metadata']['category']}")
        except Exception as e:
            print(f"  ✗ Error adding document {i}: {e}")
    
    print(f"\n✓ Knowledge base now contains {len(kb.documents)} documents")
    return kb


def demo_3_retrieve_knowledge(kb: KnowledgeBase):
    """Demo 3: Retrieve relevant knowledge for queries"""
    print_section("DEMO 3: Retrieve Relevant Knowledge")
    
    queries = [
        "What is the minimum distance between drones?",
        "What formations can I use for 10 drones?",
        "How can drones avoid collisions?",
        "How long can a drone fly on one battery charge?",
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\nQuery {i}: \"{query}\"")
        print("-" * 70)
        
        try:
            results = kb.search(query, top_k=2)
            
            if results:
                for j, (doc, score, metadata) in enumerate(results, 1):
                    print(f"\n  Match {j} (relevance: {score:.2f}):")
                    print(f"  Category: {metadata.get('category', 'unknown')}")
                    print(f"  Content: {doc[:200]}...")
            else:
                print("  No relevant documents found")
        except Exception as e:
            print(f"  ✗ Error during search: {e}")


def demo_4_rag_enhanced_response(kb: KnowledgeBase):
    """Demo 4: Generate LLM response with RAG context"""
    print_section("DEMO 4: Generate RAG-Enhanced Responses")
    
    # Initialize LLM client
    print("\nInitializing LLM client...")
    try:
        llm_client = LLMClient()
        print("  ✓ LLM client initialized")
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return
    
    # Example queries for RAG-enhanced responses
    rag_queries = [
        "I want to create a swarm of 8 drones. What formation would you recommend and why?",
        "What safety considerations should I keep in mind for drone swarm operations?",
    ]
    
    for i, user_query in enumerate(rag_queries, 1):
        print(f"\nQuery {i}: \"{user_query}\"")
        print("-" * 70)
        
        try:
            # Retrieve relevant knowledge
            print("\nRetrieving relevant knowledge...")
            knowledge_results = kb.search(user_query, top_k=3)
            
            # Build context from retrieved knowledge
            context = "Based on domain knowledge:\n"
            if knowledge_results:
                for j, (doc, score, meta) in enumerate(knowledge_results, 1):
                    context += f"\n{j}. [{meta.get('category', 'general')}] {doc[:150]}..."
            else:
                context = "No specific domain knowledge found."
            
            print(f"Retrieved context:\n{context[:300]}...")
            
            # Prepare enhanced prompt for LLM
            enhanced_prompt = f"""
You are a drone swarm expert. Use the following domain knowledge to answer the user's query.

Domain Knowledge:
{context}

User Query: {user_query}

Provide a detailed, practical answer based on the domain knowledge above.
"""
            
            print(f"\nGenerating LLM response with RAG context...")
            # In actual use, you would call:
            # response = llm_client.chat_completion([
            #     {"role": "system", "content": "You are a drone swarm expert."},
            #     {"role": "user", "content": enhanced_prompt}
            # ])
            # print(f"LLM Response:\n{response}")
            
            # For demo, show the enhanced prompt
            print("\n[Mock Response - would use real LLM in production]")
            print("System would use this enhanced prompt to generate response:")
            print(enhanced_prompt[:400] + "...")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")


def demo_5_mission_planning(kb: KnowledgeBase):
    """Demo 5: Use RAG for mission planning"""
    print_section("DEMO 5: RAG-Assisted Mission Planning")
    
    print("\nScenario: Plan a drone swarm mission for surveillance")
    print("-" * 70)
    
    mission_requirements = {
        "num_drones": 10,
        "duration": "30 minutes",
        "area": "100x100 meters",
        "obstacles": "buildings and trees",
        "safety_critical": True,
    }
    
    print(f"\nMission Requirements:")
    for key, value in mission_requirements.items():
        print(f"  • {key}: {value}")
    
    # Build queries for mission planning
    mission_queries = [
        "What formation is best for area surveillance with 10 drones?",
        "How should drones handle collision avoidance around obstacles?",
        "What is the recommended separation distance for this mission?",
    ]
    
    print(f"\nRetrieval-Augmented Planning:")
    for i, query in enumerate(mission_queries, 1):
        print(f"\n  {i}. {query}")
        try:
            results = kb.search(query, top_k=1)
            if results:
                doc, score, meta = results[0]
                print(f"     Relevant knowledge (score: {score:.2f}): {doc[:120]}...")
        except Exception as e:
            print(f"     ✗ Error: {e}")
    
    print("\n✓ Mission planning with RAG context complete")
    print("\nNext steps:")
    print("  1. Generate detailed waypoints using LLM with RAG context")
    print("  2. Validate plan against retrieved safety requirements")
    print("  3. Execute mission in AirSim with RAG-informed parameters")


def demo_6_save_knowledge_base(kb: KnowledgeBase):
    """Demo 6: Save and reload knowledge base"""
    print_section("DEMO 6: Persist Knowledge Base")
    
    print(f"\nCurrent knowledge base: {kb.name}")
    print(f"Documents: {len(kb.documents)}")
    
    try:
        print("\nSaving knowledge base to cache...")
        kb.save_to_cache()
        print(f"  ✓ Saved to {kb.cache_file}")
        
        # Show cache file info
        if kb.cache_file.exists():
            file_size = kb.cache_file.stat().st_size / 1024
            print(f"  • Cache file size: {file_size:.2f} KB")
            print(f"  • For future use: KB will auto-load from cache")
    except Exception as e:
        print(f"  ✗ Error saving: {e}")


def main():
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " " * 15 + "RAG WORKFLOW DEMONSTRATION" + " " * 27 + "║")
    print("║" + " " * 12 + "Retrieval-Augmented Generation for Drone Swarms" + " " * 10 + "║")
    print("╚" + "="*68 + "╝")
    
    print("""
This demo shows how RAG enhances LLM-based drone swarm control:
  1. Initialize embedding model and knowledge base
  2. Add domain knowledge (safety, formations, collision avoidance)
  3. Retrieve relevant knowledge for specific queries
  4. Generate LLM responses augmented with retrieved context
  5. Use RAG for intelligent mission planning
  6. Persist knowledge base for reuse
    """)
    
    # Run demonstrations
    print("\nStarting demonstrations...")
    
    # Demo 1: Initialize
    result = demo_1_initialize_rag()
    if result is None:
        print("\n✗ Failed to initialize RAG system. Aborting.")
        return
    
    embedding_model, kb = result
    
    # Demo 2: Add knowledge
    demo_2_add_knowledge(kb)
    
    # Demo 3: Retrieve knowledge
    demo_3_retrieve_knowledge(kb)
    
    # Demo 4: RAG-enhanced responses
    demo_4_rag_enhanced_response(kb)
    
    # Demo 5: Mission planning
    demo_5_mission_planning(kb)
    
    # Demo 6: Save knowledge base
    demo_6_save_knowledge_base(kb)
    
    # Final summary
    print_section("SUMMARY")
    print("""
What RAG Does:
  ✓ Retrieves relevant domain knowledge for each query
  ✓ Provides context to LLM for better responses
  ✓ Reduces hallucinations with grounded information
  ✓ Makes LLM expertise domain-specific

Expected Benefits for Drone Swarms:
  ✓ Safer mission planning (considers documented safety rules)
  ✓ Better formation selection (uses known best practices)
  ✓ Smarter collision avoidance (retrieves proven strategies)
  ✓ More reliable code generation (grounded in domain knowledge)

Next Steps:
  1. Run: python rag_workflow_demo.py
  2. Customize knowledge base with your domain documents
  3. Integrate with fly_to_goals.py for RAG-enhanced missions
  4. Monitor LLM outputs to verify knowledge is being used correctly
    """)
    
    print("\n✓ RAG Workflow Demo Completed!\n")


if __name__ == "__main__":
    main()
