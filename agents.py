"""The LLM steps of the workflow. Everything else in the project is plain code.

Each LLM step returns a Pydantic model, so its answer is checked before code uses it.
NativeOutput makes the model server itself return JSON in that shape: small local
models often answer in plain text when asked to use an output tool instead.
"""

import textwrap
from collections.abc import Callable
from dataclasses import dataclass

from pydantic_ai import Agent, ModelRetry, NativeOutput, RunContext
from pydantic_ai.models import Model

from filters import filter_papers
from models import Constraints, Paper, RelevanceJudgement, RelevanceOutcome
from openalex import search_openalex

OUTPUT_RETRIES = 3  # how often the LLM may retry an answer that doesn't fit the model
# Small local models have a short context window: keep the candidate list short.
MAX_CANDIDATES_FOR_LLM = 10
MAX_ABSTRACT_CHARS = 500
MAX_EXTRA_SEARCHES = 1  # the relevance LLM may search again once per request

CONSTRAINTS_INSTRUCTIONS = """\
Read the user's request for a research paper and fill in its constraints.

- topic: the subject only, as short search words. No years or citation numbers.
- year and citations: pick the comparison that matches the wording and copy the
  number exactly as written. Never calculate a different number.
  "more than", "over", "after" and "before" do NOT include the number itself.
    "after 2022"                       -> ">" 2022
    "2022 or later", "since 2022"      -> ">=" 2022
    "before 2015"                      -> "<" 2015
    "2015 or earlier"                  -> "<=" 2015
    "in 2020"                          -> "=" 2020
    "more than 500", "over 500"        -> ">" 500
    "at least 100", "100 or more"      -> ">=" 100
    "fewer than 50", "under 50"        -> "<" 50
    "at most 50", "no more than 50"    -> "<=" 50
    "about", "around", "roughly", "approximately", "~" -> "about"
- Leave year or citations empty if the user gave no rule for it. Never invent one.
- recent: true only if the request contains a word like "recent", "new", "latest"
  or "newest". A year rule such as "after 2022" is NOT a request for recent.
  Do not turn "recent" into a year.
"""

constraints_agent = Agent(
    output_type=NativeOutput(Constraints),
    instructions=CONSTRAINTS_INSTRUCTIONS,
    retries=OUTPUT_RETRIES,
)


def extract_constraints(request: str, model: Model | str) -> Constraints:
    """LLM step 1: turn the user's free-text request into checked Constraints."""
    return constraints_agent.run_sync(request, model=model).output


RELEVANCE_INSTRUCTIONS = """\
You judge which research paper best fits a user's request. You get the request and
a numbered list of candidate papers that already meet the year and citation rules.

- paper_number: the number of the candidate most clearly about the requested topic.
  Use null if none of them is really about it.
- If no candidate is really about the topic (or there are none): set paper_number
  to null and put better search words in search_words. You may also call the
  search_papers tool with those words, then choose from the longer list.
- explanation: do exactly what the request asks for. If it asks for a summary of
  5-7 sentences, write 5-7 sentences. If it asks "would it be useful for ...",
  answer that question. If it asks for nothing special, explain in 2-3 sentences
  why the paper matches. If none fits, say why.
- uncertainty: real doubts, for example the topic only partly matches or the
  abstract is missing. Use null if there are none.
- Use only the titles and abstracts given. Do not add facts such as authors, years
  or citation counts that are not in the list.
"""


@dataclass
class RelevanceDeps:
    """What the relevance step's tool and validator need during one run."""

    constraints: Constraints
    current_year: int
    candidates: list[Paper]  # grows when search_papers finds new papers
    search: Callable[[Constraints, int], list[Paper]]  # tests pass a fake
    searches_used: int = 0


relevance_agent = Agent(
    output_type=NativeOutput(RelevanceJudgement),
    deps_type=RelevanceDeps,
    instructions=RELEVANCE_INSTRUCTIONS,
    retries=OUTPUT_RETRIES,
)


@relevance_agent.tool
def search_papers(ctx: RunContext[RelevanceDeps], query: str) -> str:
    """Search for more papers with different words, if no candidate fits.

    The same year and citation rules apply. New papers are numbered after the
    existing candidates.

    Args:
        query: Better search words for the topic the user asked about.
    """
    deps = ctx.deps
    if deps.searches_used >= MAX_EXTRA_SEARCHES:
        return "No more searches allowed. Choose a candidate, or answer null."
    new_papers = _search_more(deps, query)
    if not new_papers:
        return "The search found no new papers that meet the rules."
    first_number = len(deps.candidates) - len(new_papers) + 1
    return _format_candidates(new_papers, first_number)


def _search_more(deps: RelevanceDeps, query: str) -> list[Paper]:
    """Code, not LLM: one extra search with new words, filtered, without repeats.

    Used by the search_papers tool and by the fallback in judge_relevance.
    """
    deps.searches_used += 1
    constraints = deps.constraints.model_copy(update={"topic": query})
    found = deps.search(constraints, deps.current_year)
    verdicts = filter_papers(found, constraints, deps.current_year)
    shown_urls = {paper.url for paper in deps.candidates}
    new_papers = [
        verdict.paper
        for verdict in verdicts
        if verdict.accepted and verdict.paper.url not in shown_urls
    ][:MAX_CANDIDATES_FOR_LLM]
    deps.candidates.extend(new_papers)
    return new_papers


@relevance_agent.output_validator
def _check_paper_number(
    ctx: RunContext[RelevanceDeps], judgement: RelevanceJudgement
) -> RelevanceJudgement:
    """Code checks the LLM: the number must point at a shown candidate."""
    number, shown = judgement.paper_number, len(ctx.deps.candidates)
    if number is not None and not 1 <= number <= shown:
        raise ModelRetry(f"paper_number must be between 1 and {shown}, or null.")
    return judgement


def judge_relevance(
    request: str,
    candidates: list[Paper],
    constraints: Constraints,
    current_year: int,
    model: Model | str,
    search: Callable[[Constraints, int], list[Paper]] = search_openalex,
) -> RelevanceOutcome:
    """LLM step 4: pick the candidate that best fits the request, and explain why."""
    deps = RelevanceDeps(
        constraints=constraints,
        current_year=current_year,
        candidates=list(candidates[:MAX_CANDIDATES_FOR_LLM]),  # a copy: it may grow
        search=search,
    )
    judgement = _search_again_if_needed(
        _ask(request, deps, model), request, deps, model
    )
    return RelevanceOutcome(
        paper=judgement.chosen_from(deps.candidates),
        explanation=judgement.explanation,
        uncertainty=judgement.uncertainty,
        extra_searches=deps.searches_used,
    )


def _search_again_if_needed(
    judgement: RelevanceJudgement,
    request: str,
    deps: RelevanceDeps,
    model: Model | str,
) -> RelevanceJudgement:
    """Fallback: small models suggest new words instead of calling the tool.

    If nothing fit and no search happened yet, code searches with the LLM's words
    and asks again with the longer list.
    """
    words = judgement.search_words
    if judgement.paper_number is not None or not words:
        return judgement
    if deps.searches_used >= MAX_EXTRA_SEARCHES:
        return judgement
    if not _search_more(deps, words):
        return judgement
    return _ask(request, deps, model)


def _ask(request: str, deps: RelevanceDeps, model: Model | str) -> RelevanceJudgement:
    listed = _format_candidates(deps.candidates) if deps.candidates else "none yet"
    prompt = f"Request: {request}\n\nCandidates:\n{listed}"
    return relevance_agent.run_sync(prompt, deps=deps, model=model).output


def _format_candidates(papers: list[Paper], first_number: int = 1) -> str:
    """The numbered list the LLM reads: title, year, citations, short abstract."""
    return "\n\n".join(
        _format_candidate(number, paper)
        for number, paper in enumerate(papers, first_number)
    )


def _format_candidate(number: int, paper: Paper) -> str:
    year = paper.year if paper.year is not None else "year unknown"
    citations = paper.citation_count if paper.citation_count is not None else "unknown"
    abstract = (
        textwrap.shorten(paper.abstract, MAX_ABSTRACT_CHARS, placeholder=" ...")
        if paper.abstract
        else "no abstract available"
    )
    return (
        f"[{number}] {paper.title}\n"
        f"    {year}, {citations} citations\n"
        f"    Abstract: {abstract}"
    )
