"""The LLM steps of the workflow. Everything else in the project is plain code.

Each LLM step returns a Pydantic model, so its answer is checked before code uses it.
NativeOutput makes the model server itself return JSON in that shape: small local
models often answer in plain text when asked to use an output tool instead.
"""

import textwrap

from pydantic_ai import Agent, ModelRetry, NativeOutput, RunContext
from pydantic_ai.models import Model

from models import Constraints, Paper, RelevanceJudgement

OUTPUT_RETRIES = 3  # how often the LLM may retry an answer that doesn't fit the model
# Small local models have a short context window: keep the candidate list short.
MAX_CANDIDATES_FOR_LLM = 10
MAX_ABSTRACT_CHARS = 500

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
- explanation: do exactly what the request asks for. If it asks for a summary of
  5-7 sentences, write 5-7 sentences. If it asks "would it be useful for ...",
  answer that question. If it asks for nothing special, explain in 2-3 sentences
  why the paper matches. If none fits, say why.
- uncertainty: real doubts, for example the topic only partly matches or the
  abstract is missing. Use null if there are none.
- Use only the titles and abstracts given. Do not add facts such as authors, years
  or citation counts that are not in the list.
"""

relevance_agent = Agent(
    output_type=NativeOutput(RelevanceJudgement),
    deps_type=list[Paper],  # the candidates shown, so the validator can check numbers
    instructions=RELEVANCE_INSTRUCTIONS,
    retries=OUTPUT_RETRIES,
)


@relevance_agent.output_validator
def _check_paper_number(
    ctx: RunContext[list[Paper]], judgement: RelevanceJudgement
) -> RelevanceJudgement:
    """Code checks the LLM: the number must point at a shown candidate."""
    number, shown = judgement.paper_number, len(ctx.deps)
    if number is not None and not 1 <= number <= shown:
        raise ModelRetry(f"paper_number must be between 1 and {shown}, or null.")
    return judgement


def judge_relevance(
    request: str, candidates: list[Paper], model: Model | str
) -> RelevanceJudgement:
    """LLM step 4: pick the candidate that best fits the request, and explain why."""
    if not candidates:
        raise ValueError("judge_relevance needs at least one candidate")
    shown = candidates[:MAX_CANDIDATES_FOR_LLM]
    prompt = f"Request: {request}\n\nCandidates:\n{_format_candidates(shown)}"
    return relevance_agent.run_sync(prompt, deps=shown, model=model).output


def _format_candidates(papers: list[Paper]) -> str:
    """The numbered list the LLM reads: title, year, citations, short abstract."""
    return "\n\n".join(
        _format_candidate(number, paper) for number, paper in enumerate(papers, 1)
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
