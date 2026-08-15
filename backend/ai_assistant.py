
from datetime import date, timedelta
import re


# ==========================================
# AI Assistant - Offline Task Parser
# ==========================================


# ------------------------------------------
# Detect Priority
# ------------------------------------------

def detect_priority(text: str) -> str:
    """
    Detect task priority from natural language.

    High priority:
        urgent, critical, asap, emergency, high priority

    Low priority:
        low priority, low urgency, whenever

    Default:
        Medium
    """

    text_lower = text.lower()

    high_words = [
        "urgent",
        "urgently",
        "critical",
        "asap",
        "emergency",
        "high priority",
        "very important",
    ]

    low_words = [
        "low priority",
        "low urgency",
        "whenever",
        "not urgent",
    ]

    for word in high_words:
        if word in text_lower:
            return "High"

    for word in low_words:
        if word in text_lower:
            return "Low"

    return "Medium"


# ------------------------------------------
# Detect Due Date
# ------------------------------------------

def detect_due_date(text: str):
    """
    Detect simple due-date phrases.

    Supported examples:

        tomorrow
        today
        in 3 days
        in 5 days
        by 2026-04-01
    """

    text_lower = text.lower()

    today = date.today()

    # --------------------------------------
    # Today
    # --------------------------------------

    if "today" in text_lower:
        return today

    # --------------------------------------
    # Tomorrow
    # --------------------------------------

    if "tomorrow" in text_lower:
        return today + timedelta(days=1)

    # --------------------------------------
    # In X days
    # --------------------------------------

    match = re.search(r"in\s+(\d+)\s+days?", text_lower)

    if match:
        number_of_days = int(match.group(1))
        return today + timedelta(days=number_of_days)

    # --------------------------------------
    # YYYY-MM-DD
    # --------------------------------------

    match = re.search(
        r"\b(\d{4})-(\d{2})-(\d{2})\b",
        text
    )

    if match:
        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))

        try:
            return date(year, month, day)

        except ValueError:
            return None

    return None


# ------------------------------------------
# Clean Title
# ------------------------------------------

def clean_title(text: str) -> str:
    """
    Remove common AI parser instructions from the
    beginning/end of the user's sentence.
    """

    title = text.strip()

    # Remove priority words
    priority_patterns = [
        r"\bvery important\b",
        r"\bhigh priority\b",
        r"\blow priority\b",
        r"\blow urgency\b",
        r"\burgent\b",
        r"\burgently\b",
        r"\bcritical\b",
        r"\basap\b",
        r"\bemergency\b",
        r"\bnot urgent\b",
        r"\bwhenever\b",
    ]

    for pattern in priority_patterns:
        title = re.sub(pattern, "", title, flags=re.IGNORECASE)

    # Remove due-date phrases
    title = re.sub(
        r"\bby\s+\d{4}-\d{2}-\d{2}\b",
        "",
        title,
        flags=re.IGNORECASE
    )

    title = re.sub(
        r"\bin\s+\d+\s+days?\b",
        "",
        title,
        flags=re.IGNORECASE
    )

    title = re.sub(
        r"\btomorrow\b",
        "",
        title,
        flags=re.IGNORECASE
    )

    title = re.sub(
        r"\btoday\b",
        "",
        title,
        flags=re.IGNORECASE
    )

    # Remove extra spaces
    title = re.sub(r"\s+", " ", title)

    # Remove unnecessary punctuation
    title = title.strip(" ,.-")

    # Capitalize first letter
    if title:
        title = title[0].upper() + title[1:]

    return title


# ------------------------------------------
# Main AI Parser
# ------------------------------------------

def parse_task(text: str) -> dict:
    """
    Convert natural-language task text into
    structured task information.

    Example:

        Input:
            "Fix authentication urgently by 2026-04-01"

        Output:
            {
                "title": "Fix authentication",
                "priority": "High",
                "due_date": date(2026, 4, 1)
            }
    """

    if not text or not text.strip():
        raise ValueError("Task description cannot be empty.")

    text = text.strip()

    priority = detect_priority(text)

    due_date = detect_due_date(text)

    title = clean_title(text)

    if not title:
        raise ValueError(
            "Could not determine a task title."
        )

    return {
        "title": title,
        "priority": priority,
        "due_date": due_date,
        "description": text,
    }
