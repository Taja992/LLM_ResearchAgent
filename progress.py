"""Progress reports: the agent's steps, and a way to announce each one as it runs.

Used by workflow.py (to announce) and by a display such as a web page (to listen).
Plain code, no LLM.
"""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel


class StepName(StrEnum):
    READ_REQUEST = "read_request"
    SEARCH = "search"
    CHECK_RULES = "check_rules"
    PICK_PAPER = "pick_paper"
    EXTRA_SEARCH = "extra_search"
    BUILD_ANSWER = "build_answer"


class StepStatus(StrEnum):
    STARTED = "started"
    FINISHED = "finished"


class Step(BaseModel, frozen=True):
    """One step as a display shows it."""

    name: StepName
    done_by: Literal["LLM", "CODE"]
    title: str
    description: str


# In workflow order. The extra search only happens inside "Pick best paper".
STEPS = (
    Step(
        name=StepName.READ_REQUEST,
        done_by="LLM",
        title="Read request",
        description="Turns your words into a topic and rules",
    ),
    Step(
        name=StepName.SEARCH,
        done_by="CODE",
        title="Search OpenAlex",
        description="Finds papers that match the rules",
    ),
    Step(
        name=StepName.CHECK_RULES,
        done_by="CODE",
        title="Check rules",
        description="Re-checks every paper's year and citations",
    ),
    Step(
        name=StepName.PICK_PAPER,
        done_by="LLM",
        title="Pick best paper",
        description="Chooses the paper most about your topic",
    ),
    Step(
        name=StepName.EXTRA_SEARCH,
        done_by="CODE",
        title="Extra search",
        description="Searches again with better words, if nothing fits",
    ),
    Step(
        name=StepName.BUILD_ANSWER,
        done_by="CODE",
        title="Build answer",
        description="Copies the real facts into the answer",
    ),
)

type StepReporter = Callable[[StepName, StepStatus], None]


def ignore_progress(step: StepName, status: StepStatus) -> None:
    """The default reporter: nobody is listening, so do nothing."""


@contextmanager
def reported(on_step: StepReporter, step: StepName) -> Iterator[None]:
    """Announce `step` as started, run the code inside the `with`, then as finished."""
    on_step(step, StepStatus.STARTED)
    yield
    on_step(step, StepStatus.FINISHED)
