import os

from dotenv import load_dotenv
from openai import OpenAI


# Load variables from .env
load_dotenv()

# Read the API key safely
api_key = os.getenv("OPENAI_API_KEY")

# Check that the key exists without printing it
if not api_key:
    raise ValueError("OPENAI_API_KEY is not configured in .env")

print("API key loaded successfully.")

# Create OpenAI client
client = OpenAI(api_key=api_key)

# First API request
response = client.responses.create(
    model="gpt-5-mini",
    input="Say hello to TaskFlow in one short sentence."
)

print("AI response:")
print(response.output_text)
