"""Our own data shapes, shared by the search, the filter and the agent.

Each model says what the data looks like; other files decide where it comes from.
"""

from enum import StrEnum
from typing import Self

from pydantic import BaseModel, Field


class Paper(BaseModel):
    """One research paper, with facts taken from the search tool's data."""

    title: str
    authors: list[str]
    year: int | None
    citation_count: int | None
    citation_source: str
    url: str
    abstract: str | None


class Comparison(StrEnum):
    """How a paper's number must compare to a rule's value."""

    LESS_THAN = "<"
    AT_MOST = "<="
    MORE_THAN = ">"
    AT_LEAST = ">="
    EQUAL = "="
    ABOUT = "about"


class NumberRule(BaseModel):
    """One rule on a number, e.g. '> 2022' (after 2022) or '>= 100' (at least 100)."""

    comparison: Comparison
    value: int = Field(ge=0)


class Constraints(BaseModel):
    """What the user asked for. The LLM fills this in; Pydantic checks the shape."""

    topic: str = Field(min_length=1, description="What the paper should be about.")
    year: NumberRule | None = Field(
        default=None, description="Publication year rule, if the user gave one."
    )
    citations: NumberRule | None = Field(
        default=None, description="Citation count rule, if the user gave one."
    )
    recent: bool = Field(
        default=False, description="True if the user asked for a 'recent' paper."
    )


class Verdict(BaseModel):
    """The filter's decision on one paper: accepted, or rejected with reasons."""

    paper: Paper
    reasons: list[str] = Field(
        default_factory=list, description="Why the paper fails; empty if it passes."
    )

    @property
    def accepted(self) -> bool:
        return not self.reasons


class AllowedRange(BaseModel):
    """The whole numbers a rule allows, both ends included. None = no limit."""

    low: int | None = None
    high: int | None = None

    def contains(self, number: int) -> bool:
        above_low = self.low is None or number >= self.low
        below_high = self.high is None or number <= self.high
        return above_low and below_high

    @property
    def is_empty(self) -> bool:
        """True if no number fits, e.g. low 2024 and high 2014."""
        return self.low is not None and self.high is not None and self.low > self.high


class ResolvedRule(BaseModel):
    """A user's rule together with the exact range of numbers it allows."""

    rule: NumberRule
    allowed: AllowedRange


class PaperAnswer(BaseModel):
    """The agent's final answer.

    Facts are copied from a Paper (the tool's data); only `explanation` and
    `uncertainty` come from the LLM.
    """

    title: str
    authors: list[str]
    year: int | None
    citation_count: int | None
    citation_source: str
    url: str
    explanation: str
    uncertainty: str | None = None

    @classmethod
    def from_paper(
        cls, paper: Paper, explanation: str, uncertainty: str | None = None
    ) -> Self:
        """Build the answer: facts from the paper, words from the LLM."""
        return cls(
            title=paper.title,
            authors=paper.authors,
            year=paper.year,
            citation_count=paper.citation_count,
            citation_source=paper.citation_source,
            url=paper.url,
            explanation=explanation,
            uncertainty=uncertainty,
        )


class RelevanceJudgement(BaseModel):
    """The LLM's verdict on the candidates: which one fits best, and why."""

    paper_number: int | None = Field(
        description="Number of the best matching candidate, or null if none fits."
    )
    explanation: str = Field(
        description="Why it matches, in the form the user asked for (or why none fit)."
    )
    uncertainty: str | None = Field(
        default=None, description="Any doubts about the match; null if none."
    )
    search_words: str | None = Field(
        default=None,
        description="If no candidate fits: better search words to try. Else null.",
    )

    def chosen_from(self, candidates: list[Paper]) -> Paper | None:
        """The paper the number points at (numbers start at 1), or None."""
        if self.paper_number is None:
            return None
        return candidates[self.paper_number - 1]


class RelevanceOutcome(BaseModel):
    """Result of the relevance step: the chosen paper (or None) and the LLM's words."""

    paper: Paper | None
    explanation: str
    uncertainty: str | None
    extra_searches: int  # searches after the first: by the tool or the code fallback
