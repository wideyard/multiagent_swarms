"""
LLM API Client - Integrated from NeLV/try.py
Supports calling LLM APIs for SDF generation
"""

from openai import OpenAI
from typing import List, Dict
import os
import json
import re


class LLMClient:
    """Wrapper for LLM API calls supporting multiple providers"""
    
    def __init__(self, 
                 api_key: str = None,
                 base_url: str = None,
                 model: str = None):
        """
        Initialize LLM client
        
        Args:
            api_key: API key (defaults to env var OPENAI_API_KEY)
            base_url: API base URL (defaults to env var OPENAI_BASE_URL)
            model: Model name (defaults to env var LLM_MODEL)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = model or os.getenv("LLM_MODEL", "gpt-3.5-turbo")
        
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        self.conversation_history = []
        
    def chat_completion(self, messages: List[Dict], temperature: float = 0.7) -> str:
        """
        Generic chat completion wrapper
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            
        Returns:
            Response text from the LLM
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error calling LLM API: {e}")
            return ""
    
    def add_user_message(self, content: str):
        """Add user message to conversation history"""
        self.conversation_history.append({"role": "user", "content": content})
    
    def add_assistant_message(self, content: str):
        """Add assistant message to conversation history"""
        self.conversation_history.append({"role": "assistant", "content": content})
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    def get_history(self) -> List[Dict]:
        """Get conversation history"""
        return self.conversation_history


class SDFGenerator:
    """Generates SDF code for 3D shapes using LLM"""
    
    SDF_PROMPT = """Generate 3D meshes based on SDFs (signed distance functions).

### Function signatures (REQUIRED PARAMETERS):

**Basic shapes:**
- sphere(radius) - e.g., sphere(1)
- box(size) or box((x,y,z)) - e.g., box(2) or box((1,2,3))
- rounded_box(size, radius) - e.g., rounded_box((1,2,3), 0.25)
- torus(major_radius, minor_radius) - e.g., torus(2, 0.5)
- capsule(p1, p2, radius) - e.g., capsule(-Z, Z, 0.5)
- capped_cylinder(p1, p2, radius) - e.g., capped_cylinder(-Z, Z, 0.5)
- cylinder(radius) - e.g., cylinder(0.5)
- pyramid(h) - e.g., pyramid(2)
- tetrahedron(r) - e.g., tetrahedron(1)
- octahedron(r) - e.g., octahedron(1)
- cone(...) - e.g., capped_cone(-Z, Z, 1, 0.5)
- ellipsoid((x,y,z)) - e.g., ellipsoid((1,2,3))

### Example of valid code:

```python
from sdf import *

f = pyramid(2)  # 2-unit tall pyramid
# or combine shapes:
f = sphere(1.5) & box(3)
c = cylinder(0.5)
f -= c.orient(X) | c.orient(Y) | c.orient(Z)
```

### Operations:** 
- Union: a | b
- Difference: a - b  
- Intersection: a & b

### Transforms:**
- translate((x, y, z))
- scale(factor) or scale((x, y, z))
- rotate(angle, axis)
- orient(axis)

**CRITICAL RULES:**
1. Always import: from sdf import *
2. Define variable 'f' as the final shape
3. ALL shape functions MUST have parameters (radius, size, height, etc.)
4. Do NOT include f.save() call
5. Never leave function calls empty - sphere() is INVALID, use sphere(1) instead
- Must return valid Python code
"""
    
    def __init__(self, llm_client: LLMClient):
        """
        Initialize SDF Generator
        
        Args:
            llm_client: LLMClient instance for API calls
        """
        self.llm_client = llm_client
    
    def extract_code_from_response(self, response: str) -> str:
        """
        Extract Python code from LLM response
        
        Args:
            response: LLM response text
            
        Returns:
            Extracted Python code (without save call)
        """
        # Find code block in response
        pattern = r'```(?:python)?\s*(.*?)```'
        matches = re.findall(pattern, response, re.DOTALL)
        
        if matches:
            code = matches[-1]  # Take the last code block
            # Remove save call
            code = re.sub(r"f\.save\('out\.stl'\)", "", code)
            code = re.sub(r'f\.save\("out\.stl"\)', "", code)
            return code.strip()
        
        return ""
    
    def generate_sdf_code(self, description: str) -> str:
        """
        Generate SDF code for a shape description
        
        Args:
            description: Natural language description of the shape
            
        Returns:
            Python code using sdf library
        """
        # Build prompt
        full_prompt = self.SDF_PROMPT + f"\n\n### Task:\nMake code to model a {description}\n\nRespond with ONLY the Python code block."
        
        # Add to conversation
        self.llm_client.add_user_message(full_prompt)
        
        # Get response
        messages = self.llm_client.get_history()
        response = self.llm_client.chat_completion(messages, temperature=0.7)
        
        # Add assistant response
        self.llm_client.add_assistant_message(response)
        
        # Extract code
        code = self.extract_code_from_response(response)
        return code
    
    def clear_context(self):
        """Clear conversation context"""
        self.llm_client.clear_history()


# Example usage
if __name__ == "__main__":
    # Initialize client
    client = LLMClient()
    
    # Test basic completion
    response = client.chat_completion([
        {"role": "user", "content": "Hello, what is 2+2?"}
    ])
    print("Response:", response)
    
    # Test SDF generation
    generator = SDFGenerator(client)
    code = generator.generate_sdf_code("cube with rounded edges")
    print("\nGenerated SDF code:")
    print(code)
