"""Tests for demo_run.py: a run that pauses between steps, with a fake workflow."""

from collections.abc import Generator

from demo_run import DemoRun
from models import NoMatch
from progress import StepName, StepStatus

ANSWER = NoMatch(papers_checked=0, rejections=[], explanation="None fit.")


class FakeGraph:
    def __init__(self) -> None:
        self.drawings: list[str] = []

    def html(self, body: str) -> object:
        self.drawings.append(body)
        return None


def two_steps(run: DemoRun) -> Generator[StepName, None, NoMatch]:
    for step in (StepName.READ_REQUEST, StepName.SEARCH):
        run.show_progress(step, StepStatus.STARTED)
        run.show_progress(step, StepStatus.FINISHED)
        yield step
    return ANSWER


def test_with_pause_on_it_runs_one_step_then_waits() -> None:
    run = DemoRun(graph=FakeGraph())
    run.steps = two_steps(run)

    run.advance(pause=True)

    assert run.waiting
    assert run.answer is None
    next_step = run.board.next_step()
    assert next_step is not None
    assert next_step.name is StepName.SEARCH


def test_with_pause_off_it_runs_to_the_answer() -> None:
    run = DemoRun(graph=FakeGraph())
    run.steps = two_steps(run)

    run.advance(pause=False)

    assert run.answer == ANSWER
    assert not run.waiting
    assert run.steps is None


def test_the_graph_is_redrawn_as_steps_start_and_finish() -> None:
    graph = FakeGraph()
    run = DemoRun(graph=graph)
    run.steps = two_steps(run)

    run.advance(pause=True)

    assert len(graph.drawings) == 3  # started, finished, paused
    assert 'class="node llm done"' in graph.drawings[-1]
    assert 'class="wire code paused"' in graph.drawings[-1]
