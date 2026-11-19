"""One agent run on the web demo that can pause between steps.

Streamlit re-runs the page script on every click, so the run is kept in
st.session_state between clicks: the paused workflow (a generator), the step
graph and, at the end, the answer. No Streamlit import: it only needs a place
to draw the graph, so it can be tested with a fake one.
"""

from dataclasses import dataclass, field
from typing import Protocol

from progress import StepName, StepStatus
from step_graph import StepBoard
from workflow import Answer, PaperSteps


class GraphSpot(Protocol):
    """Anywhere the graph can be drawn (Streamlit's st.empty() placeholder)."""

    def html(self, body: str) -> object: ...


@dataclass
class DemoRun:
    board: StepBoard = field(default_factory=StepBoard)
    steps: PaperSteps | None = None  # the paused workflow; None when finished
    answer: Answer | None = None
    graph: GraphSpot | None = None  # set on every page run (old spots go stale)
    selected: StepName | None = None  # the step whose code is shown
    waiting: bool = False  # True only while paused, waiting for "Continue"

    def show_progress(self, step: StepName, status: StepStatus) -> None:
        """The workflow's `on_step`: update the graph as each step starts and ends."""
        self.board.update(step, status)
        self.redraw()

    def redraw(self) -> None:
        if self.graph is not None:
            self.graph.html(self.board.html(self.selected, self.waiting))

    def advance(self, pause: bool) -> None:
        """Run the next step; with `pause` off, keep going until the answer."""
        if self.steps is None:
            return
        self.waiting = False
        try:
            next(self.steps)
            while not pause:
                next(self.steps)
        except StopIteration as finished:
            self.answer, self.steps = finished.value, None
        self.waiting = self.steps is not None
        self.redraw()  # shows the pause mark (or the finished graph)
