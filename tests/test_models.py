"""Tests for models.py: the shapes accept good data and reject bad data."""

import pytest
from pydantic import ValidationError

from models import Comparison, Constraints, NumberRule, Paper, PaperAnswer


def test_constraints_read_from_llm_style_json() -> None:
    # Roughly what the LLM will send for:
    # "a paper on RAG published before 2021 with more than 500 citations"
    llm_json = """{
        "topic": "retrieval-augmented generation",
        "year": {"comparison": "<", "value": 2021},
        "citations": {"comparison": ">", "value": 500}
    }"""

    constraints = Constraints.model_validate_json(llm_json)

    assert constraints.topic == "retrieval-augmented generation"
    assert constraints.year == NumberRule(comparison=Comparison.LESS_THAN, value=2021)
    assert constraints.citations == NumberRule(
        comparison=Comparison.MORE_THAN, value=500
    )
    assert constraints.recent is False


def test_only_topic_is_required() -> None:
    constraints = Constraints(topic="graph neural networks")

    assert constraints.year is None
    assert constraints.citations is None
    assert constraints.recent is False


def test_unknown_comparison_is_rejected() -> None:
    with pytest.raises(ValidationError):
        NumberRule.model_validate({"comparison": "roughly", "value": 100})


def test_negative_value_is_rejected() -> None:
    with pytest.raises(ValidationError):
        NumberRule(comparison=Comparison.AT_LEAST, value=-1)


def test_empty_topic_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Constraints(topic="")


def test_answer_copies_every_fact_from_the_paper() -> None:
    paper = Paper(
        title="Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
        authors=["Patrick Lewis", "Ethan Perez"],
        year=2020,
        citation_count=10277,
        citation_source="OpenAlex",
        url="https://doi.org/10.48550/arxiv.2005.11401",
        abstract="Large pre-trained language models ...",
    )

    answer = PaperAnswer.from_paper(
        paper, explanation="Introduces RAG.", uncertainty="None worth noting."
    )

    facts = answer.model_dump(exclude={"explanation", "uncertainty"})
    assert facts == paper.model_dump(exclude={"abstract"})
    assert answer.explanation == "Introduces RAG."
    assert answer.uncertainty == "None worth noting."


def test_answer_uncertainty_is_optional() -> None:
    paper = Paper(
        title="T",
        authors=[],
        year=None,
        citation_count=None,
        citation_source="OpenAlex",
        url="https://openalex.org/W1",
        abstract=None,
    )

    answer = PaperAnswer.from_paper(paper, explanation="Fits the topic.")

    assert answer.uncertainty is None
    assert answer.year is None  # missing facts stay missing, never invented
