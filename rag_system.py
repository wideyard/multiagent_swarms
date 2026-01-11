"""
Retrieval-Augmented Generation (RAG) System for Domain Knowledge
Uses Qwen text-embedding-v4 for vector storage and retrieval
"""

import os
import json
import numpy as np
from typing import List, Tuple, Optional
from openai import OpenAI
import pickle
from pathlib import Path


class QwenEmbedding:
    """Wrapper for Qwen embedding model"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize Qwen embedding client
        
        Args:
            api_key: DashScope API key (defaults to DASHSCOPE_API_KEY env var)
            base_url: API base URL (defaults to Beijing region)
        """
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        self.base_url = base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"
        
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY not set. Please set it in environment variables.")
        
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        self.model = "text-embedding-v4"
    
    def embed(self, text: str) -> np.ndarray:
        """
        Get embedding vector for text
        
        Args:
            text: Input text to embed
            
        Returns:
            Embedding vector as numpy array
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            embedding = response.data[0].embedding
            return np.array(embedding)
        except Exception as e:
            print(f"Error embedding text: {e}")
            raise
    
    def embed_batch(self, texts: List[str]) -> List[np.ndarray]:
        """
        Get embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        for text in texts:
            embeddings.append(self.embed(text))
        return embeddings


class KnowledgeBase:
    """Vector database for domain knowledge"""
    
    def __init__(self, embedding_model: QwenEmbedding, name: str = "knowledge_base"):
        """
        Initialize knowledge base
        
        Args:
            embedding_model: QwenEmbedding instance
            name: Knowledge base name
        """
        self.embedding_model = embedding_model
        self.name = name
        self.documents = []  # List of document texts
        self.embeddings = []  # List of embedding vectors
        self.metadata = []  # List of metadata dicts
        self.cache_file = Path(f"{name}_cache.pkl")
        
        # Try to load from cache
        self.load_from_cache()
    
    def add_document(self, text: str, metadata: Optional[dict] = None):
        """
        Add a document to the knowledge base
        
        Args:
            text: Document text
            metadata: Optional metadata dict
        """
        # Embed the document
        embedding = self.embedding_model.embed(text)
        
        # Store document and embedding
        self.documents.append(text)
        self.embeddings.append(embedding)
        self.metadata.append(metadata or {})
        
        print(f"✓ Added document ({len(text)} chars)")
    
    def add_documents_from_file(self, file_path: str, chunk_size: int = 500):
        """
        Load documents from a text file and chunk them
        
        Args:
            file_path: Path to text file
            chunk_size: Number of characters per chunk
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split into chunks
            chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
            
            for i, chunk in enumerate(chunks):
                self.add_document(chunk, {"source": file_path, "chunk": i})
            
            print(f"✓ Loaded {len(chunks)} chunks from {file_path}")
            
        except Exception as e:
            print(f"Error loading file: {e}")
            raise
    
    def add_documents_from_dict(self, docs_dict: dict):
        """
        Add documents from a dictionary
        
        Args:
            docs_dict: Dict with keys as titles and values as content
        """
        for title, content in docs_dict.items():
            self.add_document(content, {"title": title})
        
        print(f"✓ Added {len(docs_dict)} documents")
    
    def search(self, query: str, top_k: int = 3) -> List[Tuple[str, float, dict]]:
        """
        Search for relevant documents
        
        Args:
            query: Search query
            top_k: Number of top results to return
            
        Returns:
            List of (document, similarity_score, metadata) tuples
        """
        if not self.documents:
            return []
        
        # Embed the query
        query_embedding = self.embedding_model.embed(query)
        
        # Calculate cosine similarity with all documents
        similarities = []
        for i, doc_embedding in enumerate(self.embeddings):
            # Cosine similarity
            similarity = np.dot(query_embedding, doc_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding) + 1e-10
            )
            similarities.append((i, similarity))
        
        # Sort by similarity and get top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for idx, score in similarities[:top_k]:
            results.append((
                self.documents[idx],
                float(score),
                self.metadata[idx]
            ))
        
        return results
    
    def save_to_cache(self):
        """Save knowledge base to cache file"""
        try:
            cache_data = {
                'documents': self.documents,
                'embeddings': self.embeddings,
                'metadata': self.metadata
            }
            with open(self.cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            print(f"✓ Saved knowledge base cache to {self.cache_file}")
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    def load_from_cache(self):
        """Load knowledge base from cache file"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                self.documents = cache_data['documents']
                self.embeddings = cache_data['embeddings']
                self.metadata = cache_data['metadata']
                print(f"✓ Loaded knowledge base cache with {len(self.documents)} documents")
            except Exception as e:
                print(f"Warning: Could not load cache: {e}")
    
    def get_stats(self) -> dict:
        """Get statistics about the knowledge base"""
        return {
            'num_documents': len(self.documents),
            'total_chars': sum(len(d) for d in self.documents),
            'avg_doc_length': sum(len(d) for d in self.documents) / len(self.documents) if self.documents else 0,
            'cache_file': str(self.cache_file)
        }


class RAGLLMClient:
    """LLM client enhanced with RAG"""
    
    def __init__(self, knowledge_base: KnowledgeBase, api_key: Optional[str] = None, 
                 base_url: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize RAG-enhanced LLM client
        
        Args:
            knowledge_base: KnowledgeBase instance
            api_key: LLM API key (defaults to OPENAI_API_KEY)
            base_url: LLM API base URL
            model: LLM model name
        """
        self.knowledge_base = knowledge_base
        
        # Initialize LLM client
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        self.model = model or os.getenv("LLM_MODEL")
        
        if not all([self.api_key, self.base_url, self.model]):
            raise ValueError("Missing LLM configuration. Set OPENAI_API_KEY, OPENAI_BASE_URL, LLM_MODEL")
        
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
    
    def query(self, user_query: str, top_k: int = 3, include_context: bool = True) -> str:
        """
        Query with RAG enhancement
        
        Args:
            user_query: User's question/task
            top_k: Number of knowledge documents to retrieve
            include_context: Whether to include knowledge in the prompt
            
        Returns:
            LLM response
        """
        # Retrieve relevant knowledge
        if include_context:
            retrieved_docs = self.knowledge_base.search(user_query, top_k=top_k)
            
            # Build context string
            context = ""
            if retrieved_docs:
                context = "## Relevant Domain Knowledge:\n"
                for doc, score, metadata in retrieved_docs:
                    context += f"\n### Document (similarity: {score:.2f})\n"
                    if metadata and 'title' in metadata:
                        context += f"Title: {metadata['title']}\n"
                    context += f"{doc}\n"
            
            # Build enhanced prompt
            enhanced_prompt = f"""{context}

## Task:
{user_query}

Please use the above domain knowledge to provide a more informed and accurate response."""
        else:
            enhanced_prompt = user_query
        
        # Call LLM
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": enhanced_prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error calling LLM: {e}")
            raise


# Example usage
if __name__ == "__main__":
    print("RAG System Example")
    print("="*60)
    
    # Sample domain knowledge for drone swarm control
    domain_knowledge = {
        "Drone Basics": """
        Drones are unmanned aerial vehicles. Each drone has:
        - Position (x, y, z coordinates)
        - Velocity (movement speed and direction)
        - Battery level
        - IMU sensors (inertial measurement unit)
        
        Drones can perform basic operations:
        - Takeoff: Rise from ground
        - Land: Descend to ground
        - Arm: Prepare motors
        - Disarm: Stop motors
        """,
        
        "Swarm Control": """
        Swarm control involves coordinating multiple drones:
        - Flocking: Drones maintain formation
        - Distributed control: Each drone makes local decisions
        - Consensus: Drones agree on targets
        - Collision avoidance: Maintain safe distances
        """,
        
        "Path Planning": """
        Path planning algorithms for drones:
        - A*: Grid-based pathfinding
        - RRT: Rapidly exploring random trees
        - Artificial Potential Field (APF): Physics-inspired
        - Trajectory optimization: Smooth paths
        """,
        
        "Simulation": """
        AirSim is a simulator for drones:
        - API-based control
        - Multi-drone support
        - Physics simulation
        - Sensor simulation (camera, lidar, GPS)
        """
    }
    
    # Initialize components
    print("\n1. Initializing Qwen embedding model...")
    try:
        embedding_model = QwenEmbedding()
        print("✓ Embedding model initialized")
    except ValueError as e:
        print(f"⚠ {e}")
        print("Note: Set DASHSCOPE_API_KEY to use RAG with Qwen embeddings")
        exit(1)
    
    print("\n2. Building knowledge base...")
    kb = KnowledgeBase(embedding_model, "drone_knowledge")
    kb.add_documents_from_dict(domain_knowledge)
    kb.save_to_cache()
    
    print("\n3. Knowledge base statistics:")
    stats = kb.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n4. Testing knowledge retrieval...")
    test_queries = [
        "How do drones take off?",
        "What is swarm control?",
        "How does AirSim work?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        results = kb.search(query, top_k=2)
        for doc, score, meta in results:
            print(f"  ✓ Match (score: {score:.2f})")
            print(f"    {doc[:100]}...")
    
    print("\n5. Testing RAG-enhanced LLM (if configured)...")
    try:
        rag_client = RAGLLMClient(kb)
        
        query = "What are the basic operations a drone can perform?"
        print(f"\nQuery: {query}")
        response = rag_client.query(query, top_k=2)
        print(f"\nResponse:\n{response}")
        
    except ValueError as e:
        print(f"⚠ {e}")
        print("Note: Set OPENAI_API_KEY, OPENAI_BASE_URL, LLM_MODEL to use RAG with LLM")
