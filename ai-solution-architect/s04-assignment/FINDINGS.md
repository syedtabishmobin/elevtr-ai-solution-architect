# Technique Outputs

## Zero-Shot Prompting

### Model Output

```text
=== zero — messages sent ===
[user] Extract the policyholder name, policy number, incident date, claim type, and amount from t...

=== zero — model output ===
{
  "policyholder_name": "Priya Nair",
  "policy_number": "AC-99841",
  "incident_date": "12 July 2026",
  "claim_type": "Car accident (rear-ended)",
  "amount": "S$8,200"
}
```

**Token Usage**
- Input: 109
- Output: 197

---

## Few-Shot Prompting

### Model Output

```text
=== few — messages sent ===
[user] Extract the policyholder name, policy number, incident date, claim type, and amount from t...
[assistant] policyholder_name: Tan Wei Ming
policy_number: AC-55102
incident_date: 2026-06-03
claim_ty...
[user] Extract the policyholder name, policy number, incident date, claim type, and amount from t...
[assistant] policyholder_name: Aisha Rahman
policy_number: HP-20331
incident_date: 2026-05-21
claim_ty...
[user] Extract the policyholder name, policy number, incident date, claim type, and amount from t...

=== few — model output ===
policyholder_name: Priya Nair
policy_number: AC-99841
incident_date: 2026-07-12
claim_type: auto
amount: 8200
```

**Token Usage**
- Input: 321
- Output: 175

---

## Chain-of-Thought Prompting

### Model Output

```text
=== cot — messages sent ===
[user] A member booked a non-emergency knee MRI costing $650, scheduled 3 days from now. No pre-a...

=== cot — model output ===
Step-by-step reasoning

1) Policy trigger: Policy HP-2026 requires pre-authorization for imaging costing over $500.  
   - The MRI costs $650, so a pre-authorization is required.

2) Current status vs. timing: The MRI is scheduled in 3 days and no pre-auth has been submitted.  
   - Standard (non-urgent) pre-auth decisions take 5 business days — too long to meet the appointment.  
   - The insurer’s urgent turnaround is 24 hours, which could produce a decision before the scheduled MRI if an urgent review is requested and accepted.

3) Risk to the claim: Because no pre-auth was obtained and the service exceeds the $500 threshold, the claim is at material risk of denial and the member could be held financially responsible if the insurer enforces the pre-auth requirement. An urgent pre-auth could avoid denial if approved; if not approved or if urgent review is not granted, risk remains high.

4) Immediate actions the member should take (order matters):
   a. Ask the ordering provider to submit a pre-authorization immediately and request that it be filed as an urgent/expedited review because the service is scheduled within 72 hours. Providers usually must submit clinical justification (order, notes, CPT code, reason for urgency).  
   b. Call the insurer’s pre-auth/prior-authorization line right away (have member ID, appointment date, CPT 73721/73722 or specific knee MRI CPT ready) and request an urgent review; confirm the criteria for “urgent” and tell them the appointment is in 3 days. Ask for a reference number and expected decision time.  
   c. Provide any additional documentation the insurer requests (clinical notes, imaging indication) immediately.  
   d. If the insurer will not or cannot grant urgent review or denies the request, ask the provider to reschedule the MRI until an approval is obtained to avoid an out-of-pocket denial.  
   e. Keep a record of all calls, names, dates, times, and reference numbers; if a claim is denied later, be prepared to appeal with the documentation that an urgent request was made.

Checklist of items to have ready for urgent submission:
- Member name and ID, DOB  
- Provider name and contact, facility name  
- Scheduled date/time of MRI  
- CPT code for the knee MRI and ICD diagnosis code(s)  
- Clinical notes/order explaining indication and urgency  
- Cost estimate or charge estimate ($650)  
- Request that the review be expedited (24-hour turnaround)

One-line conclusion
Yes — the claim is at significant risk of denial because the $650 MRI requires pre-authorization; immediately have the provider submit an urgent pre-auth request (and/or call the insurer yourself) or postpone the appointment until authorization is obtained.
```

**Token Usage**
- Input: 85
- Output: 1,089

---

## System Prompting

### Model Output

```text
=== system — messages sent ===
[system] You are a claims-intake assistant for a regulated insurer. Extract exactly the fields requ...
[user] Extract the policyholder name, policy number, incident date, claim type, and amount from t...

=== system — model output ===
policyholder name: Marcus
policy number: AC-77215
incident date: null
claim type: someone hit my car in the carpark
amount: 3400
```

**Token Usage**
- Input: 118
- Output: 493

## Technique Comparison

The **chain-of-thought** prompt changed the output the most. Unlike the extraction prompts, it produced a long reasoning response with multiple steps, recommendations, and a conclusion.

This was also clearly reflected in the token usage. The **chain-of-thought** prompt used only `81` input tokens but generated `1,089` output tokens, compared with `197` for **zero-shot**, `175` for **few-shot**, and `493` for the **system prompt**.

The **few-shot** prompt required the most input tokens because it included worked examples, but it produced one of the shortest and most consistently formatted outputs. This showed that examples can improve output structure without requiring a long generated response.

Overall, the results showed that prompting technique affects not only the style and reliability of the output, but also token usage and therefore potential cost and latency.

#

# Part 3 — Custom Prompt: IT Support Ticket

For this exercise, I replaced the insurance claims scenario with a fictional IT support ticket for a Power BI dashboard refresh failure. The fields I wanted to extract were requester name, dashboard name, incident date, environment, error message, and business purpose.

The system-prompt test intentionally omitted the environment and business purpose to check whether the model would leave these values as `null` rather than infer or invent them.

## Custom Input Text

```text
From: Emma Lee
Subject: Customer Analytics dashboard issue

Hi Support,

The Customer Analytics dashboard stopped refreshing on 9 August 2026.
The error message says "Gateway connection unavailable".

Please investigate.

Thanks,
Emma Lee
```

## Adapted Instruction

```text
Extract the requester name, dashboard name, incident date, environment, error message, and business purpose from this support ticket.
```

## System Prompt

```text
You are an IT support ticket intake assistant. Extract exactly the fields requested, one per line as 'field: value'. Dates must be YYYY-MM-DD. Use only information explicitly stated in the ticket. If a field is not present, output null for it. Never infer, assume, or invent a value.
```

## Zero-Shot Prompting

### Model Output

```text
=== zero — messages sent ===
[user] Extract the requester name, dashboard name, incident date, environment, error message, and...

=== zero — model output ===
Requester name: Daniel Wong
Dashboard name: Sales Performance dashboard
Incident date: 8 August 2026 (2026-08-08)
Environment: Production
Error message: "Data source credentials have expired"
Business purpose: Used for weekly management reporting
```

**Token Usage**
- Input: 107
- Output: 189

---

## Few-Shot Prompting

### Model Output

```text
=== few — messages sent ===
[user] Extract the requester name, dashboard name, incident date, environment, error message, and...
[assistant] requester_name: Sarah Lim
dashboard_name: Finance Summary
incident_date: 2026-08-03
enviro...
[user] Extract the requester name, dashboard name, incident date, environment, error message, and...
[assistant] requester_name: Ahmed Khan
dashboard_name: Operations KPI
incident_date: 2026-08-05
enviro...
[user] Extract the requester name, dashboard name, incident date, environment, error message, and...

=== few — model output ===
requester_name: Daniel Wong
dashboard_name: Sales Performance
incident_date: 2026-08-08
environment: production
error_message: Data source credentials have expired
business_purpose: weekly management reporting
```

**Token Usage**
- Input: 346
- Output: 181

---

## Chain-of-Thought Prompting

### Model Output

```text
=== cot — messages sent ===
[user] A production Power BI dashboard used for daily executive reporting failed to refresh this ...

=== cot — model output ===
Step-by-step thinking and actions

1) Triage (0–10 min)
- Confirm the cause in Power BI: open the dataset’s Refresh History and error details to verify “data source credentials expired.”
- Identify which credential expired (which datasource type, which user/service principal, whether the dataset uses the on-premises gateway or cloud connection).
- Evaluate impact: which visuals/pages depend on that dataset, whether any incremental partitions are still valid, and whether any cached tiles are still current.

2) Immediate remediation (first priority — fastest path to restore)
- If gateway-based: go to the gateway admin (Power BI service → Manage gateways) and update the data source credentials there.
- If cloud connection: go to the dataset settings (Power BI service → Datasets → Data source credentials) and re-authenticate the connector (enter new password or re-authorize OAuth).
- If the expired identity is an Azure AD user/password, reset or re-enter the updated password or re-grant consent. If it’s a service principal/secret, rotate the secret and update it in Power BI.
- After updating credentials, start an on-demand refresh and watch the refresh logs.

3) If the refresh will not complete before the deadline (workaround)
- Produce a manual snapshot of required metrics from the source system (SQL query export, BI query, or last-successful extract) and assemble the executive report (Excel, PDF, PPT).
- Alternatively export the last successful Power BI report/dashboard pages (cached tiles or .pbix if available) and send as interim deliverable, with a clear note that data is stale or partial.
- Prioritize the key executive numbers/visuals — it’s better to deliver a small set of correct/justified figures than the full dashboard late.

4) Communication (immediate)
- Notify the report owner and executives immediately: state the issue, expected time to fix or ETA for interim report, and what interim deliverable they will receive (with data currency explicitly stated).
- Escalate internally to the on-call DBA/infra owner if access to the source system is required to reset credentials.

5) Verify and close (after remediation)
- Confirm the scheduled refreshs run successfully for a few cycles and that all visuals reflect expected data.
- Record the incident: what expired, why it wasn’t detected, who took action, how long it took, and what interim data was delivered.

6) Remediation / prevention (post-incident)
- Implement credential-expiry monitoring/alerts (Azure AD alerts, calendar reminders, Key Vault notifications).
- Where possible use non-expiring service principals with certificate-based auth or managed identities and integrate secrets with Azure Key Vault for automated rotation.
- Configure the on-prem gateway and Power BI connectors to use service accounts that follow rotation/runbook procedures rather than personal accounts.
- Add automated synthetic refresh checks and alerting (if refresh fails, page the support team before next scheduled run).
- Update runbooks with step-by-step instructions for updating credentials, performing an emergency manual extract, and notifying stakeholders.

Risk assessment (concise)
- Business/reputational risk: High — executives may make decisions on stale or missing data; missing/delayed report harms credibility.
- Operational risk: Medium — manual work and potential for errors in interim reports.
- Security risk: Low-to-medium depending on workaround (e.g., if team shares accounts or exposes credentials in email).
- SLA/regulatory risk: depends on contractual/regulatory requirements for timeliness/accuracy.

One-line conclusion
Risk is high (delayed or stale executive reporting with reputational/decision-making impact); immediately update the expired credentials in Power BI/Gateway (or extract and send a manual snapshot if refresh can’t finish within 2 hours), notify stakeholders with an ETA, then harden credential management and monitoring to prevent recurrence.
```

**Token Usage**
- Input: 64
- Output: 1,872

---

## System Prompting

The system-prompt input deliberately did not provide an environment or business purpose.

### Model Output

```text
=== system — messages sent ===
[system] You are an IT support ticket intake assistant. Extract exactly the fields requested, one p...
[user] Extract the requester name, dashboard name, incident date, environment, error message, and...

=== system — model output ===
requester name: Emma Lee
dashboard name: Customer Analytics dashboard
incident date: 2026-08-09
environment: null
error message: Gateway connection unavailable
business purpose: null
```

**Token Usage**
- Input: 142
- Output: 433

## Observation

The system prompt successfully handled the missing information without making assumptions. Both `environment` and `business purpose` were absent from the source ticket, and the model returned:

```text
environment: null
business purpose: null
```

I did not run the same incomplete ticket without the system prompt, so I cannot claim a direct before/after comparison. However, with the tightened system prompt, the model correctly returned `null` for both missing fields rather than inferring values.

This demonstrates that explicitly defining how the model should handle missing information can prevent it from filling gaps with inferred or invented values.

#

# Part 4 — Swap the Model

For this part, I ran the same IT support ticket extraction task against two different models/providers:

- **OpenAI:** `gpt-5-mini`
- **Ollama:** `qwen3:8b` running locally

The prompt and application logic remained the same. Only the provider configuration and model were changed.

## OpenAI — GPT-5-mini

### Model Output

```text
-- openai / gpt-5-mini ---
requester name: Emma Lee
dashboard name: Customer Analytics
incident date: 2026-08-09
environment: null
error message: Gateway connection unavailable
business purpose: null
```

### Observation

**GPT-5-mini** returned the response almost immediately. It correctly extracted all the available information and returned `null` for both missing fields.

The output was concise and followed the requested structure, although the field names contained spaces rather than underscores.

---

## Ollama — Qwen3:8b

### Model Output

```text
--- ollama / qwen3:8b ---
requester_name: Emma Lee
dashboard_name: Customer Analytics dashboard
incident_date: 2026-08-09
environment: null
error_message: Gateway connection unavailable
business_purpose: null
```

### Observation

**Qwen3:8b** also correctly extracted all the available information and returned `null` for both missing fields. It took noticeably longer to generate the response compared with **GPT-5-mini**.

Its output followed the requested structure well and used consistent underscore-based field names. It included the word `dashboard` in the dashboard name, whereas **GPT-5-mini** returned only `Customer Analytics`.

---

## Model Comparison

| **Factor** | **OpenAI — GPT-5-mini** | **Ollama — Qwen3:8b** |
|---|---|---|
| **Provider** | OpenAI | Ollama |
| **Execution** | Cloud | Local Mac |
| **Model** | `gpt-5-mini` | `qwen3:8b` |
| **Speed** | Very fast; response returned almost immediately | Noticeably slower |
| **Extraction accuracy** | Correct | Correct |
| **Missing-field handling** | Correctly returned `null` | Correctly returned `null` |
| **Output format** | Clean, but field names used spaces | Clean and consistently used underscores |
| **Dashboard name** | `Customer Analytics` | `Customer Analytics dashboard` |
| **Overall quality for this task** | Very good | Very good |
| **API cost** | Paid API usage | No API charge for local inference |
| **Internet dependency** | Requires access to OpenAI API | Runs locally after the model is downloaded |
| **Data processing location** | Processed through OpenAI's cloud API | Processed locally through Ollama |
| **Application code change** | Provider/model configuration only | Provider/model configuration only |

## Key Findings

Both models successfully completed this relatively simple structured extraction task. They identified the same information and, importantly, both followed the instruction not to invent missing values. The `environment` and `business purpose` fields were returned as `null` by both models.

The most noticeable difference was response speed. **GPT-5-mini** returned almost immediately, while the locally running **Qwen3:8b** took noticeably longer. There were also small formatting differences. **Qwen3:8b** followed the underscore-based field naming more consistently, while **GPT-5-mini** used spaces in the field names.

For this particular extraction task, both models produced good-quality results. If speed were the main consideration, I would choose **GPT-5-mini** based on this test. However, **Qwen3:8b** could be preferable where local processing, avoiding API costs, or keeping data within the local environment is more important.

For a harder task involving more complex reasoning, I would test the candidate models against representative examples before making the decision. A model that performs well on simple extraction may not necessarily provide the same accuracy or reasoning quality on a more complex task.

The main architectural takeaway from this exercise is that the model can be treated as configuration rather than being tightly coupled to the application. The same application logic and prompt were used with both providers, while only the model and provider configuration changed.

#

## Use of Generative AI

ChatGPT was used as a supporting tool to help improve the wording, structure, and presentation of this document. The scenarios, code execution, observations, comparisons, and conclusions are based on my own work and the actual outputs generated during the assignment. The final content was reviewed and adjusted by me to reflect my own understanding and reasoning.