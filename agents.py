"""The LLM steps of the workflow. Everything else in the project is plain code.

Each LLM step returns a Pydantic model, so its answer is checked before code uses it.
"""

from pydantic_ai import Agent
from pydantic_ai.models import Model

from models import Constraints

OUTPUT_RETRIES = 3  # how often the LLM may retry an answer that doesn't fit the model

CONSTRAINTS_INSTRUCTIONS = """
Read the user's request for a research paper and fill in its constraints.

- topic: the subject only, as short search words. No years or citation numbers.
- year and citations: pick the comparison that matches the wording and copy the
  number exactly as written. Never calculate a different number.
    "after 2022" -> ">" 2022          "2022 or later", "since 2022" -> ">=" 2022
    "before 2015" -> "<" 2015         "2015 or earlier" -> "<=" 2015
    "in 2020", "from 2020" -> "=" 2020
    "more than 500" -> ">" 500        "at least 100" -> ">=" 100
    "fewer than 50" -> "<" 50         "at most 50", "no more than 50" -> "<=" 50
    "about", "around", "roughly", "approximately" -> "about"
- Leave year or citations empty if the user gave no rule for it. Never invent one.
- recent: true only if the user asks for something recent, new or latest.
  Do not turn "recent" into a year.
"""

constraints_agent = Agent(
    output_type=Constraints,
    instructions=CONSTRAINTS_INSTRUCTIONS,
    retries=OUTPUT_RETRIES,
)


def extract_constraints(request: str, model: Model | str) -> Constraints:
    """LLM step 1: turn the user's free-text request into checked Constraints."""
    return constraints_agent.run_sync(request, model=model).output
