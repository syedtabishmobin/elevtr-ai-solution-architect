# Cross-Cloud Scorecard

## Workload being placed

| Item | Definition |
|---|---|
| User and job | An internal research analyst asks policy and public-company questions through a document assistant. |
| Data | Three public company filings and two fictional course policy/FAQ files; no customer, health, payment, or production personal data. |
| Request shape | Interactive retrieval plus one model answer, with a small course evaluation batch. |
| Reliability and security | Ground answers in retrieved files, cite sources, escalate missing information, use identity-based access, and avoid secrets in Git. |
| Scale and latency | Low-volume lab traffic; four measured evaluation calls completed in 142.5 seconds end to end. |

## Four gating checks

| Gate | Azure Global Standard used in this assignment | Azure regional provisioned-throughput alternative | Evidence and decision |
|---|---|---|---|
| Availability | **Pass.** `gpt-5-mini` version `2025-08-07` was GA in the live catalog. The account, project, vector store, toolbox, and hosted agent all provisioned in Australia East. | **Fail today.** No usable Australia East provisioned entitlement for this model was exposed to this subscription. | Hosted Agents list Australia East as supported. The deployed agent reached `active`. [Hosted Agents](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/hosted-agents) |
| Residency | **Fail for sensitive production; accepted for this lab.** The Azure resource is in Australia East, but Global Standard inference may be processed globally. | **Preferred if available.** A regional provisioned deployment is the stronger placement when processing must remain in one geography/region. | Azure distinguishes global, data-zone, and regional deployment processing. The corpus here is public or fictional, so I accepted the lab exception. [Deployment types and regions](https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure-region-availability) |
| Quota | **Pass after adjustment.** Live quota was 500K TPM; the deployment uses 100K TPM and 100 requests/minute. Capacity 10 throttled the second internal model call, while capacity 100 completed all four cases. | **Fail today.** There was no usable provisioned quota for the selected model in Australia East. | Azure quota is scoped by subscription, region, model, and deployment type. [Limits, quotas, and regions](https://learn.microsoft.com/azure/foundry/agents/concepts/limits-quotas-regions) |
| Isolation | **Platform pass; lab configuration accepted.** The project and hosted workload use managed identity. The lab endpoint is public. | **Platform pass.** The production version can combine managed identity, private endpoints, and a provisioned deployment. | Foundry supports network-isolated agent designs, but this non-sensitive lab did not create a virtual network. [Agent networking](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/networking-options) |

## Practical comparison

| Dimension | Global Standard (selected) | Regional provisioned throughput (alternative) |
|---|---|---|
| Commercial model | Consumption/on-demand model; suitable for a small and variable lab workload. | Reserved provisioned capacity; more predictable throughput but a poor fit for four test calls without an existing production commitment. |
| Capacity in this subscription | 500K TPM quota, with 100K TPM allocated to this deployment. | No usable entitlement observed for this model and region. |
| Operational result | Managed file search indexed 5/5 files, hosted agent version 1 became active, and 4/4 evaluation cases passed. | Not deployable here without obtaining capacity or selecting another approved model/region. |
| Main risk | Processing boundary does not meet a strict Australia-only requirement. | Higher fixed capacity commitment and current quota blocker. |
| Best fit | This non-sensitive course lab. | A steady sensitive-production workload after capacity and residency requirements are approved. |

## Placement decision

I selected **Azure AI Foundry Global Standard in Australia East for the lab only**. It was the only path that cleared availability and quota using the signed-in subscription, and it let me use the same Azure managed vector store, toolbox, hosted identity, and agent endpoint. The deciding constraint is **data residency**. I would not place confidential client or regulated Australian data on this exact deployment. Production remains a no-ship until an approved regional/data-zone boundary is available with quota, or the organisation formally accepts the documented processing boundary.
