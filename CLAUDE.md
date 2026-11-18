# Research Scout Agent

A course assignment: an AI agent, built with **PydanticAI**, that searches for research papers, checks them against the user's constraints (topic, year, citation count), and returns a short, evidence-based recommendation. Citation counts must come from a real tool, never from the LLM's memory.

- Full brief (the requirements): [docs/ASSIGNMENT.md](docs/ASSIGNMENT.md)
- Roadmap with checkboxes: [docs/PLAN.md](docs/PLAN.md)
- Why things are the way they are: [docs/DECISIONS.md](docs/DECISIONS.md)
- How each part works (the owner's own reference): [docs/NOTES.md](docs/NOTES.md)

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

```
uv pip install -r requirements.txt     # install dependencies into .venv
.venv\Scripts\python main.py "<request>"  # run the agent
.venv\Scripts\python -m pytest         # tests
.venv\Scripts\python -m mypy .         # type check (VS Code's Mypy extension uses this one too)
uvx ruff format .                      # auto-format the code
uvx ruff check --fix .                 # lint + auto-fix
```

## Current status

Kept short: this file loads in every session.

- **Exists:** `main.py` skeleton (a PydanticAI `Agent`, an empty `search_papers` tool, a `PaperAnswer` model with only `explanation`). It runs end to end on local Ollama (`qwen2.5:7b-instruct`); any model swaps in via `MODEL` in `.env`. `requirements.txt` (pydantic-ai-slim 2.68, httpx, python-dotenv, pytest). A `.venv` made by `uv` with Python 3.12.
- **Git:** initialised, first commit made (code, `CLAUDE.md`, `.claude/`, `.vscode/`; not `docs/` or `.env`).
- **Paper API chosen:** OpenAlex, optional `OPENALEX_API_KEY` (decision 6). Field mapping in `docs/NOTES.md`.
- **`models.py`:** shared data models: `Paper`, `Constraints` (topic + optional year/citation `NumberRule`s + `recent` flag). Tests in `tests/test_models.py`.
- **`filters.py`:** `filter_papers()` / `check_paper()` give a `Verdict` (reasons) per paper. Tests in `tests/test_filters.py`. 
- **`agents.py`:** LLM step 1, `extract_constraints(request, model)` → `Constraints`. Tests in `tests/test_agents.py` with `FunctionModel`; `tests/conftest.py` blocks real LLM calls. 42 tests pass in total.
- **`openalex.py`:** `paper_from_openalex()` and `search_openalex(topic)` (real HTTP call, 25 results, optional key). Tests in `tests/test_openalex.py` (9 pass, fake network via `httpx.MockTransport`).
- **Workflow designed (decisions 9–10):** code runs fixed steps (LLM reads request → code search → code filter → LLM judges relevance, with an optional `search_papers` tool → code builds answer). Described in `README.md` "How the agent works" (README has only that section so far).
- **Model:** local Ollama `qwen2.5:7b-instruct` is final (decision 12); no cloud LLM planned.
- **Not yet:** a real-Ollama try of extraction, the search hooked into the agent, the relevance agent, wiring, evaluation, rest of README.
- **Next:** try extraction on real Ollama (needs Ollama running), then "Pass the constraints to the API" in [docs/PLAN.md](docs/PLAN.md).

## Working notes

- **`docs/` is private** (git-ignored, this machine only). Anything graded (workflow write-up, eval set and results, reflection) goes in committed files like `README.md`, never only in `docs/`. Graded files (README etc.) must not link into `docs/`; `CLAUDE.md` and `.claude/` are committed and may.
- Windows 11. The `.venv` has no `pip`: use `uv pip ...`.
- pytest exit code 5 means "no tests found". That's fine before tests exist.
