# Research Scout Agent

An AI agent, built with [PydanticAI](https://pydantic.dev/docs/ai/), that finds a research paper matching a request such as *"a paper on graph neural networks from before 2015 with at least 1000 citations"*, checks it against the constraints, and explains why it fits.

> Work in progress: the workflow below is the design; parts of it are still being built.

## How the agent works

Python code runs the steps in a fixed order. The LLM is used only where language understanding or judgement is needed. Anything that must be exact (calling the paper API, checking years and citation counts, copying facts into the answer) is plain, deterministic code. PydanticAI calls this pattern *programmatic agent hand-off*: application code decides what runs next.

```text
user request
  │
  ├─ 1. LLM   Understand the request → Constraints (structured output)
  │           topic · year rule (before / after / in) · citation rule (at least / at most / about)
  │
  ├─ 2. CODE  Search OpenAlex for the topic, with the year/citation rules as filters → candidates
  │
  ├─ 3. CODE  Filter candidates: keep, or reject with a reason (e.g. "published 2017, needs before 2015")
  │
  ├─ 4. LLM   Judge relevance: pick the best surviving candidate, explain why, note any doubts
  │           └─ optional tool: search_papers(new wording) → runs steps 2–3 again in code
  │
  └─ 5. CODE  Build the answer: title, authors, year, citations, source and link are copied
              from the chosen paper's OpenAlex data; the LLM supplies only the explanation
```

| Step | Who | Why there |
| --- | --- | --- |
| 1. Understand the request | LLM | Requests are free text ("recent", "highly cited", "before 2015"); turning them into rules needs language understanding. The output must fit a Pydantic `Constraints` model, so it's checked automatically. |
| 2. Search for candidates | Code | Calling an API must be exact and repeatable. |
| 3. Filter by year and citations | Code | Comparing numbers must be exact. An LLM can misread "after 2022" or misremember counts. |
| 4. Judge relevance | LLM | Whether a paper is really *about* the topic is a judgement call on titles and abstracts. |
| 5. Build the answer | Code | Facts are copied from the tool's data, so the LLM cannot invent a title, year or citation count. |

**When nothing fits:** if no candidate survives the filter (even after the optional re-search), code returns a clear "no matching paper found" answer, listing why candidates were rejected, instead of forcing a pick.

**Uncertainty:** the LLM's explanation must mention doubts, for example when the topic is only partly matched or "about 1000 citations" is close but not exact.

**Citation counts** always come from OpenAlex (`cited_by_count`), and each answer names that source.
