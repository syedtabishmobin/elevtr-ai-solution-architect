# ELVTR AI Solution Architect — Assignment 02

## Chunk It, Index It, Prove It

This project implements a small local retrieval evaluation pipeline that compares two document-indexing approaches:

1. Naive fixed-size chunking
2. Title-prefixed contextual chunking

The same documents and questions are used against both indexes to compare retrieval quality.

The entire project runs locally using Ollama and does not require a cloud API key.

---

## What the project does

The pipeline:

1. Reads PDF documents from `docs/`
2. Extracts text using PyPDF
3. Splits the text into fixed-size chunks
4. Generates embeddings locally using Ollama and `nomic-embed-text`
5. Stores embeddings, text, and metadata in ChromaDB
6. Creates two ChromaDB collections:
   - `naive`
   - `titled`
7. Runs the same evaluation questions against both collections
8. Compares:
   - `hit@3`
   - `answerable@3`

The ChromaDB database is generated locally inside `.index/`.

`.index/` is not committed to Git because it can be recreated at any time by running `build.py`.

---

# Architecture

```text
PDF Documents
      |
      v
Text Extraction
   (PyPDF)
      |
      v
Fixed-size Chunking
120 words / 20 overlap
      |
      +----------------------+
      |                      |
      v                      v
Naive chunks          Title-prefixed chunks
      |                      |
      v                      v
       Ollama / nomic-embed-text
                 |
                 v
             Embeddings
                 |
                 v
              ChromaDB
             .index/
          /             \
       naive           titled
          \             /
                 |
                 v
             compare.py
                 |
                 v
        Retrieval evaluation
```

---

# Technologies Used

- Python
- uv
- Ollama
- nomic-embed-text
- LiteLLM
- ChromaDB
- PyPDF
- python-dotenv
- VS Code

---

# Prerequisites

The following software is required.

## 1. VS Code

Download and install Visual Studio Code.

Recommended VS Code extensions:

- Python
- Pylance

---

## 2. Git

Verify Git is installed:

```bash
git --version
```

On macOS, Git may be installed automatically with Apple's Command Line Tools.

If prompted by macOS, install the Command Line Developer Tools.

---

## 3. uv

`uv` is used as the Python project and dependency manager.

Install on macOS:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Restart the terminal and verify:

```bash
uv --version
```

The project currently uses Python 3.11.

If required:

```bash
uv python install 3.11
```

---

## 4. Ollama

Install Ollama from:

https://ollama.com

Start the Ollama application.

Verify installation:

```bash
ollama --version
```

---

# Ollama Embedding Model

The project uses:

```text
nomic-embed-text
```

Download it:

```bash
ollama pull nomic-embed-text
```

Verify that Ollama is running:

```bash
curl http://localhost:11434/api/tags
```

The returned JSON should include:

```text
nomic-embed-text
```

On macOS, the Ollama desktop application normally runs the local server automatically.

If required, run:

```bash
ollama serve
```

---

# Clone the Repository

Clone the repository:

```bash
git clone <repository-url>
```

Move into the project directory:

```bash
cd s02-assignment
```

---

# Python Environment Setup

This project uses `uv`.

The dependencies are defined in:

```text
pyproject.toml
uv.lock
```

Create/recreate the environment using:

```bash
uv sync
```

This creates:

```text
.venv/
```

The `.venv/` folder is intentionally excluded from Git.

Verify Python:

```bash
uv run python --version
```

Expected:

```text
Python 3.11.x
```

Check which Python interpreter is being used:

```bash
uv run python -c "import sys; print(sys.executable)"
```

It should point to the `.venv` inside this project.

---

# Important Note About Moving the Project

If the project directory is moved after `.venv` has already been created, you may see a warning similar to:

```text
VIRTUAL_ENV=... does not match the project environment path `.venv`
```

The cleanest fix is:

```bash
rm -rf .venv
uv sync
```

Then verify:

```bash
uv run python --version
```

---

# Project Dependencies

The main Python packages are:

```text
chromadb
litellm
python-dotenv
pypdf
```

They are managed through `uv`.

If setting up manually:

```bash
uv add chromadb litellm python-dotenv pypdf
```

Normally this is unnecessary after cloning because:

```bash
uv sync
```

installs the required dependencies from the project files.

---

# Source Documents

Place the PDFs inside:

```text
docs/
```

Example:

```text
docs/
├── document1.pdf
├── document2.pdf
└── document3.pdf
```

The PDFs should contain extractable text.

Scanned image-only PDFs may not work because PyPDF does not perform OCR.

---

# Build the Vector Database

Make sure Ollama is running first.

Verify:

```bash
curl http://localhost:11434/api/tags
```

Then build both indexes:

```bash
uv run python build.py
```

This creates the local ChromaDB database:

```text
.index/
```

Two collections are created:

```text
naive
titled
```

The `.index/` directory is generated and therefore excluded from Git.

---

# What `build.py` Does

The script:

```text
docs/*.pdf
    |
    v
PyPDF text extraction
    |
    v
120-word chunks
20-word overlap
    |
    +------------------+
    |                  |
    v                  v
naive              title-prefixed
    |                  |
    v                  v
nomic-embed-text embeddings
    |                  |
    v                  v
ChromaDB collections
```

The `naive` collection stores normal fixed-size chunks.

The `titled` collection adds document-level context before embedding:

```text
From <document title>:

<chunk text>
```

---

# Evaluation Questions

Evaluation questions are stored in:

```text
queries.txt
```

Each line follows:

```text
question :: gold marker
```

Example:

```text
What was the company's total revenue? :: 4.2 billion
```

The gold marker must literally appear in a chunk containing the expected answer.

---

# Run the Evaluation

Run:

```bash
uv run python compare.py
```

The output compares the two collections.

Example:

```text
query                                             naive        titled
----------------------------------------------------------------------
What was the total revenue?                   hit-ambig    ANSWERABLE
Who was the CEO?                             ANSWERABLE    ANSWERABLE
----------------------------------------------------------------------
TOTAL hit@3                                       5/5           5/5
TOTAL answerable@3                                2/5           5/5
```

---

# Evaluation Metrics

## hit@3

A query is a hit if the expected gold marker appears in any of the top three retrieved chunks.

This answers:

```text
Did retrieval find the information?
```

## answerable@3

A result is answerable if:

1. the expected answer appears, and
2. the retrieved chunk contains enough document context to identify its source.

This answers:

```text
Did retrieval return enough context to confidently use the result?
```

---

# Inspect the Vector Database

The generated ChromaDB database can be inspected using:

```bash
uv run python inspect_db.py
```

This can display:

- collection names
- chunk count
- chunk IDs
- source metadata
- stored text
- embedding dimensions
- embedding vector values

The embedding model produces numerical vectors representing the semantic meaning of each chunk.

---

# Compare Embedding Vectors

To inspect differences between naive and titled embeddings:

```bash
uv run python compare_vectors.py
```

Adding document context changes the input to the embedding model, therefore the resulting embedding vector can also change.

---

# Rebuild the Database

The Chroma database is intentionally not committed.

To rebuild it at any time:

```bash
rm -rf .index
uv run python build.py
```

This gives a clean vector index based on the current contents of `docs/`.

---

# Troubleshooting

## `uv: command not found`

Restart the terminal.

If required:

```bash
source ~/.zshrc
```

---

## Ollama connection refused

Start the Ollama desktop application.

Or:

```bash
ollama serve
```

Verify:

```bash
curl http://localhost:11434/api/tags
```

---

## Embedding model not found

Run:

```bash
ollama pull nomic-embed-text
```

---

## Python version problems

Check:

```bash
uv run python --version
```

The project should use Python 3.11.

If required:

```bash
uv python install 3.11
uv python pin 3.11
rm -rf .venv
uv sync
```

---

## Virtual environment path warning after moving the project

If you see:

```text
VIRTUAL_ENV=... does not match the project environment path `.venv`
```

remove and rebuild the environment:

```bash
rm -rf .venv
uv sync
```

If an old environment is active:

```bash
deactivate
```

or, for Conda:

```bash
conda deactivate
```

---

## PDF produces zero chunks

The PDF may be scanned or image-only.

Use a PDF containing real selectable text, or add an OCR/document-processing stage.

---

## All evaluation results are MISS

Check the gold markers in:

```text
queries.txt
```

They must literally appear in the extracted PDF text.

---

# Generated and Ignored Files

The following folders are intentionally not committed:

```text
.venv/
.index/
```

They can both be recreated:

```bash
uv sync
uv run python build.py
```

Secrets are also excluded:

```text
.env
```

Never commit API keys or credentials.

---

# Typical Development Workflow

After cloning:

```bash
uv sync
ollama pull nomic-embed-text
uv run python build.py
uv run python compare.py
```

For future work:

```bash
git status
git add .
git commit -m "Describe the change"
git push
```

---

# Assignment Files

The main project artefacts are:

```text
build.py
compare.py
queries.txt
FINDINGS.md
docs/
pyproject.toml
uv.lock
```

Additional exploration scripts may include:

```text
inspect_db.py
compare_vectors.py
```

---

# Notes

This project intentionally uses local embeddings so that the complete retrieval workflow can run without cloud API keys.

The ChromaDB `.index/` directory is considered generated state. The reproducible source of truth is:

```text
docs/
+
build.py
+
pyproject.toml
+
uv.lock
+
nomic-embed-text
```

Running `build.py` recreates the vector database from these inputs.