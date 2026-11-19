"""Tests for workflow.py: the five steps together, with a fake LLM and fake search."""

import json
from typing import Any

from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from models import Constraints, NoMatch, Paper, PaperAnswer
from progress import StepName, StepReporter, StepStatus
from workflow import find_paper, paper_steps, run_to_end

CURRENT_YEAR = 2026
REQUEST = "a paper about RAG published before 2021"
CONSTRAINTS_REPLY: dict[str, Any] = {
    "topic": "RAG",
    "year": {"comparison": "<", "value": 2021},
}
OLD_PAPER = Paper(
    title="RAG for NLP",
    authors=["Patrick Lewis"],
    year=2020,
    citation_count=10277,
    citation_source="OpenAlex",
    url="https://doi.org/10.48550/arxiv.2005.11401",
    abstract="Retrieval-augmented generation.",
)
NEW_PAPER = OLD_PAPER.model_copy(
    update={"title": "Late RAG", "year": 2023, "url": "https://example.org/late"}
)
OLDER_PAPER = OLD_PAPER.model_copy(
    update={"title": "Early RAG", "year": 2019, "url": "https://example.org/early"}
)


def scripted_llm(replies: list[dict[str, Any]], prompts: list[str]) -> FunctionModel:
    """A fake LLM for both LLM steps: gives `replies` in order, records prompts."""

    def fake_llm(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        prompts.append(str(messages))
        return ModelResponse(parts=[TextPart(content=json.dumps(replies.pop(0)))])

    return FunctionModel(fake_llm)


def fake_search(constraints: Constraints, current_year: int) -> list[Paper]:
    return [NEW_PAPER, OLD_PAPER]  # NEW_PAPER breaks "before 2021"


def test_whole_workflow_returns_an_answer_built_from_the_paper() -> None:
    prompts: list[str] = []
    replies: list[dict[str, Any]] = [
        CONSTRAINTS_REPLY,
        {"paper_number": 1, "explanation": "It introduces RAG.", "uncertainty": None},
    ]

    answer = find_paper(
        REQUEST, scripted_llm(replies, prompts), CURRENT_YEAR, fake_search
    )

    assert isinstance(answer, PaperAnswer)
    assert answer.title == OLD_PAPER.title  # facts come from the paper...
    assert answer.citation_count == OLD_PAPER.citation_count
    assert answer.explanation == "It introduces RAG."  # ...words from the LLM
    assert "Late RAG" not in prompts[1]  # the filter removed it before step 4


def test_nothing_fits_explains_why_with_counts_and_the_llms_words() -> None:
    replies: list[dict[str, Any]] = [
        CONSTRAINTS_REPLY,
        {"paper_number": None, "explanation": "None fit."},
    ]

    answer = find_paper(REQUEST, scripted_llm(replies, []), CURRENT_YEAR, fake_search)

    assert isinstance(answer, NoMatch)
    assert answer.papers_checked == 2
    assert answer.rejections == ["1 paper: year needs < 2021"]  # NEW_PAPER
    assert answer.explanation == "None fit."


def record_steps(steps: list[tuple[StepName, StepStatus]]) -> StepReporter:
    def on_step(step: StepName, status: StepStatus) -> None:
        steps.append((step, status))

    return on_step


def started_and_finished(*names: StepName) -> list[tuple[StepName, StepStatus]]:
    return [(name, status) for name in names for status in StepStatus]


def test_every_step_is_announced_in_order() -> None:
    steps: list[tuple[StepName, StepStatus]] = []
    replies: list[dict[str, Any]] = [
        CONSTRAINTS_REPLY,
        {"paper_number": 1, "explanation": "It introduces RAG."},
    ]

    find_paper(
        REQUEST,
        scripted_llm(replies, []),
        CURRENT_YEAR,
        fake_search,
        record_steps(steps),
    )

    assert steps == started_and_finished(
        StepName.READ_REQUEST,
        StepName.SEARCH,
        StepName.CHECK_RULES,
        StepName.PICK_PAPER,
        StepName.BUILD_ANSWER,
    )


def test_an_extra_search_is_announced_inside_picking() -> None:
    steps: list[tuple[StepName, StepStatus]] = []
    replies: list[dict[str, Any]] = [
        CONSTRAINTS_REPLY,
        {"paper_number": None, "explanation": "Off topic.", "search_words": "RAG"},
        {"paper_number": 2, "explanation": "The new one fits."},
    ]
    searches = iter([[OLD_PAPER], [OLDER_PAPER]])  # the extra search finds a new paper

    def two_searches(constraints: Constraints, current_year: int) -> list[Paper]:
        return next(searches)

    answer = find_paper(
        REQUEST,
        scripted_llm(replies, []),
        CURRENT_YEAR,
        two_searches,
        record_steps(steps),
    )

    assert isinstance(answer, PaperAnswer)
    assert answer.title == OLDER_PAPER.title
    pick = steps.index((StepName.PICK_PAPER, StepStatus.STARTED))
    assert steps[pick : pick + 4] == [
        (StepName.PICK_PAPER, StepStatus.STARTED),
        (StepName.EXTRA_SEARCH, StepStatus.STARTED),
        (StepName.EXTRA_SEARCH, StepStatus.FINISHED),
        (StepName.PICK_PAPER, StepStatus.FINISHED),
    ]


def test_paper_steps_pauses_after_each_step_until_asked_to_go_on() -> None:
    replies: list[dict[str, Any]] = [
        CONSTRAINTS_REPLY,
        {"paper_number": 1, "explanation": "It introduces RAG."},
    ]
    prompts: list[str] = []
    steps = paper_steps(
        REQUEST, scripted_llm(replies, prompts), CURRENT_YEAR, fake_search
    )

    assert next(steps) is StepName.READ_REQUEST
    assert len(prompts) == 1  # paused: step 4's LLM call has not happened yet
    assert [next(steps), next(steps), next(steps)] == [
        StepName.SEARCH,
        StepName.CHECK_RULES,
        StepName.PICK_PAPER,
    ]
    answer = run_to_end(steps)  # step 5 builds the answer

    assert isinstance(answer, PaperAnswer)
    assert answer.title == OLD_PAPER.title
