# ELVTR AI Solution Architect - Assignment 07

## Talk to Your Docs

This project is my implementation of **Class 7 Assignment #4**. It replaces the
custom local retriever from the previous assignment with an OpenAI hosted
vector store and places that search capability behind one Microsoft Agent
Framework agent.

The agent has two tools:

1. Hosted `file_search` for evidence from the five-document corpus.
2. Local `flag_for_human` for questions the corpus cannot answer.

Every question follows the same `ask()` path. There are no question-specific
answers, expected answers in prompts, or evaluation shortcuts. The project also
adds local and hosted action budgets, a deterministic `Sources:` guardrail, a
per-question exception boundary, and readable success/failure traces.

The observed results and shipping decision are recorded in
[`FINDINGS.md`](FINDINGS.md).

## Results at a glance

| Check | Observed result |
|---|---|
| Hosted corpus | Five real files indexed once in one OpenAI vector store |
| Evaluation dataset | Eight verified cases: 4 direct, 2 multi-file, 1 missing-information, 1 distractor |
| Baseline completion | All eight rows completed |
| Citation guardrail | Seven passed; `q07` correctly failed because its answer omitted `Sources:` |
| Human escalation | `q06` searched, called `flag_for_human`, and did not invent an email address |
| Distractor values | `q07` returned the three correct 2026 values and avoided all three adjacent 2025 values |
| Deliberate tool failure | All eight rows captured the bad-store 404 as `error`; the run continued |
| Action-limit probe | Both `max_iterations` and `max_function_calls` stopped an intentional local-tool loop |
| Shipping decision | Do not ship yet; add evidence-to-citation verification first |

## Project structure

```text
s07-assignment/
├── .env.example
├── .gitattributes
├── .gitignore
├── .python-version
├── README.md
├── FINDINGS.md
├── pyproject.toml
├── uv.lock
├── store.py
├── agent.py
├── safeguards.py
├── safeguard_probe.py
├── evals.py
├── traces.py
├── datasets/
│   └── agent_eval.jsonl
├── docs/
│   ├── apple_annual_report.pdf
│   ├── microsoft_annual_report.pdf
│   ├── tesla_annual_report.pdf
│   ├── equity_research_policy.md
│   └── portfolio_research_faq.md
├── experiments/
│   ├── baseline.csv
│   ├── tool_failure.csv
│   ├── safeguards.txt
│   └── vector_store_build.txt
├── traces/
│   ├── success.txt
│   ├── refusal.txt
│   └── failure.txt
└── tests/
    ├── test_action_limits.py
    ├── test_artifacts.py
    ├── test_dataset.py
    └── test_safeguards.py
```

The local `.env`, `.venv/`, Python caches, hosted vector-store contents, and ZIP
file are excluded from Git. The source documents are included so the project
can create a new hosted store when needed.

## Technology stack

- Python 3.11
- `uv` for environment and lock-file management
- Microsoft Agent Framework 1.15.0
- Microsoft Agent Framework OpenAI integration 1.14.0
- OpenAI Responses API and hosted file search
- `gpt-4o-mini` as `OPENAI_CHAT_MODEL`
- `python-dotenv` 1.2.3 for local environment configuration

## Architecture

```text
docs/ -> store.py -> OpenAI vector store
                         |
question -> ask() -> DocsAgent
                         |
              +----------+----------+
              |                     |
              v                     v
       hosted file_search     flag_for_human
              |                     |
              +----------+----------+
                         |
                  final response
                         |
                  Sources: check
                         |
                 CSV + trace evidence
```

`max_iterations` limits Agent Framework model round trips and
`max_function_calls` limits local function executions. The OpenAI hosted tool
is also given `max_tool_calls=6`, because hosted `search_tool_call` events are
provider-executed and are not counted as local `function_call` events.

## Setup and commands

Create the environment file and set both required values:

```bash
cp .env.example .env
# Set OPENAI_API_KEY and OPENAI_CHAT_MODEL in .env
```

Install the locked environment:

```bash
uv sync
```

Build the hosted vector store once and save its ID to the ignored `.env` file:

```bash
uv run python store.py docs --save-env
```

Use the printed `vector_store_id` for all normal calls:

```bash
uv run python evals.py <vector_store_id> baseline
uv run python traces.py <vector_store_id> q01 traces/success.txt
uv run python traces.py <vector_store_id> q06 traces/refusal.txt
```

Run the deliberate hosted-tool failure without deleting the valid store:

```bash
uv run python evals.py vs_does_not_exist tool_failure
uv run python traces.py vs_does_not_exist q01 traces/failure.txt
```

Exercise the action limits and output guardrail without making an API call:

```bash
uv run python safeguard_probe.py
uv run python -m unittest discover -s tests -v
```

## Evaluation design

The JSONL dataset uses stable `qid` values and only the four permitted
categories. The questions do not contain filenames or page numbers.

- `q01`-`q03` and `q08` are direct lookups.
- `q04` and `q05` require evidence from both process documents.
- `q06` requests a support email that is not in the corpus.
- `q07` targets a financial table with adjacent 2025 values as distractors.

The expected facts were checked directly against the copied source documents
before the live evaluation was run.

## Safeguards and failure behavior

The agent uses three complementary boundaries:

1. Framework action budgets stop a local function loop and request a final
   tool-disabled response.
2. The hosted Responses API receives its own built-in tool-call budget.
3. `has_source_citation()` rejects responses with a missing or empty
   `Sources:` line.

The bad vector-store experiment fails before the model can use either tool.
`evals.py` therefore keeps the exception boundary around each dataset row. This
records all eight 404s instead of losing the run after `q01`.

## Reproducing the submission ZIP

From the repository root, create the archive while excluding local and generated
state:

```bash
zip -r s07-assignment/s07-assignment.zip s07-assignment \
  -x 's07-assignment/.venv/*' \
     's07-assignment/.env' \
     's07-assignment/__pycache__/*' \
     's07-assignment/tests/__pycache__/*' \
     's07-assignment/*.zip'
```
