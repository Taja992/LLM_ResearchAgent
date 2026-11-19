"""Tests for step_graph.py: step states and the HTML the web page shows."""

from progress import StepName, StepStatus
from step_graph import BREAK_HINT, DONE_MARK, NodeState, StepBoard


def test_every_step_starts_waiting_and_the_extra_search_is_hidden() -> None:
    board = StepBoard()

    assert set(board.states.values()) == {NodeState.WAITING}
    assert "Read request" in board.html()
    assert "Extra search" not in board.html()


def test_a_running_step_lights_its_node_and_the_wire_into_it() -> None:
    board = StepBoard()
    board.update(StepName.READ_REQUEST, StepStatus.FINISHED)
    board.update(StepName.SEARCH, StepStatus.STARTED)

    html = board.html()

    assert 'class="node llm done"' in html
    assert 'class="wire code running"' in html  # the wire into "Search OpenAlex"
    assert 'class="node code running"' in html


def test_a_finished_step_shows_a_tick() -> None:
    board = StepBoard()

    board.update(StepName.READ_REQUEST, StepStatus.STARTED)
    board.update(StepName.READ_REQUEST, StepStatus.FINISHED)

    assert board.states[StepName.READ_REQUEST] is NodeState.DONE
    assert f"{DONE_MARK}Read request" in board.html()


def test_the_extra_search_step_appears_once_it_happens() -> None:
    board = StepBoard()

    board.update(StepName.EXTRA_SEARCH, StepStatus.STARTED)

    assert "Extra search" in board.html()
    assert board.html().count('class="node') == 6  # five steps plus the extra one


def test_each_node_shows_the_real_call_it_runs() -> None:
    hint = BREAK_HINT
    assert f"extract_{hint}constraints({hint}request, model)" in StepBoard().html()


def test_the_selected_step_gets_a_ring() -> None:
    html = StepBoard().html(selected=StepName.CHECK_RULES)

    assert 'class="node code waiting selected"' in html
    assert html.count(' selected"') == 1  # only one node has the ring


def test_selecting_the_extra_search_shows_its_node() -> None:
    assert "Extra search" in StepBoard().html(selected=StepName.EXTRA_SEARCH)


def test_next_step_is_the_first_main_step_not_started() -> None:
    board = StepBoard()
    board.update(StepName.READ_REQUEST, StepStatus.FINISHED)

    next_step = board.next_step()

    assert next_step is not None
    assert next_step.name is StepName.SEARCH


def test_when_paused_the_wire_into_the_next_step_shows_a_pause_mark() -> None:
    board = StepBoard()
    board.update(StepName.READ_REQUEST, StepStatus.FINISHED)

    assert 'class="wire code paused"' in board.html(paused=True)
    assert "paused" not in board.html().split("</style>")[1]


def test_the_pause_mark_is_a_real_character() -> None:
    assert 'content: "‖"' in StepBoard().html()
