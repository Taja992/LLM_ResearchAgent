"""Tests for evaluation_cases.py: the test set meets the brief and is consistent."""

import pytest

from evaluation_cases import EVALUATION_SET, CaseCriteria, Covers
from models import Comparison

MIN_CASES = 10  # the brief asks for at least 10 test prompts
LOWER_LIMIT = {Comparison.MORE_THAN, Comparison.AT_LEAST}
UPPER_LIMIT = {Comparison.LESS_THAN, Comparison.AT_MOST}
YEAR_COMPARISONS = {
    Covers.YEAR_BEFORE: UPPER_LIMIT,
    Covers.YEAR_AFTER: LOWER_LIMIT,
    Covers.YEAR_EXACT: {Comparison.EQUAL},
}
CRITERIA = [case.metadata for case in EVALUATION_SET.cases if case.metadata]


def test_set_has_enough_cases_each_with_a_unique_name_and_criteria() -> None:
    names = [case.name for case in EVALUATION_SET.cases]
    assert len(names) >= MIN_CASES
    assert len(set(names)) == len(names)
    assert len(CRITERIA) == len(names)  # no case without criteria


def test_every_kind_of_request_from_the_brief_is_covered() -> None:
    covered = {kind for criteria in CRITERIA for kind in criteria.covers}
    assert covered == set(Covers)


@pytest.mark.parametrize("criteria", CRITERIA)
def test_criteria_agree_with_what_the_case_covers(criteria: CaseCriteria) -> None:
    assert criteria.expect_paper == (Covers.NO_GOOD_PAPER not in criteria.covers)
    if Covers.MIN_CITATIONS in criteria.covers:
        assert criteria.citations is not None
        assert criteria.citations.comparison in LOWER_LIMIT
    for kind, allowed in YEAR_COMPARISONS.items():
        if kind in criteria.covers and not criteria.recent:
            assert criteria.year is not None
            assert criteria.year.comparison in allowed
