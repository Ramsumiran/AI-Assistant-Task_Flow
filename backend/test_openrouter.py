
import os

from dotenv import load_dotenv
from openai import OpenAI


# Load variables from .env
load_dotenv()

# Read OpenRouter API key
api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    raise ValueError("OPENROUTER_API_KEY is not configured in .env")


print("OpenRouter API key loaded successfully.")


# Create OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)


# Send first request
response = client.chat.completions.create(
    model="openrouter/free",
    messages=[
        {
            "role": "user",
            "content":"You are the TaskFlow AI Assistant. Explain in one short sentence what you can help a user with."
        }
    ]

)


print("AI response:")
print(response.choices[0].message.content)