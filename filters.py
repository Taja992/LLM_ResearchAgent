"""Checks papers against the user's constraints.

Plain code, no LLM: comparing numbers must be exact. What each rule allows is
defined in rules.py; this file only checks papers against it.
"""

from models import Comparison, Constraints, Paper, ResolvedRule, Verdict
from rules import citation_rules, year_rules


def filter_papers(
    papers: list[Paper], constraints: Constraints, current_year: int
) -> list[Verdict]:
    """Give a verdict for every paper, in the same order."""
    return [check_paper(paper, constraints, current_year) for paper in papers]


def check_paper(paper: Paper, constraints: Constraints, current_year: int) -> Verdict:
    """Check one paper against every rule; collect a reason for each rule it fails."""
    results = [
        _check_number("year", paper.year, rule)
        for rule in year_rules(constraints, current_year)
    ]
    results += [
        _check_number("citations", paper.citation_count, rule)
        for rule in citation_rules(constraints)
    ]
    reasons = [reason for reason in results if reason is not None]
    return Verdict(paper=paper, reasons=reasons)


def _check_number(label: str, actual: int | None, rule: ResolvedRule) -> str | None:
    """Return why `actual` fails `rule`, or None if it passes. A missing number fails."""
    if actual is not None and rule.allowed.contains(actual):
        return None
    shown = "unknown" if actual is None else str(actual)
    return f"{label} is {shown}, needs {_describe(rule)}"


def _describe(rule: ResolvedRule) -> str:
    """A rule in words for a reason, e.g. '< 2015' or 'about 1000 (800 to 1200)'."""
    comparison, value = rule.rule.comparison, rule.rule.value
    if comparison is Comparison.ABOUT:
        return f"about {value} ({rule.allowed.low} to {rule.allowed.high})"
    return f"{comparison} {value}"
