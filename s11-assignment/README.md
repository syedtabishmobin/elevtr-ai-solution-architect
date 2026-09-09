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

## Complete implementation and reproduction walkthrough

The steps below are for macOS with zsh or bash, matching the machine used for this assignment. Use two terminal windows: one keeps Phoenix running, and the other runs the agent. Commands below the checkout step run from `s11-assignment/` unless stated otherwise.

There are two ways to use this folder. To inspect the completed submission, read `FINDINGS.md`, `OUTPUTS.md` and the screenshots; no Azure access is needed. To reproduce the live experiment, follow all the steps below. A fresh clone includes the submitted evidence, but does not include the ignored runtime databases or private Azure login state.

### Step 1 - Check and install the local tools

```bash
git --version
uv --version
az version
```

Git downloads the repository, `uv` manages Python and the project environment, and Azure CLI provides the signed-in Azure session. If a command is missing, install that tool before continuing. On a Mac with Homebrew already installed:

```bash
brew install git uv azure-cli
uv python install 3.11
```

Run only the installation commands for tools you need. If Homebrew is not installed, follow its [official installation instructions](https://brew.sh/) first, or use the vendor installation links in References. `uv python install 3.11` installs the interpreter without changing the project's source code. The checked-in `.python-version` selects Python 3.11 for this folder.

Expected result: all three version checks succeed and Python 3.11 is available. No Docker, Ollama, Langfuse account, or Azure Key Vault is required for this implementation.

### Step 2 - Open the repository and assignment folder

For a fresh checkout, run these commands from the directory where you keep projects:

```bash
git clone https://github.com/syedtabishmobin/elevtr-ai-solution-architect.git
cd elevtr-ai-solution-architect/s11-assignment
```

For the existing coursework checkout on my machine, use:

```bash
cd /Users/syedtabishmobin/Documents/ELEVTR/src/elevtr-ai-solution-architect/s11-assignment
```

Use one route, not both. A private-repository clone requires your own authorized GitHub login. GitHub access is separate from Azure authentication. The assignment source files already exist in this folder; the implementation map below explains how they fit together if you are rebuilding the same design.

### Step 3 - Install the locked project environment

```bash
uv sync --frozen
uv run --frozen python --version
uv run --frozen python agent.py --help
```

`uv sync --frozen` creates `.venv/` and installs the versions in `uv.lock`, including the development test dependency. It does not resolve a newer Phoenix version. This matters because newer dependency combinations caused actual startup failures during the assignment.

The version check should show Python 3.11, and the help command should list scenarios `A`, `B`, `C` and the `--output` option. Asking for help does not authenticate to Azure or run a model. There is no need to activate `.venv` manually when using `uv run`.

### Step 4 - Sign in and select the existing Azure subscription

```bash
az login
az account list --query '[].{name:name,id:id,isDefault:isDefault}' -o table
```

For this coursework, sign in as `tabish.mb@gmail.com` in the browser. Complete the normal sign-in/MFA flow yourself. The account list confirms which subscriptions that session can access; it does not prove permission to call a model.

For the existing coursework subscription:

```bash
az account set --subscription 58fad2b2-b3ba-4e55-a101-98c0086054d4
az account show --query '{subscription:name,id:id,user:user.name}' -o json
```

Expected result on this account: `Azure subscription 1` and `tabish.mb@gmail.com`. Another reader must select their own authorized subscription rather than use this ID without access. If browser login cannot open on the machine, Azure CLI also supports `az login --use-device-code`; follow the code and URL it displays.

### Step 5 - Verify that the model resource already exists

```bash
az cognitiveservices account show \
  -g rg-elevtr-s08-aue -n foundry-elevtr-s08-aue \
  --query '{name:name,location:location,endpoint:properties.endpoint}' -o json

az cognitiveservices account deployment list \
  -g rg-elevtr-s08-aue -n foundry-elevtr-s08-aue \
  --query '[].{deployment:name,model:properties.model.name,state:properties.provisioningState}' -o table
```

These read-only checks confirm the resource and model deployment created for S08. The expected deployment name is `gpt-5-mini-s08`, backed by `gpt-5-mini`. The resource's general Cognitive Services endpoint can differ from the OpenAI chat endpoint used below.

This assignment reuses that deployment; it does not provision a new subscription, project, hosted agent or vector store. If the resource is missing, first restore the S08 prerequisite or obtain an existing compatible Azure deployment. See [S08's setup](../s08-assignment/README.md). Do not continue with an invented endpoint. Readers using their own resource must set the resource group, account, deployment and endpoint consistently in the next step.

### Step 6 - Configure authentication and the model endpoint

In the terminal that will run the agent, set the non-secret resource configuration:

```bash
export AZURE_RESOURCE_GROUP=rg-elevtr-s08-aue
export AZURE_ACCOUNT=foundry-elevtr-s08-aue
export AZURE_MODEL=gpt-5-mini-s08
export AZURE_ENDPOINT=https://foundry-elevtr-s08-aue.openai.azure.com
```

The model setting is the Azure **deployment name**, not just the underlying model name. `agent.py` appends `/openai/v1/chat/completions` to the endpoint, so do not add that suffix to `AZURE_ENDPOINT` yourself.

Choose one supported authentication mode. For an identity with direct model inference permission:

```bash
export AZURE_AUTH=entra
```

This uses `AzureCliCredential` and the existing Azure CLI login to obtain a token. The identity needs the Azure OpenAI chat-completions data action; subscription visibility alone is insufficient. This was the mode that returned `401 PermissionDenied` in the original attempt.

For the explicitly authorized resource-key route used in the completed assignment:

```bash
export AZURE_AUTH=resource-key
```

This tells the program to retrieve the existing resource key through Azure CLI and hold it in process memory. The signed-in identity must be allowed to list that resource's keys, and key authentication must be enabled on the resource. The key is not printed, written into `.env`, committed, or retrieved from Key Vault. It is sent only as the authentication header to the configured Azure endpoint. Use only an endpoint you control and intend to authorize.

There is no automatic retry from Entra to resource-key mode. Choose the mode explicitly, and use exactly `entra` or `resource-key`. The current code treats any non-`entra` value as the resource-key branch, so do not use arbitrary values. This program reads shell environment variables directly and does **not** load an `.env` file. Exports apply only to that terminal and its child processes; repeat them if you open a new agent terminal.

### Step 7 - Start Phoenix in terminal 1

Open another terminal, change into the same assignment directory, and run:

```bash
PHOENIX_WORKING_DIR=runtime/phoenix PHOENIX_HOST=127.0.0.1 uv run --frozen phoenix serve
```

Phoenix starts its local web UI and OTLP trace collector. Its SQLite database is stored under `runtime/phoenix`, so traces remain after stopping and restarting the server. Keep this terminal running throughout A, B and C. The `127.0.0.1` host binds it to the local machine.

Open [the local Phoenix UI](http://localhost:6006) in Safari. Before the first run, `s11-assignment` may not appear yet; Phoenix creates the project when its first spans arrive. If another instance of this assignment's Phoenix server is already running and its UI works, reuse it instead of starting a second one on the same port.

### Step 8 - Verify the UI before making model calls

In terminal 2, from the assignment folder:

```bash
uv run --frozen python -c 'import httpx; r=httpx.get("http://127.0.0.1:6006", timeout=10); print("Phoenix HTTP", r.status_code); r.raise_for_status()'
```

Expected result: `Phoenix HTTP 200`. This checks the web page, not the full trace pipeline; the later UI checks prove export. The agent performs the same startup check before its model workflow. Resolve connection errors or HTTP 500 before spending money on model calls.

The default UI and exporter endpoints are different routes on the same server:

| Variable | Default | Purpose |
|---|---|---|
| `PHOENIX_UI` | `http://127.0.0.1:6006` | HTTP startup health check |
| `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` | `http://127.0.0.1:6006/v1/traces` | Receives OTLP span batches |

If you intentionally change the server address or port, update both variables in terminal 2. The project name is `s11-assignment`, set in `tracing()` through the OpenInference resource attribute.

### Step 9 - Choose a fresh output directory

For a fresh clone with no local run databases, use the collector's expected path:

```bash
RUN_OUTPUT=runtime/submission
```

On a machine that already contains those completed runs, preserve them and use a new path instead:

```bash
RUN_OUTPUT=runtime/reproduction-02
```

Use the same chosen directory for A, B and C. The shell variable is just a convenience for the following commands. Each scenario creates its own database and Markdown terminal log. An existing database or same-name terminal log causes the program to refuse overwriting it; even a failed run can leave a log behind. Choose another unused directory after a failed attempt.

### Step 10 - Run A: approved settlement

```bash
uv run --frozen python agent.py A --output "$RUN_OUTPUT"
```

The program seeds the handout's approved call, asks the model to read the claim, then asks it to propose a payout using the document's account and amount. The tool middleware recomputes the binding just before the ledger insert. The unchanged account matches the fixture approval, so there is no interactive pause.

Expected final ledger shape:

```json
[
  {"tool": "read_claim_document", "claim_id": "C-2087"},
  {"tool": "issue_payout", "account": "AC-10045", "amount": 1840.0, "claim_id": "C-2087"}
]
```

Look for `RUN A TRACE_ID`, three `MODEL_USAGE` lines, `PROPOSED_CALL`, and the final `LEDGER`. The exact prose, latency and token count can differ on a rerun. The actual submitted output is in `OUTPUTS.md`.

### Step 11 - Run B: drift must be blocked

```bash
uv run --frozen python agent.py B --output "$RUN_OUTPUT"
```

The document fixture now returns `AC-99999`, while the seeded approval still covers `AC-10045`. The model proposes the new account. The gate hashes the actual tool name and arguments, finds no matching approval, records the pending call, and returns `blocked`. Run B deliberately does not ask for approval or retry the payout.

Expected final ledger:

```json
[{"tool": "read_claim_document", "claim_id": "C-2087"}]
```

The absence of an `issue_payout` ledger entry proves the side effect did not happen. A tool-wrapper span still exists because a payout was attempted; the span's existence is not proof of payment. `APPROVAL_REQUIRED`, `LEDGER_BEFORE_APPROVAL` and `NO_MATCHING_APPROVAL` show where execution stopped.

### Step 12 - Run C: approve the exact changed call

```bash
uv run --frozen python agent.py C --output "$RUN_OUTPUT"
```

This begins exactly like B: it prints the changed account and a blocked decision before pausing. Inspect all three arguments. For the assignment fixture they are claim `C-2087`, account `AC-99999`, and amount `1840.0`. Enter your own full name at `Approver full name >`.

At the second prompt, type `approve`, a space, and the full binding displayed by **that run**. For the unchanged fixture and implementation, the command is:

```text
approve 37d9ec4f5199ea44a575f66dd076f7acd8f4f66fba34f31aea2ac0201c0b4288
```

Do not use that example if your printed arguments or binding differ. Typing only `approve` does not approve anything in this implementation. Typing `reject` or any other nonmatching response leaves the payout blocked.

After an exact approval, `approve_pending()` checks the pending binding, records the approver and timestamp, and sends the stored arguments back through `attempt()`. That second execution-time check must succeed before the ledger can grow. Expect one read entry and one payout to `AC-99999`, plus a `HUMAN_APPROVAL` line. The trace should contain both the original blocked gate and the later allowed gate with your name.

The original C approval in this repository belongs to Syed Tabish Mobin. A new reader must enter their own identity and make their own decision; the committed name is evidence of the original run, not a reusable authorization for a new one.

### Step 13 - Inspect the saved results and ledger

Each scenario writes these files beneath the chosen output directory:

| File pattern | What it records |
|---|---|
| `run-A-terminal.md` | Printed stdout, prompts and final ledger inside a Markdown code block; stderr is not captured here |
| `run-A.json` | Completed scenario, trace ID, model answer, tool result and ledger |
| `run-A-spans.jsonl` | The same span records sent to Phoenix, including parent IDs and durations |
| `run-A.sqlite` | Durable approvals, pending calls and the simulated system-of-record ledger |

The same patterns apply to B and C. A missing result JSON indicates the run did not reach successful completion, even if a terminal log exists. Do not count partial output as a pass.

Inspect B's durable ledger without modifying it:

```bash
uv run --frozen python - "$RUN_OUTPUT/run-B.sqlite" <<'PY'
import sqlite3
import sys
from pathlib import Path

uri = Path(sys.argv[1]).resolve().as_uri() + "?mode=ro"
with sqlite3.connect(uri, uri=True) as db:
    for row in db.execute("SELECT tool, args FROM ledger ORDER BY id"):
        print(row)
PY
```

Expected: only `read_claim_document`. Opening with `mode=ro` avoids accidentally creating a new empty database if the path is wrong. Use A's or C's filename to inspect their payout entries.

### Step 14 - Inspect and capture the real traces

In Safari, open `http://localhost:6006` and select `s11-assignment`. In the root-spans list, open the relevant `claim-run-B` using the trace ID printed by your run to distinguish it from older traces.

1. Expand the root and the `tool.issue_payout` branch. The full B tree has three `model.chat` spans, the read tool, the payout wrapper, and the nested `reliability.approval_gate` span.
2. Select the gate's **Info** tab to see its input and blocked output beside the full tree. Keep the whole tree visible and capture `evidence/full-trace.png`.
3. Select the gate's **Attributes** tab. Make the tool arguments, full `binding`, `decision: blocked`, and `allowed: false` visible. Capture `evidence/blocked-gate.png`.
4. Open each model span to inspect input/output token counts and latency. Open C's allowed gate to inspect `approved_by` and `approved_at`.

On macOS, `Shift-Command-5` opens the screenshot controls. Select the relevant window or region, capture the actual browser view, and save/rename the PNGs to the two filenames above. Reduce browser zoom temporarily if the trace tree and attributes do not fit; restore it afterward. Do not reconstruct the screenshots from the JSON. If using automated computer control, macOS may require Accessibility and Screen Recording permission followed by quitting and reopening the capture app. Manual screenshots do not require giving an AI control of Safari.

The presence of complete traces in Phoenix is the export check. JSONL evidence alone does not prove a backend received anything. Check that B has seven spans, C has eight, and each run has one root. The normal blocked decision is a business outcome, so the screenshot's OTel status can be `UNSET`; inspect the explicit gate decision rather than treating `UNSET` as a payout failure or success.

### Step 15 - Run the offline gate tests

```bash
uv run --frozen pytest -q
```

Expected for the checked-in implementation: `11 passed`. These tests create temporary SQLite databases and exercise the middleware without Azure model calls or an active Phoenix collector. They test binding, missing/revoked approval, restart of a database connection, invalid amounts, conflicting settlements and concurrent retries. They complement the three live ledgers; they do not replace the required real traces or human decision.

### Step 16 - Collect the evidence without confusing old and new runs

For the original local run directory, or a fresh run using `runtime/submission`:

```bash
uv run --frozen python collect_evidence.py
```

The collector reads results and spans, verifies each expected payout count, verifies the complete parent/child trace structure and gate decisions, then creates `OUTPUTS.md` and copies portable JSON/JSONL evidence into `evidence/`. It can read either the new Markdown logs or the original TXT captures. It does not call Azure, create approvals, or manufacture missing outputs.

The collector is intentionally configured for this submitted experiment: `SOURCE` is `BASE / "runtime/submission"`, the C approver assertion is `Syed Tabish Mobin`, and the output introduction says 9 September 2026. If collecting **your own new run**, first edit those explicit values in `collect_evidence.py` to the actual directory, actual approver and actual run date. Preserve the approval assertion; change its expected identity, not the evidence. There is no `--source` or `--approver` CLI option in the current helper. Back up the original evidence before replacing it, and update both screenshots from the same new runs.

To inspect or package the already committed submission on a fresh clone, skip the collector: the ignored runtime inputs are absent, but `OUTPUTS.md`, the screenshots and findings are already available. Packaging the existing deliverables does not require replaying model calls.

### Step 17 - Complete the Markdown findings

Use `FINDINGS.md` for the four-question short write-up and `OUTPUTS.md` for the longer execution transcript. Keep the short write-up to roughly the existing one-page amount of content; Markdown pagination depends on the renderer.

Address the actual Milestone 2 tool inventory, which actions would cause approval fatigue, the concrete retry/idempotency behavior, and one specific observation from the screenshot. State whether a tool really writes anything: the earlier `flag_for_human` currently returns a string, rather than creating a ticket. Use measured tokens and gate outcomes from the matching evidence. If you rerun the experiment, update the date, observations and figures rather than carrying forward old numbers. The committed findings are already complete and contain no evidence placeholders.

### Step 18 - Build and inspect the submission ZIP

```bash
uv run --frozen python package_submission.py
unzip -l s11-assignment.zip
unzip -t s11-assignment.zip
```

The packaging script checks that all eight allowlisted files exist and are nonempty, writes `s11-assignment.zip`, verifies the exact entry names and checks archive integrity. Expected result: eight files beneath one `s11-assignment/` prefix and no ZIP errors. The complete allowlist appears below. All generated document deliverables are Markdown; the two PNG files are the screenshots specifically requested by the handout.

The script replaces the existing ZIP if one exists, so copy an old archive elsewhere first if you need to retain it. It verifies packaging, not the scientific correctness of a result or the legibility of an image; the previous steps provide those checks. The submission ZIP is deliberately smaller than the GitHub folder, so it excludes this README and development helpers. A ZIP recipient can install with `uv sync --frozen --python 3.11` and run `agent.py` after setting up Azure and Phoenix as described above.

### Step 19 - Save the project changes to GitHub

If you are updating this coursework, inspect the changes from the repository root before committing:

```bash
cd ..
git status --short
git diff --check
git diff -- s11-assignment/README.md s11-assignment/FINDINGS.md
git add s11-assignment
git diff --cached --stat
git commit -m "Update Assignment 6 implementation and evidence"
git push origin main
```

Stage only the intended assignment files; review any unexpected files before committing. This assumes you have permission to push to this repository's `main` branch. Other readers should use their own branch or fork. `.gitignore` excludes runtime databases, environments and ZIPs, so the submission archive is delivered separately. Do not add Azure keys or override the ignore rules to publish the runtime directory. If there are no changes, skip the commit and push.

### Step 20 - Stop the local session

Press `Control-C` in terminal 1 to stop Phoenix when finished. Its local trace database remains on disk. Stopping Phoenix does not remove the Azure resource or stop unrelated hosted resources created by previous assignments. This assignment does not add a new hosted service; model charges come from actual inference requests. Keep the existing Azure resource if another assignment uses it.

In terminal 2, optionally clear this task's shell configuration:

```bash
unset AZURE_AUTH AZURE_RESOURCE_GROUP AZURE_ACCOUNT AZURE_MODEL AZURE_ENDPOINT
unset PHOENIX_UI OTEL_EXPORTER_OTLP_TRACES_ENDPOINT RUN_OUTPUT
```

This clears environment settings in that terminal; it does not revoke the Azure CLI login or rotate any resource key.

## Implementation map: what each part does

If implementing the design from the handout, build the components in this order. The supplied files are the completed implementation; no source-code generation step is required to run them.

| Order | Component | Implementation and reason |
|---|---|---|
| 1 | `pyproject.toml`, `uv.lock`, `.python-version` | Establish a reproducible Python 3.11 environment and pin the backend dependencies that were proven to work. |
| 2 | `canonical()` and `binding_of()` in `hitl.py` | Serialize the tool and all arguments with sorted JSON keys, then calculate full SHA-256. Sorting makes dictionary order irrelevant; changing a value changes the approval identity. |
| 3 | `validate()` | Require exactly claim ID, account and a positive finite numeric amount before considering a payout. Reject extra fields, invalid strings, booleans and non-finite numbers. |
| 4 | `Store` tables | `approvals` stores run, binding, payload, actor, timestamp and consumption state; `pending` stores the paused exact call; `ledger` records executed tool bodies and a unique settlement key. |
| 5 | `Store.attempt()` | Open a write transaction, revalidate approval, check existing settlement state, then either record a blocked pending call or insert the ledger row and consume approval. Return the observed result. |
| 6 | `Store.approve_pending()` | Compare the operator's binding with the pending call before approving it. The subsequent `attempt()` still independently checks the execution. |
| 7 | `tracing()` and `EvidenceExporter` in `agent.py` | Create the OTel provider, register an OTLP HTTP exporter and a portable JSONL exporter, and assign the Phoenix project. Both exporters receive the same completed spans. |
| 8 | `model_turn()` | Make the actual Azure HTTP request inside an LLM span, validate the HTTP response, and attach response usage, model output and a labelled cost estimate. Credentials are passed in headers and not included in span data. |
| 9 | `run()` | Create one agent root, execute the read and payout phases, hold C at the human prompt, request a final model answer, and print/save the actual ledger. The `finally` block flushes/shuts down exporters and closes the database once the workflow is entered. |
| 10 | Terminal `Tee` | Duplicate printed stdout into a Markdown code block and the terminal, so the final transcript remains the output of the executed code. |
| 11 | Tests and evidence helpers | Verify the critical execution boundary separately from model prose, collect the observed runs, and package only the checklist deliverables. |

The model does not choose an unrestricted next action. The code forces one read-tool phase, one payout-tool phase, and a final response without tools, and rejects an unexpected tool plan. It still uses the model to generate the arguments. This is why all three scenarios are comparable and why the safety boundary can be tested directly.

For amount handling, the executor converts the model's JSON numeric amount to a float before display and binding. The gate's hash therefore covers the representation that actually executes. This lab does not implement a production currency/rounding contract; an external payment integration would need fixed-precision money and currency validation in addition to the gate.

Within SQLite, `BEGIN IMMEDIATE` serializes competing writers. The stable operation key prevents duplicate settlement inserts. Approval binding and idempotency are separate controls: the binding answers whether these arguments were approved, while the business key answers whether this settlement already happened. The restart test reopens a database connection; it does not claim a full process-kill/resume demonstration of the model conversation.

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

## Troubleshooting

| Symptom | What it means | What to do |
|---|---|---|
| `uv`, `git` or `az` not found | The tool is absent or not on this terminal's PATH. | Complete Step 1, reopen the terminal if the installer requires it, and repeat the version check. |
| `401 PermissionDenied` with Entra | Login succeeded, but the principal lacks direct model inference permission. | Confirm the intended account/resource, then obtain the appropriate data-plane access from its owner or explicitly use an authorized resource-key route. Do not assume `az login` fixes a role mismatch. |
| Resource-key retrieval denied | The CLI identity cannot list the account keys, or is targeting the wrong subscription/resource. | Recheck Steps 4-6. Ask the resource owner for an approved access method; do not paste keys into the repository. |
| Model `404` or deployment not found | The deployment name or endpoint is wrong, or the deployment was removed. | Re-run the deployment list and verify all four resource environment variables. `AZURE_MODEL` must match the deployment name exactly. |
| Model `400` | The selected deployment may not support this request shape, tool choice or reasoning setting. | Use the tested `gpt-5-mini` deployment, or deliberately adapt `model_turn()` and verify the replacement model's contract. Do not treat a different model as a drop-in equivalent without checking. |
| Model `429` | Azure quota or throughput was exceeded. | Inspect the Azure deployment capacity and wait for the indicated retry interval. Preserve the failed output, then retry in a fresh output directory when capacity is available. |
| Phoenix connection refused | The local server is stopped or the port is wrong. | Start Step 7 and wait for startup to finish; verify the UI URL before rerunning the agent. |
| Port 6006 already in use | Another server is already listening. | Check whether it is the existing assignment Phoenix instance and reuse it if appropriate. Do not terminate an unrelated process just to free the port. |
| Phoenix import/dataclass error | An incompatible dependency combination was installed. | Run `uv sync --frozen` in this folder and use the checked-in lockfile; avoid an unpinned global Phoenix install. |
| Phoenix HTTP 500 mentioning `TemplateResponse` | Web-framework versions do not match the pinned Phoenix version. | Restore the locked environment, then stop and restart that Phoenix process. The working versions are FastAPI 0.115.6 and Starlette 0.41.3. |
| JSONL exists but no Phoenix trace appears | Local export succeeded, but OTLP export or UI filtering may not have. | Check the server and agent stderr, the `/v1/traces` endpoint, project name and UI date range. Match the printed trace ID. Treat absent backend traces as incomplete tracing evidence. |
| `FileExistsError` | That scenario's database or Markdown log already exists. | Use another unused output directory. Preserve the prior evidence rather than deleting it blindly. |
| C remains blocked after typing `approve` | The response does not contain the exact full binding. | The accepted response is `approve ` followed by the full printed SHA-256. A mismatched response finishes as blocked; use a fresh run to try again. |
| C's approval is rejected as changed or missing | The pending call no longer matches the operator's binding. | Inspect the current call and obtain a new approval for those actual arguments. Never reuse approval from a different payload. |
| Collector cannot find `run-A.json` | It points at a directory without all completed runs. | Follow Step 16: verify `SOURCE`, all three scenarios and their output files. A fresh clone lacks local runtime inputs by design. |
| Collector fails on C approver | A new run used a different actual reviewer from the original experiment. | Update the helper's expected actor to the real reviewer for the new evidence; do not rename the recorded reviewer to satisfy the assertion. |
| ZIP builder reports a missing file | One of the eight required artifacts is absent or empty. | Complete the relevant code, screenshot, output or findings step; do not insert dummy evidence to pass packaging. |

The model's final prose is not the control plane. A model can suggest unsupported explanations or offer actions that the tool set cannot perform. The gate attributes, actual ledger and saved tool outputs are the evidence for whether a payout happened.

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
│   └── test_gate.py
└── evidence/
    ├── full-trace.png
    ├── blocked-gate.png
    ├── metrics.json
    ├── run-A.json
    ├── run-A-spans.jsonl
    ├── run-B.json
    ├── run-B-spans.jsonl
    ├── run-C.json
    └── run-C-spans.jsonl
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

## Final verification checklist

- Local dependencies install from the lockfile and the CLI help command works.
- The intended Azure account, subscription, resource and deployment have been checked.
- Phoenix's UI loads and receives the matching run trace IDs.
- A has one payout to the approved account without an interrupt.
- B has no payout, and its custom gate span explicitly shows a blocked decision.
- C first blocks, then records the exact approving human/binding and one payout.
- The complete trace screenshot and blocked-gate screenshot are real, readable captures.
- Offline tests pass; measured outputs remain separate from test fixtures.
- `OUTPUTS.md` preserves the actual terminal output; `FINDINGS.md` answers all four questions without placeholders.
- The ZIP lists exactly the eight required files and passes its integrity check.
- No credentials, local databases, environments or unrelated documents are staged in Git.

The loop-budget/circuit-breaker cost comparison, full process-kill checkpoint recovery and JSONL override golden-set are optional stretch tasks in the handout. This submission does not claim those experiments. It includes a fixed tool budget and a SQLite reconnection test, but neither is presented as a completed stretch demonstration.

## References

- Assignment #6, "Trace It, Then Gate It", supplied course handout.
- [uv installation](https://docs.astral.sh/uv/getting-started/installation/)
- [uv Python installation](https://docs.astral.sh/uv/guides/install-python/)
- [uv locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/)
- [Azure CLI installation on macOS](https://learn.microsoft.com/cli/azure/install-azure-cli-macos)
- [Phoenix OTLP configuration](https://arize.com/docs/phoenix/self-hosting/configuration)
- [Phoenix cost tracking](https://arize.com/docs/phoenix/tracing/how-to-tracing/cost-tracking)
- [Azure model chat API](https://learn.microsoft.com/en-us/rest/api/microsoft-foundry/azureopenai/chat)
- [GPT-5 mini reference pricing](https://developers.openai.com/api/docs/models/gpt-5-mini)
