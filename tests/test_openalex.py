"""Tests for openalex.py. Uses saved sample data, never the live API."""

import httpx
import pytest

from models import Comparison, Constraints, NumberRule
from openalex import (
    API_KEY_ENV_VAR,
    CITATION_SOURCE,
    OPENALEX_WORKS_URL,
    paper_from_openalex,
    rebuild_abstract,
    search_openalex,
)

CURRENT_YEAR = 2026
TOPIC_ONLY = Constraints(topic="graph neural networks")

# Trimmed copy of a real OpenAlex result (fetched by hand on 2026-11-18).
SAMPLE_WORK = {
    "id": "https://openalex.org/W2116341502",
    "doi": "https://doi.org/10.1109/tnn.2008.2005605",
    "display_name": "The Graph Neural Network Model",
    "publication_year": 2008,
    "cited_by_count": 12638,
    "authorships": [
        {"author": {"display_name": "Franco Scarselli"}},
        {"author": {"display_name": "Marco Gori"}},
    ],
    "abstract_inverted_index": {
        "Many": [0],
        "underlying": [1],
        "data": [2, 4],
        "and": [3],
    },
}


def test_paper_copies_facts_from_openalex() -> None:
    paper = paper_from_openalex(SAMPLE_WORK)

    assert paper.title == "The Graph Neural Network Model"
    assert paper.authors == ["Franco Scarselli", "Marco Gori"]
    assert paper.year == 2008
    assert paper.citation_count == 12638
    assert paper.citation_source == CITATION_SOURCE
    assert paper.url == "https://doi.org/10.1109/tnn.2008.2005605"
    assert paper.abstract == "Many underlying data and data"


def test_missing_doi_falls_back_to_openalex_page() -> None:
    work = {**SAMPLE_WORK, "doi": None}

    assert paper_from_openalex(work).url == "https://openalex.org/W2116341502"


def test_missing_optional_fields_become_none_or_empty() -> None:
    work = {"id": "https://openalex.org/W1", "display_name": "Bare paper"}

    paper = paper_from_openalex(work)

    assert paper.authors == []
    assert paper.year is None
    assert paper.citation_count is None
    assert paper.abstract is None


def test_rebuild_abstract_puts_words_in_position_order() -> None:
    assert rebuild_abstract({"world": [1], "hello": [0]}) == "hello world"


def test_rebuild_abstract_handles_no_abstract() -> None:
    assert rebuild_abstract(None) is None
    assert rebuild_abstract({}) is None


def fake_openalex(
    seen: list[httpx.Request], status_code: int = 200
) -> httpx.MockTransport:
    """A fake network: records each request and answers with SAMPLE_WORK."""

    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(status_code, json={"results": [SAMPLE_WORK]})

    return httpx.MockTransport(handle)


def test_search_returns_papers_from_the_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)
    seen: list[httpx.Request] = []

    papers = search_openalex(TOPIC_ONLY, CURRENT_YEAR, transport=fake_openalex(seen))

    assert [paper.title for paper in papers] == ["The Graph Neural Network Model"]
    assert papers[0].citation_count == 12638


def test_search_sends_topic_and_no_key_when_none_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)
    seen: list[httpx.Request] = []

    search_openalex(TOPIC_ONLY, CURRENT_YEAR, transport=fake_openalex(seen))

    request = seen[0]
    assert str(request.url).startswith(OPENALEX_WORKS_URL)
    assert request.url.params["search"] == "graph neural networks"
    assert "api_key" not in request.url.params


def test_search_sends_api_key_when_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(API_KEY_ENV_VAR, "test-key")
    seen: list[httpx.Request] = []

    search_openalex(TOPIC_ONLY, CURRENT_YEAR, transport=fake_openalex(seen))

    assert seen[0].url.params["api_key"] == "test-key"


def test_search_raises_on_server_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)

    with pytest.raises(httpx.HTTPStatusError):
        search_openalex(
            TOPIC_ONLY, CURRENT_YEAR, transport=fake_openalex([], status_code=500)
        )


def rule(comparison: Comparison, value: int) -> NumberRule:
    return NumberRule(comparison=comparison, value=value)


def sent_filter(
    constraints: Constraints, monkeypatch: pytest.MonkeyPatch
) -> str | None:
    """Run a search on the fake network and return the 'filter' it sent, if any."""
    monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)
    seen: list[httpx.Request] = []
    search_openalex(constraints, CURRENT_YEAR, transport=fake_openalex(seen))
    return seen[0].url.params.get("filter")


@pytest.mark.parametrize(
    ("constraints", "expected_filter"),
    [
        (TOPIC_ONLY, None),
        (
            Constraints(topic="rag", year=rule(Comparison.MORE_THAN, 2022)),
            "publication_year:>2022",
        ),
        (  # OpenAlex has no >=, so "2022 or later" becomes ">2021"
            Constraints(topic="rag", year=rule(Comparison.AT_LEAST, 2022)),
            "publication_year:>2021",
        ),
        (
            Constraints(topic="rag", year=rule(Comparison.AT_MOST, 2015)),
            "publication_year:<2016",
        ),
        (
            Constraints(topic="rag", year=rule(Comparison.EQUAL, 2020)),
            "publication_year:2020",
        ),
        (
            Constraints(
                topic="rag",
                year=rule(Comparison.LESS_THAN, 2021),
                citations=rule(Comparison.ABOUT, 1000),
            ),
            "publication_year:<2021,cited_by_count:800-1200",
        ),
        (  # "recent" and "2022 or later" combine into one range: 2024 and up
            Constraints(topic="rag", year=rule(Comparison.AT_LEAST, 2022), recent=True),
            "publication_year:>2023",
        ),
    ],
)
def test_search_sends_rules_as_openalex_filter(
    constraints: Constraints,
    expected_filter: str | None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert sent_filter(constraints, monkeypatch) == expected_filter


def test_contradictory_rules_skip_the_search() -> None:
    seen: list[httpx.Request] = []
    constraints = Constraints(
        topic="rag", year=rule(Comparison.LESS_THAN, 2015), recent=True
    )

    papers = search_openalex(constraints, CURRENT_YEAR, transport=fake_openalex(seen))

    assert papers == []
    assert seen == []  # no request was made
