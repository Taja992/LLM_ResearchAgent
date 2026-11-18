"""Run the evaluation: every test case through the real agent, graded by code.

python evaluate.py

Uses the real model and live OpenAlex (one or two requests per case), so run it
on purpose. Prints the results table and saves every answer to RESULTS_FILE.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from pydantic import BaseModel
from pydantic_ai.models import Model
from pydantic_evals import Dataset
from pydantic_evals.reporting import EvaluationReport

from evaluation_cases import EVALUATION_SET, Answer, CaseCriteria, RunResult
from evaluation_checks import all_checks
from main import configure
from models import Constraints, Paper
from openalex import search_openalex
from workflow import find_paper

RESULTS_FILE = Path("evaluation_results.json")
ONE_CASE_AT_A_TIME = 1  # one local model can't usefully answer several at once

type Search = Callable[[Constraints, int], list[Paper]]
type Report = EvaluationReport[str, RunResult, CaseCriteria]


@dataclass
class RecordingSearch:
    """Wraps a search: passes every call through and keeps what came back."""

    search: Search
    papers_seen: list[Paper] = field(default_factory=list)
    searches: int = 0

    def __call__(self, constraints: Constraints, current_year: int) -> list[Paper]:
        papers = self.search(constraints, current_year)
        self.searches += 1
        self.papers_seen += papers
        return papers


class CheckRecord(BaseModel):
    passed: bool
    reason: str | None


class CaseRecord(BaseModel):
    """One case in the results file: the answer and how each check went."""

    case: str
    request: str
    answer: Answer
    searches: int
    checks: dict[str, CheckRecord]


class EvaluationRecord(BaseModel):
    """The whole results file."""

    model: str
    run_on: date
    cases: list[CaseRecord]
    crashed: dict[str, str]  # case name -> error message


def run_case(
    request: str, model: Model | str, current_year: int, search: Search
) -> RunResult:
    """One test run: the real workflow, with every search recorded."""
    recorder = RecordingSearch(search)
    answer = find_paper(request, model, current_year, recorder)
    return RunResult(
        answer=answer, papers_seen=recorder.papers_seen, searches=recorder.searches
    )


def evaluate(
    model: Model | str, current_year: int, search: Search = search_openalex
) -> Report:
    """Run every test case and grade it with every automatic check."""
    dataset = Dataset(
        name=EVALUATION_SET.name,
        cases=EVALUATION_SET.cases,
        evaluators=all_checks(current_year),
    )

    def task(request: str) -> RunResult:
        return run_case(request, model, current_year, search)

    return dataset.evaluate_sync(task, max_concurrency=ONE_CASE_AT_A_TIME)


def to_record(report: Report, model: str, run_on: date) -> EvaluationRecord:
    """The report in a plain shape for the results file (no raw search data)."""
    cases = [
        CaseRecord(
            case=case.name,
            request=case.inputs,
            answer=case.output.answer,
            searches=case.output.searches,
            checks={
                name: CheckRecord(passed=result.value, reason=result.reason)
                for name, result in case.assertions.items()
            },
        )
        for case in report.cases
    ]
    crashed = {failure.name: failure.error_message for failure in report.failures}
    return EvaluationRecord(model=model, run_on=run_on, cases=cases, crashed=crashed)


def main() -> None:
    model = configure()
    today = date.today()
    report = evaluate(model, today.year)
    report.print(include_reasons=True)
    record = to_record(report, model, today)
    RESULTS_FILE.write_text(record.model_dump_json(indent=2), encoding="utf-8")
    print(f"Saved every answer to {RESULTS_FILE}")


if __name__ == "__main__":
    main()
