"""Our own data shapes, shared by the search, the filter and the agent.

Each model says what the data looks like; other files decide where it comes from.
"""

from enum import StrEnum

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
