"""The step graph for the web demo: which state each step is in, drawn as HTML.

Looks like a node editor: one node per step, joined by wires. The wire into a
running step animates. No Streamlit here, so it can be tested without a browser.
All motion is plain CSS (Streamlit runs no JavaScript in st.html), using only
features Chrome and Firefox both support.
"""

from dataclasses import dataclass, field
from enum import StrEnum
from html import escape

from progress import STEPS, Step, StepName, StepStatus
from step_code import step_code


class PillState(StrEnum):
    WAITING = "waiting"
    RUNNING = "running"
    DONE = "done"


STATE_LABELS = {
    PillState.WAITING: "waiting",
    PillState.RUNNING: "running",
    PillState.DONE: "done",
}
DONE_MARK = "&#10003; "  # a tick, written so any text encoding shows it
OPTIONAL_STEPS = {StepName.EXTRA_SEARCH}  # only shown once it actually happens
BREAK_AFTER = ("_", ".", "(")  # long calls wrap here, never mid-word
# An invisible "zero-width space": a place a line may break. Streamlit removes
# <wbr> tags, but keeps this because it is plain text.
BREAK_HINT = "&#8203;"

STYLE = """
<style>
.canvas {
  background-color: #0b0d10;
  background-image: radial-gradient(#262b34 1px, transparent 1px);
  background-size: 18px 18px;
  border: 1px solid #1f232a; border-radius: 14px;
  padding: 24px 20px; overflow-x: auto;
  scrollbar-width: thin; scrollbar-color: #2f343e transparent;
  font-family: Inter, system-ui, -apple-system, "Segoe UI", sans-serif;
}
.graph { display: flex; align-items: stretch; }
.llm  { --c: #38bdf8; --tint: rgba(56, 189, 248, 0.14); --line: rgba(56, 189, 248, 0.55); }
.code { --c: #4ade80; --tint: rgba(74, 222, 128, 0.14); --line: rgba(74, 222, 128, 0.55); }

.node {
  position: relative; flex: 1 1 0; min-width: 124px; background: #15181d;
  border: 1px solid #2b2f37; border-radius: 10px; color: #e5e7eb;
  display: flex; flex-direction: column;
  transition: opacity 0.3s ease, border-color 0.3s ease;
}
.node .call {
  margin: auto 10px 10px; padding: 6px 8px; background: #0b0d10;
  border: 1px solid #23272e; border-radius: 6px; color: #c9d1d9;
  font: 11px/1.45 ui-monospace, "Cascadia Mono", Consolas, monospace;
  overflow-wrap: normal; word-break: normal;
}
.node .head {
  display: flex; justify-content: space-between; align-items: center;
  padding: 7px 12px; background: var(--tint); border-radius: 9px 9px 0 0;
  font: 600 11px/1.4 ui-monospace, "Cascadia Mono", Consolas, monospace;
  letter-spacing: 0.08em; color: var(--c);
}
.node .state { color: #9ca3af; font-weight: 500; letter-spacing: 0.04em; }
.node .name {
  padding: 10px 12px 3px; font-size: 13px; font-weight: 700;
  letter-spacing: 0.06em; text-transform: uppercase;
}
.node .desc { padding: 0 12px 12px; font-size: 12.5px; color: #9aa3b2; line-height: 1.4; }
.port {
  position: absolute; top: 50%; width: 8px; height: 8px; margin-top: -4px;
  background: #3b414d; border-radius: 2px;
}
.port.in { left: -5px; }
.port.out { right: -5px; }

.node.waiting .head, .node.waiting .name, .node.waiting .desc, .node.waiting .call { opacity: 0.45; }
.node.running {
  border-color: var(--c);
  animation: glow 1.4s ease-in-out infinite;
}
.node.running .state, .node.done .state { color: var(--c); }
.node.done { border-color: var(--line); }
.node.selected { outline: 2px solid #f8fafc; outline-offset: 4px; }
.node.running .port, .node.done .port { background: var(--c); }

.wire { position: relative; flex: 0 0 40px; height: 2px; align-self: center; background: #2f343e; }
.wire.done { background: var(--c); }
.wire.running {
  background: repeating-linear-gradient(90deg, var(--c) 0 6px, transparent 6px 14px);
  animation: flow 0.7s linear infinite;
}
.wire.running::after {
  content: ""; position: absolute; top: -3px; left: 0; width: 8px; height: 8px;
  border-radius: 50%; background: var(--c); box-shadow: 0 0 10px 2px var(--c);
  animation: travel 1s ease-in-out infinite;
}

@keyframes glow {
  0%, 100% { box-shadow: 0 0 0 0 transparent; }
  50% { box-shadow: 0 0 18px 1px var(--c); }
}
@keyframes flow { from { background-position: 0 0; } to { background-position: 14px 0; } }
@keyframes travel {
  from { transform: translateX(-4px); opacity: 0; }
  20% { opacity: 1; }
  to { transform: translateX(36px); opacity: 0; }
}
@media (prefers-reduced-motion: reduce) {
  .node.running, .wire.running, .wire.running::after { animation: none; }
}
</style>
"""


@dataclass
class StepBoard:
    """Remembers the state of every step while the agent runs."""

    states: dict[StepName, PillState] = field(
        default_factory=lambda: {step.name: PillState.WAITING for step in STEPS}
    )

    def update(self, step: StepName, status: StepStatus) -> None:
        """Fits progress.StepReporter, so it can be passed as `on_step`."""
        started = status is StepStatus.STARTED
        self.states[step] = PillState.RUNNING if started else PillState.DONE

    def html(self, selected: StepName | None = None) -> str:
        """All visible steps in order, each wire taking the next step's state.

        The `selected` step gets a ring, so you can see which code is shown.
        """
        visible = [
            step
            for step in STEPS
            if step.name not in OPTIONAL_STEPS
            or step.name == selected
            or self.states[step.name] is not PillState.WAITING
        ]
        nodes = [_node(step, self.states[step.name], selected) for step in visible]
        parts = [nodes[0]]
        for step, node in zip(visible[1:], nodes[1:], strict=True):
            parts += [_wire(step, self.states[step.name]), node]
        graph = "".join(parts)
        return f'{STYLE}<div class="canvas"><div class="graph">{graph}</div></div>'


def _node(step: Step, state: PillState, selected: StepName | None) -> str:
    mark = DONE_MARK if state is PillState.DONE else ""
    ring = " selected" if step.name == selected else ""
    return (
        f'<div class="node {step.done_by.lower()} {state}{ring}">'
        '<span class="port in"></span><span class="port out"></span>'
        f'<div class="head"><span>{step.done_by}</span>'
        f'<span class="state">{STATE_LABELS[state]}</span></div>'
        f'<div class="name">{mark}{escape(step.title)}</div>'
        f'<div class="desc">{escape(step.description)}</div>'
        f'<div class="call">{_breakable(step_code(step.name).call)}</div>'
        "</div>"
    )


def _wire(into: Step, state: PillState) -> str:
    """A wire runs when the step it leads into runs, and is lit once that is done."""
    return f'<div class="wire {into.done_by.lower()} {state}"></div>'


def _breakable(code: str) -> str:
    """Escape the code and allow line breaks only after `_`, `.` and `(`."""
    html = escape(code)
    for mark in BREAK_AFTER:
        html = html.replace(mark, f"{mark}{BREAK_HINT}")
    return html
