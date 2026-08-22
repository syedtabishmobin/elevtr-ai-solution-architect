# ELVTR AI Solution Architect - Assignment 07

## Talk to Your Docs

This project is my completed implementation of **Class 7 Assignment #4** for
the ELVTR AI Solution Architect course.

In Class 6, the document pipeline used a custom chunker, embedder, and local
retriever. This assignment deliberately moves that retrieval work into an
OpenAI hosted vector store and focuses on the agent layer instead. A Microsoft
Agent Framework agent searches the documents before every answer, then decides
whether the available evidence is sufficient or it must call a second tool to
request human review.

The goal is not just to produce fluent answers. The goal is to make the agent's
actions visible and to make failures safe. A correct-looking response is marked
as a citation-format failure when the required source line is absent,
unsupported questions must be escalated, tool activity is captured in traces,
and a broken hosted search dependency must not silently turn into a guessed
answer.

The completed experiment analysis and shipping decision are recorded in
[`FINDINGS.md`](FINDINGS.md).

---

## Learning objectives

This assignment demonstrates:

1. How to upload a real document corpus to one reusable OpenAI vector store.
2. How to expose hosted file search as a tool on a Microsoft Agent Framework
   agent.
3. How to provide a second local tool for explicit human escalation.
4. How to route every application and evaluation question through one reusable
   `ask()` function.
5. Why a model must search before answering instead of relying on parametric
   knowledge.
6. How `max_iterations`, `max_function_calls`, and `max_tool_calls` cover
   different parts of an agent's action budget.
7. How a deterministic output guardrail detects missing or empty source
   citations without making another model call.
8. How to build a stable JSONL evaluation set with direct, multi-file,
   missing-information, and distractor cases.
9. How to keep an evaluation run complete when one question raises an API or
   hosted-tool exception.
10. How to capture ACT / OBSERVE / DECIDE traces for hosted and local tools.
11. How to distinguish an agent failure from a harness-level dependency
    failure.
12. How saved evidence supports a concrete ship or no-ship decision.

---

## Results at a glance

The required live and offline experiments were completed on **22 August 2026**.

| Check | Observed result |
|---|---|
| Hosted corpus | Five real files uploaded once to one OpenAI vector store |
| Vector-store reuse | The generated ID was saved locally in the ignored `.env` file and reused |
| Evaluation dataset | Eight verified rows: 4 direct, 2 multi-file, 1 missing-information, 1 distractor |
| Baseline completion | All eight questions produced CSV rows |
| Citation-format guardrail | Seven rows passed; `q07` failed because it omitted the required `Sources:` line |
| Human escalation | `q06` searched, called `flag_for_human`, and did not invent a support address |
| Distractor behavior | `q07` selected all three correct 2026 values and avoided the adjacent 2025 values |
| Deliberate hosted failure | All eight bad-store requests were preserved as `error/error` rows with 404 evidence |
| Success trace | Hosted search query, completed search, and final grounded answer captured |
| Refusal trace | Hosted search plus the real `flag_for_human` call and result captured |
| Failure trace | Full caught bad-vector-store exception captured |
| Action-limit probe | Both framework limits stopped an intentional local-tool loop |
| Automated checks | 14 tests passed in the workspace; the ZIP was separately checked against the exact 10-file submission allowlist |
| Shipping decision | Do not ship yet; add evidence-to-citation matching first |

These results should not be read as a claim of seven-out-of-eight factual
accuracy. The required CSV stores only the first 200 characters of each answer,
and this assignment does not add a separate semantic answer scorer. Seven of
eight baseline rows passed the non-empty `Sources:` **format** check. The saved
rows and traces support the specific observations above; the more detailed
interpretation is in `FINDINGS.md`.

---

## Rubric and evidence map

| Rubric area | Implementation | Saved GitHub evidence |
|---|---|---|
| Real hosted corpus and one reusable agent path | `store.py`, `agent.py`, `ask()` | `experiments/vector_store_build.txt`, `traces/success.txt` |
| Hosted search plus a second escalation tool | `file_search`, `flag_for_human` | `traces/refusal.txt`, baseline `q06` |
| Action limit and output guardrail | Agent budgets, `has_source_citation()`, scripted probe | `experiments/safeguards.txt`, baseline `q07`, 14 tests |
| Eight-to-twelve-row evaluation set and baseline | JSONL dataset and `evals.py` | `datasets/agent_eval.jsonl`, `experiments/baseline.csv` |
| Deliberate tool failure and two required traces | Per-row exception boundary and trace renderer | `experiments/tool_failure.csv`, `traces/success.txt`, `traces/failure.txt` |
| Findings and shipping decision | Seven numbered findings sections | `FINDINGS.md` |

---

## Repository structure

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

The local `.env`, `.venv/`, Python caches, submission ZIP, and hosted
vector-store contents are excluded from Git. The five source files are included
so the project can build a fresh hosted store when another user reproduces the
assignment.

This tree describes the complete GitHub project, not the submission archive.
The assignment handout requests a smaller ZIP containing exactly ten files; the
precise allowlist and packaging command are documented below.

Several entries in the repository, including the detailed `README.md`, tests,
source documents, refusal trace, safeguard probe, and supplemental experiment
evidence, improve reproducibility but are not requested inside the submitted
archive.

### File descriptions

| File | Purpose |
|---|---|
| `store.py` | Creates a fresh vector store named `s07-knowledge-base`, uploads every file under `docs/`, waits for indexing, reports failures, and optionally saves the resulting ID to `.env` |
| `agent.py` | Defines the agent instructions, local escalation tool, action budgets, `DocsAgent`, and the one reusable `ask()` path |
| `safeguards.py` | Implements the deterministic `Sources:` line format check |
| `safeguard_probe.py` | Uses a scripted client to prove that both local action limits and citation-format guardrail cases actually fire |
| `evals.py` | Runs every JSONL question through `ask()`, catches failures per row, and saves the required CSV columns |
| `traces.py` | Converts hosted search and local function events into readable ACT / OBSERVE / DECIDE evidence |
| `datasets/agent_eval.jsonl` | Contains the eight verified evaluation contracts |
| `experiments/vector_store_build.txt` | Records the five filenames uploaded during the real store build without publishing the store ID |
| `experiments/baseline.csv` | Contains all eight rows from the valid hosted-store run |
| `experiments/tool_failure.csv` | Contains all eight rows from the deliberate nonexistent-store run |
| `experiments/safeguards.txt` | Contains the observed action-limit and citation-guardrail probe output |
| `traces/success.txt` | Rendered hosted-tool-event and final-answer trace for the clean `q01` answer |
| `traces/refusal.txt` | Additional proof that `q06` invoked `flag_for_human`, not merely refusal wording |
| `traces/failure.txt` | Full caught exception from the broken hosted-tool case |
| `FINDINGS.md` | Answers all seven assignment questions using actual `qid` values and observed results |
| `tests/test_action_limits.py` | Verifies `max_iterations` and `max_function_calls` independently |
| `tests/test_artifacts.py` | Verifies row counts, saved statuses, traces, upload manifest, 404 evidence, and the absence of findings placeholders |
| `tests/test_dataset.py` | Verifies schema, unique IDs, row count, allowed values, natural question wording, and category mix |
| `tests/test_safeguards.py` | Verifies non-empty-source, handled-refusal, missing-source, and empty-source guardrail cases |
| `pyproject.toml` | Declares the project, Python requirement, and direct dependency pins |
| `uv.lock` | Locks the complete transitive dependency graph |
| `.env.example` | Documents the three environment settings without containing a real secret or store ID |
| `.gitignore` | Excludes secrets, environments, caches, platform files, and ZIP archives |
| `.gitattributes` | Keeps text line endings consistent and treats the reused PDFs as binary files in Git |

---

## Document corpus

The corpus is copied from the previous S06 assignment. It combines three
company filings with two controlled Markdown documents that contain clear
policy and assistant-behavior facts.

| Document | Role in this assignment | Representative facts used |
|---|---|---|
| `apple_annual_report.pdf` | Dense financial-table source; despite the inherited filename, the relevant file is Apple's Q3 2026 Form 10-Q | June 27, 2026 product, services, and total net-sales values plus adjacent 2025 distractors |
| `microsoft_annual_report.pdf` | Microsoft FY2025 Form 10-K and additional real filing material | Contains unrelated contact addresses that must not be treated as the portfolio assistant's support address |
| `tesla_annual_report.pdf` | Tesla FY2025 Form 10-K and additional real filing material | Expands the hosted corpus beyond the controlled notes |
| `equity_research_policy.md` | Controlled policy source | Risk threshold, announcement review timing, escalation record, review cadence, and retention rules |
| `portfolio_research_faq.md` | Controlled assistant-behavior source | S06 baseline embedding-model fact, four-closest-chunks fact, general-knowledge prohibition, and deletion behavior |

The `nomic-embed-text` / Ollama and four-closest-chunks statements in the FAQ
are **facts inside the reused corpus** tested by `q03` and `q08`. They do not
describe the S07 runtime. S07 uses OpenAI hosted file search.

The upload manifest records all five files. No custom chunker, embedder, local
vector index, or second retrieval implementation is used in this project.
OpenAI's hosted file-search service handles server-side parsing, chunking,
embedding, and indexing.

The eight-question dataset directly targets the policy, FAQ, and Apple filing.
Microsoft and Tesla were indexed as part of the real corpus, but no positive
expected answer requires either filing. This is not a claim of full five-file
evaluation coverage.

---

## Technology stack

- **Python 3.11** from `.python-version`
- **uv 0.12.1** during the completed run for environment and lock management
- **Microsoft Agent Framework 1.15.0** as the main agent package
- **Microsoft Agent Framework OpenAI integration 1.14.0** from the lockfile
- **OpenAI Python SDK 2.54.0** from the lockfile
- **OpenAI Responses API** for model and hosted-tool execution
- **OpenAI hosted file search** over one vector store
- **gpt-4o-mini** as the configured `OPENAI_CHAT_MODEL`
- **python-dotenv 1.2.3** for local configuration
- **Python `unittest`** for the 14 offline validation checks

The version difference between `agent-framework` 1.15.0 and its OpenAI
integration 1.14.0 is expected in the resolved dependency set. The lockfile
records the tested combination.

---

## Architecture

```text
                         ONE-TIME HOSTED SETUP

   docs/ ------------------------------------------------------+
      |                                                        |
      v                                                        |
   store.py                                                    |
      |                                                        |
      +--> create s07-knowledge-base vector store              |
      +--> upload each real file with purpose=user_data        |
      +--> create_and_poll until each file is indexed          |
      +--> save OPENAI_VECTOR_STORE_ID in ignored .env         |
                                                               |
                                                               v
                                                      OpenAI vector store
                                                               |
                                                               |
                            RUNTIME AGENT PATH                 |
                                                               |
   user/eval question                                          |
      |                                                        |
      v                                                        |
   ask(agent, question)                                        |
      |                                                        |
      v                                                        |
   DocsAgent -------------------> hosted file_search -----------+
      |                              |
      |                              v
      |                         search result/status
      |                              |
      +---- sufficient evidence <---+
      |             |
      |             +--> grounded final answer + Sources line
      |
      +---- insufficient evidence
                    |
                    +--> local flag_for_human
                              |
                              +--> refusal + flagged Sources line

                            EVALUATION HARNESS

   datasets/agent_eval.jsonl
      |
      v
   evals.py --> ask() --> citation check --> experiments/<name>.csv
      |
      +--> per-row try/except preserves later cases after an error

   traces.py --> response.messages --> ACT / OBSERVE / DECIDE files

   safeguard_probe.py --> scripted local loop --> action-limit evidence
```

### 1. Hosted indexing path

`store.py` performs the one-time hosted setup:

1. It verifies that the requested document directory exists.
2. It recursively discovers and sorts all real files.
3. It refuses to build an empty store.
4. It creates a fresh vector store named exactly
   `s07-knowledge-base`.
5. It uploads each source with OpenAI file purpose `user_data`.
6. It attaches each uploaded file with
   `vector_stores.files.create_and_poll(...)`.
7. It raises a `RuntimeError` containing the filename and indexing error if
   OpenAI reports `last_error`.
8. It returns `(vector_store_id, uploaded_filenames)`.
9. With `--save-env`, it writes `OPENAI_VECTOR_STORE_ID` to the local ignored
   `.env` file.

The completed run uploaded exactly five files. The public manifest records the
count and names, while the actual hosted resource ID remains local.

`store.py` creates a **new remote vector store every time it runs**. That can
incur hosted storage/API usage. Build once for an experiment and reuse the
saved ID instead of rebuilding before every question.

### 2. Runtime agent path

`agent.py` exposes:

```python
async def ask(agent: Agent, question: str) -> dict[str, Any]:
    ...
```

Every baseline question and trace uses this same function. It returns:

```python
{
    "response": "the final response text",
    "flagged": True or False,
    "messages": response.messages,
}
```

The expected answer, category, notes, and expected behavior are never passed to
the agent. `ask()` receives only the natural question. The `flagged` value is
based on an actual `function_call` named `flag_for_human`; refusal-style wording
alone does not count.

### 3. Agent instructions

The instructions establish a general decision contract rather than
question-specific rules:

- always search the knowledge base before answering;
- answer from the retrieved evidence;
- invoke `flag_for_human` exactly once when the search does not contain the
  answer;
- do not imitate an escalation without making the tool call;
- end a grounded answer with `Sources: <actual filenames>`; and
- end a handled refusal with
  `Sources: none (flagged for human review)`.

The stricter escalation wording matters. It makes the tool invocation itself
observable and prevents a fluent refusal from being mistaken for proof that the
second tool was used.

### 4. The two tools

| Tool | Execution location | Purpose | Observable content types |
|---|---|---|---|
| `file_search` | OpenAI hosted Responses API | Find evidence in the one configured vector store | `search_tool_call`, `search_tool_result` |
| `flag_for_human` | Local Python process through Agent Framework | Explicitly escalate an unsupported question instead of guessing | `function_call`, `function_result` |

Hosted file search is provider-executed. The saved trace exposes the search
queries and completion status, but it does not preserve the raw retrieved
passages. A completed search event proves that search ran; it does not by itself
prove which passage supported the final statement.

### 5. Evaluation path

`evals.py`:

1. loads all non-empty JSONL rows;
2. builds one agent for the supplied vector-store ID;
3. sends each natural question through `ask()`;
4. evaluates the full returned text with `has_source_citation()`;
5. stores only the first 200 characters of the response as required;
6. catches exceptions around each individual question;
7. writes one row with the exact required columns; and
8. reopens the finished CSV and verifies that its row count equals the dataset
   row count.

The guardrail and `flagged` values are calculated from the full response before
the response preview is truncated. This explains why a 200-character preview
may omit the terminal source line while the guardrail still records `pass`.

When execution reaches final validation, the row-count check detects a mismatch
instead of reporting that output as complete. An abrupt process interruption
can still leave a partial CSV before this validation is reached.

### 6. Failure path

A nonexistent vector-store ID causes the OpenAI Responses request to fail with
a 404 before the model can recover through another tool. That is a
harness-level dependency failure, not a reasoning problem the agent can solve.

The evaluator therefore records:

```text
flagged=error
guardrail=error
response=ChatClientException: ... Error code: 404 ...
```

and continues to the next row. The completed failure CSV contains all eight
rows. This is containment by the harness, not successful recovery by the
agent.

---

## Safeguards

The project uses several separate boundaries because no single limit covers
every failure mode.

### Framework action limits

The client is configured with:

```python
client.function_invocation_configuration["max_iterations"] = 6
client.function_invocation_configuration["max_function_calls"] = 6
```

| Setting | What it limits | What it does not directly count |
|---|---|---|
| `max_iterations` | Agent Framework model round trips in the local function-invocation loop | It is not a semantic answer-quality check |
| `max_function_calls` | Locally executed function calls such as `flag_for_human` | Provider-hosted `search_tool_call` events |

When a local limit is exhausted, Agent Framework disables tools for the final
turn. The deterministic probe observed the exact fallback:

```text
Function invocation limit reached before a final answer could be produced.
```

Both probe cases produced two scripted model turns, one tool execution, and a
final `tool_choice` of `none`.

The probe uses a deterministic scripted client and local loop. It proves the
framework behavior without spending API tokens. It does not claim to reproduce
a live hosted-search runaway.

### Hosted tool-call limit

The agent also passes:

```python
default_options={"max_tool_calls": 6}
```

This is the provider-side budget for hosted tools such as OpenAI file search.
It complements rather than replaces the two framework settings. The setting is
configured in the real agent, but the completed evidence does not claim that a
live baseline question exhausted this hosted budget.

### Deterministic citation-format guardrail

`has_source_citation()` uses a line-anchored, case-insensitive check for:

```text
Sources: <non-empty value>
```

It returns one of these shapes:

```python
{"value": "pass", "reason": "equity_research_policy.md"}
{"value": "fail", "reason": "no Sources: line found"}
{"value": "fail", "reason": "Sources: line was empty"}
```

This is intentionally deterministic. It does not spend tokens on another model
call and cannot be persuaded by confident wording.

Its scope is also intentionally limited. It detects whether a non-empty source
line exists, but it does not:

- withhold the answer by itself;
- enforce that `Sources:` is the final line;
- validate a filename;
- prove that a cited passage supports the answer;
- require two filenames for a multi-file case; or
- correlate the citation with the hosted search result.

`evals.py` records the `pass` or `fail` signal alongside the answer preview. A
production delivery layer would still need to withhold or route a failed
answer. `q07` demonstrates why the signal is useful; the shipping decision
identifies evidence-to-citation matching as the next safeguard.

### Per-question exception boundary

The required `try/except` in `evals.py` is a separate operational safeguard. It
does not repair a failed hosted tool, but it preserves the rest of the run. In
the deliberate failure experiment, this boundary captured eight independent
404 rows instead of losing `q02` through `q08` after the first exception.

Neither the framework limit nor citation check caught this specific 404. The
request failed before a usable response existed. No answer was generated, so
there was no silent hallucinated recovery.

---

## Trace and observability design

`traces.py` walks `response.messages` and recognizes both provider-hosted and
local content types.

| Event | Trace label | Example |
|---|---|---|
| Hosted search request | `ACT` | `file_search(queries=[...])` |
| Hosted search completion | `OBSERVE` | `file_search search completed` |
| Local escalation call | `ACT` | `flag_for_human({'reason': ...})` |
| Local escalation result | `OBSERVE` | `flag_for_human returned Flagged for human review: ...` |
| Final answer | `DECIDE` | Answer text plus the required source line |
| Caught dependency exception | `ERROR` | `ChatClientException` with the 404 details |

Current Agent Framework `function_result` content does not repeat the function
name. The renderer therefore remembers the earlier `function_call` name by
`call_id` and uses that mapping when it prints the result. Without this mapping,
the refusal trace would incorrectly display an unnamed function result.

### Saved success trace

`traces/success.txt` proves that `q01` did not jump directly to a remembered
answer:

```text
ACT      -> file_search(...)
OBSERVE  -> file_search search completed
DECIDE   -> ... 70 out of 100 ...
Sources: equity_research_policy.md
```

### Saved refusal trace

`traces/refusal.txt` provides stronger evidence than the CSV boolean alone:

```text
ACT      -> file_search(...)
OBSERVE  -> file_search search completed
ACT      -> flag_for_human(...)
OBSERVE  -> flag_for_human returned ...
DECIDE   -> ... flagged this for human review ...
Sources: none (flagged for human review)
```

### Saved failure trace

`traces/failure.txt` contains the expected caught exception for
`vs_does_not_exist`. There is no final model answer, so there is no opportunity
for a hallucinated recovery.

---

## Evaluation dataset

`datasets/agent_eval.jsonl` contains exactly eight JSON objects, one per line.
The required category mix adds up to seven, while the assignment requires eight
to twelve rows, so this implementation includes a fourth direct lookup as the
eighth valid case.

### Dataset schema

| Field | Meaning |
|---|---|
| `qid` | Stable identifier used across saved runs and findings |
| `category` | `direct_lookup`, `multi_file`, `missing_information`, or `distractor` |
| `question` | Realistic user wording with no filename or page-number hints |
| `expected_behavior` | `answer_with_sources` or `flag_for_human` |
| `notes` | Human verification contract describing what a grader should inspect |

### Required mix and cases

| QID | Category | Expected behavior | What the case tests |
|---|---|---|---|
| `q01` | `direct_lookup` | `answer_with_sources` | Exact risk threshold of 70 out of 100 |
| `q02` | `direct_lookup` | `answer_with_sources` | Two-business-day announcement review timing rather than the 90-day portfolio cadence |
| `q03` | `direct_lookup` | `answer_with_sources` | Corpus fact: `nomic-embed-text` running locally through Ollama in the S06 demonstration |
| `q04` | `multi_file` | `answer_with_sources` | Escalation record requirements plus the prohibition on filling gaps from general knowledge; the expected contract cites both `equity_research_policy.md` and `portfolio_research_faq.md` |
| `q05` | `multi_file` | `answer_with_sources` | Approved replacement retention plus deletion from the retrieval index; the expected contract cites both `equity_research_policy.md` and `portfolio_research_faq.md` |
| `q06` | `missing_information` | `flag_for_human` | Missing portfolio-assistant support email; unrelated corporate contacts must not be reused |
| `q07` | `distractor` | `answer_with_sources` | Expected contract: 2026 product, services, and total net sales of `$78,678`, `$30,739`, and `$109,417` million, beside three plausible 2025 values |
| `q08` | `direct_lookup` | `answer_with_sources` | Corpus fact: four **closest** chunks in the earlier demonstration |

### Expectation verification

The expectations were checked against the real source files before the live
run. Important traps include:

- `q01`: do not replace the risk score with a timing value;
- `q02`: do not answer with the separate 90-day portfolio cadence;
- `q04`: do not omit evidence, source file, or decision date, and do not allow
  general knowledge;
- `q05`: do not leave approved superseded notes active or leave deleted sources
  indexed;
- `q06`: do not repurpose an unrelated company-report email address;
- `q07`: do not use `$66,613`, `$27,423`, and `$94,036` million from the
  adjacent 2025 column; and
- `q08`: do not reduce the answer to merely "four chunks" without the word
  "closest".

---

## Understanding the CSV output

Both experiment files use these exact columns:

| Column | Meaning |
|---|---|
| `qid` | Stable dataset identifier |
| `category` | Dataset category copied into the result |
| `expected_behavior` | Expected routing behavior copied into the result |
| `flagged` | `True` only when the message history contains a real `flag_for_human` function call; `False` otherwise; `error` when the request raised |
| `guardrail` | `pass`, `fail`, or `error` from the citation check / exception path |
| `response` | First 200 characters of the answer or caught exception, as required by the assignment |

The 200-character limit means some final `Sources:` lines are not visible in the
CSV preview even when the guardrail value is `pass`. Full behavior should be
interpreted together with the saved traces, especially for `q06`.

### Observed baseline cases

| QID | Flagged | Guardrail | Evidence-backed observation |
|---|---:|---:|---|
| `q01` | `False` | `pass` | Returned 70 out of 100 and cited `equity_research_policy.md`; clean trace saved |
| `q02` | `False` | `pass` | Returned two business days and the CSV contains the policy citation |
| `q03` | `False` | `pass` | Returned the S06 `nomic-embed-text` / Ollama corpus fact and cited the FAQ |
| `q04` | `False` | `pass` | Answered rather than escalating; the required 200-character CSV preview is truncated |
| `q05` | `False` | `pass` | Answered rather than escalating; the required 200-character CSV preview is truncated |
| `q06` | `True` | `pass` | Did not invent a support address; real escalation call and result are visible in the refusal trace |
| `q07` | `False` | `fail` | Returned all three correct 2026 values but omitted the `Sources:` line |
| `q08` | `False` | `pass` | Returned the four-closest-chunks corpus fact; the 200-character preview is truncated |

The clean pass chosen for the assignment findings is `q01`. The distractor
finding is deliberately not described as a complete pass: the values were
correct, but the missing source line caused the guardrail to fail.

The stored preview cannot fully audit the complete content or citation list for
`q04`, `q05`, or `q08`. No claim beyond the saved evidence is made here.

### Observed tool-failure run

The command using `vs_does_not_exist` produced:

- eight output rows for eight input rows;
- `flagged=error` in every row;
- `guardrail=error` in every row;
- a captured OpenAI 404 in every response preview; and
- no generated answer that could hide the dependency failure.

Neither the action limit nor citation regex caught this specific break. The API
request failed before either one could act. The per-row exception boundary was
the safeguard that preserved the complete run.

### Observed safeguard probe

The offline probe produced:

| Probe | Model turns | Tool executions | Final tool choice | Result |
|---|---:|---:|---|---|
| `max_iterations=1` | 2 | 1 | `none` | Limit fallback returned |
| `max_function_calls=1` | 2 | 1 | `none` | Limit fallback returned |
| Missing `Sources:` line | n/a | n/a | n/a | `fail` |
| Empty `Sources:` line | n/a | n/a | n/a | `fail` |
| Non-empty source-line format | n/a | n/a | n/a | `pass` |

This separate probe avoids pretending that a hosted 404 demonstrates a local
action limit. Each safeguard is exercised against the failure type it can
actually detect.

---

## Prerequisites

### 1. Git

Verify Git is available:

```bash
git --version
```

### 2. Python and uv

The project requires Python 3.11 or newer. The pinned `.python-version` is
`3.11`.

Verify `uv`:

```bash
uv --version
```

If `uv` is not installed, follow the official installation method for the
current operating system, restart the terminal, and verify the command before
continuing.

### 3. OpenAI API access

A valid OpenAI API key is required for:

- creating the hosted vector store;
- uploading and indexing the five source files;
- running the baseline agent;
- capturing live success and refusal traces; and
- reproducing the deliberate bad-store API response.

The configured account must have access to the selected chat model and hosted
file-search/vector-store features. Live runs can incur API and hosted-storage
usage and are subject to the account's rate limits.

### 4. Required environment values

`OpenAIChatClient()` needs both the key and model configuration. This project
uses:

```text
OPENAI_API_KEY=<your real key>
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_VECTOR_STORE_ID=<saved after store.py runs>
```

`OPENAI_VECTOR_STORE_ID` is added automatically when `store.py` is run with
`--save-env`. Evaluation and trace scripts still require the ID as a positional
argument; they do not silently read it as their CLI argument.

---

## Installation

Clone the repository and enter the assignment folder:

```bash
git clone https://github.com/syedtabishmobin/elevtr-ai-solution-architect.git
cd elevtr-ai-solution-architect/s07-assignment
```

Install the exact locked environment:

```bash
uv sync --locked
```

Manual virtual-environment activation is not required because the documented
commands use `uv run`.

Create the local environment file:

```bash
cp .env.example .env
```

Edit `.env` and replace only the example API-key value. Keep the configured
model unless another supported model is intentionally being evaluated:

```text
OPENAI_API_KEY=your_real_key_here
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_VECTOR_STORE_ID=replace_after_running_store_py
```

The `.env` file is ignored. Never commit, upload, print, or add it to the ZIP.

---

## Quick start

Run all commands in this section from `s07-assignment/` because the application
uses working-directory-relative paths for `docs/`, `datasets/`, `experiments/`,
and `traces/`.

### 1. Install and verify dependencies

```bash
uv sync --locked
uv run python -c "from agent_framework import Agent; from agent_framework.openai import OpenAIChatClient; print('imports ok')"
```

### 2. Create the hosted vector store once

```bash
uv run python store.py docs --save-env
```

Expected output shape:

```text
vector_store_id=vs_...
uploaded_files=5
- apple_annual_report.pdf
- equity_research_policy.md
- microsoft_annual_report.pdf
- portfolio_research_faq.md
- tesla_annual_report.pdf
Saved OPENAI_VECTOR_STORE_ID to .env
```

Do not rerun this command before every question. It creates a fresh hosted
store. Reuse the saved ID for the normal evaluation and trace commands.

### 3. Read the saved store ID without printing the API key

```bash
uv run python -c "from dotenv import dotenv_values; print(dotenv_values('.env')['OPENAI_VECTOR_STORE_ID'])"
```

Copy the printed ID into the commands below, or load it into a shell variable:

```bash
VECTOR_STORE_ID="$(uv run python -c "from dotenv import dotenv_values; print(dotenv_values('.env')['OPENAI_VECTOR_STORE_ID'])")"
```

### 4. Run the baseline

```bash
uv run python evals.py "$VECTOR_STORE_ID" baseline
```

Expected completion message:

```text
Wrote experiments/baseline.csv (8 rows)
```

Running the same named experiment again overwrites that named CSV.

### 5. Inspect the baseline

```bash
sed -n '1,240p' experiments/baseline.csv
```

Check at least:

- `q01` for a grounded direct lookup;
- `q06` for `flagged=True` and a passing source line;
- `q07` for the correct numbers plus the observed guardrail failure; and
- a total of eight rows.

### 6. Run the deliberate hosted-tool failure

```bash
uv run python evals.py vs_does_not_exist tool_failure
```

Expected completion message:

```text
Wrote experiments/tool_failure.csv (8 rows)
```

This method is safer than deleting the valid hosted store and produces the
required 404 evidence.

### 7. Capture the required traces

```bash
uv run python traces.py "$VECTOR_STORE_ID" q01 traces/success.txt
uv run python traces.py vs_does_not_exist q01 traces/failure.txt
```

The project also captures the refusal path explicitly:

```bash
uv run python traces.py "$VECTOR_STORE_ID" q06 traces/refusal.txt
```

Each command overwrites the supplied trace path.

### 8. Exercise the safeguards offline

```bash
uv run python safeguard_probe.py
```

This updates `experiments/safeguards.txt` without using the OpenAI API.

### 9. Run all automated checks

```bash
uv run python -m unittest discover -s tests -v
```

Expected summary:

```text
Ran 14 tests

OK
```

---

## Test suite

The tests are intentionally offline. They validate the harness and saved
artifacts without rebuilding the hosted store or spending API tokens.

| Test group | Checks | Coverage |
|---|---:|---|
| Action-limit tests | 2 | Independent `max_iterations` and `max_function_calls` exhaustion |
| Saved-artifact tests | 5 | Baseline alignment, 404 preservation, trace evidence, upload manifest, and findings placeholders |
| Dataset tests | 3 | Row count/IDs, field/value contract, and required category mix |
| Citation-guardrail tests | 4 | Non-empty source-line pass, handled-refusal pass, missing-line fail, and empty-line fail |
| **Total** | **14** | Complete offline validation suite |

These tests do not verify that the remote vector store still exists, make live
model calls, or provide a semantic score for every baseline answer. The tests
are intentionally retained in GitHub but excluded from the submission ZIP
because they are not part of the handout's exact `SUBMIT` tree. The minimal ZIP
is validated separately by checking its exact entry allowlist, comparing every
archived file with its repository source, and compiling the four included
Python files for syntax after extraction.

---

## Troubleshooting

### `SettingNotFoundError` for the chat model

Cause: `OPENAI_CHAT_MODEL` is missing or the `.env` file was not loaded from the
assignment directory.

Check only the key names, not secret values:

```bash
awk -F= '/^[A-Za-z_][A-Za-z0-9_]*=/{print $1}' .env
```

The output should include:

```text
OPENAI_API_KEY
OPENAI_CHAT_MODEL
OPENAI_VECTOR_STORE_ID
```

### Authentication or permission error

Confirm that `OPENAI_API_KEY` is a current key for an account with access to the
configured model and vector-store/file-search APIs. Do not paste the key into an
issue, trace, CSV, README, or terminal transcript intended for submission.

### `RateLimitError` or HTTP 429

The evaluator catches exceptions per question, so later rows should still be
written. Wait for the account limit window, reduce concurrent external use, and
rerun the named experiment. A rerun overwrites only the corresponding CSV.

### Bad vector-store 404 during a normal run

Confirm that the ID came from the successful `store.py` output and that it was
copied without extra whitespace. The deliberate string
`vs_does_not_exist` belongs only in the failure experiment.

If the hosted store was deleted, run `store.py docs --save-env` once to create a
new one and use the new ID.

### Missing or empty document directory

Run commands from `s07-assignment/` and confirm that `docs/` contains the five
expected files. `store.py` raises a clear error for a missing directory or a
directory with no files.

### `flagged=False` for a missing-information answer

`ask()` requires an actual `function_call` named `flag_for_human`. A model that
merely writes "flagged for human review" does not satisfy this evidence check.
Inspect a refusal trace and confirm that it includes both:

```text
ACT      -> flag_for_human(...)
OBSERVE  -> flag_for_human returned ...
```

### `guardrail=fail` on an otherwise correct answer

Inspect the end of the full response or capture a trace. The agent must include
a non-empty `Sources:` line. `q07` is the observed example: its numbers were
correct, but the missing line caused the deterministic format check to fail.

Remember that the current evaluator records the failure; it does not itself
remove the answer from the CSV.

### Baseline CSV does not show the full source line

This is expected for longer answers. The assignment requires the response
column to be truncated to 200 characters. The `flagged` and guardrail values
were calculated before truncation. Use the saved traces for the available
message-level evidence; do not treat the preview as a complete transcript.

### Trace shows only a final answer

The renderer must handle `search_tool_call` and `search_tool_result`, not only
local `function_call` and `function_result` contents. The included `traces.py`
handles all four types.

### Vector-store upload fails for one document

`store.py` raises a filename-specific `RuntimeError` when OpenAI returns
`last_error`. Check that the file is readable and supported, then create a fresh
store after correcting the source. Do not use a partially indexed store as the
baseline.

### Fewer output rows than dataset rows

The evaluator reopens the CSV and raises if its row count does not match the
dataset. Check for an interrupted process or filesystem error. Model and API
exceptions inside an individual case should be captured as a row rather than
terminating the run.

### Import or environment mismatch

Recreate the locked environment:

```bash
uv sync --locked
```

Then verify the important installed versions:

```bash
uv run python -c "import importlib.metadata as m; print(m.version('agent-framework')); print(m.version('agent-framework-openai')); print(m.version('openai'))"
```

The completed lock resolves `1.15.0`, `1.14.0`, and `2.54.0` respectively.

---

## Security and repository hygiene

- `.env` contains the real API key and vector-store ID and is ignored.
- `.env.example` contains documentation values only.
- `.venv/` is local and ignored.
- Python caches are ignored.
- ZIP files are ignored so a regenerated submission archive is not accidentally
  committed.
- The hosted vector-store contents are not copied into the repository.
- The public upload manifest lists filenames and count but not the live store
  ID.
- The failure experiment uses a nonsense ID instead of deleting the valid
  hosted resource.
- Evaluation prompts contain only the natural questions; expected answers and
  notes remain on the harness side.

---

## Reproducing the complete assignment

From a clean clone:

```bash
cd s07-assignment
cp .env.example .env
# Add a real OPENAI_API_KEY and keep/set OPENAI_CHAT_MODEL.
uv sync --locked
uv run python store.py docs --save-env
VECTOR_STORE_ID="$(uv run python -c "from dotenv import dotenv_values; print(dotenv_values('.env')['OPENAI_VECTOR_STORE_ID'])")"
uv run python evals.py "$VECTOR_STORE_ID" baseline
uv run python evals.py vs_does_not_exist tool_failure
uv run python traces.py "$VECTOR_STORE_ID" q01 traces/success.txt
uv run python traces.py "$VECTOR_STORE_ID" q06 traces/refusal.txt
uv run python traces.py vs_does_not_exist q01 traces/failure.txt
uv run python safeguard_probe.py
uv run python -m unittest discover -s tests -v
```

Live model wording can vary between runs. Reproduction should compare required
behaviors, tool events, qid coverage, factual traps, guardrail states, and error
handling rather than expecting byte-identical answer prose.

---

## Submission archive

The PDF handout specifies an exact ten-file submission tree. Create the ZIP
from the repository root by naming only those files, while preserving the
required `s07-assignment/` wrapper:

```bash
rm -f s07-assignment/s07-assignment.zip
zip s07-assignment/s07-assignment.zip \
  s07-assignment/store.py \
  s07-assignment/agent.py \
  s07-assignment/safeguards.py \
  s07-assignment/evals.py \
  s07-assignment/datasets/agent_eval.jsonl \
  s07-assignment/experiments/baseline.csv \
  s07-assignment/experiments/tool_failure.csv \
  s07-assignment/traces/success.txt \
  s07-assignment/traces/failure.txt \
  s07-assignment/FINDINGS.md
```

Validate compressed-file integrity:

```bash
unzip -t s07-assignment/s07-assignment.zip
```

Inspect the final paths:

```bash
unzip -Z1 s07-assignment/s07-assignment.zip
```

Then enforce the exact allowlist rather than checking only the entry count:

```bash
python3 -c "import zipfile; expected={'s07-assignment/store.py','s07-assignment/agent.py','s07-assignment/safeguards.py','s07-assignment/evals.py','s07-assignment/datasets/agent_eval.jsonl','s07-assignment/experiments/baseline.csv','s07-assignment/experiments/tool_failure.csv','s07-assignment/traces/success.txt','s07-assignment/traces/failure.txt','s07-assignment/FINDINGS.md'}; actual=set(zipfile.ZipFile('s07-assignment/s07-assignment.zip').namelist()); assert actual == expected, {'missing': sorted(expected-actual), 'extra': sorted(actual-expected)}; print('exact 10-file allowlist: OK')"
```

Calculate a checksum for handoff:

```bash
shasum -a 256 s07-assignment/s07-assignment.zip
```

The archive must contain exactly these ten file entries:

```text
s07-assignment/store.py
s07-assignment/agent.py
s07-assignment/safeguards.py
s07-assignment/evals.py
s07-assignment/datasets/agent_eval.jsonl
s07-assignment/experiments/baseline.csv
s07-assignment/experiments/tool_failure.csv
s07-assignment/traces/success.txt
s07-assignment/traces/failure.txt
s07-assignment/FINDINGS.md
```

It must not contain any other file. In particular, the detailed README,
documents, tests, local environment, project configuration, dependency lock,
extra refusal trace, safeguard probe, and supporting experiment files remain in
GitHub but are deliberately excluded from the assignment ZIP. The PDF does not
request `README.md` in the ZIP; it remains available in the repository:

```text
s07-assignment/README.md
s07-assignment/docs/
s07-assignment/tests/
s07-assignment/pyproject.toml
s07-assignment/uv.lock
s07-assignment/.env.example
s07-assignment/.gitignore
s07-assignment/.gitattributes
s07-assignment/.python-version
s07-assignment/safeguard_probe.py
s07-assignment/traces.py
s07-assignment/experiments/safeguards.txt
s07-assignment/experiments/vector_store_build.txt
s07-assignment/traces/refusal.txt
s07-assignment/.env
s07-assignment/.venv/
__pycache__/
*.pyc
another ZIP file
```

---

## Limitations and next safeguard

This assignment proves that the agent can search, answer, escalate, expose
traces, and fail visibly. It does not yet prove that every cited filename
actually supplied the fact used in the final answer.

Current evidence limitations are:

- responses in the required CSV are truncated to 200 characters;
- there is no automated semantic correctness score for every answer;
- the syntax-only guardrail cannot verify citation truth;
- the saved hosted traces do not preserve raw retrieved passages;
- multi-file citation completeness is not automatically enforced;
- the local action-limit probe is scripted rather than a live hosted runaway;
- `max_tool_calls=6` is configured but was not observed exhausting during the
  baseline;
- Microsoft and Tesla are indexed but not targeted by a positive expected
  answer; and
- offline tests cannot prove that the remote hosted store remains available.

The most important next safeguard is an evidence-to-citation verifier that:

1. obtains the filenames returned by hosted search;
2. parses the filenames in the final `Sources:` line;
3. rejects missing, invented, or unmatched filenames; and
4. withholds the answer when the stated evidence cannot be connected to the
   search result.

I would add a second agent only if the application needs a genuinely separate
responsibility, such as independent compliance review or conflict resolution
between sources. I would not add another agent merely to complicate a workflow
that is currently a search-and-answer tool-use pattern.

---

## Final outcome

The completed project includes:

- one real hosted five-file knowledge base;
- one reusable agent path;
- hosted search and explicit human escalation tools;
- local and hosted action budgets;
- a deterministic citation-format guardrail;
- an eight-row verified evaluation dataset;
- a complete valid-store baseline;
- a complete deliberate 404 experiment;
- success, refusal, and failure traces;
- directly exercised safeguard evidence;
- a concise findings document with no placeholders;
- a locked Python environment;
- 14 passing automated checks; and
- a validated submission ZIP containing exactly the handout's ten requested
  files and no repository support files.

The evidence supports a clear decision: the architecture is a useful and safe
coursework prototype, but it should not be placed behind a real user-facing
chat until citations are verified against the search evidence rather than only
checked for presence.
