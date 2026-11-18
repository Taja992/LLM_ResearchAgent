"""Tests for evaluation_checks.py: each check on hand-made answers, no real runs."""

from pydantic_evals.evaluators import EvaluatorContext
from pydantic_evals.otel import SpanTreeRecordingError

from evaluation_cases import CaseCriteria, Covers, RunResult, rule
from evaluation_checks import (
    Context,
    ExplanationMatchesFacts,
    FactsMatchSearch,
    FoundWhenExpected,
    KeepsRules,
    ValidSource,
)
from models import NoMatch, Paper, PaperAnswer

CURRENT_YEAR = 2026
REQUEST = "a paper about RAG before 2021 with more than 500 citations"
PAPER = Paper(
    title="RAG for NLP",
    authors=["Patrick Lewis"],
    year=2020,
    citation_count=10277,
    citation_source="OpenAlex",
    url="https://doi.org/10.48550/arxiv.2005.11401",
    abstract="Retrieval-augmented generation.",
)
CRITERIA = CaseCriteria(
    covers=[Covers.YEAR_BEFORE, Covers.MIN_CITATIONS],
    year=rule("<", 2021),
    citations=rule(">", 500),
    relevant_if="RAG.",
)
NO_MATCH = NoMatch(papers_checked=3, rejections=[], explanation="None fit.")


def answer(explanation: str = "It introduces RAG.", **changes: object) -> PaperAnswer:
    """An answer built from PAPER, with any fact changed to test a check."""
    built = PaperAnswer.from_paper(PAPER, explanation)
    return built.model_copy(update=changes)


def context(
    result: PaperAnswer | NoMatch, criteria: CaseCriteria = CRITERIA
) -> Context:
    """What pydantic_evals hands a check after one test run."""
    return EvaluatorContext(
        name="test",
        inputs=REQUEST,
        metadata=criteria,
        expected_output=None,
        output=RunResult(answer=result, papers_seen=[PAPER], searches=1),
        duration=0.0,
        _span_tree=SpanTreeRecordingError("not recorded in tests"),
        attributes={},
        metrics={},
    )


def test_found_when_expected_passes_for_a_paper_and_for_a_correct_no_match() -> None:
    no_paper = CRITERIA.model_copy(update={"expect_paper": False})
    assert FoundWhenExpected().evaluate(context(answer()))["found_when_expected"].value
    assert (
        FoundWhenExpected()
        .evaluate(context(NO_MATCH, no_paper))["found_when_expected"]
        .value
    )
    assert (
        not FoundWhenExpected().evaluate(context(NO_MATCH))["found_when_expected"].value
    )


def test_keeps_rules_passes_when_both_rules_hold() -> None:
    results = KeepsRules(CURRENT_YEAR).evaluate(context(answer()))
    assert results["year_rule"].value
    assert results["citation_rule"].value


def test_keeps_rules_names_the_broken_rule() -> None:
    results = KeepsRules(CURRENT_YEAR).evaluate(context(answer(year=2023)))
    assert not results["year_rule"].value
    assert results["year_rule"].reason == "year is 2023, needs < 2021"


def test_keeps_rules_skips_rules_the_case_does_not_have() -> None:
    no_rules = CaseCriteria(covers=[Covers.BROAD_TOPIC], relevant_if="Anything.")
    assert KeepsRules(CURRENT_YEAR).evaluate(context(answer(), no_rules)) == {}


def test_keeps_rules_checks_recent_with_the_current_year() -> None:
    recent = CaseCriteria(covers=[Covers.YEAR_AFTER], recent=True, relevant_if="x")
    results = KeepsRules(CURRENT_YEAR).evaluate(context(answer(), recent))
    assert not results["year_rule"].value  # 2020 is not in the last 3 years


def test_valid_source_needs_a_doi_or_openalex_link() -> None:
    assert ValidSource().evaluate(context(answer()))["valid_source"].value
    made_up = answer(url="https://example.org/paper")
    assert not ValidSource().evaluate(context(made_up))["valid_source"].value


def test_facts_must_match_a_paper_the_search_returned() -> None:
    assert FactsMatchSearch().evaluate(context(answer()))["facts_match_search"].value
    wrong_count = answer(citation_count=99999)
    assert (
        not FactsMatchSearch()
        .evaluate(context(wrong_count))["facts_match_search"]
        .value
    )


def test_explanation_may_repeat_the_facts_and_the_request() -> None:
    text = "Published in 2020 with 10,277 citations; you asked for before 2021."
    results = ExplanationMatchesFacts().evaluate(context(answer(text)))
    assert results["explanation_matches_facts"].value


def test_explanation_with_a_wrong_year_or_count_fails() -> None:
    text = "Published in 2019, it has 12,000 citations."
    results = ExplanationMatchesFacts().evaluate(context(answer(text)))
    assert not results["explanation_matches_facts"].value
    assert results["explanation_matches_facts"].reason == (
        "numbers not in the facts: [2019, 12000]"
    )


def test_paper_checks_do_not_apply_to_a_no_match_answer() -> None:
    checks = [
        KeepsRules(CURRENT_YEAR),
        ValidSource(),
        FactsMatchSearch(),
        ExplanationMatchesFacts(),
    ]
    assert all(check.evaluate(context(NO_MATCH)) == {} for check in checks)
