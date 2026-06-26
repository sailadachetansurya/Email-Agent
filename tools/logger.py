import time
import json
import os
from pathlib import Path

LOG_DIR = os.environ.get("LOG_DIR", "logs")
LOG_FILE = os.path.join(LOG_DIR, "agent.log")


def _ensure_log_dir():
    Path(LOG_DIR).mkdir(parents=True, exist_ok=True)


def log(Task):
    _ensure_log_dir()
    entry = {
        "timestamp": time.time(),
        "ticket_id": Task.Ticket_id,
        "email_text": Task.email_text,
        "classification": Task.classification,
        "reply": Task.reply,
        "status": Task.status
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def log_raw(message, level="INFO"):
    _ensure_log_dir()
    entry = {
        "timestamp": time.time(),
        "level": level,
        "message": message
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
