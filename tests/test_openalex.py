"""Tests for openalex.py. Uses saved sample data, never the live API."""

from openalex import CITATION_SOURCE, paper_from_openalex, rebuild_abstract

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
