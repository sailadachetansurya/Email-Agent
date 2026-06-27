import os
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "output")
_current_job_file = None


def _ensure_output_dir():
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)


def start_job():
    global _current_job_file
    _ensure_output_dir()
    timestamp = datetime.now().strftime("%d-%m-%y %H-%M-%S")
    filename = f"JOB {timestamp}.txt"
    _current_job_file = os.path.join(OUTPUT_DIR, filename)
    with open(_current_job_file, "w", encoding="utf-8") as f:
        f.write(f"=== JOB: {timestamp} ===\n\n")
    return _current_job_file


def save_result(email_text, classification, reply, ticket_id=None):
    global _current_job_file
    if _current_job_file is None:
        start_job()

    with open(_current_job_file, "a", encoding="utf-8") as f:
        f.write(f"INPUT: {email_text}\n")
        f.write(f"CLASSIFICATION: {classification}\n")
        f.write(f"OUTPUT: {reply}\n")
        f.write(f"---\n\n")

    return _current_job_file


def end_job():
    global _current_job_file
    _current_job_file = None


def list_results():
    _ensure_output_dir()
    files = list(Path(OUTPUT_DIR).glob("JOB *.txt"))
    return sorted(files, key=os.path.getmtime, reverse=True)
