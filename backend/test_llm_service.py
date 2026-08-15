
from llm_service import ask_llm


prompt = """
You are the TaskFlow AI Assistant.

A user says:
"Fix authentication urgently by 2026-04-01"

Explain what information you can identify from this request.
Keep your answer short.
"""


answer = ask_llm(prompt)

print("AI response:")
print(answer)