"""Our own data shapes, shared by the search, the filter and the agent.

Each model says what the data looks like; other files decide where it comes from.
"""

from pydantic import BaseModel


class Paper(BaseModel):
    """One research paper, with facts taken from the search tool's data."""

    title: str
    authors: list[str]
    year: int | None
    citation_count: int | None
    citation_source: str
    url: str
    abstract: str | None
