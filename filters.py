"""Checks papers against the user's constraints.

Plain code, no LLM: comparing numbers must be exact.
"""

import operator
from collections.abc import Callable

from models import Comparison, Constraints, NumberRule, Paper, Verdict

RECENT_YEARS = 3  # "recent" = this year and the two before it
YEAR_ABOUT_MARGIN = 1  # "around 2015" = 2014 to 2016
CITATION_ABOUT_FRACTION = 0.2  # "about 1000 citations" = 800 to 1200

# Python's built-in comparison functions, one per Comparison (except ABOUT).
COMPARE: dict[Comparison, Callable[[int, int], bool]] = {
    Comparison.LESS_THAN: operator.lt,
    Comparison.AT_MOST: operator.le,
    Comparison.MORE_THAN: operator.gt,
    Comparison.AT_LEAST: operator.ge,
    Comparison.EQUAL: operator.eq,
}


def filter_papers(
    papers: list[Paper], constraints: Constraints, current_year: int
) -> list[Verdict]:
    """Give a verdict for every paper, in the same order."""
    return [check_paper(paper, constraints, current_year) for paper in papers]


def check_paper(paper: Paper, constraints: Constraints, current_year: int) -> Verdict:
    """Check one paper against every rule; collect a reason for each rule it fails."""
    results = [
        _check_number("year", paper.year, rule, YEAR_ABOUT_MARGIN)
        for rule in _year_rules(constraints, current_year)
    ]
    if constraints.citations:
        rule = constraints.citations
        margin = rule.value * CITATION_ABOUT_FRACTION
        results.append(_check_number("citations", paper.citation_count, rule, margin))
    reasons = [reason for reason in results if reason is not None]
    return Verdict(paper=paper, reasons=reasons)


def _year_rules(constraints: Constraints, current_year: int) -> list[NumberRule]:
    """The user's year rule, plus 'recent' turned into an ordinary year rule."""
    rules = [constraints.year] if constraints.year else []
    if constraints.recent:
        first_recent_year = current_year - RECENT_YEARS + 1
        rules.append(
            NumberRule(comparison=Comparison.AT_LEAST, value=first_recent_year)
        )
    return rules


def _check_number(
    label: str, actual: int | None, rule: NumberRule, about_margin: float
) -> str | None:
    """Return why `actual` fails `rule`, or None if it passes. A missing number fails."""
    if actual is not None and _matches(actual, rule, about_margin):
        return None
    shown = "unknown" if actual is None else str(actual)
    return f"{label} is {shown}, needs {_describe(rule, about_margin)}"


def _matches(actual: int, rule: NumberRule, about_margin: float) -> bool:
    if rule.comparison is Comparison.ABOUT:
        return abs(actual - rule.value) <= about_margin
    return COMPARE[rule.comparison](actual, rule.value)


def _describe(rule: NumberRule, about_margin: float) -> str:
    """A rule in words for a reason, e.g. '< 2015' or 'about 1000 (±200)'."""
    if rule.comparison is Comparison.ABOUT:
        return f"about {rule.value} (±{about_margin:g})"
    return f"{rule.comparison} {rule.value}"
