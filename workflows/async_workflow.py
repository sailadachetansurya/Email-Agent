import asyncio
from concurrent.futures import ThreadPoolExecutor
from my_agents import classifier_agent, reply_agent
from my_agents.audit_agent import AuditAgent
from memory.sqlite_store import DataBase
from models.schemas import EmailTask
from tools import logger
from tools.ticket_manager import create_Ticket

executor = ThreadPoolExecutor(max_workers=4)


async def process_single_email(email_text, db):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, _process_sync, email_text, db)


def _process_sync(email_text, db):
    task = EmailTask(email_text)
    task.db = db
    audit = AuditAgent(db)

    create_Ticket(task)
    audit.log_action(task.Ticket_id, "workflow_started")

    task.classification = classifier_agent.classify(task.email_text)
    task.status = "classified"
    audit.log_action(task.Ticket_id, "classified", {"classification": task.classification})
    DataBase.save_workflow_state(task.db, task.Ticket_id, task.to_dict())

    if task.classification == "urgent":
        task.reply = "no reply waiting for human response"
        task.status = "awaiting_human_response"
        audit.log_action(task.Ticket_id, "awaiting_human")
        DataBase.save_workflow_state(task.db, task.Ticket_id, task.to_dict())
    else:
        task.reply = reply_agent.generate_reply(task.email_text)
        task.status = "completed"
        audit.log_action(task.Ticket_id, "reply_generated")
        DataBase.save_workflow_state(task.db, task.Ticket_id, task.to_dict())

    logger.log(task)
    task.status = "logged & completed"
    audit.log_action(task.Ticket_id, "workflow_completed")
    DataBase.save_workflow_state(task.db, task.Ticket_id, task.to_dict())

    return task.to_dict()


async def process_batch(emails, db=None):
    if db is None:
        db = DataBase("workflow.db")

    if isinstance(emails, str):
        emails = [emails]

    tasks = [process_single_email(email, db) for email in emails]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    output = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            output.append({"email": emails[i], "error": str(result)})
        else:
            output.append(result)

    return output
