import queue
import threading
import time
import traceback
from my_agents import classifier_agent, reply_agent
from my_agents.audit_agent import AuditAgent
from memory.sqlite_store import DataBase
from models.schemas import EmailTask
from models.states import TaskState
from tools import logger
from tools.ticket_manager import create_Ticket
from tools.output_writer import save_result, start_job, end_job
from tools.metrics import track
from workflows.config import WORKFLOW_DB

MAX_WORKERS = 4
LLM_LOCK = threading.Lock()


def _process_one(email_text, idx, total, results, counter_lock, completed, cancel_event):
    if cancel_event.is_set():
        return

    db = DataBase(WORKFLOW_DB)
    try:
        task = EmailTask(email_text)
        task.db = db
        audit = AuditAgent(db)

        create_Ticket(task)
        audit.log_action(task.Ticket_id, "workflow_started")

        with LLM_LOCK:
            if cancel_event.is_set():
                return
            with track("classify"):
                task.classification = classifier_agent.classify(task.email_text)
        task.status = TaskState.CLASSIFIED
        audit.log_action(task.Ticket_id, "classified", {"classification": task.classification})
        DataBase.save_workflow_state(task.db, task.Ticket_id, task.to_dict())

        if cancel_event.is_set():
            return

        if task.classification == "urgent":
            task.reply = "no reply waiting for human response"
            task.status = TaskState.AWAITING_HUMAN
            audit.log_action(task.Ticket_id, "awaiting_human")
            DataBase.save_workflow_state(task.db, task.Ticket_id, task.to_dict())
        else:
            with LLM_LOCK:
                if cancel_event.is_set():
                    return
                with track("reply"):
                    task.reply = reply_agent.generate_reply(task.email_text)
            task.status = TaskState.COMPLETED
            audit.log_action(task.Ticket_id, "reply_generated")
            DataBase.save_workflow_state(task.db, task.Ticket_id, task.to_dict())

        save_result(task.email_text, task.classification, task.reply, task.Ticket_id)

        logger.log(task)
        task.status = TaskState.LOGGED
        audit.log_action(task.Ticket_id, "workflow_completed")
        DataBase.save_workflow_state(task.db, task.Ticket_id, task.to_dict())

        results[idx] = task.to_dict()
    except Exception as e:
        results[idx] = {"email": email_text, "error": str(e)}
        if 'task' in locals():
            try:
                task.status = TaskState.FAILED
                task.reply = f"Error: {str(e)}"
                audit.log_action(task.Ticket_id, "failed", {"error": str(e)})
                DataBase.save_workflow_state(task.db, task.Ticket_id, task.to_dict())
            except Exception:
                pass
    finally:
        db.conn.close()
        with counter_lock:
            completed[0] += 1


def process_batch_sync(emails, on_progress=None, cancel_event=None):
    if isinstance(emails, str):
        emails = [emails]

    if cancel_event is None:
        cancel_event = threading.Event()

    total = len(emails)
    results = [None] * total
    counter_lock = threading.Lock()
    completed = [0]

    job_file = start_job()

    task_queue = queue.Queue()
    for i, email in enumerate(emails):
        task_queue.put((i, email))

    def worker():
        while not cancel_event.is_set():
            try:
                idx, email = task_queue.get(timeout=0.1)
            except queue.Empty:
                break
            _process_one(email, idx, total, results, counter_lock, completed, cancel_event)
            task_queue.task_done()
            if on_progress:
                with counter_lock:
                    on_progress(completed[0], total)

    threads = []
    for _ in range(min(MAX_WORKERS, total)):
        t = threading.Thread(target=worker, daemon=True)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    end_job()

    output = []
    for i, r in enumerate(results):
        if r is None:
            output.append({"email": emails[i], "error": "cancelled"})
        else:
            output.append(r)

    return output, job_file
