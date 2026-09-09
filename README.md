# ELVTR AI Solution Architect Coursework

This repository contains my practical work for the ELVTR AI Solution Architect course. Each assignment has its own self-contained folder with source code, reproducible setup instructions, tests, evidence from completed runs, and the exact submission artifact required for that class.

## Assignments

| Folder | Focus |
|---|---|
| `s02-assignment/` | Early solution-architecture exercise and supporting deliverables |
| `s04-assignment/` | Retrieval and application foundations |
| `s05-assignment/` | Document-processing implementation |
| `s06-assignment/` | Local RAG pipeline, evaluation, and findings |
| `s07-assignment/` | Agent Framework document assistant with hosted file search, safeguards, traces, and failure testing |
| `s08-assignment/` | Assignment #5: Azure AI Foundry cloud-placement gates, managed vector store, hosted agent deployment, and live endpoint evaluation |
| `s11-assignment/` | Assignment #6: live Azure tool-agent traces in Phoenix, exact-argument approval gates, three ledger experiments and a one-page write-up |

## Latest assignment

[`s11-assignment/`](s11-assignment/) completes Assignment #6, "Trace It, Then Gate It". It uses the existing Azure model, a local Phoenix backend and a SQLite approval gate. All three live scenarios passed: approved payout, blocked account drift, and human-approved drift. Eleven gate tests passed. The folder includes actual Safari trace screenshots, terminal ledgers, a first-person `FINDINGS.md`, a one-page PDF and an exact seven-file submission ZIP builder. Payouts are strictly simulated; there is no money-transfer integration.

## Previous cloud deployment assignment

[`s08-assignment/`](s08-assignment/) ports the previous document agent to Microsoft Azure AI Foundry. It includes:

- a five-line workload definition and four evidence-backed placement gates;
- a same-cloud comparison between Global Standard and regional provisioned throughput;
- the same five source documents and eight-question dataset used in S07;
- an Azure managed vector store and file-search toolbox;
- a remotely built hosted agent using managed identity;
- four completed managed endpoint evaluations, including a real human-review tool call;
- a detailed findings write-up and an exact two-file LMS submission ZIP.

The latest live evaluation passed all four selected cases. The lab placement was approved because the corpus is public or fictional, but the findings keep sensitive production use at no-ship until an acceptable regional processing boundary has quota.

## Working with the repository

Open the README inside an assignment folder before running it. Dependencies and runtime choices differ between classes. Python assignments generally use `uv`, an assignment-local virtual environment, and an ignored `.env` file. Committed `.env.example` files contain configuration names only; credentials and access tokens are never stored in Git.

Generated environments, caches, secrets, and ZIP archives are ignored globally or inside the relevant assignment. Evidence files are committed when they support a reported result. Submission archives are deliberately limited to the allowlist in each assignment README, which can be smaller than the corresponding reproducible GitHub folder.

Some commands call billable external APIs or create cloud resources. Review each assignment's reproduction section before running provisioning or deployment commands.
