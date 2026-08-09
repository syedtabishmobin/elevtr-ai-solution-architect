"""Your first direct LLM API call — the thing underneath every chatbot."""

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-5-mini",
    messages=[
        {
            "role": "user",
            "content": "In two sentences: what does an insurance claims assistant do?",
        },
    ],
)

print(response.choices[0].message.content)

u = response.usage
print(f"\n[tokens] in: {u.prompt_tokens} out: {u.completion_tokens}")