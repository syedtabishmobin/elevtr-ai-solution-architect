# Class 8 Assignment #5 - Findings

## 1. The workload I placed

The user is an internal research analyst asking questions through the same document assistant from S07. The data is three public company filings and two fictional course policy files, so this lab does not contain client or regulated personal data. Each request needs managed retrieval, a grounded answer, and a visible source line; missing information must go to a human instead of being guessed. Traffic is small and interactive rather than a large batch. Identity-based access, reproducible deployment, and a safe production boundary matter more here than maximum throughput.

## 2. Gates before deployment

I ran the four gates before treating Azure as the destination. Availability passed: `gpt-5-mini` version `2025-08-07` was GA, Hosted Agents were supported in Australia East, and the actual account and project provisioned there. Quota also passed, but only after a real correction. The subscription showed 500K TPM for Global Standard. My first 10K TPM deployment completed file search and then throttled the agent's second model call. I raised it to 100K TPM and the final run passed.

Isolation passed as a platform capability. The project and hosted agent use managed identities, and Foundry supports private networking. I did not build a VNet for this public/fictional lab corpus. Residency was the important failure: an Australia East resource using Global Standard does not mean every inference is processed only in Australia. I accepted that for this lab, but not for confidential production data. The detailed comparison and evidence links are in `cross-cloud-scorecard.md`.

## 3. What I ported and what changed

I reused the five S07 documents and all eight existing evaluation questions. I moved document retrieval to an Azure managed vector store, which finished with five files completed and zero failures. I exposed it through a Foundry toolbox and kept the same `flag_for_human` behavior inside the hosted agent.

The client now calls the named managed-agent endpoint instead of constructing the agent locally. The hosted package uses Python 3.13, 0.5 CPU, 1 GiB memory, managed identity, and the Responses protocol. The source was remote-built as `s08-docs-agent` version 1, and I downloaded the deployed code and verified its SHA-256 against the uploaded archive. From Azure resource creation to an active agent took 6 minutes 14 seconds; the hosted deployment operation itself took about 84 seconds.

Two portability details were only visible by running the work. Foundry rejected the optional OpenAI vector-store `description` field, so I changed the create request to the portable name-only form. I also fixed my verification call because `download_code` requires `agent_version` as a keyword argument. Neither issue changed the agent behavior.

## 4. Managed endpoint results

I ran four existing cases through the deployed endpoint: `q01`, `q04`, `q06`, and `q07`. The final run finished in 142.5 seconds and all four passed. I checked both answer content and actual tool activity.

- `q01` retrieved the 70-out-of-100 risk threshold and cited `equity_research_policy.md`.
- `q04` combined the evidence/source/date rule with the prohibition on filling gaps from general knowledge and cited both controlled files.
- `q06` did not invent a support email. Its trace contains both `file_search` and the real `flag_for_human` call, followed by `Sources: none`.
- `q07` selected Apple's 2026 product, services, and total net-sales values (`$78,678`, `$30,739`, and `$109,417` million) and cited the Apple filing rather than copying the adjacent 2025 values.

The first evaluation was not hidden. At 10K TPM the search step worked, but answer generation was rate-limited. That failed run is why I increased capacity and reran the complete set. The final CSV records four passes and the tool names observed for each response.

## 5. Decision

For this assignment I would ship the **non-sensitive lab** on Azure Global Standard because availability, quota, and the managed-agent workflow were proven with live resources. I would not ship the same placement for sensitive production data.

The deciding constraint is residency, not model quality. My alternative was regional provisioned throughput in the same cloud: it offers a better fixed placement and predictable capacity model, but this subscription had no usable entitlement for the selected model in Australia East and the fixed commitment is not sensible for four evaluation calls. The production path is to obtain an approved regional or data-zone deployment with quota, add private networking, rerun the same gates, and only then allow confidential documents.

Every value in these findings comes from the live Azure deployment or the saved evaluation. There are no assumed pass results or evidence placeholders.
