import os
import re
from pathlib import Path

OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "output")


def _ensure_output_dir():
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)


def _sanitize_filename(text, max_len=50):
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'\s+', '_', text.strip())
    return text[:max_len]


def save_result(email_text, classification, reply, ticket_id=None):
    _ensure_output_dir()

    email_part = _sanitize_filename(email_text)
    filename = f"{email_part}-{classification}.txt"
    filepath = os.path.join(OUTPUT_DIR, filename)

    counter = 1
    while os.path.exists(filepath):
        filename = f"{email_part}-{classification}-{counter}.txt"
        filepath = os.path.join(OUTPUT_DIR, filename)
        counter += 1

    content = f"Ticket: {ticket_id or 'N/A'}\n"
    content += f"Classification: {classification}\n"
    content += f"---\n"
    content += f"Email:\n{email_text}\n"
    content += f"---\n"
    content += f"Reply:\n{reply}\n"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath


def list_results():
    _ensure_output_dir()
    files = list(Path(OUTPUT_DIR).glob("*.txt"))
    return sorted(files, key=os.path.getmtime, reverse=True)
