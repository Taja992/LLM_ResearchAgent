"""Tests for step_code.py: the code shown for each step is real and up to date."""

import inspect
import re

from progress import StepName
from step_code import STEP_FUNCTIONS, code_of, step_code, workflow_lines
from workflow import find_paper


def test_every_step_has_real_code() -> None:
    for step in StepName:
        view = step_code(step)
        assert view.source.lstrip().startswith(("def ", "@"))
        assert re.fullmatch(r"\w+\.py, line \d+", view.location)


def test_the_call_line_shows_the_function_and_its_parameters() -> None:
    view = step_code(StepName.READ_REQUEST)

    assert view.call == "extract_constraints(request, model)"
    assert view.location.startswith("agents.py, line ")


def test_each_linked_function_is_really_called_by_the_workflow() -> None:
    workflow = inspect.getsource(find_paper)
    for function in STEP_FUNCTIONS.values():
        assert function.__name__ in workflow  # the link can't go stale quietly


def test_method_code_is_dedented() -> None:
    view = code_of(STEP_FUNCTIONS[StepName.BUILD_ANSWER])

    assert view.call == "PaperAnswer.from_paper(paper, explanation, uncertainty)"
    assert view.source.startswith("@classmethod")


def test_workflow_lines_cover_the_step_and_its_block() -> None:
    lines = code_of(find_paper).source.splitlines()

    picked = [lines[n - 1] for n in workflow_lines(StepName.PICK_PAPER)]

    assert "StepName.PICK_PAPER" in picked[0]
    assert any("judge_relevance(" in line for line in picked)
    assert not any("BUILD_ANSWER" in line for line in picked)


def test_every_step_is_found_in_the_workflow() -> None:
    for step in StepName:
        assert workflow_lines(step)
