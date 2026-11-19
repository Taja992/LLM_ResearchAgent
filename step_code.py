"""The real code behind each step, read from the source files (never typed by hand).

Used by the web demo to show which function each step runs. If the code changes,
the page shows the new code. Plain code, no LLM.
"""

import inspect
import textwrap
from collections.abc import Callable
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from agents import extract_constraints, judge_relevance
from filters import filter_papers
from models import PaperAnswer
from openalex import search_openalex
from progress import StepName
from workflow import find_paper

# The function that does the work of each step (tests check find_paper calls it).
STEP_FUNCTIONS: dict[StepName, Callable[..., Any]] = {
    StepName.READ_REQUEST: extract_constraints,
    StepName.SEARCH: search_openalex,
    StepName.CHECK_RULES: filter_papers,
    StepName.PICK_PAPER: judge_relevance,
    StepName.EXTRA_SEARCH: search_openalex,  # the same search, with new words
    StepName.BUILD_ANSWER: PaperAnswer.from_paper,
}


class CodeView(BaseModel, frozen=True):
    """One function as the page shows it."""

    call: str  # e.g. "extract_constraints(request, model)"
    source: str
    location: str  # e.g. "agents.py, line 60"


def code_of(function: Callable[..., Any]) -> CodeView:
    """The function's call line, full source and where it lives."""
    lines, first_line = inspect.getsourcelines(function)
    parameters = ", ".join(inspect.signature(function).parameters)
    return CodeView(
        call=f"{function.__qualname__}({parameters})",
        source=textwrap.dedent("".join(lines)),
        location=f"{Path(inspect.getfile(function)).name}, line {first_line}",
    )


def step_code(step: StepName) -> CodeView:
    return code_of(STEP_FUNCTIONS[step])


# How each step's line is found in find_paper: the `with reported(...)` line names
# the step. The extra search is started from inside step 4, on this line.
WORKFLOW_MARKERS = {step: f"StepName.{step.name}" for step in StepName} | {
    StepName.EXTRA_SEARCH: "_reported_extra_search("
}


def workflow_lines(step: StepName) -> list[int]:
    """Lines of find_paper (1 = its first line) that run this step.

    The line that names the step, plus the indented block under it.
    """
    lines = code_of(find_paper).source.splitlines()
    start = next(i for i, line in enumerate(lines) if WORKFLOW_MARKERS[step] in line)
    end = start + 1
    while end < len(lines) and _indent(lines[end]) > _indent(lines[start]):
        end += 1
    return list(range(start + 1, end + 1))


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip())
