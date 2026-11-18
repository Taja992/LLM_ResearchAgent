"""Tests for filters.py: every comparison, its edges, and the reasons given."""

import pytest

from filters import check_paper, filter_papers
from models import Comparison, Constraints, NumberRule, Paper

CURRENT_YEAR = 2026
TOPIC = "anything"


def make_paper(year: int | None = 2020, citations: int | None = 100) -> Paper:
    return Paper(
        title="A paper",
        authors=[],
        year=year,
        citation_count=citations,
        citation_source="test",
        url="https://example.org",
        abstract=None,
    )


def rule(comparison: Comparison, value: int) -> NumberRule:
    return NumberRule(comparison=comparison, value=value)


@pytest.mark.parametrize(
    ("year_rule", "year", "accepted"),
    [
        (rule(Comparison.MORE_THAN, 2022), 2022, False),  # "after 2022"
        (rule(Comparison.MORE_THAN, 2022), 2023, True),
        (rule(Comparison.AT_LEAST, 2022), 2022, True),  # "2022 or later"
        (rule(Comparison.LESS_THAN, 2015), 2015, False),  # "before 2015"
        (rule(Comparison.LESS_THAN, 2015), 2014, True),
        (rule(Comparison.AT_MOST, 2015), 2015, True),  # "2015 or earlier"
        (rule(Comparison.EQUAL, 2020), 2020, True),  # "in 2020"
        (rule(Comparison.EQUAL, 2020), 2021, False),
        (rule(Comparison.ABOUT, 2015), 2014, True),  # "around 2015" = 2014-2016
        (rule(Comparison.ABOUT, 2015), 2016, True),
        (rule(Comparison.ABOUT, 2015), 2017, False),
    ],
)
def test_year_rules(year_rule: NumberRule, year: int, accepted: bool) -> None:
    constraints = Constraints(topic=TOPIC, year=year_rule)

    verdict = check_paper(make_paper(year=year), constraints, CURRENT_YEAR)

    assert verdict.accepted is accepted


@pytest.mark.parametrize(
    ("citation_rule", "citations", "accepted"),
    [
        (rule(Comparison.AT_LEAST, 100), 100, True),  # "at least 100"
        (rule(Comparison.AT_LEAST, 100), 99, False),
        (rule(Comparison.MORE_THAN, 500), 500, False),  # "more than 500"
        (rule(Comparison.MORE_THAN, 500), 501, True),
        (rule(Comparison.AT_MOST, 50), 50, True),  # "at most 50"
        (rule(Comparison.ABOUT, 1000), 800, True),  # "about 1000" = 800-1200
        (rule(Comparison.ABOUT, 1000), 1200, True),
        (rule(Comparison.ABOUT, 1000), 799, False),
    ],
)
def test_citation_rules(
    citation_rule: NumberRule, citations: int, accepted: bool
) -> None:
    constraints = Constraints(topic=TOPIC, citations=citation_rule)

    verdict = check_paper(make_paper(citations=citations), constraints, CURRENT_YEAR)

    assert verdict.accepted is accepted


@pytest.mark.parametrize(("year", "accepted"), [(2024, True), (2023, False)])
def test_recent_means_last_three_years(year: int, accepted: bool) -> None:
    constraints = Constraints(topic=TOPIC, recent=True)

    verdict = check_paper(make_paper(year=year), constraints, CURRENT_YEAR)

    assert verdict.accepted is accepted


def test_no_rules_accepts_any_paper() -> None:
    verdict = check_paper(make_paper(), Constraints(topic=TOPIC), CURRENT_YEAR)

    assert verdict.accepted
    assert verdict.reasons == []


def test_missing_number_is_rejected_not_guessed() -> None:
    constraints = Constraints(topic=TOPIC, year=rule(Comparison.LESS_THAN, 2015))

    verdict = check_paper(make_paper(year=None), constraints, CURRENT_YEAR)

    assert verdict.reasons == ["year is unknown, needs < 2015"]


def test_every_failed_rule_gives_a_reason() -> None:
    constraints = Constraints(
        topic=TOPIC,
        year=rule(Comparison.LESS_THAN, 2015),
        citations=rule(Comparison.ABOUT, 1000),
    )

    verdict = check_paper(
        make_paper(year=2017, citations=50), constraints, CURRENT_YEAR
    )

    assert verdict.reasons == [
        "year is 2017, needs < 2015",
        "citations is 50, needs about 1000 (800 to 1200)",
    ]


def test_filter_papers_gives_one_verdict_per_paper_in_order() -> None:
    constraints = Constraints(topic=TOPIC, year=rule(Comparison.MORE_THAN, 2022))
    papers = [make_paper(year=2020), make_paper(year=2024)]

    verdicts = filter_papers(papers, constraints, CURRENT_YEAR)

    assert [verdict.accepted for verdict in verdicts] == [False, True]
