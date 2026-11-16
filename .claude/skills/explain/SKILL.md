---
name: explain
description: Walk through existing code in plain words so the owner understands how it works. Use when the owner asks "how does X work", "explain this file", "walk me through", or selects code and asks about it.
---

# Explain

Helps the owner understand code that already exists. Explaining only: don't change anything unless asked.

## How to explain
1. **Start with the big picture.** In one or two sentences: what this code is for, and where it sits in the agent's workflow (request → constraints → search → filter → LLM judgment → answer; what calls it, what it calls).
2. **Say who does the work:** is this part the LLM, or plain deterministic code? Why?
3. **Then go piece by piece,** top to bottom, in plain words. Quote short snippets only when that helps.
4. **Name the patterns.** If a design pattern or Python / PydanticAI feature is used (a decorator, a Pydantic model, a tool, structured output, retries, dependency injection), say what it is and what problem it solves here.
5. **Explain jargon** the first time it appears (agent, tool call, structured output, DOI, OpenAlex...).
6. **Show how to try it:** a command to run or a test to read.

## Keep it right-sized
- Pitch it for someone mid-level in Python, in simple everyday English.
- Keep it short: lists over paragraphs. Offer to go deeper on any part instead of covering everything at once.
- If you spot a code smell or bug while explaining, mention it at the end as a suggestion. Don't fix it unasked.
