"""Paper data from OpenAlex (https://openalex.org), turned into our own Paper model.

Plain code, no LLM: every fact here is copied from OpenAlex's data.
"""

import os
from typing import Any

import httpx

from models import Paper

CITATION_SOURCE = "OpenAlex"
OPENALEX_WORKS_URL = "https://api.openalex.org/works"
API_KEY_ENV_VAR = "OPENALEX_API_KEY"  # optional; read from the environment (.env)
RESULTS_PER_SEARCH = 25
REQUEST_TIMEOUT_SECONDS = 10.0
# Only ask OpenAlex for the fields paper_from_openalex() uses: smaller, faster responses.
SELECTED_FIELDS = (
    "id,doi,display_name,publication_year,"
    "cited_by_count,authorships,abstract_inverted_index"
)


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


def search_openalex(
    topic: str, transport: httpx.BaseTransport | None = None
) -> list[Paper]:
    """Search OpenAlex for papers on a topic and return them as Papers.

    `transport` is only for tests: they pass a fake network so no real request is made.
    """
    params: dict[str, str | int] = {
        "search": topic,
        "per_page": RESULTS_PER_SEARCH,
        "select": SELECTED_FIELDS,
    }
    api_key = os.getenv(API_KEY_ENV_VAR)
    if api_key:
        params["api_key"] = api_key

    with httpx.Client(transport=transport, timeout=REQUEST_TIMEOUT_SECONDS) as client:
        response = client.get(OPENALEX_WORKS_URL, params=params)
    response.raise_for_status()  # stop with an error on 4xx/5xx instead of using bad data
    return [paper_from_openalex(work) for work in response.json()["results"]]
