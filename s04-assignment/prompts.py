"""The prompting ladder applied to an IT support ticket.

Run:
    uv run python prompts.py zero
    uv run python prompts.py few
    uv run python prompts.py cot
    uv run python prompts.py system
"""
import sys
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()
MODEL = "gpt-5-mini"

SUPPORT_TICKET = """\
From: Daniel Wong
Subject: Power BI dashboard refresh failure

Hi Support,

The Sales Performance dashboard failed to refresh this morning.
The issue started on 8 August 2026 and is affecting the production environment.

The error message says "Data source credentials have expired".
The dashboard is used for the weekly management reporting.

Please investigate this as soon as possible.

Thanks,
Daniel Wong
"""

# Deliberately missing the environment:
TERSE_TICKET = """\
From: Emma Lee
Subject: Customer Analytics dashboard issue

Hi Support,

The Customer Analytics dashboard stopped refreshing on 9 August 2026.
The error message says "Gateway connection unavailable".

Please investigate.

Thanks,
Emma Lee
"""

INSTRUCTION = (
    "Extract the requester name, dashboard name, incident date, environment, "
    "error message, and business purpose from this support ticket."
)

SUPPORT_QUESTION = (
    "A production Power BI dashboard used for daily executive reporting "
    "failed to refresh this morning because its data source credentials "
    "have expired. The next executive report is due in 2 hours. "
    "What is the risk and what should the support team do?"
)

TECHNIQUES = {

    # 1. Zero-shot: ask the model to extract the fields without examples.
    "zero": [
        {
            "role": "user",
            "content": f"{INSTRUCTION}\n\n{SUPPORT_TICKET}",
        },
    ],

    # 2. Few-shot: provide two examples showing the expected output format.
    "few": [
        {
            "role": "user",
            "content": (
                f"{INSTRUCTION}\n\n"
                "From: Sarah Lim\n"
                "Subject: Finance dashboard issue\n\n"
                "The Finance Summary dashboard failed on 3 August 2026 "
                "in the test environment. The error message says "
                "\"Dataset timeout\". The dashboard is used for monthly "
                "finance reporting."
            ),
        },
        {
            "role": "assistant",
            "content": (
                "requester_name: Sarah Lim\n"
                "dashboard_name: Finance Summary\n"
                "incident_date: 2026-08-03\n"
                "environment: test\n"
                "error_message: Dataset timeout\n"
                "business_purpose: monthly finance reporting"
            ),
        },
        {
            "role": "user",
            "content": (
                f"{INSTRUCTION}\n\n"
                "From: Ahmed Khan\n"
                "Subject: Operations dashboard failure\n\n"
                "The Operations KPI dashboard stopped refreshing on "
                "5 August 2026 in the development environment. "
                "The error says \"Gateway offline\". It is used for "
                "daily operations monitoring."
            ),
        },
        {
            "role": "assistant",
            "content": (
                "requester_name: Ahmed Khan\n"
                "dashboard_name: Operations KPI\n"
                "incident_date: 2026-08-05\n"
                "environment: development\n"
                "error_message: Gateway offline\n"
                "business_purpose: daily operations monitoring"
            ),
        },
        {
            "role": "user",
            "content": f"{INSTRUCTION}\n\n{SUPPORT_TICKET}",
        },
    ],

    # 3. Chain-of-thought exercise: reasoning rather than extraction.
    "cot": [
        {
            "role": "user",
            "content": (
                f"{SUPPORT_QUESTION}\n\n"
                "Think step by step, then give a one-line conclusion."
            ),
        },
    ],

    # 4. System prompt: define format and behaviour for missing information.
    "system": [
        {
            "role": "system",
            "content": (
                "You are an IT support ticket intake assistant. "
                "Extract exactly the fields requested, one per line as "
                "'field: value'. Dates must be YYYY-MM-DD. "
                "Use only information explicitly stated in the ticket. "
                "If a field is not present, output null for it. "
                "Never infer, assume, or invent a value."
            ),
        },
        {
            "role": "user",
            "content": f"{INSTRUCTION}\n\n{TERSE_TICKET}",
        },
    ],
}

technique = sys.argv[1] if len(sys.argv) > 1 else "zero"
messages = TECHNIQUES[technique]

print(f"=== {technique} — messages sent ===")
for m in messages:
    print(f"[{m['role']}] {m['content'][:90]}...")

response = client.chat.completions.create(
    model=MODEL,
    messages=messages,
)

print(f"\n=== {technique} — model output ===")
print(response.choices[0].message.content)

u = response.usage
print(f"\n[tokens] in: {u.prompt_tokens} out: {u.completion_tokens}")

# """The prompting ladder from class, runnable one rung at a time.
 
# Run:  uv run python prompts.py zero
#       uv run python prompts.py few
#       uv run python prompts.py cot
#       uv run python prompts.py system
# """
# import sys
# from dotenv import load_dotenv
# from openai import OpenAI
 
# load_dotenv()
# client = OpenAI()
# MODEL = "gpt-5-mini"
 
# CLAIM_EMAIL = """\
# From: Priya Nair <priya.n@example.com>
# Subject: Car accident - need to claim
 
# Hi, I was rear-ended at the Clementi Ave 2 junction on 12 July 2026.
# My policy number is AC-99841. The workshop quoted S$8,200 for the repairs.
# I have the police report and photos of the damage. What do I do next?"""
 
# # This one is DELIBERATELY missing the incident date:
# TERSE_EMAIL = """\
# Hi, someone hit my car in the carpark. Policy AC-77215.
# Workshop says S$3,400. - Marcus"""
 
# INSTRUCTION = ("Extract the policyholder name, policy number, incident date, "
#                "claim type, and amount from this email.")
 
# MRI_QUESTION = ("A member booked a non-emergency knee MRI costing $650, "
#                 "scheduled 3 days from now. No pre-authorization submitted. "
#                 "Policy HP-2026: pre-auth required for imaging over $500; "
#                 "standard decisions take 5 business days; urgent 24 hours. "
#                 "Is the claim at risk, and what should the member do?")
 
# TECHNIQUES = {
#     # 1. Zero-shot: just ask. Watch the format wander.
#     "zero": [
#         {"role": "user", "content": f"{INSTRUCTION}\n\n{CLAIM_EMAIL}"},
#     ],
#     # 2. Few-shot: two worked examples BEFORE the real email.
#     #    The examples ARE the format spec.
#     "few": [
#         {"role": "user", "content": f"{INSTRUCTION}\n\n"
#          "From: Tan Wei Ming\nSubject: Windscreen claim\n\nMy windscreen "
#          "cracked on 3 June 2026. Policy AC-55102. Quote is S$480."},
#         {"role": "assistant", "content":
#          "policyholder_name: Tan Wei Ming\npolicy_number: AC-55102\n"
#          "incident_date: 2026-06-03\nclaim_type: auto\namount: 480"},
#         {"role": "user", "content": f"{INSTRUCTION}\n\n"
#          "From: Aisha Rahman\nSubject: hospital bill\n\nAdmitted overnight "
#          "on 21 May 2026 after a fall. Policy HP-20331. Bill was S$2,150."},
#         {"role": "assistant", "content":
#          "policyholder_name: Aisha Rahman\npolicy_number: HP-20331\n"
#          "incident_date: 2026-05-21\nclaim_type: health\namount: 2150"},
#         {"role": "user", "content": f"{INSTRUCTION}\n\n{CLAIM_EMAIL}"},
#     ],
#     # 3. Chain-of-thought: a multi-step RULE, asked step by step.
#     #    (Note the task changed — reasoning, not extraction.)
#     "cot": [
#         {"role": "user", "content": f"{MRI_QUESTION}\n\n"
#          "Think step by step, then give a one-line conclusion."},
#     ],
#     # 4. System prompt: standing policy on every call — including what to do
#     #    when a field is MISSING (null, never a guess). Tested on Marcus.
#     "system": [
#         {"role": "system", "content":
#          "You are a claims-intake assistant for a regulated insurer. Extract "
#          "exactly the fields requested, one per line as 'field: value'. Dates "
#          "as YYYY-MM-DD, amounts as plain numbers. If a field is not present "
#          "in the email, output null for it - never infer or invent a value."},
#         {"role": "user", "content": f"{INSTRUCTION}\n\n{TERSE_EMAIL}"},
#     ],
# }
 
# technique = sys.argv[1] if len(sys.argv) > 1 else "zero"
# messages = TECHNIQUES[technique]
 
# print(f"=== {technique} — messages sent ===")
# for m in messages:
#     print(f"[{m['role']}] {m['content'][:90]}...")
 
# response = client.chat.completions.create(model=MODEL, messages=messages)
# print(f"\n=== {technique} — model output ===")
# print(response.choices[0].message.content)
# u = response.usage
# print(f"\n[tokens] in: {u.prompt_tokens}  out: {u.completion_tokens}")
