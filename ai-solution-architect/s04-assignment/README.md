# Class 4 Bonus Assignment — Direct LLM API Calls, Prompting and Model Swapping

This project contains my implementation of the **Class 4 Bonus Assignment** for the ELVTR AI Solution Architect course.

The assignment explores how an application interacts directly with a Large Language Model (LLM), how different prompting techniques affect model behaviour and token usage, and how the same application logic can be used with different model providers.

The implementation covers:

- Direct LLM API calls using the OpenAI Python SDK
- Zero-shot prompting
- Few-shot prompting
- Chain-of-thought prompting
- System prompting and missing-value handling
- Adapting prompts to a custom IT support scenario
- Switching between a cloud-hosted OpenAI model and a locally hosted model through Ollama
- Comparing model behaviour, output quality, speed, cost considerations, and deployment characteristics

Detailed execution outputs and observations are available in [`FINDINGS.md`](FINDINGS.md).

---

## 1. Learning Objectives

The main objectives of this assignment are to understand:

1. How to call an LLM directly from Python.
2. What information is actually sent to the model through the `messages` array.
3. How different prompting techniques influence model responses.
4. How prompt design affects output structure, consistency, and token usage.
5. How system instructions can reduce unsupported assumptions and hallucinations.
6. How to handle missing information explicitly using `null`.
7. How an application can switch between different model providers without changing its core business logic.
8. The architectural trade-offs between cloud-hosted and locally hosted LLMs.

---

## 2. Project Structure

```text
s04-assignment/
├── .python-version
├── README.md
├── FINDINGS.md
├── hello.py
├── prompts.py
├── swap.py
├── pyproject.toml
└── uv.lock
```

Local development also uses:

```text
.env
.venv/
```

These files/directories are intentionally excluded from source control.

### File Descriptions

| File | Purpose |
|---|---|
| `hello.py` | Makes the first direct LLM API call using the OpenAI Python SDK |
| `prompts.py` | Demonstrates zero-shot, few-shot, chain-of-thought, and system prompting |
| `swap.py` | Runs the same task against different LLM providers/models |
| `FINDINGS.md` | Captures model outputs, token usage, observations, and model comparison |
| `pyproject.toml` | Defines the Python project and dependencies |
| `uv.lock` | Locks dependency versions for reproducible installation |
| `.python-version` | Defines the Python version used by the project |
| `README.md` | Project documentation and execution instructions |

---

## 3. Technology Stack

The project uses:

- **Python**
- **uv** for Python project and dependency management
- **OpenAI Python SDK**
- **python-dotenv** for environment-variable management
- **OpenAI GPT-5-mini** as the cloud-hosted model
- **Ollama** for local model execution
- **Qwen3:8b** as the locally hosted generative model

The project deliberately uses the OpenAI-compatible API exposed by Ollama so that both providers can be accessed using a similar application interface.

---

## 4. Prerequisites

Before running the project, the following are required:

### Python and uv

Verify that `uv` is available:

```bash
uv --version
```

### OpenAI API Access

An OpenAI API key is required for the OpenAI examples.

Create a `.env` file in the project directory:

```text
OPENAI_API_KEY=your-openai-api-key
```

> **Important:** Never commit `.env` or an API key to source control.

### Ollama

Ollama is required to run the local-model portion of the assignment.

Verify the installation:

```bash
ollama --version
```

---

## 5. Environment Setup

From the `s04-assignment` directory, install/synchronise the project dependencies:

```bash
uv sync
```

The project dependencies are defined in `pyproject.toml` and locked in `uv.lock`.

Commands throughout this project are run through `uv`:

```bash
uv run python <script-name>.py
```

This ensures that the Python interpreter and dependencies from the project environment are used.

---

# Part 1 — Direct LLM API Call

## 6. First API Call

`hello.py` demonstrates a basic direct call to an LLM using the OpenAI Python SDK.

Run:

```bash
uv run python hello.py
```

The script:

1. Loads environment variables from `.env`.
2. Creates an OpenAI client.
3. Sends a user message to `gpt-5-mini`.
4. Receives the generated response.
5. Prints the response.
6. Displays input and output token usage.

Conceptually:

```text
Python Application
        │
        ▼
OpenAI Python SDK
        │
        ▼
OpenAI API
        │
        ▼
GPT-5-mini
        │
        ▼
Generated Response
```

This demonstrates the basic interaction underneath an LLM-powered application.

---

# Part 2 — Prompting Techniques

## 7. Prompting Ladder

`prompts.py` demonstrates four different prompting approaches.

### Zero-Shot Prompting

Run:

```bash
uv run python prompts.py zero
```

The model receives an instruction and input without examples.

Conceptually:

```text
Instruction + Input
        │
        ▼
       LLM
        │
        ▼
      Output
```

This tests how well the model can interpret and perform the task without additional examples.

---

### Few-Shot Prompting

Run:

```bash
uv run python prompts.py few
```

Few-shot prompting supplies example input/output pairs before the actual request.

Conceptually:

```text
Instruction
    +
Example Input 1
Example Output 1
    +
Example Input 2
Example Output 2
    +
Actual Input
        │
        ▼
       LLM
        │
        ▼
Structured Output
```

The examples act as an implicit specification for expected formatting and behaviour.

---

### Chain-of-Thought Prompting

Run:

```bash
uv run python prompts.py cot
```

This exercise asks the model to reason through a multi-step problem before producing a conclusion.

The experiment also demonstrates the effect that more extensive reasoning can have on generated token counts and response length.

---

### System Prompting

Run:

```bash
uv run python prompts.py system
```

The system prompt defines behavioural constraints such as:

- Required output structure
- Date formatting
- Missing-value handling
- Avoiding unsupported assumptions
- Returning `null` when information is unavailable

This demonstrates how system-level instructions can establish boundaries around model behaviour.

---

# Part 3 — Custom IT Support Scenario

## 8. Scenario Adaptation

The original insurance extraction exercise was adapted to a fictional **IT support / Power BI dashboard incident** scenario.

The model extracts the following fields:

```text
requester name
dashboard name
incident date
environment
error message
business purpose
```

The test intentionally leaves some information out of the source text.

For example:

```text
environment
business purpose
```

may not be provided.

The system prompt explicitly instructs the model to return:

```text
null
```

rather than infer or invent missing information.

This demonstrates an important production AI principle:

> A model should be told not only what successful output looks like, but also how to behave when the required information is unavailable.

The actual outputs and observations from this experiment are documented in [`FINDINGS.md`](FINDINGS.md).

---

# Part 4 — Model and Provider Swapping

## 9. Provider Abstraction

`swap.py` demonstrates how the same application logic can work with different LLM providers.

Two configurations are tested:

### OpenAI

```text
Provider: OpenAI
Model: gpt-5-mini
Execution: Cloud
```

### Ollama

```text
Provider: Ollama
Model: qwen3:8b
Execution: Local
```

The core application request remains the same.

Only provider-specific configuration changes, including:

```text
API endpoint
API key/configuration
model name
```

Conceptually:

```text
                 Python Application
                         │
                         ▼
                 Provider Configuration
                    /             \
                   /               \
                  ▼                 ▼
              OpenAI              Ollama
                │                    │
                ▼                    ▼
          GPT-5-mini             Qwen3:8b
             Cloud                 Local
```

This demonstrates the architectural principle that the model/provider can be treated as configuration rather than being tightly coupled throughout the application.

---

## 10. Installing the Local Model

To run the local-model example, download Qwen3:8b through Ollama:

```bash
ollama pull qwen3:8b
```

Verify installed models:

```bash
ollama list
```

The local model is then available through Ollama's local API.

---

## 11. Running the Provider Comparison

### OpenAI

```bash
uv run python swap.py openai
```

### Ollama / Qwen

```bash
uv run python swap.py ollama
```

Both commands execute the same extraction task using different underlying models.

The observed outputs and detailed comparison are recorded in [`FINDINGS.md`](FINDINGS.md).

---

# 12. Cloud vs Local Model Considerations

The exercise highlights several architectural trade-offs.

| Consideration | OpenAI / GPT-5-mini | Ollama / Qwen3:8b |
|---|---|---|
| Hosting | Cloud | Local |
| API usage | Paid | No external API charge |
| Internet requirement | Required | Not required for inference after setup |
| Data processing | Cloud API | Local machine |
| Hardware dependency | Provider-managed | Local hardware |
| Model management | Provider-managed | Locally managed |
| Application integration | OpenAI SDK | OpenAI-compatible Ollama endpoint |

The actual experiment showed that both models handled the simple structured extraction task successfully, although their response speed and formatting differed.

See [`FINDINGS.md`](FINDINGS.md) for the recorded comparison.

---

# 13. Key Architectural Takeaways

This assignment demonstrated several concepts relevant to AI solution architecture.

### Prompt Design Is Part of Application Design

Changing the prompt can significantly change:

- Output format
- Consistency
- Reasoning depth
- Token usage
- Latency
- Cost

Prompt design therefore needs to be treated as an engineering concern rather than only as natural-language instructions.

### Missing Data Behaviour Should Be Explicit

Models should not be expected to automatically know when inference is undesirable.

Explicit instructions such as:

```text
If a field is not present, output null.
Never infer, assume, or invent missing information.
```

can provide clearer behavioural boundaries.

### Few-Shot Examples Can Act as Specifications

Providing examples can help communicate:

- Expected field names
- Formatting
- Date conventions
- Value representation

without retraining the underlying model.

### Token Usage Matters

Different prompting strategies can produce significantly different input and output token counts.

This affects:

- Cost
- Response time
- Scalability

and should therefore be considered when designing production AI solutions.

### Models Should Not Be Tightly Coupled to Application Logic

The model-swapping exercise demonstrated that application logic can remain largely unchanged while the underlying model/provider changes.

This provides flexibility to select models based on requirements such as:

- Accuracy
- Latency
- Cost
- Data residency
- Privacy
- Local/offline operation
- Model capability

### Model Selection Is Task Dependent

A model that performs well for structured extraction may not necessarily be the best choice for a complex reasoning task.

Model selection should therefore be based on representative evaluation of the actual workload rather than assuming that one model is universally best.

---

# 14. Findings

Detailed outputs from all prompting experiments, token counts, the custom scenario, model comparison, and observations are documented in:

**[`FINDINGS.md`](FINDINGS.md)**

This includes:

- Zero-shot output
- Few-shot output
- Chain-of-thought output
- System-prompt output
- Token usage comparison
- Custom IT support scenario
- Missing-field/null handling
- GPT-5-mini output
- Qwen3:8b output
- Cloud vs local model comparison
- Key findings and observations

---

# 15. Security

API credentials are not stored in the source code.

The OpenAI API key is loaded from:

```text
.env
```

using `python-dotenv`.

The following local resources should not be committed:

```text
.env
.venv/
```

The `.env` file must also not be included in the assignment submission ZIP.

---

# 16. Reproducing the Assignment

A clean environment can reproduce the Python dependencies using:

```bash
uv sync
```

Create the local `.env` file containing:

```text
OPENAI_API_KEY=your-openai-api-key
```

For local model execution, install Ollama and pull:

```bash
ollama pull qwen3:8b
```

Then run the exercises:

```bash
uv run python hello.py

uv run python prompts.py zero
uv run python prompts.py few
uv run python prompts.py cot
uv run python prompts.py system

uv run python swap.py openai
uv run python swap.py ollama
```

---

# 17. Use of Generative AI

ChatGPT was used as a supporting tool to help improve the wording, structure, and presentation of the project documentation. The code was executed by me, and the observations, comparisons, and conclusions documented in this project are based on the actual assignment results and my understanding of the concepts.