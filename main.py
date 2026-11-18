"""Run the research agent from the command line.

python main.py "a paper on graph neural networks from before 2015 with at least 1000 citations"
"""

import io
import os
import sys
from datetime import date

from dotenv import load_dotenv

from workflow import find_paper

# Swap models by changing MODEL in .env ("provider:model-name"); see .env.example.
DEFAULT_MODEL = "ollama:qwen2.5:7b-instruct"
DEFAULT_REQUEST = "a paper about graph neural networks"
# Ollama's local server; only used when MODEL starts with "ollama:".
OLLAMA_BASE_URL = "http://localhost:11434/v1"


def configure() -> str:
    """Load settings from .env and prepare the console; return the model to use."""
    load_dotenv()  # MODEL and OPENALEX_API_KEY come from .env
    os.environ.setdefault("OLLAMA_BASE_URL", OLLAMA_BASE_URL)
    os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")  # so names like "Küttler" print right
    return os.getenv("MODEL", DEFAULT_MODEL)


def main() -> None:
    model = configure()
    request = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_REQUEST
    answer = find_paper(request, model, date.today().year)
    print(answer.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
