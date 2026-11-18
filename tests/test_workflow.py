"""Tests for workflow.py: the five steps together, with a fake LLM and fake search."""

import json
from typing import Any

from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from models import Constraints, NoMatch, Paper, PaperAnswer
from workflow import find_paper

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
