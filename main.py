"""Research agent starting point.

    python main.py "a paper on graph neural networks from before 2015 with at least 1000 citations"
"""
import os
import sys

from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic_ai import Agent, ToolOutput

load_dotenv()
os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
# Ollama's local server; only used when MODEL starts with "ollama:".
os.environ.setdefault("OLLAMA_BASE_URL", "http://localhost:11434/v1")

# Swap models by changing MODEL in .env ("provider:model-name"); see .env.example.
DEFAULT_MODEL = "ollama:qwen2.5:7b-instruct"


class PaperAnswer(BaseModel):
    # TODO: title, authors, year, citation_count, citation_source, url, explanation
    explanation: str


agent = Agent(
    os.getenv("MODEL", DEFAULT_MODEL),
    output_type=ToolOutput(PaperAnswer),  # answer via a tool call: more reliable on small local models
    retries=3,
    instructions="You help users find research papers. Use your tools; never invent citation counts.",
)


@agent.tool_plain
def search_papers(query: str) -> list[dict]:
    """Search for papers on a topic."""
    # TODO: call a real API (OpenAlex, Semantic Scholar, Crossref...)
    return []


if __name__ == "__main__":
    request = sys.argv[1] if len(sys.argv) > 1 else "a paper about graph neural networks"
    print(agent.run_sync(request).output.model_dump_json(indent=2))
