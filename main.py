import asyncio
from llm.client import chat
from memory.sqlite_store import DataBase
from workflows import email_workflow
from workflows.async_workflow import process_batch
from my_agents.agent import Agent


def process_single():
    db = DataBase("workflow.db")
    fake_mail = "Our production server is down. Immediate assistance required."
    email_workflow.process_email(fake_mail, db)


def process_list(emails):
    if isinstance(emails, str):
        emails = [emails]
    results = asyncio.run(process_batch(emails))
    for r in results:
        print(r)


if __name__ == "__main__":
    sample_emails = [
        "Our production server is down. Immediate assistance required.",
        "Could you please approve the budget for the new project?",
        "I would like to request time off next week.",
        "The customer is complaining about delayed delivery.",
        "Please review the attached invoice for payment."
    ]
    process_list(sample_emails)
