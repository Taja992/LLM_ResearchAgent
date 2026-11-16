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
- **Not yet:** git repo, a free cloud LLM chosen for the README, a real paper search, filtering, evaluation, README.
- **Next:** Phase 0, step 1 in [docs/PLAN.md](docs/PLAN.md).

## Working notes

- **`docs/` is private** (git-ignored, this machine only). Anything graded (workflow write-up, eval set and results, reflection) goes in committed files like `README.md`, never only in `docs/`. Committed files must not link into `docs/`.
- Windows 11. The `.venv` has no `pip`: use `uv pip ...`.
- pytest exit code 5 means "no tests found". That's fine before tests exist.
