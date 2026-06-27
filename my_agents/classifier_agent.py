
from llm.client import chat


def classify(email_text):
    prompt = f"""Classify this email into EXACTLY one of these three words: low, medium, urgent.

Rules:
- Reply with ONLY the single word: low, medium, or urgent
- Do NOT explain, do NOT add punctuation, do NOT use markdown
- Just one word

Email: {email_text}

Classification:"""
    result = chat(prompt).strip().lower()
    result = result.replace(".", "").replace("!", "").replace("*", "").replace("\n", "").strip()
    for valid in ["urgent", "medium", "low"]:
        if valid in result:
            return valid
    return "medium"