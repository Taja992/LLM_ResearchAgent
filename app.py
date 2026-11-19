"""Web demo: run the real agent and watch each step light up.

streamlit run app.py

Only shows things: the agent's work happens in workflow.paper_steps, and every
fact shown comes from its answer. Uses the real model and live OpenAlex.
"""

from dataclasses import dataclass
from datetime import date

import streamlit as st

from code_html import code_html
from demo_run import DemoRun
from main import configure
from models import NoMatch, PaperAnswer
from progress import STEPS, StepName
from step_code import code_of, step_code, workflow_lines
from workflow import paper_steps

EXAMPLE_REQUESTS = (
    (
        "Find a research paper about LLM agents for software engineering that was "
        "published after 2022 and has at least 100 citations."
    ),
    (
        "Find a paper about retrieval-augmented generation published before 2021 "
        "with more than 500 citations. Summarize its contribution in 5-7 sentences."
    ),
    (
        "Find a recent paper about AI agents using tools and explain whether it "
        "would be useful for someone building autonomous software agents."
    ),
)
UNKNOWN = "unknown"
RUN_KEY = "run"  # the current DemoRun, kept between page reruns
GO_ON_KEY = "go_on"  # set by the Continue button
# Fixed heights (pixels): picking a step or getting an answer never moves the page.
ANSWER_HEIGHT = 367  # from the title down to the "Find a paper" row
CODE_HEIGHT = 560
# Use the full width with small margins (no centring gap on wide screens).
PAGE_STYLE = """
<style>
[data-testid="stMainBlockContainer"] {
  max-width: none; padding: 4.5rem 2.5rem 4rem;  /* top: clear of the toolbar */
}
[data-testid="stMainBlockContainer"] h1 { padding-top: 0; }  /* title level with the answer box */
</style>
"""


@dataclass
class Inputs:
    """What the user chose in the left column on this page run."""

    request: str
    clicked: bool  # "Find a paper" was clicked
    pause: bool  # "Pause between steps" is on


def main() -> None:
    model = configure()
    st.set_page_config(page_title="Research Scout Agent", layout="wide")
    st.html(PAGE_STYLE)

    inputs_column, answer_column = st.columns([9, 11], gap="large")
    with inputs_column:
        inputs = show_inputs()
    answer_box = answer_column.container(height=ANSWER_HEIGHT, border=True)
    graph, continue_spot = st.empty(), st.empty()
    selected = pick_step()

    run = current_run(inputs, model)
    run.graph, run.selected = graph, selected
    run.redraw()
    with st.container(height=CODE_HEIGHT, border=False):
        show_code(selected)

    if inputs.clicked or st.session_state.pop(GO_ON_KEY, False):
        continue_spot.empty()  # no stale Continue button while a step runs
        run.advance(inputs.pause)
    if run.waiting and (next_step := run.board.next_step()):
        continue_spot.button(
            f"Continue → {next_step.title}", type="primary", on_click=_go_on
        )
    if run.answer:
        with answer_box:
            show_answer(run.answer)


def show_inputs() -> Inputs:
    """Title, example picker, request box, the button and the pause toggle."""
    st.title("Research Scout Agent")
    st.caption(
        "Finds a research paper that fits your request, using OpenAlex. "
        "Cyan steps use the LLM; green steps are plain code."
    )
    example = st.selectbox("Try an example", EXAMPLE_REQUESTS)
    request = st.text_area("Your request", value=example, height=120)
    find_column, pause_column = st.columns([1, 2], vertical_alignment="center")
    clicked = find_column.button("Find a paper", type="primary")
    pause = pause_column.toggle(
        "Pause between steps",
        help="When on, the agent stops after each step until you click Continue.",
    )
    return Inputs(request=request, clicked=clicked, pause=pause)


def pick_step() -> StepName:
    """The step buttons under the graph; one step is always picked."""
    return st.segmented_control(
        "Show the code for a step",
        [step.name for step in STEPS],
        format_func=_title,
        default=StepName.READ_REQUEST,
        required=True,  # so the code area never disappears and the page keeps its height
    )


def current_run(inputs: Inputs, model: str) -> DemoRun:
    """The run kept between page reruns; "Find a paper" starts a new one."""
    if not inputs.clicked:
        return st.session_state.setdefault(RUN_KEY, DemoRun())
    run = st.session_state[RUN_KEY] = DemoRun()  # the workflow waits before step 1
    run.steps = paper_steps(
        inputs.request, model, date.today().year, on_step=run.show_progress
    )
    return run


def show_answer(answer: PaperAnswer | NoMatch) -> None:
    """The answer card, with normal Streamlit elements (inside the answer box)."""
    match answer:
        case PaperAnswer():
            st.subheader(answer.title)
            st.caption(", ".join(answer.authors))
            year, citations, source = st.columns(3)
            year.metric("Year", _or_unknown(answer.year))
            citations.metric("Citations", _or_unknown(answer.citation_count))
            source.metric("Citation source", answer.citation_source)
            st.markdown(f"[{answer.url}]({answer.url})")
            st.write(answer.explanation)
            if answer.uncertainty:
                st.info(f"Doubts: {answer.uncertainty}")
        case NoMatch():
            st.subheader(answer.message)
            st.metric("Papers checked", answer.papers_checked)
            for rejection in answer.rejections:
                st.write(f"- {rejection}")
            st.write(answer.explanation)


def show_code(step: StepName) -> None:
    """Where the workflow runs this step (lit up), next to the function it calls."""
    workflow, function = code_of(paper_steps), step_code(step)
    left, right = st.columns(2)
    with left:
        st.caption(f"Where it runs: `paper_steps` in {workflow.location}")
        st.html(code_html(workflow.source, workflow_lines(step)))
    with right:
        st.caption(f"What it calls: `{function.call}` in {function.location}")
        st.html(code_html(function.source))


def _go_on() -> None:
    """The Continue button's click: run the next step on this page run."""
    st.session_state[GO_ON_KEY] = True


def _title(step: StepName) -> str:
    return next(s.title for s in STEPS if s.name == step)


def _or_unknown(number: int | None) -> int | str:
    """A missing year or count is shown as 'unknown', never guessed."""
    return UNKNOWN if number is None else number


main()
