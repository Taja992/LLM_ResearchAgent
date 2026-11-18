"""Tests for agents.py, using FunctionModel: a fake LLM we script ourselves."""

from typing import Any

from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from agents import extract_constraints
from models import Comparison, Constraints, NumberRule

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
    """A fake LLM reply: a call to the agent's output tool with these arguments."""
    output_tool = info.output_tools[0].name
    return ModelResponse(parts=[ToolCallPart(tool_name=output_tool, args=args)])


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
    assert '"after 2022" -> ">" 2022' in seen[1]
