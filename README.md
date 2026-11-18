# Research Scout Agent

An AI agent, built with [PydanticAI](https://pydantic.dev/docs/ai/), that finds a research paper matching a request such as *"a paper on graph neural networks from before 2015 with at least 1000 citations"*, checks it against the constraints, and explains why it fits.

## How the agent works

Python code runs five steps in a fixed order; the LLM never decides what happens next. The LLM is used only where language understanding or judgement is needed. Anything that must be exact (calling the paper API, checking years and citation counts, copying facts into the answer) is plain, deterministic code. PydanticAI calls this pattern *programmatic agent hand-off*. The whole workflow is one short function, [`find_paper`](workflow.py), where each step is marked `# LLM` or `# CODE`.

```text
user request
  │
  ├─ 1. LLM   Understand the request → Constraints (structured output)
  │           topic · year rule · citation rule · "recent" flag
  │           comparisons: <  <=  >  >=  =  about   ("after 2022" → > 2022)
  │
  ├─ 2. CODE  Search OpenAlex for the topic, with the year/citation rules as filters → candidates
  │
  ├─ 3. CODE  Filter candidates again: keep, or reject with a reason ("year is 2017, needs < 2015")
  │
  ├─ 4. LLM   Judge relevance: pick the best candidate *by number*, explain why, note doubts
  │           └─ if nothing fits: one more search with better words, via the search_papers
  │              tool or a code fallback (small models rarely call tools) → steps 2–3 in code
  │
  └─ 5. CODE  Build the answer: title, authors, year, citations, source and link are copied
              from the chosen paper's OpenAlex data; the LLM supplies only explanation + uncertainty
```

| Step | Who | Where in the code | Why there |
| --- | --- | --- | --- |
| 1. Understand the request | LLM | `extract_constraints` in [agents.py](agents.py) | Requests are free text ("recent", "more than 500", "around 2015"); turning them into rules needs language understanding. The answer must fit the `Constraints` model, so it's checked automatically. |
| 2. Search for candidates | Code | `search_openalex` in [openalex.py](openalex.py) | Calling an API must be exact and repeatable. |
| 3. Filter by year and citations | Code | `filter_papers` in [filters.py](filters.py), rule meanings in [rules.py](rules.py) | Comparing numbers must be exact. An LLM can misread "after 2022" or misremember counts. |
| 4. Judge relevance | LLM | `judge_relevance` in [agents.py](agents.py) | Whether a paper is really *about* the topic is a judgement call on titles and abstracts. |
| 5. Build the answer | Code | `PaperAnswer.from_paper` in [models.py](models.py) | Facts are copied from the tool's data, so the LLM cannot invent a title, year or citation count. |

### How the LLM's answers are checked

- **Structured output:** both LLM steps must answer in a Pydantic model. With `NativeOutput`, the model server itself forces the reply into that JSON shape; if it still doesn't fit, PydanticAI sends the error back and the LLM retries (up to 3 times).
- **Pointing, not typing:** in step 4 the LLM only gives a candidate's number. An output validator rejects numbers outside the list, and code then copies that paper's real facts.
- **Double check:** the year and citation rules are sent to OpenAlex *and* re-checked in code for every paper. A paper with a missing year or citation count fails the rule instead of being guessed.
- **One meaning for every rule:** "about" (±1 year, ±20 % citations), "recent" (the last 3 years) and "or later" are defined once in [rules.py](rules.py), used by both the OpenAlex query and the filter.

**Uncertainty:** every answer has a separate `uncertainty` field where the LLM states its doubts (for example, the topic only partly matches), or `null` if it has none.

**When nothing fits:** if no candidate fits (even after the extra search), the agent answers "No matching paper found." instead of forcing a pick. Code adds how many papers were checked and how many failed each rule (e.g. "18 papers: year needs < 2015"); the LLM adds why the papers that passed the rules still weren't about the topic.

**Citation counts** always come from OpenAlex (`cited_by_count`), and each answer names that source.

### Example

```text
python main.py "Find a research paper about LLM agents for software engineering that was published
                after 2022 and has at least 100 citations. Explain why the paper is relevant and
                provide the source of the citation count."
```

```json
{
  "title": "Demystifying LLM-Based Software Engineering Agents",
  "authors": ["Chunqiu Steven Xia", "Yinlin Deng", "Soren Dunn", "Lingming Zhang"],
  "year": 2025,
  "citation_count": 1052,
  "citation_source": "OpenAlex",
  "url": "https://doi.org/10.1145/3715754",
  "explanation": "The paper 'Demystifying LLM-Based Software Engineering Agents' (2025, 1052 citations) is the most relevant to the topic of LLM agents for software engineering. It discusses recent advancements in using autonomous LLM-based agents for end-to-end software development tasks, which aligns well with the request. ...",
  "uncertainty": null
}
```
