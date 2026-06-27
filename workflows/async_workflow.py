import asyncio
import traceback
from concurrent.futures import ThreadPoolExecutor
from my_agents import classifier_agent, reply_agent
from my_agents.audit_agent import AuditAgent
from memory.sqlite_store import DataBase
from models.schemas import EmailTask
from models.states import TaskState
from tools import logger
from tools.ticket_manager import create_Ticket
from tools.output_writer import save_result, start_job, end_job
from tools.metrics import track

executor = ThreadPoolExecutor(max_workers=4)


async def process_single_email(email_text):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, _process_sync, email_text)


def _process_sync(email_text):
    db = DataBase("workflow.db")
    try:
        with track("classify"):
            task = EmailTask(email_text)
            task.db = db
            audit = AuditAgent(db)

            create_Ticket(task)
            audit.log_action(task.Ticket_id, "workflow_started")

            task.classification = classifier_agent.classify(task.email_text)
            task.status = TaskState.CLASSIFIED
            audit.log_action(task.Ticket_id, "classified", {"classification": task.classification})
            DataBase.save_workflow_state(task.db, task.Ticket_id, task.to_dict())

        with track("reply"):
            if task.classification == "urgent":
                task.reply = "no reply waiting for human response"
                task.status = TaskState.AWAITING_HUMAN
                audit.log_action(task.Ticket_id, "awaiting_human")
                DataBase.save_workflow_state(task.db, task.Ticket_id, task.to_dict())
            else:
                task.reply = reply_agent.generate_reply(task.email_text)
                task.status = TaskState.COMPLETED
                audit.log_action(task.Ticket_id, "reply_generated")
                DataBase.save_workflow_state(task.db, task.Ticket_id, task.to_dict())

        save_result(task.email_text, task.classification, task.reply, task.Ticket_id)

        logger.log(task)
        task.status = TaskState.LOGGED
        audit.log_action(task.Ticket_id, "workflow_completed")
        DataBase.save_workflow_state(task.db, task.Ticket_id, task.to_dict())

        return task.to_dict()
    except Exception as e:
        if 'task' in locals():
            task.status = TaskState.FAILED
            task.reply = f"Error: {str(e)}"
            audit.log_action(task.Ticket_id, "failed", {"error": str(e), "traceback": traceback.format_exc()})
            DataBase.save_workflow_state(task.db, task.Ticket_id, task.to_dict())
        raise
    finally:
        db.conn.close()


async def process_batch(emails):
    if isinstance(emails, str):
        emails = [emails]

    job_file = start_job()
    tasks = [process_single_email(email) for email in emails]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    end_job()

    output = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            output.append({"email": emails[i], "error": str(result)})
        else:
            output.append(result)

    return output, job_file
