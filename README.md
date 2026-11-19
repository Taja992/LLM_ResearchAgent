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
- **Steady answers:** both LLM steps run at temperature 0, so the model always gives its most likely answer and reads the same request the same way each time. Without it, the evaluation saw the same request read differently from run to run (e.g. "before 2012" dropped).
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

## Evaluation

The agent was tested with 12 requests ([evaluation_cases.py](evaluation_cases.py)). They cover broad and narrow topics, before / after / exact years, minimum citations, unclear requests, and two requests where no good paper exists. Code checks the exact things: the year rule, the citation rule, a valid link and source, and that the paper's details match what OpenAlex returned ([evaluation_checks.py](evaluation_checks.py)). The first run passed 48 of 50 checks. After a fix (temperature 0), the second run passed 53 of 55 ([evaluation_results.json](evaluation_results.json)). Relevance and usefulness of the explanation were scored by hand for 10 of the requests: 19/20 for relevance and 15/20 for the explanation. The method, every answer and every score are in [documentation/SCORING.md](documentation/SCORING.md).

Run it yourself with `python evaluate.py` (it uses the real model and OpenAlex).

## Reflection

### What worked well?

Splitting the work between the LLM and plain code worked well. The LLM only does two jobs: it reads the request, and it chooses the best paper from a numbered list. Everything that must be exact is done by code: searching OpenAlex, checking the year and citation count, and copying the paper's details. Because of this, the title, year, citation count and link were correct in every answer, in both test runs. The agent also says "No matching paper found" when nothing fits, instead of choosing a bad paper.

### What failed or was unreliable?

The small local model (qwen2.5 7B) was the weakest part. It did not always read a request the same way: in one run it dropped "before 2012", and it read "around 1000 citations" as "at least 1000". It ignored "summarize in 5-7 sentences" and wrote only 2 sentences, even after I changed the prompt. It never used the search tool it was given, and it could not use PydanticAI's default way of giving structured answers, so I switched to `NativeOutput`. Some choices were only partly right, for example a paper about clinical AI agents for a question about software agents. Also, OpenAlex's free daily limit ran out quickly when I tested without an API key.

### How often did the agent need tool calls?

Every request uses at least one tool call: the OpenAlex search, done by code. An extra search is only needed when no paper fits. This happened in 2 of 12 requests in the final run (both were "no good paper" requests), and in 3 of 12 in the first run. The LLM never called the `search_papers` tool itself. Instead, a code fallback does the extra search with the search words the LLM suggests.

### Did the LLM ever hallucinate?

The facts were never made up. In every answer, an automatic check confirmed that the title, authors, year, citation count and link match a paper that OpenAlex really returned. This is because the LLM cannot write facts; it only picks a number. The explanation text, however, sometimes said things that were not true. In the first run it said a 2023 paper was "published before 2021", and in an earlier test it said a 2020 paper was "published after 2021". It also described a 2017 paper as if it invented the transformer, when it only builds on it.

### How did you prevent incorrect answers?

Both LLM steps must answer in a fixed Pydantic shape; if the answer does not fit, PydanticAI asks again (up to 3 times). The LLM picks a paper by its number, a check rejects numbers that are not on the list, and code copies the real facts. The year and citation rules are sent to OpenAlex and then checked again in code for every paper. Temperature 0 makes the model read the same request the same way each time. The evaluation uses its own hand-written rules for each test, not the rules the LLM read. That is how it caught the wrong 2023 paper in the first run. After setting the temperature to 0, the second run found the correct paper.

### What would you improve with more time?

I would try a larger model, which should read rules more reliably and follow length instructions. I would let code double-check the rules the LLM reads, for example by noticing a year in the request that is missing from the rules. I would give the LLM longer abstracts so it can write fuller summaries. I would make the explanation check smarter, so it also catches wrong words like "before" instead of "after", not only wrong numbers. Finally, I would run each test several times, to measure how often the agent is right and not just whether it was right once.
