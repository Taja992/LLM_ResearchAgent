"""Paper data from OpenAlex (https://openalex.org), turned into our own Paper model.

Plain code, no LLM: every fact here is copied from OpenAlex's data.
"""

from typing import Any

from pydantic import BaseModel

CITATION_SOURCE = "OpenAlex"


class Paper(BaseModel):
    """One research paper, with facts taken from the search tool's data."""

    title: str
    authors: list[str]
    year: int | None
    citation_count: int | None
    citation_source: str
    url: str
    abstract: str | None


def rebuild_abstract(inverted_index: dict[str, list[int]] | None) -> str | None:
    """Turn OpenAlex's {word: [positions]} abstract back into normal text."""
    if not inverted_index:
        return None
    word_at: dict[int, str] = {}
    for word, positions in inverted_index.items():
        for position in positions:
            word_at[position] = word
    return " ".join(word_at[position] for position in sorted(word_at))


def paper_from_openalex(work: dict[str, Any]) -> Paper:
    """Convert one OpenAlex "work" (one item of the API's results list) into a Paper."""
    authors = [
        authorship["author"]["display_name"]
        for authorship in work.get("authorships", [])
    ]
    return Paper(
        title=work["display_name"],
        authors=authors,
        year=work.get("publication_year"),
        citation_count=work.get("cited_by_count"),
        citation_source=CITATION_SOURCE,
        # DOI link if there is one, else the paper's OpenAlex page
        url=work.get("doi") or work["id"],
        abstract=rebuild_abstract(work.get("abstract_inverted_index")),
    )
