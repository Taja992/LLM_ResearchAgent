"""What each rule means, as a range of allowed whole numbers.

The one place that defines "about", "recent" and "or later". Both the filter and
the OpenAlex query use it, so they can never disagree. Plain code, no LLM.
"""

import math

from models import AllowedRange, Comparison, Constraints, NumberRule, ResolvedRule

RECENT_YEARS = 3  # "recent" = this year and the two before it
YEAR_ABOUT_MARGIN = 1  # "around 2015" = 2014 to 2016
CITATION_ABOUT_FRACTION = 0.2  # "about 1000 citations" = 800 to 1200


def allowed_range(rule: NumberRule, about_margin: float) -> AllowedRange:
    """The whole numbers a rule allows, e.g. '> 2022' -> 2023 and up."""
    value = rule.value
    match rule.comparison:
        case Comparison.LESS_THAN:
            return AllowedRange(high=value - 1)
        case Comparison.AT_MOST:
            return AllowedRange(high=value)
        case Comparison.MORE_THAN:
            return AllowedRange(low=value + 1)
        case Comparison.AT_LEAST:
            return AllowedRange(low=value)
        case Comparison.EQUAL:
            return AllowedRange(low=value, high=value)
        case Comparison.ABOUT:
            return AllowedRange(
                low=math.ceil(value - about_margin),
                high=math.floor(value + about_margin),
            )


def year_rules(constraints: Constraints, current_year: int) -> list[ResolvedRule]:
    """The user's year rule, plus 'recent' turned into an ordinary year rule."""
    rules = [constraints.year] if constraints.year else []
    if constraints.recent:
        first_recent_year = current_year - RECENT_YEARS + 1
        rules.append(
            NumberRule(comparison=Comparison.AT_LEAST, value=first_recent_year)
        )
    return [_resolve(rule, YEAR_ABOUT_MARGIN) for rule in rules]


def citation_rules(constraints: Constraints) -> list[ResolvedRule]:
    """The user's citation rule, if any (a list, so callers treat it like years)."""
    rule = constraints.citations
    if rule is None:
        return []
    return [_resolve(rule, rule.value * CITATION_ABOUT_FRACTION)]


def combined_range(rules: list[ResolvedRule]) -> AllowedRange:
    """One range that satisfies every rule at once (their overlap)."""
    lows = [r.allowed.low for r in rules if r.allowed.low is not None]
    highs = [r.allowed.high for r in rules if r.allowed.high is not None]
    return AllowedRange(low=max(lows, default=None), high=min(highs, default=None))


def _resolve(rule: NumberRule, about_margin: float) -> ResolvedRule:
    return ResolvedRule(rule=rule, allowed=allowed_range(rule, about_margin))
