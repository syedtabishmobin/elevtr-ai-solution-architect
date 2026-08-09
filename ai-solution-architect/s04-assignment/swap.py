"""Same code, different model/provider.

Run:
    uv run python swap.py openai
    uv run python swap.py ollama
"""
import sys
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

PROVIDERS = {
    "openai": {
        "model": "gpt-5-mini",
    },

    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama",
        "model": "qwen3:8b",
    },
}

choice = sys.argv[1] if len(sys.argv) > 1 else "openai"
cfg = PROVIDERS[choice]

client = OpenAI(
    base_url=cfg.get("base_url"),
    api_key=cfg.get("api_key") or None,
)

response = client.chat.completions.create(
    model=cfg["model"],
    messages=[
        {
            "role": "system",
            "content": (
                "You are an IT support ticket intake assistant. "
                "Extract exactly the requested fields, one per line as "
                "'field: value'. Dates must be YYYY-MM-DD. "
                "If a field is not present, output null. "
                "Never infer, assume, or invent missing information."
            ),
        },
        {
            "role": "user",
            "content": (
                "Extract requester name, dashboard name, incident date, "
                "environment, error message, and business purpose:\n\n"
                "From: Emma Lee\n"
                "Subject: Customer Analytics dashboard issue\n\n"
                "Hi Support,\n\n"
                "The Customer Analytics dashboard stopped refreshing "
                "on 9 August 2026. "
                "The error message says \"Gateway connection unavailable\".\n\n"
                "Please investigate.\n\n"
                "Thanks,\n"
                "Emma Lee"
            ),
        },
    ],
)

print(f"--- {choice} / {cfg['model']} ---")
print(response.choices[0].message.content)