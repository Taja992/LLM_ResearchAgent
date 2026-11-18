"""Tests for agents.py, using FunctionModel: a fake LLM we script ourselves."""

import json
from collections.abc import Callable
from typing import Any

from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from agents import (
    CONSTRAINTS_INSTRUCTIONS,
    MAX_CANDIDATES_FOR_LLM,
    extract_constraints,
    judge_relevance,
)
from models import Comparison, Constraints, NumberRule, Paper, RelevanceOutcome

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


CURRENT_YEAR = 2026
RULES = Constraints(
    topic="RAG", year=NumberRule(comparison=Comparison.LESS_THAN, value=2021)
)


def make_paper(
    title: str, year: int = 2020, abstract: str | None = "An abstract."
) -> Paper:
    return Paper(
        title=title,
        authors=[],
        year=year,
        citation_count=100,
        citation_source="OpenAlex",
        url=f"https://example.org/{title}",
        abstract=abstract,
    )


CANDIDATES = [make_paper("Paper about cooking"), make_paper("Paper about RAG")]
PICK_SECOND: dict[str, Any] = {"paper_number": 2, "explanation": "It is about RAG."}

Reply = ModelResponse | dict[str, Any]


def call_search(query: str) -> ModelResponse:
    """A fake LLM reply that calls the search_papers tool."""
    return ModelResponse(
        parts=[ToolCallPart(tool_name="search_papers", args={"query": query})]
    )


def no_search(constraints: Constraints, current_year: int) -> list[Paper]:
    raise AssertionError("no search expected in this test")


def judge(
    candidates: list[Paper],
    replies: list[Reply],
    search: Callable[[Constraints, int], list[Paper]] = no_search,
    prompts: list[str] | None = None,
) -> RelevanceOutcome:
    """Run judge_relevance with a fake LLM that gives `replies` in order."""

    def fake_llm(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        if prompts is not None:
            prompts.append(str(messages))
        reply = replies.pop(0)
        return reply if isinstance(reply, ModelResponse) else answer_with(info, reply)

    return judge_relevance(
        REQUEST, candidates, RULES, CURRENT_YEAR, FunctionModel(fake_llm), search
    )


def test_llm_picks_a_candidate_by_number() -> None:
    outcome = judge(CANDIDATES, [PICK_SECOND])

    assert outcome.paper == CANDIDATES[1]
    assert outcome.explanation == "It is about RAG."
    assert outcome.extra_searches == 0


def test_llm_can_say_none_fits() -> None:
    outcome = judge(CANDIDATES, [{"paper_number": None, "explanation": "None fit."}])

    assert outcome.paper is None


def test_number_outside_the_list_is_sent_back_and_retried() -> None:
    replies: list[Reply] = [{"paper_number": 7, "explanation": "x"}, PICK_SECOND]

    outcome = judge(CANDIDATES, replies)

    assert outcome.paper == CANDIDATES[1]
    assert replies == []  # the out-of-range answer was rejected first


def test_llm_sees_request_and_numbered_candidates() -> None:
    prompts: list[str] = []
    long_abstract = "word " * 500
    candidates = [
        make_paper(f"Paper {n}", abstract=long_abstract) for n in range(1, 15)
    ]

    judge(candidates, [PICK_SECOND], prompts=prompts)

    assert REQUEST in prompts[0]
    assert "[1] Paper 1" in prompts[0]
    assert f"[{MAX_CANDIDATES_FOR_LLM}] Paper {MAX_CANDIDATES_FOR_LLM}" in prompts[0]
    assert f"[{MAX_CANDIDATES_FOR_LLM + 1}]" not in prompts[0]  # list is capped
    assert long_abstract not in prompts[0]  # abstracts are shortened


def test_no_candidates_still_lets_the_llm_answer() -> None:
    prompts: list[str] = []

    outcome = judge([], [{"paper_number": None, "explanation": "x"}], prompts=prompts)

    assert outcome.paper is None
    assert "none yet" in prompts[0]


def test_search_tool_adds_new_candidates_after_the_old_ones() -> None:
    searched: list[Constraints] = []
    prompts: list[str] = []

    def fake_search(constraints: Constraints, current_year: int) -> list[Paper]:
        searched.append(constraints)
        return [
            CANDIDATES[0],  # already shown: dropped
            make_paper("RAG survey"),  # new and passes the rules
            make_paper("Late RAG paper", year=2022),  # fails "before 2021": dropped
        ]

    replies: list[Reply] = [
        call_search("retrieval augmented generation"),
        {"paper_number": 3, "explanation": "A survey of RAG."},
    ]
    outcome = judge(CANDIDATES, replies, search=fake_search, prompts=prompts)

    assert outcome.paper is not None
    assert outcome.paper.title == "RAG survey"
    assert outcome.extra_searches == 1
    assert searched[0].topic == "retrieval augmented generation"
    assert searched[0].year == RULES.year  # same rules, new words
    assert "[3] RAG survey" in prompts[1]  # what the tool told the LLM
    assert "Late RAG paper" not in prompts[1]


def test_only_one_extra_search_is_allowed() -> None:
    searches: list[str] = []

    def fake_search(constraints: Constraints, current_year: int) -> list[Paper]:
        searches.append(constraints.topic)
        return []

    replies: list[Reply] = [call_search("first"), call_search("second"), PICK_SECOND]
    outcome = judge(CANDIDATES, replies, search=fake_search)

    assert searches == ["first"]  # the second call was refused, not searched
    assert outcome.extra_searches == 1


def test_fallback_searches_with_the_llms_words_when_it_did_not_use_the_tool() -> None:
    searched: list[str] = []
    prompts: list[str] = []

    def fake_search(constraints: Constraints, current_year: int) -> list[Paper]:
        searched.append(constraints.topic)
        return [make_paper("RAG survey")]

    replies: list[Reply] = [
        {"paper_number": None, "explanation": "None fit.", "search_words": "RAG"},
        {"paper_number": 3, "explanation": "A survey of RAG."},
    ]
    outcome = judge(CANDIDATES, replies, search=fake_search, prompts=prompts)

    assert searched == ["RAG"]
    assert outcome.paper is not None
    assert outcome.paper.title == "RAG survey"
    assert outcome.extra_searches == 1
    assert "[3] RAG survey" in prompts[1]  # asked again with the longer list


def test_no_fallback_after_the_tool_already_searched() -> None:
    searched: list[str] = []

    def fake_search(constraints: Constraints, current_year: int) -> list[Paper]:
        searched.append(constraints.topic)
        return []

    replies: list[Reply] = [
        call_search("first"),
        {"paper_number": None, "explanation": "x", "search_words": "second"},
    ]
    outcome = judge(CANDIDATES, replies, search=fake_search)

    assert searched == ["first"]
    assert outcome.paper is None


def test_no_fallback_without_search_words() -> None:
    outcome = judge(CANDIDATES, [{"paper_number": None, "explanation": "None fit."}])

    assert outcome.extra_searches == 0  # no_search would have failed the test


def test_no_second_question_when_the_fallback_finds_nothing_new() -> None:
    replies: list[Reply] = [
        {"paper_number": None, "explanation": "None fit.", "search_words": "RAG"}
    ]

    outcome = judge(CANDIDATES, replies, search=lambda constraints, year: [])

    assert outcome.paper is None
    assert outcome.extra_searches == 1
    assert replies == []  # only one LLM answer was needed
