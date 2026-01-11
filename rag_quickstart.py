#!/usr/bin/env python3
"""
Quick guide to using RAG system with LLM AirSim Swarm Controller
"""

import os
import sys


def main():
    print("="*70)
    print("RAG System Quick Start Guide")
    print("="*70)
    
    # Check environment
    print("\n1. Environment Setup:")
    print("-" * 70)
    
    dashscope_key = os.getenv("DASHSCOPE_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    openai_base = os.getenv("OPENAI_BASE_URL")
    llm_model = os.getenv("LLM_MODEL")
    
    if dashscope_key:
        print("  ✓ DASHSCOPE_API_KEY configured (for Qwen embedding)")
    else:
        print("  ⚠ DASHSCOPE_API_KEY not set")
        print("    Set with: $env:DASHSCOPE_API_KEY = 'sk-xxx'")
    
    if openai_key and openai_base and llm_model:
        print("  ✓ OpenAI API configured (for LLM)")
    else:
        print("  ⚠ OpenAI API not fully configured")
        print("    Set OPENAI_API_KEY, OPENAI_BASE_URL, LLM_MODEL")
    
    # Usage examples
    print("\n2. Usage Examples:")
    print("-" * 70)
    
    print("""
Example 1: Use RAG system directly
---
from rag_system import QwenEmbedding, KnowledgeBase

embedding = QwenEmbedding()
kb = KnowledgeBase(embedding, "my_kb")

kb.add_document("Drones need 2m spacing for safety")
results = kb.search("How far apart should drones be?")
print(results)
---

Example 2: RAG-enhanced LLM chat
---
from rag_integration import RAGEnhancedLLMClient

rag_llm = RAGEnhancedLLMClient(use_rag=True)
response = rag_llm.chat_completion([
    {"role": "user", "content": "What formations can 10 drones make?"}
])
print(response)
---

Example 3: RAG-enhanced swarm controller
---
from rag_integration import create_rag_enhanced_controller

drone_names = [f"Drone{i}" for i in range(1, 11)]
controller = create_rag_enhanced_controller(drone_names, use_rag=True)

controller.prepare_mission("Form a cube with the drones")
# controller.start_mission()  # Uncomment to run
---

Example 4: Run all examples
---
python rag_examples.py
---
    """)
    
    # Key features
    print("\n3. Key Features:")
    print("-" * 70)
    print("""
  • Qwen Embedding Integration
    - Uses text-embedding-v4 model from DashScope
    - 1536-dimensional vectors
    - Automatic caching for efficiency
  
  • Knowledge Retrieval
    - Vector similarity search
    - Top-K document retrieval
    - Metadata tracking
  
  • Automatic Enhancement
    - RAG-enhanced chat
    - RAG-enhanced SDF generation
    - Seamless integration with existing controller
  
  • Persistence
    - Cache knowledge bases to disk
    - Load pre-computed embeddings
    - Avoid re-embedding costs
    """)
    
    # Next steps
    print("\n4. Next Steps:")
    print("-" * 70)
    print("""
  1. Set DASHSCOPE_API_KEY environment variable
  2. (Optional) Set OPENAI_API_KEY for LLM enhancement
  3. Run: python rag_examples.py
  4. Integrate with your application:
     
     from rag_integration import create_rag_enhanced_controller
     controller = create_rag_enhanced_controller(drone_names)
     controller.prepare_mission("Your task description")
    """)
    
    # Testing
    print("\n5. Testing RAG System:")
    print("-" * 70)
    
    try:
        print("\nTesting imports...")
        from rag_system import QwenEmbedding, KnowledgeBase
        print("  ✓ rag_system.py imported")
        
        from rag_integration import RAGEnhancedLLMClient
        print("  ✓ rag_integration.py imported")
        
        from rag_examples import (
            example_1_basic_rag,
            example_2_rag_enhanced_llm,
            example_3_rag_sdf_generation,
            example_4_rag_controller,
            example_5_load_custom_knowledge
        )
        print("  ✓ rag_examples.py imported")
        
        print("\n✓ All RAG modules loaded successfully!")
        
    except ImportError as e:
        print(f"  ✗ Import error: {e}")
        return 1
    
    # Documentation
    print("\n6. Documentation:")
    print("-" * 70)
    print("""
  Main documentation: RAG_README.md
  
  Quick reference:
  - QwenEmbedding: Qwen embedding wrapper
  - KnowledgeBase: Vector database for documents
  - RAGLLMClient: Basic RAG client
  - RAGEnhancedLLMClient: Integrated with existing LLM client
  - create_rag_enhanced_controller: Factory function for controller
    """)
    
    print("\n" + "="*70)
    print("RAG System Ready!")
    print("="*70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
