
import os
import re

from dotenv import load_dotenv
from openai import OpenAI


# Load environment variables from .env
load_dotenv()


# Get OpenRouter API key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


if not OPENROUTER_API_KEY:
    raise ValueError(
        "OPENROUTER_API_KEY is not configured in .env"
    )


# Create OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)


def ask_llm(prompt: str) -> str:
    """
    Send a prompt to the online LLM
    and return the AI's text response.
    """

    response = client.chat.completions.create(
        model="openrouter/free",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content

# ==========================================================
# structured task extraction
# =========================================================

def ask_llm_for_task(prompt: str) -> str:
    """
    Ask the LLM to return structured TaskFlow task data.
    """

    response = client.chat.completions.create(
        model="openrouter/free",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are the TaskFlow AI Assistant. "
                    "Return task information as valid JSON only. "
                    "Do not use markdown code fences."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content

def clean_json_response(response_text: str) -> str:
    """
    Remove Markdown code fences from an LLM JSON response.
    """

    response_text = response_text.strip()

    # Remove ```json at the beginning
    response_text = re.sub(
        r"^```json\s*",
        "",
        response_text,
        flags=re.IGNORECASE
    )

    # Remove ``` at the end
    response_text = re.sub(
        r"\s*```$",
        "",
        response_text
    )

    return response_text.strip()