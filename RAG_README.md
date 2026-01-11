# RAG System for Drone Swarm Control

## Overview

This is a **Retrieval-Augmented Generation (RAG)** system that enhances LLM understanding of drone swarm tasks using domain knowledge retrieval. It uses **Qwen's text-embedding-v4** model from DashScope and integrates with your existing LLM AirSim swarm controller.

## Components

### 1. **rag_system.py** - Core RAG Implementation
- **QwenEmbedding**: Wrapper for Qwen embedding API
- **KnowledgeBase**: Vector database for domain knowledge
- **RAGLLMClient**: LLM client enhanced with knowledge retrieval

### 2. **rag_integration.py** - Integration with Swarm Controller
- **RAGEnhancedLLMClient**: Extends LLMClient with RAG capabilities
- **RAGEnhancedSDFGenerator**: Generates SDF code with knowledge
- **create_rag_enhanced_controller()**: Factory function for RAG-enabled controller

### 3. **rag_examples.py** - Usage Examples
Five examples demonstrating RAG capabilities

## Setup

### 1. Install Dependencies

```bash
pip install numpy openai
```

### 2. Configure API Keys

```powershell
# Set DashScope API key for embedding (Qwen)
$env:OPENAI_API_KEY = "sk-xxx"

# Set OpenAI-compatible API keys for LLM
$env:OPENAI_API_KEY = "your-llm-api-key"
$env:OPENAI_BASE_URL = "https://your-llm-api-url"
$env:LLM_MODEL = "your-model-name"
```

## Quick Start

### Basic RAG Usage

```python
from rag_system import QwenEmbedding, KnowledgeBase

# Initialize embedding model
embedding = QwenEmbedding()

# Create knowledge base
kb = KnowledgeBase(embedding, "my_knowledge_base")

# Add domain knowledge
kb.add_document("""
Drone safety requirements:
- Minimum separation distance: 1 meter
- Maximum altitude: 120 meters
- Maximum speed: 20 m/s
""", metadata={"type": "safety"})

# Search for relevant knowledge
results = kb.search("How far apart should drones be?", top_k=3)

for doc, score, meta in results:
    print(f"Match (score: {score:.2f}): {doc[:100]}...")
```

### RAG-Enhanced LLM

```python
from rag_integration import RAGEnhancedLLMClient

# Create RAG-enhanced LLM client
rag_llm = RAGEnhancedLLMClient(use_rag=True)

# Use chat with automatic knowledge enhancement
response = rag_llm.chat_completion([
    {"role": "user", "content": "What formations can 10 drones make?"}
])

print(response)
```

### Integration with Swarm Controller

```python
from rag_integration import create_rag_enhanced_controller

# Create controller with RAG enhancement
drone_names = [f"Drone{i}" for i in range(1, 11)]
controller = create_rag_enhanced_controller(drone_names, use_rag=True)

# Use normally - LLM will automatically use domain knowledge
controller.prepare_mission("Form a sphere with the drones")
controller.start_mission()
```

## How RAG Works

### 1. **Knowledge Storage**
Domain knowledge is stored as text documents with embeddings:
```
Document: "Sphere formation requires even distribution of drones..."
Embedding: [0.123, -0.456, 0.789, ...] (1536 dimensions)
```

### 2. **Query Processing**
User query is embedded using the same model:
```
Query: "How to arrange drones in a sphere?"
Query Embedding: [0.111, -0.444, 0.777, ...]
```

### 3. **Knowledge Retrieval**
Cosine similarity finds most relevant documents:
```
Similarity = dot(query_embedding, doc_embedding) / (||query|| * ||doc||)
Top-3 documents with highest similarity are retrieved
```

### 4. **Prompt Enhancement**
Retrieved knowledge is added to LLM prompt:
```
Prompt = """
## Domain Knowledge:
[Retrieved documents]

## Task:
[User query]
"""
```

## Example Knowledge Base

The system comes with domain knowledge about:

- **AirSim Control**: API methods, parameters, best practices
- **Swarm Formation**: Grid, circle, V, cube formations
- **Waypoint Generation**: Distribution algorithms, optimization
- **SDF and Shapes**: Common shapes, parameters, combination
- **Collision Avoidance**: Safety margins, algorithms
- **Task Description**: How to describe drone tasks

## API Reference

### QwenEmbedding
```python
embedding = QwenEmbedding(api_key="sk-xxx", base_url="https://...")
vector = embedding.embed("Some text")  # Returns numpy array
vectors = embedding.embed_batch(["text1", "text2"])  # Batch embedding
```

### KnowledgeBase
```python
kb = KnowledgeBase(embedding_model, "kb_name")

# Add documents
kb.add_document(text, metadata={"type": "safety"})
kb.add_documents_from_file("knowledge.txt", chunk_size=500)
kb.add_documents_from_dict({"title1": "content1", "title2": "content2"})

# Search
results = kb.search("query", top_k=3)  # Returns [(doc, score, meta), ...]

# Persistence
kb.save_to_cache()  # Save to disk
kb.load_from_cache()  # Load from disk

# Statistics
stats = kb.get_stats()
```

### RAGLLMClient
```python
rag_client = RAGLLMClient(knowledge_base, api_key="...", base_url="...", model="...")

response = rag_client.query(
    user_query="What is the best formation?",
    top_k=3,  # Number of documents to retrieve
    include_context=True  # Include knowledge in prompt
)
```

### RAGEnhancedLLMClient
```python
rag_llm = RAGEnhancedLLMClient(use_rag=True)

# Automatic RAG enhancement for chat
response = rag_llm.chat_completion([
    {"role": "user", "content": "How do drones avoid collisions?"}
])

# Automatic RAG enhancement for SDF generation
code = rag_llm.generate_sdf_code("A pyramid shape")
```

## Performance Considerations

### Embedding Costs
- Each document embedding costs ~0.1¢ (DashScope pricing)
- Caching recommended to avoid re-embedding

### Retrieval Speed
- Cosine similarity: O(n) where n = number of documents
- Typical: <100ms for 1000 documents
- For >10000 docs, consider vector database (Pinecone, Milvus, etc)

### Knowledge Base Size
- Default: ~4KB of default domain knowledge
- Recommended: 10-100KB for good coverage
- Maximum: Limited by embedding budget

## Advanced Usage

### Custom Knowledge Base

```python
# Create specialized knowledge base for your domain
domain_kb = KnowledgeBase(embedding, "my_domain")

# Load from custom document
with open("my_docs.txt") as f:
    for line in f:
        domain_kb.add_document(line.strip())

domain_kb.save_to_cache()

# Use with RAG
rag_llm = RAGEnhancedLLMClient()
rag_llm.knowledge_base = domain_kb
```

### Hybrid Approach

```python
# Combine multiple knowledge bases
kb1 = KnowledgeBase.load_from_cache("drone_knowledge")
kb2 = KnowledgeBase.load_from_cache("formation_knowledge")

# Merge if needed
for doc in kb2.documents:
    kb1.add_document(doc)
```

### Fine-tuning

```python
# The system automatically learns from successful queries
# Feedback mechanism (optional):

if query_result_was_good:
    kb.add_document(f"Question: {query}\nAnswer: {result}")
```

## Troubleshooting

### "DASHSCOPE_API_KEY not set"
```powershell
$env:DASHSCOPE_API_KEY = "your-key"
```

### Slow embedding
- DashScope embedding takes 0.5-2 seconds per document
- Use batch operations when possible
- Cache results aggressively

### Poor search results
- Add more relevant documents
- Use longer, more specific queries
- Increase `top_k` parameter

### LLM not using knowledge
- Check `use_rag=True`
- Verify knowledge base has documents
- Check search results for relevance

## Running Examples

```bash
# Test all RAG functionality
python rag_examples.py

# Or in interactive mode
python -i rag_examples.py
```

## Future Enhancements

- [ ] GPU-accelerated similarity search
- [ ] Hierarchical knowledge base with categorization
- [ ] Automatic knowledge extraction from execution logs
- [ ] Vector database integration (Pinecone, Milvus)
- [ ] Multi-language support
- [ ] Knowledge pruning and optimization
- [ ] Feedback loop for continuous improvement

## References

- [DashScope API Documentation](https://help.aliyun.com/zh/model-studio/)
- [Embedding Models](https://help.aliyun.com/zh/model-studio/user-guide/text-embedding)
- [RAG Overview](https://en.wikipedia.org/wiki/Retrieval-augmented_generation)
- [Cosine Similarity](https://en.wikipedia.org/wiki/Cosine_similarity)

## License

Same as parent project

## Author

Integrated RAG system for LLM AirSim Swarm Controller
