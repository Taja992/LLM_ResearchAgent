"""Tests for agents.py, using FunctionModel: a fake LLM we script ourselves."""

import json
from typing import Any

import pytest
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from agents import (
    CONSTRAINTS_INSTRUCTIONS,
    MAX_CANDIDATES_FOR_LLM,
    extract_constraints,
    judge_relevance,
)
from models import Comparison, Constraints, NumberRule, Paper

REQUEST = "a paper about RAG published before 2021 with more than 500 citations"
GOOD_ANSWER: dict[str, Any] = {
    "topic": "retrieval-augmented generation",
    "year": {"comparison": "<", "value": 2021},
    "citations": {"comparison": ">", "value": 500},
}
BAD_ANSWER: dict[str, Any] = {
    "topic": "retrieval-augmented generation",
    "year": {"comparison": "?"},
}


def answer_with(info: AgentInfo, args: dict[str, Any]) -> ModelResponse:
    """A fake LLM reply: these fields as JSON text, like a native-output model."""
    return ModelResponse(parts=[TextPart(content=json.dumps(args))])


def test_llm_answer_becomes_constraints() -> None:
    def fake_llm(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        return answer_with(info, GOOD_ANSWER)

    constraints = extract_constraints(REQUEST, model=FunctionModel(fake_llm))

    assert constraints == Constraints(
        topic="retrieval-augmented generation",
        year=NumberRule(comparison=Comparison.LESS_THAN, value=2021),
        citations=NumberRule(comparison=Comparison.MORE_THAN, value=500),
    )


def test_bad_answer_is_sent_back_and_retried() -> None:
    answers = [BAD_ANSWER, GOOD_ANSWER]  # wrong first, right after the retry

    def fake_llm(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        return answer_with(info, answers.pop(0))

    constraints = extract_constraints(REQUEST, model=FunctionModel(fake_llm))

    assert constraints.year == NumberRule(comparison=Comparison.LESS_THAN, value=2021)
    assert answers == []  # both answers were used: the first was rejected


def test_llm_receives_the_request_and_instructions() -> None:
    seen: list[str] = []

    def fake_llm(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        seen.append(str(messages))
        seen.append(info.instructions or "")
        return answer_with(info, GOOD_ANSWER)

    extract_constraints(REQUEST, model=FunctionModel(fake_llm))

    assert REQUEST in seen[0]
    assert CONSTRAINTS_INSTRUCTIONS.strip() in seen[1]


def make_paper(title: str, abstract: str | None = "An abstract.") -> Paper:
    return Paper(
        title=title,
        authors=[],
        year=2020,
        citation_count=100,
        citation_source="OpenAlex",
        url="https://example.org",
        abstract=abstract,
    )


CANDIDATES = [make_paper("Paper about cooking"), make_paper("Paper about RAG")]
PICK_SECOND: dict[str, Any] = {"paper_number": 2, "explanation": "It is about RAG."}


def test_llm_picks_a_candidate_by_number() -> None:
    def fake_llm(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        return answer_with(info, PICK_SECOND)

    judgement = judge_relevance(REQUEST, CANDIDATES, model=FunctionModel(fake_llm))

    assert judgement.explanation == "It is about RAG."
    assert judgement.chosen_from(CANDIDATES) == CANDIDATES[1]


def test_llm_can_say_none_fits() -> None:
    def fake_llm(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        return answer_with(info, {"paper_number": None, "explanation": "None fit."})

    judgement = judge_relevance(REQUEST, CANDIDATES, model=FunctionModel(fake_llm))

    assert judgement.chosen_from(CANDIDATES) is None


def test_number_outside_the_list_is_sent_back_and_retried() -> None:
    answers = [{"paper_number": 7, "explanation": "x"}, PICK_SECOND]

    def fake_llm(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        return answer_with(info, answers.pop(0))

    judgement = judge_relevance(REQUEST, CANDIDATES, model=FunctionModel(fake_llm))

    assert judgement.paper_number == 2
    assert answers == []  # the out-of-range answer was rejected first


def test_llm_sees_request_and_numbered_candidates() -> None:
    seen: list[str] = []
    long_abstract = "word " * 500
    candidates = [make_paper(f"Paper {n}", long_abstract) for n in range(1, 15)]

    def fake_llm(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        seen.append(str(messages))
        return answer_with(info, PICK_SECOND)

    judge_relevance(REQUEST, candidates, model=FunctionModel(fake_llm))

    prompt = seen[0]
    assert REQUEST in prompt
    assert "[1] Paper 1" in prompt
    assert f"[{MAX_CANDIDATES_FOR_LLM}] Paper {MAX_CANDIDATES_FOR_LLM}" in prompt
    assert f"[{MAX_CANDIDATES_FOR_LLM + 1}]" not in prompt  # list is capped
    assert long_abstract not in prompt  # abstracts are shortened


def test_no_candidates_is_an_error() -> None:
    def never_called(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        raise AssertionError("the LLM must not be asked when there are no candidates")

    with pytest.raises(ValueError):
        judge_relevance(REQUEST, [], model=FunctionModel(never_called))
