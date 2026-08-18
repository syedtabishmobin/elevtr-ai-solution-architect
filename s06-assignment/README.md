# ELVTR AI Solution Architect - Class 6 Assignment #3

This project reuses the Class 5 RAG pipeline and adds a repeatable evaluation
harness. It runs ten verified questions through the same production path,
checks retrieval and evidence with transparent rules, adds a Ragas rubric judge,
and compares a baseline retrieval depth of four chunks with six chunks.

## Project structure

```text
s06-assignment/
├── build.py
├── rag.py
├── checks.py
├── metrics.py
├── evals.py
├── compare.py
├── datasets/rag_eval.jsonl
├── experiments/
├── docs/
├── FINDINGS.md
├── pyproject.toml
└── uv.lock
```

## Models and services

- `ollama/mxbai-embed-large` embeds documents and questions locally.
- `ollama/qwen3:8b` generates grounded answers locally.
- `gpt-5-mini` grades the observable rubric through Ragas.
- ChromaDB stores the generated local index in `.index/`.

The `.env`, `.venv`, `.index`, and final ZIP are intentionally excluded from
Git and from the submission archive.

## Experiment design

The dataset contains the assignment's required mix: four direct lookups, two
numeric questions, one completeness question, one two-source comparison, one
missing-information case, and one difficult PDF-table case. Some categories
overlap with ordinary user behavior, but every row has one stable primary label.

The only changed variable is retrieval depth:

- `baseline`: `top_k=4`
- `top_k_6`: `top_k=6`

All other code, prompts, models, documents, questions, and grading rules remain
the same. The exact terminal sequence is supplied in the accompanying handoff.

