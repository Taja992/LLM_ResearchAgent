"""The agent's workflow: five steps in a fixed order, decided by code, not the LLM.

Two steps use the LLM (understanding and judging text); three are plain code
(searching, checking numbers, copying facts). See README "How the agent works".
Each step is announced to `on_step` as it starts and finishes (for a live display).
`paper_steps` can pause after each step (the web demo's "Continue" button);
`find_paper` runs all the steps without pausing.
"""

from collections.abc import Generator

from pydantic_ai.models import Model

from agents import extract_constraints, judge_relevance
from filters import filter_papers, summarize_rejections
from models import Constraints, NoMatch, Paper, PaperAnswer, Search
from openalex import search_openalex
from progress import StepName, StepReporter, ignore_progress, reported

type Answer = PaperAnswer | NoMatch
# Hands back each finished step's name, then (when done) the answer.
type PaperSteps = Generator[StepName, None, Answer]


def find_paper(
    request: str,
    model: Model | str,
    current_year: int,
    search: Search = search_openalex,
    on_step: StepReporter = ignore_progress,
) -> Answer:
    """Find one paper that fits the request, or explain why none does."""
    return run_to_end(paper_steps(request, model, current_year, search, on_step))


def paper_steps(
    request: str,
    model: Model | str,
    current_year: int,
    search: Search = search_openalex,
    on_step: StepReporter = ignore_progress,
) -> PaperSteps:
    """The five steps in order. `yield` pauses after each one until asked to go on."""
    with reported(on_step, StepName.READ_REQUEST):  # 1. LLM: read the request
        constraints = extract_constraints(request, model)
    yield StepName.READ_REQUEST
    with reported(on_step, StepName.SEARCH):  # 2. CODE: search OpenAlex
        found = search(constraints, current_year)
    yield StepName.SEARCH
    with reported(on_step, StepName.CHECK_RULES):  # 3. CODE: check the rules
        verdicts = filter_papers(found, constraints, current_year)
        accepted = [verdict.paper for verdict in verdicts if verdict.accepted]
    yield StepName.CHECK_RULES
    with reported(on_step, StepName.PICK_PAPER):  # 4. LLM: pick (may search again)
        outcome = judge_relevance(
            request,
            accepted,
            constraints,
            current_year,
            model,
            _reported_extra_search(search, on_step),
        )
    yield StepName.PICK_PAPER
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


def run_to_end(steps: PaperSteps) -> Answer:
    """Go through every step without pausing; the generator's return is the answer."""
    while True:
        try:
            next(steps)
        except StopIteration as finished:
            return finished.value


def _reported_extra_search(search: Search, on_step: StepReporter) -> Search:
    """The same search, announced as "Extra search" (step 4 only searches again)."""

    def extra_search(constraints: Constraints, current_year: int) -> list[Paper]:
        with reported(on_step, StepName.EXTRA_SEARCH):
            return search(constraints, current_year)

    return extra_search
