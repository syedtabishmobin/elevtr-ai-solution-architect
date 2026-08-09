# ELVTR AI Solution Architect - Assignment 02

This repository contains my implementation of the ELVTR AI Solution Architect
retrieval and chunking exercise.

## Objective

The project compares two document indexing approaches:

1. Naive fixed-size chunking
2. Title-prefixed contextual chunking

The same queries are evaluated against both ChromaDB indexes.

## Technology

- Python
- uv
- Ollama
- nomic-embed-text
- LiteLLM
- ChromaDB
- PyPDF

## Project Structure

- `docs/` - source documents
- `build.py` - extracts, chunks, embeds and indexes the documents
- `compare.py` - evaluates retrieval performance
- `queries.txt` - evaluation questions and gold markers
- `FINDINGS.md` - observations from the experiment
- `inspect_db.py` - inspects ChromaDB contents and embeddings
- `compare_vectors.py` - explores generated vectors
- `.index/` - local persisted ChromaDB vector database

## Environment

The project uses Python managed through `uv`.

```bash
uv sync