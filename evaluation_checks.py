"""Automatic checks for the evaluation: the criteria plain code can verify exactly.

No LLM here: code graders are objective and repeatable. Each check returns named
results ({} means "doesn't apply", e.g. paper checks on a "no match" answer).
Rules always come from the test case's hand-written criteria, never from the LLM.
"""

import re
from dataclasses import dataclass

from pydantic_evals.evaluators import EvaluationReason, Evaluator, EvaluatorContext

from evaluation_cases import CaseCriteria, RunResult
from filters import check_number
from models import PaperAnswer, ResolvedRule, RuleField
from openalex import CITATION_SOURCE
from rules import citation_rules, year_rules

type Context = EvaluatorContext[str, RunResult, CaseCriteria]
type Results = dict[str, EvaluationReason]

VALID_LINK_PREFIXES = ("https://doi.org/", "https://openalex.org/")
FACT_FIELDS = {"title", "authors", "year", "citation_count", "url"}
# Each pattern has one (group): the number re.findall returns.
YEAR_IN_TEXT = re.compile(r"\b((?:19|20)\d{2})\b")
CITATIONS_IN_TEXT = re.compile(r"(\d[\d,]*)\s+citations")
NUMBER_IN_TEXT = re.compile(r"(\d[\d,]*)")


@dataclass
class FoundWhenExpected(Evaluator[str, RunResult, CaseCriteria]):
    """A paper was found if, and only if, the case expects one."""

    def evaluate(self, ctx: Context) -> Results:
        found = isinstance(ctx.output.answer, PaperAnswer)
        expected = _criteria(ctx).expect_paper
        reason = f"found a paper: {found}, expected one: {expected}"
        return {"found_when_expected": EvaluationReason(found == expected, reason)}


@dataclass
class KeepsRules(Evaluator[str, RunResult, CaseCriteria]):
    """The paper's year and citations keep the case's rules (reuses the filter's check)."""

    current_year: int

    def evaluate(self, ctx: Context) -> Results:
        answer = ctx.output.answer
        if not isinstance(answer, PaperAnswer):
            return {}
        constraints = _criteria(ctx).as_constraints(ctx.inputs)
        checks: dict[str, tuple[RuleField, int | None, list[ResolvedRule]]] = {
            "year_rule": (
                "year",
                answer.year,
                year_rules(constraints, self.current_year),
            ),
            "citation_rule": (
                "citations",
                answer.citation_count,
                citation_rules(constraints),
            ),
        }
        return {
            name: _all_kept(field, number, rules)
            for name, (field, number, rules) in checks.items()
            if rules
        }


@dataclass
class ValidSource(Evaluator[str, RunResult, CaseCriteria]):
    """The link is a DOI or OpenAlex link, and the citation source is OpenAlex."""

    def evaluate(self, ctx: Context) -> Results:
        answer = ctx.output.answer
        if not isinstance(answer, PaperAnswer):
            return {}
        valid = answer.url.startswith(VALID_LINK_PREFIXES) and (
            answer.citation_source == CITATION_SOURCE
        )
        reason = f"link {answer.url}, source {answer.citation_source}"
        return {"valid_source": EvaluationReason(valid, reason)}


@dataclass
class FactsMatchSearch(Evaluator[str, RunResult, CaseCriteria]):
    """No made-up facts: the answer equals a paper OpenAlex really returned."""

    def evaluate(self, ctx: Context) -> Results:
        answer = ctx.output.answer
        if not isinstance(answer, PaperAnswer):
            return {}
        facts = answer.model_dump(include=FACT_FIELDS)
        matches = any(
            paper.model_dump(include=FACT_FIELDS) == facts
            for paper in ctx.output.papers_seen
        )
        reason = None if matches else "no paper OpenAlex returned has these facts"
        return {"facts_match_search": EvaluationReason(matches, reason)}


@dataclass
class ExplanationMatchesFacts(Evaluator[str, RunResult, CaseCriteria]):
    """Years and citation counts in the explanation are the paper's (or the request's)."""

    def evaluate(self, ctx: Context) -> Results:
        answer = ctx.output.answer
        if not isinstance(answer, PaperAnswer):
            return {}
        request_numbers = _numbers_matching(NUMBER_IN_TEXT, ctx.inputs)
        allowed = {answer.year, answer.citation_count} | request_numbers
        mentioned = _numbers_matching(YEAR_IN_TEXT, answer.explanation)
        mentioned |= _numbers_matching(CITATIONS_IN_TEXT, answer.explanation)
        wrong = sorted(mentioned - allowed)
        reason = f"numbers not in the facts: {wrong}" if wrong else None
        return {"explanation_matches_facts": EvaluationReason(not wrong, reason)}


def _criteria(ctx: Context) -> CaseCriteria:
    if ctx.metadata is None:
        raise ValueError(f"Test case {ctx.name!r} has no criteria")
    return ctx.metadata


def _all_kept(
    field: RuleField, number: int | None, rules: list[ResolvedRule]
) -> EvaluationReason:
    """Pass if `number` keeps every rule; the reason lists the ones it breaks."""
    broken = [str(r) for rule in rules if (r := check_number(field, number, rule))]
    return EvaluationReason(not broken, "; ".join(broken) or None)


def _numbers_matching(pattern: re.Pattern[str], text: str) -> set[int]:
    """Whole numbers the pattern finds in the text; '1,052' counts as 1052."""
    return {int(number.replace(",", "")) for number in pattern.findall(text)}
