"""The agent's workflow: five steps in a fixed order, decided by code, not the LLM.

Two steps use the LLM (understanding and judging text); three are plain code
(searching, checking numbers, copying facts). See README "How the agent works".
"""

from collections.abc import Callable

from pydantic_ai.models import Model

from agents import extract_constraints, judge_relevance
from filters import filter_papers, summarize_rejections
from models import Constraints, NoMatch, Paper, PaperAnswer
from openalex import search_openalex


def find_paper(
    request: str,
    model: Model | str,
    current_year: int,
    search: Callable[[Constraints, int], list[Paper]] = search_openalex,
) -> PaperAnswer | NoMatch:
    """Find one paper that fits the request, or explain why none does."""
    constraints = extract_constraints(request, model)  # 1. LLM: read the request
    found = search(constraints, current_year)  # 2. CODE: search OpenAlex
    verdicts = filter_papers(found, constraints, current_year)  # 3. CODE: check rules
    accepted = [verdict.paper for verdict in verdicts if verdict.accepted]
    outcome = judge_relevance(  # 4. LLM: pick the best fit (may search once more)
        request, accepted, constraints, current_year, model, search
    )
    if outcome.paper is None:  # CODE: counts why papers failed; LLM: why none fit
        return NoMatch(
            papers_checked=len(found),
            rejections=summarize_rejections(verdicts),
            explanation=outcome.explanation,
        )
    return PaperAnswer.from_paper(  # 5. CODE: facts from the paper, words from the LLM
        outcome.paper, outcome.explanation, outcome.uncertainty
    )
