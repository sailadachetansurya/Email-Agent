from my_agents import classifier_agent, reply_agent
from my_agents.audit_agent import AuditAgent
from memory.sqlite_store import DataBase
from models.schemas import EmailTask
from tools import logger
from tools.ticket_manager import create_Ticket
from tools.output_writer import save_result


def route_task(task):
    """Route task based on current status to next execution function."""
    match task.status:
        case "pending":
            return _start_workflow
        case "classified":
            return _check_urgent
        case "awaiting_human_response":
            return _awaiting_human_response
        case "completed":
            return _log_task
        case "logged & completed":
            return None
        case _:
            return None


def _start_workflow(task):
    """Start the workflow by creating ticket and classifying."""
    create_Ticket(task)
    audit = AuditAgent(task.db)
    audit.log_action(task.Ticket_id, "workflow_started")
    task.classification = classifier_agent.classify(task.email_text)
    task.status = "classified"
    audit.log_action(task.Ticket_id, "classified", {"classification": task.classification})
    DataBase.save_workflow_state(task.db, task.Ticket_id, task.to_dict())
    return route_task(task)


def _check_urgent(task):
    """Check if email is urgent."""
    audit = AuditAgent(task.db)
    if task.classification == "urgent":
        task.reply = "no reply waiting for human response"
        task.status = "awaiting_human_response"
        audit.log_action(task.Ticket_id, "awaiting_human", {"reason": "urgent classification"})
        DataBase.save_workflow_state(task.db, task.Ticket_id, task.to_dict())
    else:
        task.reply = reply_agent.generate_reply(task.email_text)
        task.status = "completed"
        audit.log_action(task.Ticket_id, "reply_generated")
        DataBase.save_workflow_state(task.db, task.Ticket_id, task.to_dict())
    return route_task(task)


def _awaiting_human_response(task):
    """Resume workflow - this step needs human intervention."""
    return None


def resume_workflow(db, task_dict):
    """Resume a paused workflow from saved state."""
    task = EmailTask.from_dict(task_dict)
    task.db = db
    audit = AuditAgent(db)
    audit.log_action(task.Ticket_id, "workflow_resumed")
    task.reply = reply_agent.generate_reply(task.email_text)
    task.status = "completed"
    audit.log_action(task.Ticket_id, "reply_generated")
    save_result(task.email_text, task.classification, task.reply, task.Ticket_id)
    DataBase.save_workflow_state(db, task.Ticket_id, task.to_dict())
    return route_task(task)


def _log_task(task):
    """Log and complete the task."""
    audit = AuditAgent(task.db)
    logger.log(task)
    task.status = "logged & completed"
    audit.log_action(task.Ticket_id, "workflow_completed")
    DataBase.save_workflow_state(task.db, task.Ticket_id, task.to_dict())


def process_email(email_text, db):
    task = EmailTask(email_text)
    task.db = db

    create_Ticket(task)
    audit = AuditAgent(db)
    audit.log_action(task.Ticket_id, "workflow_started")

    task.classification = classifier_agent.classify(task.email_text)
    task.status = "classified"
    audit.log_action(task.Ticket_id, "classified", {"classification": task.classification})
    DataBase.save_workflow_state(task.db, task.Ticket_id, task.to_dict())

    if task.classification == "urgent":
        task.reply = "no reply waiting for human response"
        task.status = "awaiting_human_response"
        audit.log_action(task.Ticket_id, "awaiting_human", {"reason": "urgent classification"})
        DataBase.save_workflow_state(task.db, task.Ticket_id, task.to_dict())
        save_result(task.email_text, task.classification, task.reply, task.Ticket_id)
        return
    else:
        task.reply = reply_agent.generate_reply(task.email_text)
        task.status = "completed"
        audit.log_action(task.Ticket_id, "reply_generated")
        DataBase.save_workflow_state(task.db, task.Ticket_id, task.to_dict())

    save_result(task.email_text, task.classification, task.reply, task.Ticket_id)

    logger.log(task)
    task.status = "logged & completed"
    audit.log_action(task.Ticket_id, "workflow_completed")
    DataBase.save_workflow_state(task.db, task.Ticket_id, task.to_dict())
