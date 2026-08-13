# ELVTR AI Solution Architect - Assignment 05

## Keep It Fresh: Building an Idempotent and Fresh RAG Pipeline

This project is my implementation of **Class 5 Assignment #2** for the ELVTR
AI Solution Architect course.

The assignment builds on the retrieval work from S02, but shifts the focus from
retrieval quality to the reliability of the indexing pipeline. The main goal is
to show that a Retrieval-Augmented Generation (RAG) system is also a data
pipeline: it must be safe to run repeatedly, detect changed content, remove
deleted content, and keep the read and write paths on the same embedding
contract.

The project runs locally with Python, `uv`, Ollama, LiteLLM, and ChromaDB. It
uses five source documents, splits them into overlapping chunks, stores their
embeddings in a persistent local index, retrieves relevant context for a
question, and generates a grounded answer with source citations.

The completed measurements, outputs, and explanations are recorded in
[`FINDINGS.md`](FINDINGS.md).

---

## Learning objectives

This assignment demonstrates:

1. Why a RAG write path must be designed as a repeatable data pipeline.
2. How deterministic chunk IDs and `upsert` make indexing idempotent.
3. Why editing a source file does not automatically refresh an existing index.
4. How an upsert-only pipeline can retain chunks from a deleted document.
5. How delta synchronisation identifies new, changed, unchanged, and removed
   chunks.
6. How tombstones remove ghost documents without re-embedding the whole corpus.
7. Why positional chunk IDs can cause a cascade of changes after text is
   inserted near the beginning of a document.
8. Why document and query embeddings must use the same model and preprocessing
   contract.
9. How to compare the time and estimated cost of a full rebuild with a small
   delta update.

---

## Results at a glance

The experiments produced the following results on an Apple M1 Pro:

| Experiment | Result |
|---|---|
| Corpus size | 5 documents and 1,613 chunks |
| Idempotency | Both builds finished with exactly 1,613 chunks |
| Stale source edit | The assistant continued returning the old value until the index was refreshed |
| Full rebuild after one edit | 47.620 seconds with the baseline embedding model |
| Deleted FAQ before tombstoning | 1,610 desired chunks but 1,613 chunks still in Chroma |
| Tombstone sync | Removed 3 chunks and re-embedded 0 |
| Document restoration | Added 3 chunks and re-embedded only those 3 |
| Cascade Edit A | 1 changed chunk and 0 new chunks |
| Cascade Edit B | 2 changed chunks and 0 new chunks |
| Model-contract test | Chroma expected 768 dimensions but received 1,024 |
| Final full re-embed | 1 minute 24.06 seconds with `mxbai-embed-large` |
| Estimated full-index price | $0.00540615 at the assignment comparison rate |
| Estimated Edit A delta price | $0.00000335 at the same rate |

These results show that a small content change should not require the whole
corpus to be embedded again. They also show that deletion and embedding-model
changes need explicit handling; neither problem can be detected reliably by an
upsert-only content pipeline.

---

## Project structure

```text
s05-assignment/
├── .gitignore
├── .python-version
├── README.md
├── FINDINGS.md
├── build.py
├── ask.py
├── sync.py
├── pyproject.toml
├── uv.lock
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
| `build.py` | Reads the source documents, creates chunks and hashes, generates embeddings, and upserts the desired state into ChromaDB |
| `ask.py` | Embeds a question, retrieves the four closest chunks, shows the retrieval trace, and generates a grounded answer with source citations |
| `sync.py` | Compares the desired state on disk with the current index and applies only additions, updates, and deletions |
| `FINDINGS.md` | Contains the measured evidence and written analysis required by the assignment |
| `docs/` | Contains the five-document corpus used for the experiments |
| `pyproject.toml` | Defines the Python project and direct dependencies |
| `uv.lock` | Locks all dependency versions for reproducible installation |
| `.python-version` | Selects Python 3.11 for the project |
| `.gitignore` | Excludes generated indexes, virtual environments, secrets, caches, and submission archives |

The three annual reports reuse the corpus from S02. The two Markdown files are
shareable coursework scenarios that provide safe, editable facts for the stale,
ghost, and cascade experiments.

---

## Technology stack

- **Python 3.11** for the application code
- **uv** for Python version and dependency management
- **Ollama** for local embedding and generation models
- **LiteLLM** as the common interface for local model calls
- **ChromaDB** for the persistent vector index
- **PyPDF** for extracting text from PDF documents
- **python-dotenv** for optional environment-variable loading
- **mxbai-embed-large** as the final embedding model
- **Qwen3:8b** as the local answer-generation model

The assignment starts with `nomic-embed-text` as the 768-dimensional baseline
and later switches to `mxbai-embed-large`, which produces 1,024-dimensional
embeddings. The final committed configuration uses `mxbai-embed-large`.

---

## Architecture

```text
Source of truth: docs/
        |
        v
PDF / Markdown / text extraction
        |
        v
120-word chunks with 20-word overlap
        |
        +-------------------------------+
        |                               |
        v                               v
Deterministic chunk ID           SHA-1 content hash
source::position                 change detection
        |                               |
        +---------------+---------------+
                        |
                        v
                Ollama embeddings
                        |
                        v
              ChromaDB collection
                    .index/
                        |
          +-------------+-------------+
          |                           |
          v                           v
    Read path: ask.py          Delta path: sync.py
 question -> embedding        compare disk and index
 -> top-4 retrieval           -> add changed content
 -> grounded answer           -> update changed content
 -> source citation           -> delete missing content
```

### The write path

`build.py` treats `docs/` as the source of truth. It reads every supported file,
splits the extracted text into fixed-size windows, and creates a desired record
for every chunk.

Each record contains:

- a deterministic ID in the form `source::position`;
- the chunk text;
- the source filename; and
- a shortened SHA-1 hash of the chunk text.

The deterministic ID gives the same chunk the same identity on every unchanged
run. Chroma's `upsert` operation then updates the existing record instead of
adding a duplicate. Together, these choices make repeated builds idempotent.

### The read path

`ask.py` uses the shared `embed()` function imported from `build.py`. It embeds
the user's question, retrieves the four closest chunks, prints their distances
and source filenames, and passes only that retrieved context to Qwen3:8b.

The model is instructed to:

- answer only from the supplied context;
- cite the source filename in square brackets; and
- say that it does not know when the answer is not present.

### The delta-sync path

`sync.py` compares two states:

- **Desired state:** the IDs and content hashes produced from the current files
  in `docs/`.
- **Existing state:** the IDs and hashes already stored in ChromaDB.

It classifies every record as:

- `unchanged` - the ID exists and the content hash still matches;
- `new` - the desired ID does not exist in Chroma;
- `changed` - the ID exists but its content hash differs; or
- `removed` - the ID exists in Chroma but no longer exists on disk.

Only new and changed chunks are embedded. Removed IDs are explicitly deleted,
which acts as the tombstone step and prevents deleted documents from remaining
searchable.

---

## Prerequisites

### 1. Git

Verify that Git is installed:

```bash
git --version
```

### 2. uv

Install `uv` on macOS or Linux if needed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Restart the terminal and verify the installation:

```bash
uv --version
```

### 3. Ollama

Install Ollama from <https://ollama.com> and start the desktop application.
Download the models used by the finished project:

```bash
ollama pull mxbai-embed-large
ollama pull qwen3:8b
```

To reproduce the original model-switching experiment, also download the
baseline model:

```bash
ollama pull nomic-embed-text
```

Verify that Ollama is running and the models are available:

```bash
ollama list
curl http://localhost:11434/api/tags
```

If `qwen3:8b` is too large for the machine, pull `qwen3:1.7b` and change the
`CHAT` constant in `ask.py`. This changes the generation model only; it does not
change the embedding dimensions stored in Chroma.

---

## Installation

Clone the repository and enter the assignment directory:

```bash
git clone https://github.com/syedtabishmobin/elevtr-ai-solution-architect.git
cd elevtr-ai-solution-architect/s05-assignment
```

Create the project environment and install the locked dependencies:

```bash
uv sync
```

All commands in this project use `uv run`, so manually activating `.venv` is not
required.

If the terminal still has another assignment's virtual environment activated,
run:

```bash
deactivate
uv sync
```

This avoids the warning that the active `VIRTUAL_ENV` does not match this
project's `.venv` directory.

---

## Quick start

### 1. Build the local index

```bash
uv run python build.py
```

With the supplied corpus, the final line should report five documents and 1,613
chunks:

```text
indexed 1613 chunks from 5 docs -> 1613 in collection
```

The generated Chroma database is stored in `.index/`. It is intentionally
excluded from Git because it can be rebuilt from the committed source files.

### 2. Ask a grounded question

```bash
uv run python ask.py "What risk score triggers an additional risk review?"
```

The command first shows the retrieved chunks and then prints an answer similar
to:

```text
The risk score that triggers an additional risk review is 70 out of 100
[equity_research_policy.md].
```

More example questions:

```bash
uv run python ask.py "Which companies are covered by the demonstration corpus?"
uv run python ask.py "How many chunks are supplied to the answer model?"
```

Because generation is probabilistic, the wording may vary, but the answer must
remain grounded in the retrieved context and cite the source file.

### 3. Confirm that the index is current

```bash
uv run python sync.py
```

Immediately after a clean build, the output should show no work:

```text
unchanged: 1613
new      : 0
changed  : 0
removed  : 0

re-embedded 0 of 1613 chunks (0.0% of a full reindex)
collection now holds 1613 chunks
```

---

## Assignment experiments

The experiments below intentionally create stale, incomplete, or incompatible
states. They are documented here for reproducibility, but they are not required
for normal use of the completed project. Restore the source files and rebuild
the final index after reproducing them.

### 1. Idempotency

Start with no generated index and run the same build twice:

```bash
rm -rf .index
uv run python build.py
uv run python build.py
```

Both runs should finish with the same collection count. This proves that stable
IDs and `upsert` prevent duplicate records.

### 2. Stale-answer experiment

1. Build the index while the risk threshold in
   `docs/equity_research_policy.md` is `70 out of 100`.
2. Change the source value to `85 out of 100` without running `build.py` or
   `sync.py`.
3. Ask the same question again:

```bash
uv run python ask.py "What risk score triggers an additional risk review?"
```

The assistant continues returning the old indexed value even though the source
file has changed. There is no automatic warning because the read path queries
Chroma rather than inspecting the source files.

The brute-force fix is a full rebuild:

```bash
time sh -c 'rm -rf .index && uv run python build.py'
```

In this experiment, reflecting a one-value edit by rebuilding the whole corpus
took 47.620 seconds with the baseline model.

### 3. Ghost-document experiment

Move the FAQ out of the source folder and run the upsert-only build:

```bash
mv docs/portfolio_research_faq.md portfolio_research_faq.md.saved
uv run python build.py
```

The measured output was:

```text
indexed 1610 chunks from 4 docs -> 1613 in collection
```

The first number describes the state currently visible on disk. The second
number includes three FAQ chunks retained from an earlier run. Upsert can add or
replace the IDs it receives, but it cannot infer that records from an absent
file should be deleted.

Apply the tombstones:

```bash
uv run python sync.py
uv run python ask.py "How many chunks are supplied to the answer model?"
```

The sync removed three chunks without embedding any unchanged content. The
assistant then correctly reported that the answer was not present in the
remaining context.

Restore the source and sync only its returned chunks:

```bash
mv portfolio_research_faq.md.saved docs/portfolio_research_faq.md
uv run python sync.py
```

The restoration added and embedded three chunks while leaving the other 1,610
chunks unchanged.

### 4. Chunk-cascade experiment

Both edits must start from the same saved source and matching index state.

- **Edit A:** changing one word near the end of the policy changed one chunk.
- **Edit B:** inserting a sentence at the beginning changed both chunks in the
  policy.

The IDs use the filename and ordinal chunk position. An insertion near the top
shifts the word windows that follow it, so later positional IDs can keep their
names while receiving different content hashes.

A content-derived ID could allow unchanged text to retain its identity after an
early insertion. The trade-offs are that identical content needs source-aware
namespacing, an edited chunk appears as a delete-plus-add event, and ordering and
citations require separate metadata.

### 5. Embedding-contract experiment

This experiment begins with an index created by the 768-dimensional
`nomic-embed-text` model. Change the `EMBED` constant to:

```python
EMBED = "ollama/mxbai-embed-large"
```

Run delta sync without rebuilding:

```bash
uv run python sync.py
```

It reports that all 1,613 chunks are unchanged because the diff compares source
content hashes, not the embedding model. Querying the old index then raises:

```text
Collection expecting embedding with dimension of 768, got 1024
```

The failure appears on the read path because the new query vector is the first
new embedding generated after the model change. If the two models produced the
same number of dimensions, the mismatch could remain silent and reduce retrieval
quality without raising an error.

A production design should store an embedding-contract version with every
record. That contract should cover the model, vector dimensions, task prefixes,
and preprocessing rules. A contract change should mark the entire corpus for
re-embedding.

Perform the required clean migration with:

```bash
time sh -c 'rm -rf .index && uv run python build.py'
```

---

## Cost comparison

The corpus contained 1,081,230 characters, estimated by the assignment as
270,307.5 tokens using `characters / 4`. At the assignment yardstick of `$0.02`
per one million tokens:

```text
Full index:  270,307.5 / 1,000,000 x $0.02 = $0.00540615
Edit A:      270,307.5 x 1 / 1,613 / 1,000,000 x $0.02 = $0.00000335
```

At 1,000 times the corpus size, the proportional estimates become:

```text
Full index:  $5.40615000
Edit A:      $0.00335161
```

For this corpus, I would update the index whenever an approved source document
changes and run a weekly check to confirm that the index still matches the
source files. I would reserve a full rebuild for embedding-contract migrations
or recovery from a damaged index. This keeps answers current without repeatedly
processing documents that have not changed.

---

## Design limitations and production improvements

This implementation is intentionally small and focused on the assignment. A
production version should consider:

- storing an `embedding_contract` version in chunk metadata;
- using source-aware, content-addressed chunk IDs where appropriate;
- recording document versions and ingestion timestamps;
- using a proper change feed or event queue instead of manual sync commands;
- running scheduled reconciliation to detect missed events;
- making index updates transactional or using versioned collections;
- retaining audit logs for additions, changes, and tombstones;
- adding retrieval evaluation with questions that have known-correct sources;
- adding OCR or rejecting scanned PDFs explicitly; and
- monitoring freshness lag, failed embeddings, document counts, chunk counts,
  and retrieval quality.

---

## Git and generated files

The following paths are intentionally ignored:

```text
.index/       generated ChromaDB index
.venv/       local Python environment
.env         local secrets or provider configuration
__pycache__/ Python bytecode cache
*.zip        local submission archives
.DS_Store    macOS metadata
```

Before committing, inspect the repository state:

```bash
git status --short
git diff --cached
```

The source documents in this repository are shareable coursework inputs. If a
different private corpus is used, do not include it in Git or in the submission
archive; list the document titles in `FINDINGS.md` instead.

---

## Submission

The assignment submission requires one ZIP archive and the completed findings
write-up. The ZIP must contain the source code, dependency files, documentation,
and shareable corpus, but not generated or secret material.

From the repository root, create the archive with:

```bash
zip -r s05-assignment.zip s05-assignment \
  -x 's05-assignment/.index/*' \
     's05-assignment/.venv/*' \
     's05-assignment/.env' \
     's05-assignment/*.zip' \
     's05-assignment/**/__pycache__/*' \
     's05-assignment/**/.DS_Store'
```

Inspect the archive before submitting:

```bash
unzip -l s05-assignment.zip
```

The archive should include:

```text
s05-assignment/
├── pyproject.toml
├── uv.lock
├── build.py
├── ask.py
├── sync.py
├── README.md
├── FINDINGS.md
└── docs/
```

It must not include `.index/`, `.venv/`, `.env`, caches, secrets, or another ZIP
file.

---

## Troubleshooting

| Symptom | Resolution |
|---|---|
| `uv: command not found` | Restart the terminal and check the PATH instructions printed by the `uv` installer. |
| `VIRTUAL_ENV` does not match `.venv` | Run `deactivate`, remain in `s05-assignment`, and run `uv sync` again. |
| Connection refused on port 11434 | Start the Ollama desktop application or run `ollama serve`. |
| Ollama reports that a model was not found | Pull `mxbai-embed-large` and `qwen3:8b`; pull `nomic-embed-text` when reproducing the model-switch experiment. |
| The first build is slow | This is expected because all document chunks are embedded locally and speed depends on the CPU/GPU. |
| `qwen3:8b` does not fit in memory | Pull `qwen3:1.7b` and update `CHAT` in `ask.py`. |
| A PDF produces no chunks | The file is probably image-only; use an extractable PDF, add OCR, or document the limitation. |
| `sync.py` says everything changed | Inspect the source diff for accidental encoding or line-ending changes. |
| `sync.py` reports zero work after a model swap | This is the expected experiment result because the current diff tracks content, not the model contract. |
| Chroma expects 768 dimensions but receives 1,024 | The index was built with `nomic-embed-text` but queried with `mxbai-embed-large`; remove `.index/` and rebuild with the selected model. |

---

## Final verification

Before committing or submitting, run:

```bash
uv sync
uv run python sync.py
uv run python ask.py "What risk score triggers an additional risk review?"
git status --short
```

The sync should report no changes, the question should return a cited answer,
and Git should not list `.index/`, `.venv/`, `.env`, caches, or ZIP archives as
tracked files.
