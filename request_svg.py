# scripts/request_svg.py
import sys
import os

# Ensure repo root is on sys.path so `import src...` works when running this script
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.llm_client import LLMClient, SVGGenerator

desc = sys.argv[1] if len(sys.argv) > 1 else "Generate SVG outline of letter A"
client = LLMClient()
svg_gen = SVGGenerator(client)
svg = svg_gen.generate_svg(desc)
if svg:
    out = os.path.join("outputs", "generated.svg")
    os.makedirs("outputs", exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(svg)
    print("Saved SVG to", out)
else:
    print("No SVG returned by LLM")