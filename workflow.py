"""The agent's workflow: five steps in a fixed order, decided by code, not the LLM.

Two steps use the LLM (understanding and judging text); three are plain code
(searching, checking numbers, copying facts). See README "How the agent works".
Each step is announced to `on_step` as it starts and finishes (for a live display).
"""

from collections.abc import Callable

from pydantic_ai.models import Model

from agents import extract_constraints, judge_relevance
from filters import filter_papers, summarize_rejections
from models import Constraints, NoMatch, Paper, PaperAnswer
from openalex import search_openalex
from progress import StepName, StepReporter, ignore_progress, reported

type Search = Callable[[Constraints, int], list[Paper]]


def find_paper(
    request: str,
    model: Model | str,
    current_year: int,
    search: Search = search_openalex,
    on_step: StepReporter = ignore_progress,
) -> PaperAnswer | NoMatch:
    """Find one paper that fits the request, or explain why none does."""
    with reported(on_step, StepName.READ_REQUEST):  # 1. LLM: read the request
        constraints = extract_constraints(request, model)
    with reported(on_step, StepName.SEARCH):  # 2. CODE: search OpenAlex
        found = search(constraints, current_year)
    with reported(on_step, StepName.CHECK_RULES):  # 3. CODE: check the rules
        verdicts = filter_papers(found, constraints, current_year)
        accepted = [verdict.paper for verdict in verdicts if verdict.accepted]
    with reported(on_step, StepName.PICK_PAPER):  # 4. LLM: pick (may search again)
        outcome = judge_relevance(
            request,
            accepted,
            constraints,
            current_year,
            model,
            _reported_extra_search(search, on_step),
        )
    with reported(on_step, StepName.BUILD_ANSWER):  # 5. CODE: build the answer
        if outcome.paper is None:  # code counts why papers failed; LLM says why
            return NoMatch(
                papers_checked=len(found),
                rejections=summarize_rejections(verdicts),
                explanation=outcome.explanation,
            )
        return PaperAnswer.from_paper(  # facts from the paper, words from the LLM
            outcome.paper, outcome.explanation, outcome.uncertainty
        )


def _reported_extra_search(search: Search, on_step: StepReporter) -> Search:
    """The same search, announced as "Extra search" (step 4 only searches again)."""

    def extra_search(constraints: Constraints, current_year: int) -> list[Paper]:
        with reported(on_step, StepName.EXTRA_SEARCH):
            return search(constraints, current_year)

    return extra_search
