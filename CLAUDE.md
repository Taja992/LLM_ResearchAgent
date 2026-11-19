# Research Scout Agent

A course assignment: an AI agent, built with **PydanticAI**, that searches for research papers, checks them against the user's constraints (topic, year, citation count), and returns a short, evidence-based recommendation. Citation counts must come from a real tool, never from the LLM's memory.

- Full brief (the requirements): [docs/ASSIGNMENT.md](docs/ASSIGNMENT.md)
- Roadmap with checkboxes: [docs/PLAN.md](docs/PLAN.md)
- Why things are the way they are: [docs/DECISIONS.md](docs/DECISIONS.md)
- How each part works (the owner's own reference): [docs/NOTES.md](docs/NOTES.md)
- Optional web demo for the video: [docs/WEBPLAN.md](docs/WEBPLAN.md)

## How we work (most important)

The owner is **learning** while building this. Understanding matters as much as the code.

- **Talk before building.** Say what you'll do, which files change, and why, before writing code. One small idea per step.
- **Explain as you go,** in simple, everyday English: what each part does, why it's built that way, the pattern or Python feature used and what problem it solves. Explain a technical term the first time it appears. A C# comparison is welcome when it really helps.
- **The owner decides.** For a real choice, use the AskUserQuestion menu in plain words, recommended option first. Never a lettered or numbered text list of questions.
- **Clear over clever.** The owner must be able to explain this code to a teacher or in the demo video.
- **Never commit or push.** Leave changes uncommitted and suggest a commit message.
- Skills: `/next-step` (do the next small step), `/check` (format, lint, tests), `/explain` (walk through existing code), `/handoff` (wrap up and write a prompt for a fresh Claude session).

## Code rules

- **LLM vs code split:** the LLM understands the request and judges relevance; plain Python does anything that must be exact (calling the API, filtering by year and citations). Keep that line obvious in the code, because the assignment grades it.
- **Never trust the LLM with facts.** Title, authors, year, citation count and link must come from the tool's data.
- **Quality first (owner's priority):** good design patterns and coding practices, no code smells, clean easy-to-read code.
  - **Separation of concerns:** one clear job per file and per function (`models.py` data shapes, `openalex.py` talking to OpenAlex, `main.py` the workflow). Don't mix fetching, checking and presenting in one function.
  - **Don't reinvent the wheel:** use what Python, Pydantic, PydanticAI, httpx and pytest already provide before writing your own. Say which built-in feature was used.
  - **No smells:** no duplicated logic, no long functions or deep nesting, no dead code or unused imports, no vague names, no catch-all `except`.
  - Before `/check`, review the new code against these points and fix it; mention anything you chose to leave.
- Type hints everywhere. Pydantic models for anything structured.
- No magic numbers or strings: use named constants or settings.
- Don't build ahead: add structure only when a step needs it.
- Tests come in the same step as the code. Tests must not call the real API or a real LLM (use fake data and PydanticAI's `TestModel` / `FunctionModel`).
- Secrets live in `.env` (git-ignored). Never read, print or commit `.env`; `.env.example` shows the variable names.

## Commands

```text
uv pip install -r requirements.txt     # install dependencies into .venv
.venv\Scripts\python main.py "<request>"  # run the agent
.venv\Scripts\python evaluate.py      # real evaluation run (live OpenAlex: run on purpose)
.venv\Scripts\python -m pytest         # tests
.venv\Scripts\python -m mypy .         # type check (VS Code's Mypy extension uses this one too)
uvx ruff format .                      # auto-format the code
uvx ruff check --fix .                 # lint + auto-fix
```

## Current status

Kept short: this file loads in every session.

- **Exists:** the full agent runs end to end: `main.py` (command line) → `workflow.find_paper()` (five steps in order) → `PaperAnswer` or `NoMatch`. Local Ollama `qwen2.5:7b-instruct`; any model swaps in via `MODEL` in `.env`. `requirements.txt` (pydantic-ai-slim 2.68, pydantic-evals 2.68, httpx, python-dotenv, pytest). A `.venv` made by `uv` with Python 3.12.
- **Git:** initialised, first commit made (code, `CLAUDE.md`, `.claude/`, `.vscode/`; not `docs/` or `.env`).
- **Paper API chosen:** OpenAlex, optional `OPENALEX_API_KEY` (decision 6). Field mapping in `docs/NOTES.md`.
- **`models.py`:** shared data models: `Paper`, `Constraints` (topic + optional year/citation `NumberRule`s + `recent` flag), `Verdict`, `AllowedRange`, `PaperAnswer` (`from_paper()` copies facts; LLM gives explanation + uncertainty). Tests in `tests/test_models.py`.
- **`rules.py`:** what each rule allows (`AllowedRange`), shared by filter and OpenAlex query.
- **`filters.py`:** `filter_papers()` / `check_paper()` give a `Verdict` (reasons) per paper. Tests in `tests/test_filters.py`.
- **`agents.py`:** LLM step 1 `extract_constraints(request, model)` → `Constraints`; LLM step 4 `judge_relevance(request, candidates, constraints, current_year, model)` → `RelevanceOutcome` (picks by number; validator checks it; `search_papers` tool + code fallback for one extra search, decision 27). Both use `NativeOutput` (decision 25). Tests in `tests/test_agents.py` with `FunctionModel`; `tests/conftest.py` blocks real LLM calls. 78 tests pass in total.
- **`openalex.py`:** `paper_from_openalex()` and `search_openalex(constraints, current_year)` (topic + year/citation rules sent as OpenAlex filters, 25 results, optional key). Tests in `tests/test_openalex.py` (9 pass, fake network via `httpx.MockTransport`).
- **Workflow designed (decisions 9–10):** code runs fixed steps (LLM reads request → code search → code filter → LLM judges relevance, with an optional `search_papers` tool → code builds answer). Described in `README.md` "How the agent works" (README has only that section so far).
- **Model:** local Ollama `qwen2.5:7b-instruct` is final (decision 12); no cloud LLM planned.
- **Evaluation method chosen (decision 31):** code checks the exact criteria, the owner scores relevance/usefulness with a 0–2 rubric. The research with sources is at the bottom of `docs/NOTES.md`, not in the README (owner's choice).
- **`evaluation_cases.py`:** `EVALUATION_SET`, a `pydantic_evals` `Dataset` of 12 cases, each with hand-written `CaseCriteria` (decision 32). Output per run is `RunResult` (answer + papers the searches returned + search count). Tests in `tests/test_evaluation_cases.py`.
- **`evaluation_checks.py`:** five `pydantic_evals` evaluators for the exact criteria (decision 33). Tests in `tests/test_evaluation_checks.py`.
- **`evaluate.py`:** runs the evaluation for real (`.venv\Scripts\python evaluate.py`; uses live OpenAlex, run on purpose). Results in `evaluation_results.json` (run 2, 53/55 checks) and `evaluation_results_before_fixes.json` (run 1, 48/50). Both agents use temperature 0 (decision 34). **All graded code is done.**
- **`progress.py` (branch `web`):** `find_paper(..., on_step=...)` announces each step started/finished for the web demo (decision 38). Tests in `tests/test_progress.py` and `tests/test_workflow.py`. 110 tests pass in total.
- **Owner's scores:** in `documentation/SCORING.md` (drafted by Claude, reviewed and confirmed by the owner): 10 of the 12 cases scored (owner's choice): relevant 19/20, explanation 15/20.
- **README:** "How the agent works" (final), Evaluation (short, links `documentation/SCORING.md`) and Reflection.
- **Not yet:** README setup / install / API key / how to run / model choice (Phase 5), public repo, demo video. No code needed.
- **Next:** WEBPLAN step 2, the Streamlit page ([docs/WEBPLAN.md](docs/WEBPLAN.md)), on branch `web`. Also still open: README setup sections and model choice (Phase 5), the demo video. Ollama must be running for real tries (the app, or `ollama serve`).

## Working notes

- **`docs/` is private** (git-ignored, this machine only). **`documentation/` is public** (committed): graded extras like `SCORING.md` go there. Anything graded (workflow write-up, eval set and results, reflection) goes in committed files like `README.md`, never only in `docs/`. Graded files (README etc.) must not link into `docs/`; `CLAUDE.md` and `.claude/` are committed and may.
- **Live OpenAlex requests are rationed** (the daily budget is small). At most one or two per step, and only when the step really needs real data. Send them through the project's own code (`search_openalex` after `load_dotenv()`), so the owner's `OPENALEX_API_KEY` is used; never raw `curl`, which goes without the key. pytest never calls OpenAlex. Prefer the docs or the saved sample data.
- Windows 11. The `.venv` has no `pip`: use `uv pip ...`.
- pytest exit code 5 means "no tests found". That's fine before tests exist.
