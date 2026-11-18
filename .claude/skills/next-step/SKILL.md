---
name: next-step
description: Run the next small build step of this project in the guided, explain-as-you-go style. Use when the owner says "next step", "let's continue", "what's next", or names a step to work on.
---

# Next step

Builds the project one small, understandable piece at a time. The owner is learning, so the explanation matters as much as the code.

## 1. Find the step
- Read **Current status** in `CLAUDE.md`, then the first unticked box in `docs/PLAN.md`. If the owner named a step, use that one instead.
- Check `docs/ASSIGNMENT.md` for what this step must deliver.
- If the step is bigger than about one file or one idea, split it, and only do the first part now.

## 2. Say the plan first (short)
Before writing anything, tell the owner in a few lines:
- what this piece adds, and why it's needed now
- which files will change
- whether this piece is **LLM work or plain code**, and why it belongs there
- any real choice they need to make, with your recommendation

If there's a real choice, ask it with the **AskUserQuestion menu** in plain, everyday words (recommended option first), and wait for the answer. Never use a text list of lettered or numbered questions. Otherwise go ahead.

When a step depends on an outside service (an LLM provider, a paper API, PydanticAI itself), check its current docs instead of relying on memory, and say what you checked. Live OpenAlex requests are rationed: see "Working notes" in `CLAUDE.md` (one or two per step at most, through the project's code so the key is used, never raw `curl`).

## 3. Build it
- Follow the code rules in `CLAUDE.md`.
- Write the test in the same step as the behavior. No real API or LLM calls in tests.
- Keep it to what this piece needs. Don't add anything for "later".

## 4. Check it
- **Review your own code first** against the "Quality first" rules in `CLAUDE.md`: separation of concerns, nothing reinvented that a library already does, no smells (duplication, long functions, vague names, dead code). Fix what you find.
- Then run the `/check` skill. Fix anything it reports before moving on.
- In step 5, say in one line what the review found or changed.

## 5. Explain what was built
In plain words, walk through each new or changed file:
- what each part does, and why it's built that way
- the design pattern or Python / PydanticAI feature used, and what problem it solves
- how to run or try it (the exact command)

Link files as clickable paths. Keep it brief: a short list per file, not an essay.

## 6. Update the docs
- Tick the box in `docs/PLAN.md`, and add any newly found work as new boxes.
- Update **Current status** in `CLAUDE.md`.
- Add any decision to `docs/DECISIONS.md` (what and why, one or two lines).
- Update `docs/NOTES.md` (the owner's reference, sorted by feature, with a table of contents at the top):
  - Keep it simple: short plain feature names ("Searches OpenAlex", "Filters by year"), **3 to 8 bullets each**, max 20 words a bullet, saying how it works. No lists of file names, no history, no tiny details.
  - A new feature gets a new heading and a line in the table of contents. If a feature would pass 8 bullets, merge or drop some.
  - **Fix or remove any bullet this step made untrue**, and don't repeat a point that's already there.
  - **Link code names to their exact lines**, relative from `docs/`: `[`rebuild_abstract`](../openalex.py#L25-L33)`. Mark notes about code that doesn't exist yet "(no code yet)".
  - **Re-check every existing link** whenever code changed (any file, including formatting): open the file with line numbers and fix links that now point at the wrong lines.
  - **Search the whole file for "(no code yet)"**, including overview sections like "Agent workflow", and update any note this step made true.
  - **Caveats:** when something goes wrong or turns out limited (a model misbehaves, an API limit, a known weakness), add a short bullet to the "Caveats" section. It feeds the demo and the reflection.

## 7. Stop
Leave everything uncommitted (the owner reviews and commits). Suggest a commit message, and say what the next piece would be. Don't start it.
