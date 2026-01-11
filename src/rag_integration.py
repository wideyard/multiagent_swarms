"""
Integration of RAG system with LLM AirSim Swarm Controller
Enhances task understanding and shape generation with domain knowledge
"""

from .rag_system import QwenEmbedding, KnowledgeBase, RAGLLMClient
from .llm_client import LLMClient, SDFGenerator
import os


class RAGEnhancedLLMClient(LLMClient):
    """
    Extended LLMClient with RAG capabilities
    Automatically enhances prompts with relevant domain knowledge
    """
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None,
                 use_rag: bool = True, knowledge_base: KnowledgeBase = None):
        """
        Initialize RAG-enhanced LLM client
        
        Args:
            api_key: LLM API key
            base_url: LLM API base URL
            model: LLM model name
            use_rag: Whether to use RAG enhancement
            knowledge_base: Pre-built knowledge base (optional)
        """
        super().__init__(api_key, base_url, model)
        
        self.use_rag = use_rag
        self.knowledge_base = knowledge_base
        self.rag_client = None
        
        if use_rag:
            self._initialize_rag()
    
    def _initialize_rag(self):
        """Initialize RAG system if enabled"""
        try:
            # Initialize embedding model
            embedding_model = QwenEmbedding()
            
            # Create or load knowledge base
            if self.knowledge_base is None:
                self.knowledge_base = KnowledgeBase(embedding_model, "swarm_knowledge")
                
                # Add domain knowledge for drone swarm control
                self._build_default_knowledge_base()
            
            # Initialize RAG client
            self.rag_client = RAGLLMClient(
                self.knowledge_base,
                api_key=self.api_key,
                base_url=self.base_url,
                model=self.model
            )
            
            print("[RAG] RAG system initialized successfully")
            
        except Exception as e:
            print(f"[RAG] Warning: Could not initialize RAG: {e}")
            self.use_rag = False
    
    def _build_default_knowledge_base(self):
        """Build default knowledge base for drone swarm control"""
        
        domain_docs = {
            "AirSim Drone Control": """
            AirSim provides API-based control for multi-rotor drones:
            - armDisarm(arm, vehicle_name): Prepare drone for flight
            - takeoff(vehicle_name): Take off to default height
            - land(vehicle_name): Land the drone
            - moveToPosition(x, y, z, velocity, vehicle_name): Move to target position
            - getMultirotorState(vehicle_name): Get drone state and position
            - enableApiControl(is_enabled, vehicle_name): Enable/disable API control
            - setSimulationMode(mode): Change simulation mode
            """,
            
            "Swarm Formation": """
            Drone swarm formation techniques:
            - Grid formation: Drones arranged in regular grid pattern
            - Circle formation: Drones arranged in circular pattern
            - V-formation: Birds-like V shape for energy efficiency
            - Line formation: Drones in straight line
            
            Each formation type has different spacing requirements:
            - Safe minimum distance: 1-2 meters
            - Optimal spacing: 2-3 meters for 10+ drones
            - Formation diameter: Should fit simulation space
            """,
            
            "Waypoint Generation": """
            Point distribution for drone positions:
            - Uniform distribution: Regular grid spacing
            - Random distribution: Stochastic placement
            - Clustered distribution: Multiple clusters
            - SDF-based distribution: Points on shape surface
            
            Generation methods:
            - L-BFGS-B optimization: Find optimal point locations
            - K-means clustering: Distribute clusters evenly
            - Sampling: Direct point sampling from shape
            """,
            
            "SDF and Shape": """
            Signed Distance Functions (SDF) for 3D shapes:
            - SDF value: Distance to nearest surface (positive outside, negative inside)
            - Common shapes: sphere, box, cylinder, torus, pyramid
            - Combined shapes: Union, intersection, subtraction
            - Point on surface: SDF value ≈ 0
            
            Shape parameters:
            - Sphere: radius (1-10 units typical)
            - Box: width, height, depth
            - Cylinder: radius, height
            - Pyramid: base size, height
            """,
            
            "Collision Avoidance": """
            Multi-drone collision avoidance:
            - Minimum separation: 0.5-1.0 meters
            - Avoidance radius: 2-3 meters per drone
            - Velocity limits: 1-5 m/s for safe operation
            - Safety margin: Add 20% buffer to minimum distances
            
            Avoidance algorithms:
            - Artificial Potential Field: Repulsive forces between drones
            - Velocity obstacles: Predict and avoid collisions
            - Distributed control: Each drone makes local decisions
            """,
            
            "Task Description Guide": """
            When describing drone swarm tasks:
            - Shape description: Clearly state target 3D shape
            - Formation type: Specify formation arrangement
            - Execution time: How long task should take
            - Constraints: Altitude limits, speed limits, space limits
            
            Examples:
            - "Form a sphere with 10 drones, 5m diameter"
            - "Create a cube formation with 2m spacing"
            - "Arrange in circular pattern, 3m radius"
            """,
        }
        
        # Add documents to knowledge base
        for title, content in domain_docs.items():
            self.knowledge_base.add_document(content, {"title": title, "type": "system"})
        
        # Save to cache for reuse
        self.knowledge_base.save_to_cache()
        
        print(f"[RAG] Built default knowledge base with {len(domain_docs)} documents")
    
    def generate_sdf_code(self, description: str) -> str:
        """
        Generate SDF code with RAG enhancement
        
        Args:
            description: Natural language shape description
            
        Returns:
            Python code defining SDF function
        """
        
        # Retrieve relevant knowledge
        if self.use_rag and self.rag_client:
            try:
                # Get domain knowledge about shapes and SDFs
                knowledge = self.knowledge_base.search(description, top_k=2)
                
                # Build enhanced prompt
                context = ""
                if knowledge:
                    context = "## Relevant Domain Knowledge:\n"
                    for doc, score, meta in knowledge:
                        context += f"\n{doc}\n"
                
                enhanced_prompt = self.SDF_PROMPT.replace(
                    "Generate Python code",
                    f"{context}\nGenerate Python code"
                )
                
                # Generate code with LLM
                response = self.chat_completion([
                    {"role": "user", "content": enhanced_prompt.format(description=description)}
                ])
                
                return response if response else ""
                
            except Exception as e:
                print(f"[RAG] Warning: RAG enhancement failed, using standard generation: {e}")
        
        # Fall back to standard generation
        return super().generate_sdf_code(description)


class RAGEnhancedSDFGenerator(SDFGenerator):
    """
    Extended SDFGenerator with RAG-enhanced LLM client
    """
    
    def __init__(self, llm_client: RAGEnhancedLLMClient = None):
        """
        Initialize RAG-enhanced SDF generator
        
        Args:
            llm_client: RAGEnhancedLLMClient instance
        """
        if llm_client is None:
            llm_client = RAGEnhancedLLMClient(use_rag=True)
        
        super().__init__(llm_client)


# Helper function to create RAG-enhanced controller
def create_rag_enhanced_controller(drone_names: list, use_rag: bool = True):
    """
    Factory function to create LLM controller with RAG
    
    Args:
        drone_names: List of drone names
        use_rag: Whether to enable RAG enhancement
        
    Returns:
        LLMAirSimSwarmController with RAG capabilities
    """
    from integrated_controller import LLMAirSimSwarmController
    
    # Create RAG-enhanced LLM client
    llm_client = RAGEnhancedLLMClient(use_rag=use_rag)
    
    # Create controller (we'll override its components)
    controller = LLMAirSimSwarmController(
        drone_names=drone_names,
        verbose=True
    )
    
    # Replace LLM client with RAG-enhanced version
    controller.llm_client = llm_client
    controller.sdf_generator = RAGEnhancedSDFGenerator(llm_client)
    
    return controller


# Example usage
if __name__ == "__main__":
    print("RAG-Enhanced LLM Client Example")
    print("="*60 + "\n")
    
    try:
        # Create RAG-enhanced LLM client
        print("Creating RAG-enhanced LLM client...")
        rag_llm = RAGEnhancedLLMClient(use_rag=True)
        
        # Test basic chat
        print("\n1. Testing basic chat with RAG:")
        response = rag_llm.chat_completion([
            {"role": "user", "content": "What is the minimum safe distance between drones?"}
        ])
        print(f"Response: {response}\n")
        
        # Test SDF generation with RAG
        print("2. Testing SDF generation with RAG enhancement:")
        sdf_code = rag_llm.generate_sdf_code("A small sphere")
        print(f"Generated code preview:\n{sdf_code[:200]}...\n")
        
        # Test controller creation with RAG
        print("3. Creating RAG-enhanced controller:")
        drone_names = [f"Drone{i}" for i in range(1, 6)]
        controller = create_rag_enhanced_controller(drone_names, use_rag=True)
        print("✓ Controller created with RAG enhancement")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
