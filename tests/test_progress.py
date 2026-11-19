"""Tests for progress.py: steps are announced around the code they wrap."""

from progress import STEPS, StepName, StepStatus, reported


def test_reported_announces_start_before_and_finish_after_the_code() -> None:
    events: list[str] = []

    with reported(lambda step, status: events.append(status), StepName.SEARCH):
        events.append("working")

    assert events == [StepStatus.STARTED, "working", StepStatus.FINISHED]


def test_every_step_has_display_details_once() -> None:
    assert [step.name for step in STEPS] == list(StepName)
