"""Tests for rules.py: what range of numbers each rule allows."""

import pytest

from models import AllowedRange, Comparison, Constraints, NumberRule
from rules import allowed_range, citation_rules, combined_range, year_rules

CURRENT_YEAR = 2026


def rule(comparison: Comparison, value: int) -> NumberRule:
    return NumberRule(comparison=comparison, value=value)


@pytest.mark.parametrize(
    ("number_rule", "margin", "expected"),
    [
        (rule(Comparison.LESS_THAN, 2015), 1, AllowedRange(high=2014)),
        (rule(Comparison.AT_MOST, 2015), 1, AllowedRange(high=2015)),
        (rule(Comparison.MORE_THAN, 2022), 1, AllowedRange(low=2023)),
        (rule(Comparison.AT_LEAST, 2022), 1, AllowedRange(low=2022)),
        (rule(Comparison.EQUAL, 2020), 1, AllowedRange(low=2020, high=2020)),
        (rule(Comparison.ABOUT, 2015), 1, AllowedRange(low=2014, high=2016)),
        # A margin that isn't whole: only whole numbers inside it count.
        (rule(Comparison.ABOUT, 1234), 246.8, AllowedRange(low=988, high=1480)),
    ],
)
def test_allowed_range(
    number_rule: NumberRule, margin: float, expected: AllowedRange
) -> None:
    assert allowed_range(number_rule, margin) == expected


def test_about_citations_means_twenty_percent() -> None:
    constraints = Constraints(topic="t", citations=rule(Comparison.ABOUT, 1000))

    [resolved] = citation_rules(constraints)

    assert resolved.allowed == AllowedRange(low=800, high=1200)


def test_recent_becomes_a_year_rule() -> None:
    [resolved] = year_rules(Constraints(topic="t", recent=True), CURRENT_YEAR)

    assert resolved.rule == rule(Comparison.AT_LEAST, 2024)


def test_combined_range_is_the_overlap() -> None:
    constraints = Constraints(
        topic="t", year=rule(Comparison.LESS_THAN, 2026), recent=True
    )

    combined = combined_range(year_rules(constraints, CURRENT_YEAR))

    assert combined == AllowedRange(low=2024, high=2025)


def test_contradictory_rules_give_an_empty_range() -> None:
    constraints = Constraints(
        topic="t", year=rule(Comparison.LESS_THAN, 2015), recent=True
    )

    assert combined_range(year_rules(constraints, CURRENT_YEAR)).is_empty


def test_no_rules_means_no_limits() -> None:
    assert combined_range([]) == AllowedRange()
