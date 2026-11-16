---
name: check
description: Run all code quality checks (formatting, lint, types, tests) and report the results in plain words. Use after changing code, before a commit, or when the owner asks "does it all pass?".
---

# Check

Runs every quality check from the project root and explains the results simply.

1. `uvx ruff format --check .` checks the formatting
2. `uvx ruff check .` finds code smells and likely bugs
3. `.venv/Scripts/python -m mypy .` checks the type hints
4. `.venv/Scripts/python -m pytest` runs the tests

Notes:
- Run all four even if one fails, so the owner sees the whole picture.
- pytest exit code 5 means "no tests found". That's fine before any tests exist, not a failure.
- Formatting and many lint issues fix themselves: `uvx ruff format .` and `uvx ruff check --fix .`. Say which fixes were automatic.
- Tests must never call the real paper API or a real LLM. If one does (slow, needs a key, fails offline), report it as a problem.

## Report
Give a short table (check, pass or fail, one-line summary). For each failure:
- explain in plain words what's wrong and why it matters
- fix it if it's in code Claude wrote this session. If the owner wrote it, explain the fix and let them choose.
