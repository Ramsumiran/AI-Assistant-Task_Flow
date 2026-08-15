
import os

from dotenv import load_dotenv
from openai import OpenAI


# Load variables from .env
load_dotenv()


# Create OpenRouter client
client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)


def chat_with_ai(message: str) -> str:
    """
    Send a conversational message to the online LLM
    and return its text response.
    """

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b:free",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are TaskFlow AI Assistant. "
                    "You are a friendly, helpful conversational assistant. "
                    "Answer clearly and simply. "
                    "Do not create, update, delete, or modify tasks. "
                    "Only have a conversation with the user."
                )
            },
            {
                "role": "user",
                "content": message
            }
        ]
    )

    return response.choices[0].message.content
