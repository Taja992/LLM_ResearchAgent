"""Tests for evaluate.py: a whole evaluation run with a fake LLM and fake search."""

import itertools
import json
from datetime import date
from typing import Any

from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from evaluate import EvaluationRecord, RecordingSearch, evaluate, to_record
from evaluation_cases import EVALUATION_SET
from models import Constraints, Paper, PaperAnswer

CURRENT_YEAR = 2026
PAPER = Paper(
    title="A paper",
    authors=["A. Author"],
    year=2020,
    citation_count=5000,
    citation_source="OpenAlex",
    url="https://doi.org/10.1/abc",
    abstract="About things.",
)
# The two LLM steps take turns, one case at a time: read the request, then pick.
REPLIES: list[dict[str, Any]] = [
    {"topic": "things"},
    {"paper_number": 1, "explanation": "Published in 2020."},
]


def fake_llm() -> FunctionModel:
    replies = itertools.cycle(REPLIES)

    def answer(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        return ModelResponse(parts=[TextPart(content=json.dumps(next(replies)))])

    return FunctionModel(answer)


def fake_search(constraints: Constraints, current_year: int) -> list[Paper]:
    return [PAPER]


def test_recording_search_passes_results_through_and_keeps_them() -> None:
    recorder = RecordingSearch(fake_search)
    constraints = Constraints(topic="things")

    assert recorder(constraints, CURRENT_YEAR) == [PAPER]
    recorder(constraints, CURRENT_YEAR)

    assert recorder.searches == 2
    assert recorder.papers_seen == [PAPER, PAPER]


def test_evaluate_runs_every_case_through_every_check() -> None:
    report = evaluate(fake_llm(), CURRENT_YEAR, fake_search)

    assert len(report.cases) == len(EVALUATION_SET.cases)
    assert not report.failures
    for case in report.cases:
        assert case.output.searches == 1
        assert case.assertions["facts_match_search"].value  # recorded search
    found_when_expected = {
        case.name: case.assertions["found_when_expected"].value for case in report.cases
    }
    assert not found_when_expected["no_paper_llm_knitting_before_2015"]


def test_results_record_keeps_answers_and_checks_but_not_raw_search_data() -> None:
    report = evaluate(fake_llm(), CURRENT_YEAR, fake_search)

    record = to_record(report, "fake", date(2026, 11, 18))
    reloaded = EvaluationRecord.model_validate_json(record.model_dump_json())

    assert reloaded == record
    answer = reloaded.cases[0].answer
    assert isinstance(answer, PaperAnswer)  # read back as the right model
    assert answer.title == PAPER.title
    assert "papers_seen" not in record.model_dump_json()
