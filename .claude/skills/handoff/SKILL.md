---
name: handoff
description: Wrap up this session and write a prompt for a fresh Claude instance to continue the work. Use when the owner says "handoff", "wrap up", "new instance", or is switching Claude sessions (usually at the end of a phase or partway through a big one).
---

# Handoff

The owner switches Claude instances every phase (sometimes mid-phase). The next instance starts cold, so anything not written down is lost. Goal: **docs hold the durable facts; the prompt holds only what's left over.**

## 1. Check the repo state
- If this is a git repo: `git status --short` and `git log --oneline -5`. If it isn't yet, say so.
- If there are uncommitted changes, run the `check` skill and note the result. Suggest a commit message. Don't commit.

## 2. Make the docs current
Anything from this session that should outlive it goes in the docs, not just the prompt:
- **Current status** in `CLAUDE.md`: where things stand and what's next.
- `docs/PLAN.md`: tick finished items, add newly discovered work as items.
- `docs/DECISIONS.md`, `docs/NOTES.md`: anything decided, built, or verified and not yet written up.

Tell the owner which docs you changed.

## 3. Collect loose ends from this conversation
Things the docs don't capture well:
- manual tests the owner hasn't reported back on
- offers made but not decided (say they're undecided, so the next instance asks instead of doing them)
- known rough edges or bugs deliberately left for later
- environment quirks that confused us (editor extensions, paths, API rate limits, etc.)
- open questions the owner asked that weren't fully answered

If a loose end is really future work, put it in `docs/PLAN.md` instead.

## 4. Write the prompt
Fill in this template. Keep it short: point to files rather than repeating them.

```text
We're continuing <phase / step> of this project (Research Scout Agent, a PydanticAI course assignment). I'm learning as we build, so follow "How we work" in CLAUDE.md exactly: talk before building, small steps, explanations in simple English, AskUserQuestion for real choices, leave changes uncommitted, suggest a commit message.

Before proposing anything, read:
- CLAUDE.md, docs/PLAN.md, docs/DECISIONS.md, docs/NOTES.md (and docs/ASSIGNMENT.md for the requirements)
- <the code files the next step builds on>

Where we are:
- <2-4 bullets: what's done, what exists, what doesn't yet>

Loose ends (ask me about these when relevant, don't just do them):
- <from step 3, or "none">

First task: run the next-step skill for <the next piece>. <What you expect it to involve.> If that's too big for one step, split it and tell me the split first.
```

## 5. Hand it over
- Start your message with "Written for: the next Claude instance, continuing <phase>."
- Give the prompt in a single `text` code block so it copies cleanly.
- After it, add a short "Before you switch" list: commit (with the suggested message) if needed, and any quick manual test worth doing first.
