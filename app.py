"""Web demo: run the real agent and watch each step light up.

streamlit run app.py

Only shows things: the agent's work happens in find_paper, and every fact shown
comes from its answer. Uses the real model and live OpenAlex.
"""

from datetime import date

import streamlit as st

from code_html import code_html
from main import configure
from models import NoMatch, PaperAnswer
from pills import StepBoard
from progress import STEPS, StepName, StepStatus
from step_code import code_of, step_code, workflow_lines
from workflow import find_paper

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
# Use most of the screen, with slim margins (Streamlit's "wide" has none).
PAGE_STYLE = """
<style>
[data-testid="stMainBlockContainer"] {
  max-width: 1440px; padding: 3rem 2.5rem 4rem;
}
</style>
"""


def main() -> None:
    model = configure()
    st.set_page_config(page_title="Research Scout Agent", layout="wide")
    st.html(PAGE_STYLE)
    st.title("Research Scout Agent")
    st.caption(
        "Finds a research paper that fits your request, using OpenAlex. "
        "Cyan steps use the LLM; green steps are plain code."
    )

    example = st.selectbox("Try an example", EXAMPLE_REQUESTS)
    request = st.text_area("Your request", value=example, height=90)
    clicked = st.button("Find a paper", type="primary")
    graph = st.empty()
    selected = st.segmented_control(
        "Show the code for a step", [step.name for step in STEPS], format_func=_title
    )
    board: StepBoard = st.session_state.get("board", StepBoard())
    graph.html(board.html(selected))
    if selected:
        show_code(selected)

    if clicked:
        board = StepBoard()

        def show_progress(step: StepName, status: StepStatus) -> None:
            board.update(step, status)
            graph.html(board.html(selected))

        answer = find_paper(request, model, date.today().year, on_step=show_progress)
        st.session_state.update(answer=answer, board=board)

    if "answer" in st.session_state:
        show_answer(st.session_state.answer)


def show_answer(answer: PaperAnswer | NoMatch) -> None:
    """The answer card, with normal Streamlit elements."""
    with st.container(border=True):
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
    workflow, function = code_of(find_paper), step_code(step)
    left, right = st.columns(2)
    with left:
        st.caption(f"Where it runs: `find_paper` in {workflow.location}")
        st.html(code_html(workflow.source, workflow_lines(step)))
    with right:
        st.caption(f"What it calls: `{function.call}` in {function.location}")
        st.html(code_html(function.source))


def _title(step: StepName) -> str:
    return next(s.title for s in STEPS if s.name == step)


def _or_unknown(number: int | None) -> int | str:
    """A missing year or count is shown as 'unknown', never guessed."""
    return UNKNOWN if number is None else number


main()
