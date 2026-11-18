"""The evaluation set: test requests, each with its own pass criteria.

Data only, no checks: the checks (next step) compare every answer with the
criteria written here. The expected rules are written by hand, so a check never
trusts the rules the LLM read from the request.
"""

from enum import StrEnum

from pydantic import BaseModel, Field
from pydantic_evals import Case, Dataset

from models import Comparison, Constraints, NoMatch, NumberRule, Paper, PaperAnswer


class Covers(StrEnum):
    """The kinds of request the brief says the set must include."""

    BROAD_TOPIC = "broad topic"
    NARROW_TOPIC = "narrow topic"
    YEAR_BEFORE = "before a year"
    YEAR_AFTER = "after a year"
    YEAR_EXACT = "exact year"
    MIN_CITATIONS = "minimum citations"
    NO_GOOD_PAPER = "no good paper"
    AMBIGUOUS = "ambiguous request"


class CaseCriteria(BaseModel):
    """What a correct answer to one test request looks like."""

    covers: list[Covers] = Field(min_length=1)
    year: NumberRule | None = Field(default=None, description="Year rule it must keep")
    citations: NumberRule | None = Field(
        default=None, description="Citation rule it must keep"
    )
    recent: bool = Field(default=False, description="Must be from the last 3 years")
    expect_paper: bool = Field(
        default=True, description="False when 'No matching paper found' is right"
    )
    relevant_if: str = Field(
        min_length=1, description="What a relevant paper is about (for the rubric)"
    )

    def as_constraints(self, request: str) -> Constraints:
        """The hand-written rules in the shape rules.py reads (topic = the request)."""
        return Constraints(
            topic=request, year=self.year, citations=self.citations, recent=self.recent
        )


Answer = PaperAnswer | NoMatch


class RunResult(BaseModel):
    """What one test run produced: the answer, plus every paper the searches returned."""

    answer: Answer
    papers_seen: list[Paper] = Field(description="The real OpenAlex data, to compare")
    searches: int = Field(ge=1, description="1, or more if the agent searched again")


def rule(comparison: str, value: int) -> NumberRule:
    """Short way to write a rule, e.g. rule(">", 2022)."""
    return NumberRule(comparison=Comparison(comparison), value=value)


EVALUATION_SET: Dataset[str, RunResult, CaseCriteria] = Dataset(
    name="research_scout",
    cases=[
        Case(
            name="brief_llm_agents_for_software",
            inputs="Find a research paper about LLM agents for software engineering "
            "that was published after 2022 and has at least 100 citations. Explain "
            "why the paper is relevant and provide the source of the citation count.",
            metadata=CaseCriteria(
                covers=[Covers.NARROW_TOPIC, Covers.YEAR_AFTER, Covers.MIN_CITATIONS],
                year=rule(">", 2022),
                citations=rule(">=", 100),
                relevant_if="LLM-based agents doing software engineering tasks.",
            ),
        ),
        Case(
            name="brief_rag_before_2021",
            inputs="Find a paper about retrieval-augmented generation published "
            "before 2021 with more than 500 citations. Summarize its contribution "
            "in 5-7 sentences.",
            metadata=CaseCriteria(
                covers=[Covers.YEAR_BEFORE, Covers.MIN_CITATIONS],
                year=rule("<", 2021),
                citations=rule(">", 500),
                relevant_if="Retrieval-augmented generation; summary is 5-7 sentences.",
            ),
        ),
        Case(
            name="brief_recent_tool_using_agents",
            inputs="Find a recent paper about AI agents using tools and explain "
            "whether it would be useful for someone building autonomous software "
            "agents.",
            metadata=CaseCriteria(
                covers=[Covers.YEAR_AFTER],
                recent=True,
                relevant_if="AI agents calling tools; says if useful for autonomy.",
            ),
        ),
        Case(
            name="broad_machine_learning",
            inputs="Find a paper about machine learning.",
            metadata=CaseCriteria(
                covers=[Covers.BROAD_TOPIC],
                relevant_if="Any machine learning paper.",
            ),
        ),
        Case(
            name="broad_computer_vision_highly_cited",
            inputs="Find a paper about computer vision with at least 10000 citations.",
            metadata=CaseCriteria(
                covers=[Covers.BROAD_TOPIC, Covers.MIN_CITATIONS],
                citations=rule(">=", 10000),
                relevant_if="Any computer vision paper.",
            ),
        ),
        Case(
            name="narrow_gnn_before_2015",
            inputs="A paper on graph neural networks from before 2015 with at least "
            "1000 citations.",
            metadata=CaseCriteria(
                covers=[Covers.NARROW_TOPIC, Covers.YEAR_BEFORE, Covers.MIN_CITATIONS],
                year=rule("<", 2015),
                citations=rule(">=", 1000),
                relevant_if="Neural networks that work on graph-structured data.",
            ),
        ),
        Case(
            name="exact_year_transformer_2017",
            inputs="Find a paper about the transformer architecture published in 2017.",
            metadata=CaseCriteria(
                covers=[Covers.YEAR_EXACT],
                year=rule("=", 2017),
                relevant_if="The transformer neural network (attention) architecture.",
            ),
        ),
        Case(
            name="narrow_federated_medical_2020",
            inputs="Find a paper on federated learning for medical imaging published "
            "in 2020 with more than 200 citations.",
            metadata=CaseCriteria(
                covers=[Covers.NARROW_TOPIC, Covers.YEAR_EXACT, Covers.MIN_CITATIONS],
                year=rule("=", 2020),
                citations=rule(">", 200),
                relevant_if="Federated learning applied to medical images.",
            ),
        ),
        Case(
            name="ambiguous_around_numbers",
            inputs="A paper about contrastive learning from 2019 or later with around "
            "1000 citations.",
            metadata=CaseCriteria(
                covers=[Covers.YEAR_AFTER, Covers.AMBIGUOUS],
                year=rule(">=", 2019),
                citations=rule("about", 1000),
                relevant_if="Contrastive (self-supervised) representation learning.",
            ),
        ),
        Case(
            name="ambiguous_transformers",
            inputs="something about transformers",
            metadata=CaseCriteria(
                covers=[Covers.BROAD_TOPIC, Covers.AMBIGUOUS],
                relevant_if="Transformer models, or power transformers if the "
                "uncertainty field mentions the double meaning.",
            ),
        ),
        Case(
            name="no_paper_video_diffusion_before_2012",
            inputs="Find a paper about diffusion models for video generation published "
            "before 2012 with more than 1000 citations.",
            metadata=CaseCriteria(
                covers=[Covers.NO_GOOD_PAPER, Covers.YEAR_BEFORE, Covers.MIN_CITATIONS],
                year=rule("<", 2012),
                citations=rule(">", 1000),
                expect_paper=False,
                relevant_if="None exists: video diffusion models are from after 2020.",
            ),
        ),
        Case(
            name="no_paper_llm_knitting_before_2015",
            inputs="A paper about using large language models to grade knitting "
            "patterns, published before 2015.",
            metadata=CaseCriteria(
                covers=[Covers.NO_GOOD_PAPER, Covers.NARROW_TOPIC, Covers.YEAR_BEFORE],
                year=rule("<", 2015),
                expect_paper=False,
                relevant_if="None exists: LLMs did not exist before 2015.",
            ),
        ),
    ],
)
