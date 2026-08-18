# ELVTR AI Solution Architect - Assignment 06

## Start Testing Your RAG

This project is my implementation of **Class 6 Assignment #3** for the ELVTR
AI Solution Architect course.

Class 5 focused on keeping a Retrieval-Augmented Generation pipeline fresh and
reliable. This assignment reuses that real pipeline and adds a systematic
evaluation layer around it. Ten representative questions are sent through the
same embed, retrieve, context-building, and generation path used by the
application. Every result is then checked for answer quality, source retrieval,
required facts, quotability, and index integrity.

The project combines deterministic checks with a Ragas rubric judge. This is
important because a fluent or factually correct answer does not prove that the
RAG system worked correctly. The model may answer well even when the expected
document was not retrieved or when the required fact cannot be quoted from the
stored evidence.

The completed experiment results and shipping decision are recorded in
[`FINDINGS.md`](FINDINGS.md).

---

## Learning objectives

This assignment demonstrates:

1. How to turn realistic user questions into a reusable RAG evaluation dataset.
2. Why stable question IDs, expected sources, key facts, and trap facts make
   experiments repeatable.
3. How to expose the real RAG application behind one evaluation function.
4. How source recall distinguishes retrieval failure from generation failure.
5. How required-fact and trap checks catch observable answer mistakes.
6. Why quotability must be tested separately from answer correctness.
7. How index-integrity checks identify facts lost during document ingestion.
8. Where an LLM rubric judge adds value beyond exact string matching.
9. Why deterministic evidence checks should remain beside an LLM judge.
10. How saved experiment runs reveal per-question improvements and regressions.
11. How to compare two configurations while changing only one variable.
12. How evaluation evidence supports an explicit shipping decision.

---

## Results at a glance

Both experiments completed all ten evaluation cases.

| Experiment | Result |
|---|---|
| Evaluation dataset | 10 verified questions across six test categories |
| Baseline configuration | Four retrieved chunks per question |
| Changed configuration | Six retrieved chunks per question |
| Clean baseline passes | `q01`, `q02`, `q03`, `q05`, `q08`, `q09`, and `q10` |
| Completeness failure | `q07` omitted two required policy areas |
| Wording-sensitive failure | `q06` said four chunks but omitted that they were the closest chunks |
| Evidence failure | `q04` received a judge pass despite zero expected-source recall and failed quotability |
| PDF-table ingestion case | `q10` preserved and retrieved all three required Apple net-sales values |
| Improvements with six chunks | None |
| Regressions with six chunks | `q04` correctness changed from pass to fail |
| Shipping decision | Keep the four-chunk baseline; do not ship the six-chunk change |

The comparison showed why averages are not enough. Increasing retrieval depth
did not improve any case, did not fix the two existing answer failures, and
caused one judge result to regress.

---

## Project structure

```text
s06-assignment/
├── .env.example
├── .gitignore
├── .python-version
├── README.md
├── FINDINGS.md
├── build.py
├── rag.py
├── checks.py
├── metrics.py
├── evals.py
├── compare.py
├── pyproject.toml
├── uv.lock
├── datasets/
│   └── rag_eval.jsonl
├── experiments/
│   ├── baseline.csv
│   └── top_k_6.csv
└── docs/
    ├── apple_annual_report.pdf
    ├── microsoft_annual_report.pdf
    ├── tesla_annual_report.pdf
    ├── equity_research_policy.md
    └── portfolio_research_faq.md
```

### File descriptions

| File | Purpose |
|---|---|
| `build.py` | Reads the five source documents, creates overlapping chunks, embeds them, and upserts them into ChromaDB |
| `rag.py` | Exposes the one real `answer()` path used by every evaluation case and returns the response, exact contexts, and sources |
| `checks.py` | Implements source recall, key-fact/trap, quotability, and index-integrity checks |
| `metrics.py` | Defines the Ragas correctness rubric and its pass/fail evaluation policy |
| `evals.py` | Runs one named experiment across the full JSONL dataset and saves every result to CSV |
| `compare.py` | Compares two saved CSVs by stable question ID and prints metric changes |
| `datasets/rag_eval.jsonl` | Contains the ten verified evaluation cases and their grading contracts |
| `experiments/baseline.csv` | Stores the complete `top_k=4` baseline run |
| `experiments/top_k_6.csv` | Stores the complete `top_k=6` changed-configuration run |
| `FINDINGS.md` | Explains the observed passes, failures, evidence quality, judge behavior, comparison, and decision |
| `docs/` | Contains the same five-document shareable corpus used by the Class 5 pipeline |
| `pyproject.toml` | Declares the project and its direct Python dependencies |
| `uv.lock` | Locks the complete dependency graph for reproducible installation |
| `.env.example` | Shows the environment variable required by the cloud evaluation judge |
| `.gitignore` | Excludes secrets, environments, the generated vector index, caches, and ZIP files |

The three annual reports reuse the earlier course corpus. The two Markdown
documents are shareable coursework scenarios containing controlled policy and
assistant-behavior facts.

---

## Technology stack

- **Python 3.11** for the application and evaluator
- **uv** for Python selection, dependency installation, and locking
- **Ollama** for local embedding and answer-generation models
- **LiteLLM** as the common interface for local model calls
- **ChromaDB** for the persistent vector index
- **PyPDF** for annual-report text extraction
- **Ragas 0.3.9** for the rubric metric and experiment framework
- **OpenAI Async client** for the Ragas judge
- **python-dotenv** for loading the judge API key from `.env`
- **mxbai-embed-large** as the local embedding model
- **Qwen3:8b** as the local answer-generation model
- **GPT-5 mini** as the evaluation judge

Only the rubric judge uses a cloud model. Document embeddings and RAG answer
generation remain local through Ollama.

---

## Architecture

```text
                    Source documents: docs/
                              |
                              v
                  PDF / Markdown extraction
                              |
                              v
                 120-word overlapping chunks
                              |
                              v
             mxbai-embed-large document embeddings
                              |
                              v
                    ChromaDB index: .index/
                              |
                 +------------+------------+
                 |                         |
                 v                         v
        Evaluation question        all_indexed_chunks()
                 |                         |
                 v                         v
          question embedding       index-integrity check
                 |
                 v
        retrieve top_k chunks
                 |
                 v
       build grounded context
                 |
                 v
         Qwen3:8b generation
                 |
                 v
    response + contexts + sources
                 |
       +---------+----------+----------------+
       |                    |                |
       v                    v                v
transparent checks     Ragas judge      saved CSV row
       |                    |                |
       +--------------------+----------------+
                              |
                              v
                    compare.py + findings
```

### The indexing path

`build.py` reads PDF, Markdown, and text files from `docs/`. It splits each
document into 120-word chunks with 20 words of overlap. Stable IDs combine the
source filename with the chunk position. The chunks are embedded with
`ollama/mxbai-embed-large` and upserted into the persistent Chroma collection.

The generated `.index/` folder is local and reproducible, so it is excluded
from Git and the submission ZIP.

### The application path

`rag.py` exposes:

```python
def answer(question: str, top_k: int = 4) -> dict:
    ...
```

Every test case uses this same function. It performs the real application
sequence:

```text
question -> embed -> retrieve -> build context -> generate
```

It returns:

```python
{
    "response": "generated grounded answer",
    "contexts": ["exact retrieved chunk 1", "exact retrieved chunk 2"],
    "sources": ["source-a.md", "source-b.pdf"],
}
```

The expected answer is never passed to the generator. There are no
question-specific answers or evaluation shortcuts in the RAG path.

### The evaluation path

`evals.py` loads every JSONL row, calls `answer()`, applies the transparent
checks, asks the Ragas judge to grade the observable rubric, and writes one CSV
row containing the response and every diagnostic value.

The evaluator also verifies that the number of output rows matches the number
of dataset rows. A partial experiment is rejected rather than silently compared.

---

## Evaluation dataset

The dataset contains ten JSON objects, one per line. Each object has these
fields:

| Field | Meaning |
|---|---|
| `qid` | Stable identifier used to align cases across experiments |
| `category` | Primary test type used for grouped reasoning |
| `question` | Natural user wording without source hints |
| `expected_answer` | Concise human-verified reference answer |
| `grading_notes` | Observable requirements used by the Ragas judge |
| `source_file` | Expected evidence document or ` + ` separated documents |
| `key_facts` | Short facts that a successful response must contain |
| `trap_facts` | Plausible but incorrect values that must not appear |

### Required test mix

| Category | Cases | What it tests |
|---|---|---|
| Direct lookup | `q01`-`q04` | Retrieval and grounding for clean prose facts and rules |
| Numeric/date | `q05`, `q06` | Exact values, associated meaning, and nearby traps |
| Completeness | `q07` | Whether several required policy items are all included |
| Comparison | `q08` | Whether retrieval reaches and combines two expected files |
| Missing information | `q09` | Whether the assistant refuses instead of inventing an answer |
| Ingestion/layout | `q10` | Whether three values from a dense financial table survive extraction and retrieval |

The categories are mutually labelled for analysis, although individual cases
may exercise more than one capability.

---

## The four transparent checks

### 1. Source recall

Source recall asks what fraction of the expected source files were reached by
retrieval:

```text
expected sources retrieved / total expected sources
```

A score of `1.0` means every expected document appeared. A low score points to
a retrieval problem even when the answer sounds reasonable.

### 2. Key facts and traps

The key-fact check verifies that every required fact appears in the response and
that none of the known wrong values appear. It returns `pass` or `fail` plus the
specific missing facts and detected traps.

The matcher treats a fact as its own value rather than accepting it inside a
larger fused number. This helps detect extraction or generation errors around
financial values.

### 3. Quotability

The quotability check looks only at required facts that the response actually
states. It verifies that each one is also present in at least one exact retrieved
chunk.

This separates a correct-looking answer from an evidence-backed answer. A model
may reconstruct, remember, or guess a value even when retrieval did not supply
quotable proof.

### 4. Index integrity

The index check searches all chunks exactly as stored in ChromaDB. If a required
fact is absent from the index, changing the retriever cannot recover it. The
problem is in extraction or indexing and must be fixed earlier in the pipeline.

Missing-information cases have no positive required facts, so quotability and
index integrity are reported as `not_applicable`. Their behavior is evaluated
with the trap check and rubric judge.

---

## Ragas correctness judge

`metrics.py` defines a discrete `pass` or `fail` correctness metric. Its prompt
requires the response to satisfy every observable grading note; a missing or
contradicted requirement is a failure.

The judge is useful when:

- several facts must form a complete answer;
- wording may legitimately differ from the reference;
- a relationship or process must be explained;
- a missing-information response must refuse without guessing; or
- exact string matching does not capture the full requirement.

The judge is deliberately not the only metric. In the baseline, it passed
`q04` even though expected-source recall was zero and quotability failed. That
disagreement is valuable evidence for keeping transparent checks beside the
model-based evaluator.

---

## Prerequisites

### 1. Git

Verify Git:

```bash
git --version
```

### 2. uv

Install `uv` on macOS or Linux if needed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Restart the terminal and verify it:

```bash
uv --version
```

### 3. Ollama

Install and start Ollama, then download the two local models:

```bash
ollama pull mxbai-embed-large
ollama pull qwen3:8b
```

Verify that Ollama is running:

```bash
ollama list
curl http://localhost:11434/api/tags
```

### 4. OpenAI API key

The Ragas judge requires an OpenAI API key. The key belongs only in the local
`.env` file and must never be committed or submitted.

Create it from the safe example:

```bash
cp .env.example .env
```

Edit `.env` so it contains:

```text
OPENAI_API_KEY=your_real_key_here
```

---

## Installation

Clone the repository and enter the assignment folder:

```bash
git clone https://github.com/syedtabishmobin/elevtr-ai-solution-architect.git
cd elevtr-ai-solution-architect/s06-assignment
```

Install the locked dependencies:

```bash
uv sync
```

Manual virtual-environment activation is not required because all project
commands use `uv run`.

If a different virtual environment is already active, leave it first:

```bash
deactivate
uv sync
```

---

## Quick start

### 1. Build the vector index

Ensure Ollama is running, then execute:

```bash
uv run python build.py
```

The supplied corpus should finish with five documents and 1,613 chunks:

```text
indexed 1613 chunks from 5 docs -> 1613 in collection
```

### 2. Run the baseline

```bash
uv run python evals.py baseline 4
```

This evaluates all ten cases with four retrieved chunks and saves:

```text
experiments/baseline.csv
```

The run is valid only if the evaluator reports all ten rows:

```text
Wrote experiments/baseline.csv with 10 rows
```

### 3. Run the changed configuration

```bash
uv run python evals.py top_k_6 6
```

This changes only retrieval depth and saves:

```text
experiments/top_k_6.csv
```

Expected completion message:

```text
Wrote experiments/top_k_6.csv with 10 rows
```

### 4. Compare the saved experiments

```bash
uv run python compare.py baseline top_k_6
```

The recorded result was:

```text
baseline -> top_k_6

q04: correctness: pass -> fail
```

The comparison intentionally prints changed cases rather than hiding them
inside one average.

---

## Experiment design

The controlled variable is retrieval depth:

| Setting | Baseline | Changed run |
|---|---:|---:|
| `top_k` | 4 | 6 |
| Dataset | Same | Same |
| Source documents | Same | Same |
| Vector index | Same | Same |
| Embedding model | Same | Same |
| Generator model | Same | Same |
| System prompt | Same | Same |
| Ragas rubric | Same | Same |

Changing one variable makes the result interpretable. If the model, prompt,
chunking, and retrieval depth all changed together, it would be impossible to
say which change caused an improvement or regression.

---

## Understanding the CSV output

Each experiment row includes:

| Column | Interpretation |
|---|---|
| `qid` | Stable case identifier |
| `category` | Evaluation category |
| `question` | User question sent through the RAG path |
| `response` | Generated answer |
| `correctness` | Ragas rubric result |
| `source_recall` | Fraction of expected documents retrieved |
| `key_facts` | Required-fact and trap result |
| `quotable` | Whether stated required facts were found in retrieved chunks |
| `index_ready` | Whether all required facts exist anywhere in the index |
| `missing_facts` | Required facts omitted from the response |
| `trap_facts_found` | Known wrong values present in the response |
| `unquotable_facts` | Stated facts absent from retrieved text |
| `facts_absent_from_index` | Required facts missing from the stored index |
| `retrieved_sources` | Unique source files reached by retrieval |
| `judge_reason` | Ragas explanation for its pass or fail |

### Diagnostic patterns

- **Low source recall:** retrieval did not reach the expected document.
- **Full source recall with missing facts:** retrieval reached the file, but the
  relevant evidence was not selected or used completely.
- **Correctness pass with quotability failure:** the answer sounds acceptable,
  but the retrieved evidence cannot directly support it.
- **Index-integrity failure:** the required fact did not survive extraction or
  indexing; retriever tuning alone cannot fix it.
- **More context with no improvement:** the added chunks may be irrelevant or
  distracting rather than useful.

---

## Observed cases

### Clean pass: `q10`

The difficult-layout case asked for three values from an Apple financial table.
The response returned all three correctly, retrieval reached the Apple report,
and both quotability and index integrity passed. This shows that extraction
preserved the necessary table evidence for this specific question.

### Completeness failure: `q07`

The expected policy document was retrieved and the required facts existed in
the index. The response nevertheless omitted escalation-recording and
superseded-note requirements. This points to evidence selection or generation,
not ingestion.

### Evidence failure: `q04`

The baseline judge passed the response, but the expected FAQ was never
retrieved. Source recall was `0.0`, the required facts were missing, and
quotability failed. The case demonstrates why a judge score alone is not enough
to validate a RAG answer.

### Missing-information behavior: `q09`

The response correctly said that the research assistant's support email was
not available and did not invent one. The Ragas judge added value because this
behavior cannot be confirmed by looking for a positive required fact.

---

## Troubleshooting

### Ollama connection error

Confirm that the Ollama application is open and both models are installed:

```bash
ollama list
curl http://localhost:11434/api/tags
```

### Missing OpenAI API key

Confirm that `.env` exists in `s06-assignment/` and contains:

```text
OPENAI_API_KEY=your_real_key_here
```

Do not add quotes or commit the file.

### Empty Chroma collection

Build the index before evaluating:

```bash
uv run python build.py
```

### Ragas import error involving `langchain_community`

Reinstall the locked environment. The project pins Ragas to `0.3.9` and keeps
`langchain-community` below `0.4`:

```bash
uv sync --locked
```

### Fewer than ten CSV rows

Do not trust or compare an incomplete experiment. Read the terminal error, fix
the failed model or API call, and rerun the same named experiment. `evals.py`
checks the final row count and raises an error when a task was dropped.

### Different judge results on repeated runs

LLM judges can vary. Inspect `judge_reason` together with the deterministic
columns instead of accepting the judge label alone.

### High source recall but a failed answer

The correct file arrived, but the required chunk may not have arrived or the
generator may have ignored part of the evidence. Inspect `missing_facts`,
`quotable`, and the full response.

### Expected fact visible in the PDF but `index_ready` fails

The extraction pipeline did not preserve the fact in stored text. Inspect PDF
extraction and chunk construction before changing retrieval depth.

---

## Reproducing the complete assignment

From the assignment directory:

```bash
uv sync
cp .env.example .env
# Add the real OPENAI_API_KEY to .env.
ollama pull mxbai-embed-large
ollama pull qwen3:8b
uv run python build.py
uv run python evals.py baseline 4
uv run python evals.py top_k_6 6
uv run python compare.py baseline top_k_6
```

Then review both CSV files and record specific question IDs in `FINDINGS.md`.

---

## Submission archive

The final archive is `s06-assignment.zip`. It contains the reproducible project,
the shareable source corpus, both completed experiments, and the findings note.

It intentionally excludes:

- `.venv/` and installed packages;
- `.env` and the real API key;
- `.index/` and generated vector data;
- local Ollama model files;
- Python bytecode and cache directories;
- macOS `.DS_Store` files; and
- nested ZIP archives.

The safe `.env.example` remains in the archive because it contains only a
placeholder and documents the required configuration.

---

## Final outcome

The evaluation did not support increasing retrieval depth from four chunks to
six. The changed configuration improved no case and caused `q04` to regress.
The four-chunk baseline is therefore retained.

The larger lesson is that answer correctness, evidence quality, and ingestion
quality must be evaluated separately. A RAG system is ready to ship only when
its answers are useful *and* its evidence can be retrieved, inspected, and
quoted.
