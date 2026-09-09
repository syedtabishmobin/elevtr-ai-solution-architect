# ELVTR AI Solution Architect - Assignment 11

## Trace It, Then Gate It

This is the S11 tracing and human-in-the-loop assignment. The folder follows the repository's class numbering: Assignment #5 is in `s08-assignment`, and Assignment #6 is in `s11-assignment`.

## What it builds

The agent uses the existing Azure `gpt-5-mini-s08` deployment to read a fictional insurance claim, propose a settlement, and explain the tool result. A plain Python middleware checks an exact-call approval before inserting a simulated payout into SQLite. OpenTelemetry exports each run to a local Phoenix UI. Phoenix and plain tool middleware are both explicitly permitted alternatives in the handout.

There is no payment provider, bank connection, or money-transfer code. The $1,840 amount is fictional assignment data. Azure model inference can incur normal usage charges; the local payout does not.

## Completed results - 9 September 2026

| Run | Live model calls | Spans | Tokens | Ledger payout entries | Gate result |
|---|---:|---:|---:|---:|---|
| A: approved account | 3 | 7 | 1,139 | 1 | Allowed with handout preapproval fixture |
| B: account drift | 3 | 7 | 1,172 | 0 | Blocked: no exact approval |
| C: approved drift | 3 | 8 | 1,128 | 1 | Blocked, then allowed after human approval |

Phoenix received all three complete traces, verified in its UI. Each has one root and nested model, tool and gate spans. Runs A and B took 6.609 and 7.096 seconds; C took 16.146 seconds including the operator pause. The nine model calls used 3,439 tokens. Their combined reference-cost estimate is US$0.001971; this is not a billing statement.

The user explicitly approved the simulated C call in the task. That decision was relayed into the interactive terminal as `Syed Tabish Mobin` only after checking that the printed claim, account and amount matched. The terminal and allowed span record the full binding. The actor name is not a model-generated approval.

Both required screenshots were captured from the live Phoenix UI in Safari. `evidence/full-trace.png` shows the complete B tree with both tool spans expanded, three model token counts, and the gate's input/output. `evidence/blocked-gate.png` shows `decision=blocked`, `allowed=false`, the arguments and full binding. No trace screenshot was generated or reconstructed from text.

The final answer in B suggested checking holds or compliance flags without evidence for those possibilities. The actual tool result and gate showed an approval mismatch. This limitation is preserved in the terminal log and discussed in the findings; no final answer was edited to make it look better.

## Source material and prior work

The claim fixture comes directly from the supplied `Assignment #6 .docx.pdf`: claim `C-2087`, policy `P-55512`, amount `1840.00`, account `AC-10045`. Runs B and C change the document's account to `AC-99999`. The brief does not request an external claim document, so the fixture is embedded in `read_claim_document` as in its sample.

The Milestone 2 blast-radius analysis uses the real previous document agent in `../s07-assignment/agent.py` and its Azure port in `../s08-assignment/hosted/main.py`. Their complete tool set is `file_search` and `flag_for_human`. The latter currently returns a string; it does not create a real review ticket. The previous five-file research corpus is not needed for the claim demonstration and is not duplicated in the ZIP.

## Architecture and approval contract

1. A real Azure model call requests `read_claim_document`; the tool body appends the read to the ledger.
2. A second model call proposes `issue_payout` arguments from the returned fixture.
3. The tool wrapper computes full SHA-256 over compact, sorted JSON containing the tool name and every argument. JSON numeric amounts are converted to a float at the tool boundary before display, approval, hashing and execution.
4. `Store.attempt` starts a SQLite write transaction, rechecks the approval against the current run, binding and full payload, and fails closed on a mismatch. An approval is never inferred from the tool name or the final model answer.
5. Run C prints the exact pending call and pauses for the approver's name and `approve <full binding>`. The pending binding must still match. Execution then goes through the gate again.
6. A final model call summarizes the actual tool result. The program prints the real ledger independently of that answer.

The workflow allows two tool steps and one final model turn, disables parallel model tool calls, and stops unexpected plans. This deliberately constrained agent makes the three experiments comparable while leaving argument generation to the live model.

Preapproval in each isolated experiment is attributed to `R. Mehta (handout preapproval fixture)`; that is sample data, not a claim that a real adjuster approved anything. Human run C approval is collected separately. Each run has its own database so A does not prevent C's independent experiment.

## Idempotency and limits

The local system of record has a unique business key `settlement:v1:C-2087`, with the claim ID substituted for other claims. The ledger insert and approval consumption happen in the same transaction. Retrying the same approved settlement returns `already_paid`; changing the arguments for an existing settlement raises an error. The key is independent of process IDs, timestamps, model call IDs and deployments.

Pending approvals survive reopening the database, which is checked in tests. The full model conversation is not checkpointed, so this does not claim the optional LangGraph process-kill stretch exercise. SQLite is also not a transaction across an external payment provider. A real payout integration would need the same durable business key at the provider, an outbox and reconciliation for uncertain responses.

This is a single-operator local lab. The typed approver name is an audit label, not authenticated identity. Production approval needs authenticated reviewers, authorization and a protected store. No external payment adapter is included.

## Setup and reproduction

Use Python 3.11 and `uv`. From this folder:

```bash
uv sync --frozen
az login
```

Use the Azure account `tabish.mb@gmail.com`. The existing defaults refer to resource group `rg-elevtr-s08-aue`, account `foundry-elevtr-s08-aue`, and deployment `gpt-5-mini-s08`. No resources need to be created. The default authentication mode is Entra identity and requires the relevant Azure OpenAI data-plane permission.

If explicitly authorized to use the existing resource key, set `AZURE_AUTH=resource-key`. The program retrieves it through the authenticated Azure CLI into process memory; it does not print the key or write an `.env` file. This requires permission to list the existing resource keys. It does not modify Azure roles.

Start the tracing UI in a separate terminal:

```bash
PHOENIX_WORKING_DIR=runtime/phoenix PHOENIX_HOST=127.0.0.1 uv run phoenix serve
```

Open `http://localhost:6006`, select project `s11-assignment`, then open a `claim-run` trace. Start the backend before running the agent.

```bash
uv run python agent.py A --output runtime/reproduction
uv run python agent.py B --output runtime/reproduction
uv run python agent.py C --output runtime/reproduction
```

For C, inspect the printed account, amount and binding before answering. Enter your full name and then `approve <the displayed full SHA-256>` or `reject`. Each scenario refuses to overwrite an existing database: choose a new output directory for another experiment.

Supported environment overrides: `AZURE_ENDPOINT`, `AZURE_MODEL`, `AZURE_AUTH`, `AZURE_RESOURCE_GROUP`, `AZURE_ACCOUNT`, and `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT`. Defaults are documented directly in `agent.py`.

## Traces and operational questions

| Span type | Question it answers |
|---|---|
| `claim-run-A/B/C` (AGENT) | What happened across the whole request, and what ledger and final response resulted? |
| `model.chat` (LLM) | What did the model receive and propose, how long did it take, and how many input/output tokens did it use? |
| `tool.read_claim_document` (TOOL) | Which claim did the tool actually read and which account did it return? |
| `tool.issue_payout` (TOOL) | Which exact settlement was attempted and what did the execution wrapper return? |
| `reliability.approval_gate` (CHAIN) | Was this argument binding allowed or blocked, and who approved an allowed call? |

All spans have native OTel start/end timestamps. Tool spans record arguments and zero model tokens because local functions do not consume model tokens. Model spans record provider-reported usage and a labelled USD reference-cost estimate using $0.25 input, $0.025 cached input and $2.00 output per million tokens. These are reference estimates, not an Azure invoice. The same exported spans are saved as JSONL for inspection.

## Validation

```bash
uv run pytest -q
```

The tests cover tool-name and argument binding, reordered JSON keys, missing/revoked/wrong-run approvals, argument drift, exact approval after reconnecting to SQLite, non-finite or invalid amounts, concurrent retry and conflicting settlements. Test approvers are labelled test fixtures and are not evidence of live human approval.

## Dependency and access findings

Unrestricted dependency resolution selected Phoenix 20.9.0, which failed at import on Python 3.11 because of a dataclass mapping default. Phoenix 12.33.1 also needed a compatible evals package, so both `arize-phoenix==12.33.1` and `arize-phoenix-evals==2.8.0` are pinned and the full dependency tree is locked. The backend then started successfully.

The signed-in Azure identity initially returned `401 PermissionDenied` for the direct chat data action. Authentication success alone did not prove model-inference authorization. Failed setup attempts are not counted as completed A/B/C evidence.

After explicit user authorization, the completed runs used the existing Azure resource key retrieved by CLI into process memory. No Key Vault access, new cloud resources, role changes, or saved keys were needed. The Phoenix web UI also required `fastapi==0.115.6` and `starlette==0.41.3` because newer template APIs caused HTTP 500; those versions are pinned too.

## Files and exact submission ZIP

[`FINDINGS.md`](FINDINGS.md) is the short first-person write-up answering the four assignment questions. Its content is unchanged from the previously verified one-page write-up; Markdown pagination depends on the viewer. [`OUTPUTS.md`](OUTPUTS.md) contains the actual captured terminal output in fenced code blocks, following the evidence presentation in S04 and S05. All generated documentation is Markdown. The JSON/JSONL files in `evidence/` are machine-readable trace data for reproducibility, not document deliverables, and are excluded from the ZIP. SQLite databases and environments remain ignored under `runtime/` and `.venv/`.

### Project structure

```text
s11-assignment/
├── .python-version
├── README.md
├── FINDINGS.md
├── OUTPUTS.md
├── agent.py
├── hitl.py
├── pyproject.toml
├── uv.lock
├── collect_evidence.py
├── package_submission.py
├── tests/
└── evidence/
    ├── full-trace.png
    ├── blocked-gate.png
    └── ... machine-readable trace data
```

Like S04 and S05, the root contains the README, findings, Python entry points, dependency manifest, lockfile and Python-version file. The separate output document keeps the brief's short write-up concise. The two PNG screenshots are retained because the assignment explicitly requires screenshots.

Recheck the saved live-run evidence and build the ZIP:

```bash
uv run python collect_evidence.py
uv run python package_submission.py
```

`collect_evidence.py` requires the completed local files under `runtime/submission`; it validates their ledgers, complete trace ancestry and expected gate decisions before copying the portable evidence. A fresh clone already contains that portable evidence and `OUTPUTS.md`. New agent runs save Markdown terminal logs. The collector also reads the original local TXT captures to preserve the recorded evidence without rerunning Azure calls.

The archive contains exactly these eight files, all under `s11-assignment/`:

```text
agent.py
hitl.py
pyproject.toml
uv.lock
evidence/full-trace.png
evidence/blocked-gate.png
OUTPUTS.md
FINDINGS.md
```

This maps to the checklist's runnable code, two screenshots, three terminal ledgers and short write-up. The manifest and lockfile provide the same `uv sync --frozen` setup used by the previous assignments. The detailed README, tests, raw spans and helper scripts stay in GitHub; they are excluded from the LMS ZIP. The original handout and unrelated prior documents are excluded as well. The ZIP contains no PDF or TXT documents.

## References

- Assignment #6, "Trace It, Then Gate It", supplied course handout.
- [Phoenix OTLP configuration](https://arize.com/docs/phoenix/self-hosting/configuration)
- [Phoenix cost tracking](https://arize.com/docs/phoenix/tracing/how-to-tracing/cost-tracking)
- [Azure model chat API](https://learn.microsoft.com/en-us/rest/api/microsoft-foundry/azureopenai/chat)
- [GPT-5 mini reference pricing](https://developers.openai.com/api/docs/models/gpt-5-mini)
