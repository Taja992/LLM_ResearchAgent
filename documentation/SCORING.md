# Scoring sheet (run 2)

## Why this evaluation method

Code checks the facts that have a right or wrong answer: the year, the citation count, the link, and whether the details match the real paper. Code is fast and always gives the same result. A person scores the two things that need judgement: is the paper really about the topic, and is the explanation useful. The agent's own small model doesn't grade itself, because research shows AI judges tend to favour their own answers. Instead, Claude drafted the scores and I checked and confirmed each one. 10 of the 12 test requests are scored by hand; the two left out were clearly fine. This follows advice from [Anthropic](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) and [Zheng et al.](https://arxiv.org/abs/2306.05685)

> 10 of the 12 test requests are scored. Left out: `broad_machine_learning` and `narrow_federated_medical_2020` (both clearly fine; their kinds of request are covered by others).

## 1. brief_llm_agents_for_software

**Request:** Find a research paper about LLM agents for software engineering that was published after 2022 and has at least 100 citations. Explain why the paper is relevant and provide the source of the citation count.

**Counts as relevant:** LLM-based agents doing software engineering tasks.

**Agent's reply:**

- Paper: [Demystifying LLM-Based Software Engineering Agents](https://doi.org/10.1145/3715754) (2025, 1,053 citations)
- Explanation: The paper 'Demystifying LLM-Based Software Engineering Agents' (2025) is the most relevant to the request. It discusses recent advancements in using large language models (LLMs) for software engineering tasks, specifically focusing on autonomous agents that can perform end-to-end development tasks. The abstract mentions that these agents are equipped with the ability to use tools, run commands, and plan future actions, which aligns well with the concept of LLM agents in software engineering.
- Doubts: none given

**Relevant (0–2):** 2

**Explanation (0–2):** 2

**Note:** Exactly on topic. Citation source isn't in the text, but the answer's citation_source field says OpenAlex. (I also checked manually)

## 2. brief_rag_before_2021

**Request:** Find a paper about retrieval-augmented generation published before 2021 with more than 500 citations. Summarize its contribution in 5-7 sentences.

**Counts as relevant:** Retrieval-augmented generation; summary is 5-7 sentences.

**Agent's reply:**

- Paper: [Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://doi.org/10.48550/arxiv.2005.11401) (2020, 10,307 citations)
- Explanation: This paper titled 'Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks' is directly about retrieval-augmented generation and was published in 2020 with over 1,000 citations. It discusses how large pre-trained language models can be enhanced by accessing external knowledge sources to improve their performance on knowledge-intensive tasks.
- Doubts: none given

**Relevant (0–2):** 2

**Explanation (0–2):** 1

**Note:** The original RAG paper. Only 2 sentences, asked for 5-7. 'Over 1,000 citations' is true.

## 3. brief_recent_tool_using_agents

**Request:** Find a recent paper about AI agents using tools and explain whether it would be useful for someone building autonomous software agents.

**Counts as relevant:** AI agents calling tools; says if useful for autonomy.

**Agent's reply:**

- Paper: [AgentClinic: a multimodal benchmark for tool-using clinical AI agents](https://doi.org/10.1038/s41746-026-02674-7) (2026, 403 citations)
- Explanation: The paper 'AgentClinic: a multimodal benchmark for tool-using clinical AI agents' is the most relevant to the request as it discusses AI agents using tools in a clinical setting, which can be analogous to autonomous software agents. The abstract mentions evaluating large language models (LLMs) in simulated clinical environments that include patient interactions and usage of tools, making it highly pertinent to the topic.
- Doubts: none given

**Relevant (0–2):** 1

**Explanation (0–2):** 1

**Note:** Tool-using agents, but for clinical use, not software. Doesn't really answer 'would it be useful for building autonomous software agents'; 'highly pertinent' overclaims.

## 4. broad_computer_vision_highly_cited

**Request:** Find a paper about computer vision with at least 10000 citations.

**Counts as relevant:** Any computer vision paper.

**Agent's reply:**

- Paper: [Rethinking the Inception Architecture for Computer Vision](https://doi.org/10.1109/cvpr.2016.308) (2016, 38,427 citations)
- Explanation: Paper number 2, 'Rethinking the Inception Architecture for Computer Vision,' has a high citation count of 38,427 and directly addresses computer vision. The paper discusses convolutional networks, which are central to many state-of-the-art solutions in computer vision tasks.
- Doubts: none given

**Relevant (0–2):** 2

**Explanation (0–2):** 2

**Note:** Inception v3, clearly computer vision. Small flaw: says 'Paper number 2', an internal list number the user can't see.

## 5. narrow_gnn_before_2015

**Request:** A paper on graph neural networks from before 2015 with at least 1000 citations.

**Counts as relevant:** Neural networks that work on graph-structured data.

**Agent's reply:**

- Paper: [The Graph Neural Network Model](https://doi.org/10.1109/tnn.2008.2005605) (2008, 12,649 citations)
- Explanation: The paper titled 'The Graph Neural Network Model' was published in 2008 and has 12649 citations. It introduces the concept of graph neural networks (GNNs) which can process data represented in graph domains, making it a foundational work that predates 2015 and meets the citation requirement.
- Doubts: none given

**Relevant (0–2):** 2

**Explanation (0–2):** 2

**Note:** The original GNN paper (Scarselli et al.). Facts in the explanation are correct.

## 6. exact_year_transformer_2017

**Request:** Find a paper about the transformer architecture published in 2017.

**Counts as relevant:** The transformer neural network (attention) architecture.

**Agent's reply:**

- Paper: [Weighted Transformer Network for Machine Translation](https://doi.org/10.48550/arxiv.1711.02132) (2017, 175 citations)
- Explanation: The paper titled 'Weighted Transformer Network for Machine Translation' published in 2017 discusses a new architecture that uses only self-attention and feed-forward layers, which is referred to as the transformer architecture. This matches the request for a paper about the transformer architecture published in 2017.
- Doubts: none given

**Relevant (0–2):** 2

**Explanation (0–2):** 1

**Note:** About the transformer architecture, but a lesser-known variant, not 'Attention Is All You Need'. Explanation makes it sound like this paper introduced the transformer; it builds on it.

## 7. ambiguous_around_numbers

**Request:** A paper about contrastive learning from 2019 or later with around 1000 citations.

**Counts as relevant:** Contrastive (self-supervised) representation learning.

**Agent's reply:**

- Paper: [Contrastive Learning for Sequential Recommendation](https://doi.org/10.1109/icde53745.2022.00099) (2022, 1,225 citations)
- Explanation: The paper 'Contrastive Learning for Sequential Recommendation' published in 2022 with 1225 citations is the most relevant to the request. It discusses contrastive learning, a topic that aligns well with the user's interest, and it meets the criteria of being from 2019 or later and having around 1000 citations.
- Doubts: none given

**Relevant (0–2):** 2

**Explanation (0–2):** 1

**Note:** Contrastive learning, applied to recommendation. Explanation is vague (just 'discusses contrastive learning'). 1,225 citations is outside our 'about' range (800-1,200); the automatic check already caught that.

## 8. ambiguous_transformers

**Request:** something about transformers

**Counts as relevant:** Transformer models, or power transformers if the uncertainty field mentions the double meaning.

**Agent's reply:**

- Paper: [A survey of transformers](https://doi.org/10.1016/j.aiopen.2022.10.001) (2022, 2,135 citations)
- Explanation: This paper is titled 'A survey of transformers' and provides a comprehensive review of various Transformer variants, making it highly relevant to the topic of transformers in general.
- Doubts: none given

**Relevant (0–2):** 2

**Explanation (0–2):** 2

**Note:** A survey of machine-learning transformers is a sensible pick. Only 1 sentence, and doesn't mention 'transformers' has two meanings (the rubric doesn't require it).

## 9. no_paper_video_diffusion_before_2012

**Request:** Find a paper about diffusion models for video generation published before 2012 with more than 1000 citations.

**Counts as relevant:** None exists: video diffusion models are from after 2020.

**Agent's reply:**

- No matching paper found. (25 papers checked)
- Explanation: None of the provided papers match the request for a paper about diffusion models for video generation published before 2012 with more than 1000 citations.

**Relevant (0–2):** 2

**Explanation (0–2):** 1

**Note:** Correctly said no match. The reason only repeats the request; it doesn't say why (video diffusion models didn't exist before 2012).

## 10. no_paper_llm_knitting_before_2015

**Request:** A paper about using large language models to grade knitting patterns, published before 2015.

**Counts as relevant:** None exists: LLMs did not exist before 2015.

**Agent's reply:**

- No matching paper found. (25 papers checked)
- Explanation: None of the provided papers directly address the use of large language models to grade knitting patterns, as requested. The closest match is paper [4], which discusses leveraging large language models for automated insight generation in textile manufacturing, but it does not specifically mention grading or pattern evaluation.

**Relevant (0–2):** 2

**Explanation (0–2):** 2

**Note:** Correctly said no match, with a clear reason and the closest candidate. Odd: that candidate is a modern LLM paper, so the 'before 2015' rule was probably dropped in this run. The answer was still right.
