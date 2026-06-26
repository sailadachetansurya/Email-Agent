from my_agents import classifier_agent, reply_agent
from memory.sqlite_store import DataBase
from models.schemas import EmailTask
from tools import logger
from tools.ticket_manager import create_Ticket


def route_task(task):
    """Route task based on current status to next execution function."""
    match task.status:
        case "pending":
            print("Starting workflow...")
            return _start_workflow
        case "classified":
            print("Classification complete, checking if urgent...")
            return _check_urgent
        case "awaiting_human_response":
            print("Resuming workflow - waiting for human input...")
            return _awaiting_human_response
        case "completed":
            print("Task completed, logging...")
            return _log_task
        case "logged & completed":
            print("Task already fully processed.")
            return None  # No further action needed
        case _:
            print(f"Unknown status: {task.status}")
            return None  # Unknown status, no action


def _start_workflow(task):
    """Start the workflow by creating ticket and classifying."""
    create_Ticket(task)
    task.classification = classifier_agent.classify(task.email_text)
    task.status = "classified"
    DataBase.save_workflow_state(task.db, task.Ticket_id, task.to_dict())
    return route_task(task)  # Route to next step


def _check_urgent(task):
    """Check if email is urgent."""
    if task.classification == "urgent":
        print("This email is classified as urgent. Immediate attention required.")
        task.reply = "no reply waiting for human response"
        task.status = "awaiting_human_response"
        DataBase.save_workflow_state(task.db, task.Ticket_id, task.to_dict())
    else:
        print("Email is not urgent, generating reply...")
        task.reply = reply_agent.generate_reply(task.email_text)
        print("Generated Reply: ", task.reply)
        task.status = "completed"
        DataBase.save_workflow_state(task.db, task.Ticket_id, task.to_dict())
    return route_task(task)  # Route to next step


def _awaiting_human_response(task):
    """Resume workflow - this step needs human intervention."""
    print("Workflow paused - awaiting human input to continue.")
    print("Call resume_workflow() to continue processing.")
    return None  # Pauses here, waiting for human to call resume


def resume_workflow(db, task_dict):
    """Resume a paused workflow from saved state."""
    task = EmailTask.from_dict(task_dict)
    task.db = db
    return _awaiting_human_response(task)


def _log_task(task):
    """Log and complete the task."""
    print("Email to be classified : ", task.email_text)
    logger.log(task)
    task.status = "logged & completed"
    DataBase.save_workflow_state(task.db, task.Ticket_id, task.to_dict())


def process_email(email_text, db):
    task = EmailTask(email_text)
    task.db = db  # Set db attribute on task

    create_Ticket(task)

    task.classification = classifier_agent.classify(task.email_text)
    task.status = "classified"
    DataBase.save_workflow_state(task.db, task.Ticket_id, task.to_dict())

    if task.classification == "urgent":
        print("This email is classified as urgent. Immediate attention required.")
        task.reply = "no reply waiting for human response"
        task.status = "awaiting_human_response"
        # Pause workflow: serialize state and save to database
        DataBase.save_workflow_state(task.db, task.Ticket_id, task.to_dict())
        # Safely terminate - workflow can be resumed later
        return
    else:
        task.reply = reply_agent.generate_reply(task.email_text)
        print("Generated Reply: ", task.reply)
        task.status = "completed"
        DataBase.save_workflow_state(task.db, task.Ticket_id, task.to_dict())

    print("Email to be classified : ", task.email_text)
    logger.log(task)
    task.status = "logged & completed"
    DataBase.save_workflow_state(task.db, task.Ticket_id, task.to_dict())

    print(task.classification)
