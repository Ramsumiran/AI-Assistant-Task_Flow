
import json

from llm_service import ask_llm_for_task, clean_json_response
from models import AIParsedTask

# text = "Fix authentication urgently by 2026-04-01"


# prompt = f"""
# Convert this user request into a task:

# {text}

# Return ONLY valid JSON with exactly these fields:

# {{
#     "title": "string",
#     "description": "string",
#     "priority": "High, Medium, or Low",
#     "due_date": "YYYY-MM-DD or null"
# }}
# """


# ai_response = ask_llm_for_task(prompt)

# print("Raw AI response:")
# print(ai_response)


# # Convert JSON text into Python dictionary
# parsed = json.loads(ai_response)

# print("\nParsed Python dictionary:")
# print(parsed)
import json

from llm_service import ask_llm_for_task
from models import AIParsedTask


text = "Fix authentication urgently by 2026-04-01"


prompt = f"""
Convert this user request into a TaskFlow task.

User request:
{text}

Return ONLY valid JSON.

The JSON must contain exactly these fields:

{{
    "title": "short task title",
    "description": "task description",
    "priority": "High, Medium, or Low",
    "due_date": "YYYY-MM-DD or null"
}}

Priority must be exactly:
High, Medium, or Low.

If no deadline exists, due_date must be null.

Do not add any other fields.
"""


# --------------------------------------
# 1. Ask the online LLM
# --------------------------------------

ai_response = ask_llm_for_task(prompt)

print("Raw AI response:")
print(ai_response)


# --------------------------------------
# 2. Convert JSON text to Python dict
# --------------------------------------
cleaned_response = clean_json_response(ai_response)

print("\nCleaned AI response:")
print(cleaned_response)

parsed = json.loads(cleaned_response)
parsed = json.loads(ai_response)

print("\nParsed Python dictionary:")
print(parsed)


# --------------------------------------
# 3. Validate using Pydantic
# --------------------------------------

validated_task = AIParsedTask.model_validate(parsed)

print("\nValidated Task:")
print(validated_task)


# --------------------------------------
# 4. Show individual values
# --------------------------------------

print("\nTitle:")
print(validated_task.title)

print("\nDescription:")
print(validated_task.description)

print("\nPriority:")
print(validated_task.priority)

print("\nDue date:")
print(validated_task.due_date)