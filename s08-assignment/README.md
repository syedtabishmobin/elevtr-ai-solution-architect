# ELVTR AI Solution Architect - Assignment 08

## Cloud AI Services and Architecture

This folder contains my completed implementation of **Class 8 Assignment #5**. It ports the S07 document agent to Azure AI Foundry, runs the required cloud-placement gates, publishes the agent as a managed hosted endpoint, and records four live evaluation calls.

The LMS submission is intentionally smaller than this reproducible project. `s08-assignment.zip` contains only `cross-cloud-scorecard.md` and `FINDINGS.md`, exactly as requested by the handout.

## Outcome

| Check | Observed result |
|---|---|
| Azure account/project | `foundry-elevtr-s08-aue` / `elevtr-s08`, Australia East |
| Model | `gpt-5-mini` `2025-08-07`, Global Standard, 100K TPM allocated |
| Knowledge base | 5 files completed, 0 failed |
| Managed retrieval | `s08-document-tools` version 1 with pinned `file_search` |
| Hosted agent | `s08-docs-agent` version 1, active |
| Runtime | Python 3.13 remote build, 0.5 CPU, 1 GiB memory |
| Integrity | Downloaded deployed source matched SHA-256 `003fc4cd61cbfdae3b55285f8149f65d07dc8b8d9a5b1b1196c134ce07796df0` |
| Final evaluation | 4/4 pass in 142.5 seconds |
| Placement | Ship the public/fictional lab; no-ship sensitive production until residency is resolved |

## Architecture

```text
docs/ (same five S07 files)
        |
        v
provision.py --> Azure managed vector store (5/5 indexed)
        |                    |
        |                    v
        +--> Foundry toolbox: managed file_search
                                  |
hosted/main.py -------------------+
        |
        +--> FoundryChatClient (gpt-5-mini-s08)
        +--> flag_for_human local function
        +--> ResponsesHostServer
        |
        v
deploy.py --> remote Python 3.13 build --> hosted agent version 1
                                                |
datasets/agent_eval.jsonl                       |
        |                                       |
        v                                       v
evals.py ----------------------------> managed Responses endpoint
                                                |
                                                v
                                  experiments/managed_eval.csv
```

All runtime access uses `AzureCliCredential` and managed identity. No Azure key, GitHub token, or other secret is committed.

## Cloud placement gates

The four gates are recorded in `experiments/gates.txt` and summarized in the submission scorecard:

1. **Availability:** passed for the selected GA model and Hosted Agents in Australia East.
2. **Residency:** failed for sensitive production because Global Standard may process inference globally; accepted only for this non-sensitive lab corpus.
3. **Quota:** passed with 500K TPM available and 100K TPM allocated. The measured 10K TPM failure is preserved in the evidence.
4. **Isolation:** supported through managed identity and private networking. Managed identity is enabled; a VNet was intentionally not added to this lab.

The deciding constraint is residency. See `cross-cloud-scorecard.md` for the selected path, provisioned-throughput alternative, source links, and final decision.

## Repository structure

```text
s08-assignment/
├── .env.example
├── .gitattributes
├── .gitignore
├── .python-version
├── README.md
├── FINDINGS.md
├── cross-cloud-scorecard.md
├── pyproject.toml
├── uv.lock
├── provision.py
├── deploy.py
├── evals.py
├── hosted/
│   ├── main.py
│   └── requirements.txt
├── datasets/
│   └── agent_eval.jsonl
├── docs/
│   ├── apple_annual_report.pdf
│   ├── microsoft_annual_report.pdf
│   ├── tesla_annual_report.pdf
│   ├── equity_research_policy.md
│   └── portfolio_research_faq.md
├── experiments/
│   ├── gates.txt
│   ├── vector_store_build.txt
│   ├── deployment.txt
│   └── managed_eval.csv
└── tests/
    └── test_assignment.py
```

`.env`, `.venv/`, caches, and ZIP files are ignored. The local `.env` stores only non-secret resource identifiers and can be recreated by the provisioning command.

## Main files

| File | Purpose |
|---|---|
| `provision.py` | Discovers the five source documents, creates or reuses the managed vector store, waits for indexing, and creates the file-search toolbox. |
| `hosted/main.py` | Defines the hosted Agent Framework application, grounding rules, action limits, toolbox connection, and human-review function. |
| `deploy.py` | Builds an exact source ZIP, submits a remote Python build, waits for `active`, downloads the deployed code, and verifies its SHA-256. |
| `evals.py` | Calls the named managed endpoint for four existing S07 cases and requires expected text plus the appropriate observed tool call. |
| `experiments/managed_eval.csv` | Stores every final managed response, pass status, and called tools. |
| `FINDINGS.md` | One-page write-up based only on observed deployment and evaluation evidence. |
| `cross-cloud-scorecard.md` | Four-gate comparison and placement decision. |

## Reproduce the project

Prerequisites:

- Python 3.11 or newer locally; the hosted runtime uses Python 3.13.
- `uv` for environment and lockfile management.
- Azure CLI authenticated to a subscription that can create Foundry resources.
- An existing Foundry project and compatible model deployment, or equivalent infrastructure created first.

Install and authenticate:

```bash
uv sync
az login
cp .env.example .env
```

Set the project endpoint and deployment name in `.env`, then provision the managed retrieval resources:

```bash
uv run python provision.py --save-env
```

Deploy the hosted agent and verify the downloaded source archive:

```bash
uv run python deploy.py
```

Run the same four managed evaluation questions:

```bash
uv run python evals.py
```

Run offline artifact checks after creating the submission ZIP:

```bash
uv run pytest
```

These commands can create billable Azure resources and model usage. `provision.py` reuses a complete same-name vector store and matching toolbox so normal reruns do not duplicate them. `deploy.py` creates a new hosted-agent version each time it is run.

## Evaluation contract

The full eight-row S07 dataset is preserved, but the required managed check uses four representative questions:

| QID | Scenario | Required observed tool | Final result |
|---|---|---|---|
| `q01` | Direct policy threshold lookup | `file_search` | Pass |
| `q04` | Multi-document evidence rules | `file_search` | Pass |
| `q06` | Missing support address | `flag_for_human` (after search) | Pass |
| `q07` | Financial-table distractor | `file_search` | Pass |

The evaluator treats a non-completed managed response, an API error, empty text, missing required content, or absent required tool call as a failure. This prevented the initial capacity error from looking like a normal answer.

## Observed issues

- Foundry's OpenAI-compatible vector-store endpoint rejected the optional `description` field, so the implementation uses the supported name-only call.
- The first deployment used 10K TPM. File search completed, but the hosted agent's internal answer call was rate-limited. Increasing the deployment to 100K TPM produced the final 4/4 pass.
- The SDK's hosted-code download method requires `agent_version` as a keyword argument; the deployment verifier now uses that signature.

## References

- [Azure Foundry Hosted Agents](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/hosted-agents)
- [Foundry Agent Service overview](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/overview)
- [File search tool](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/file-search)
- [Limits, quotas, and regions](https://learn.microsoft.com/azure/foundry/agents/concepts/limits-quotas-regions)
- [Networking options](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/networking-options)
- [Data, privacy, and security](https://learn.microsoft.com/en-us/azure/foundry/responsible-ai/openai/data-privacy)

## Submission archive

The generated `s08-assignment.zip` contains exactly:

```text
s08-assignment/cross-cloud-scorecard.md
s08-assignment/FINDINGS.md
```

The code, README, documents, CSV, and supporting logs remain in GitHub for reproducibility but are deliberately excluded from the LMS ZIP.
