from memory.sqlite_store import DataBase
from workflows import email_workflow

db = DataBase("workflow.db")
if __name__ == "__main__":
    fake_mail = "Our production server is down. Immediate assistance required."
    email_workflow.process_email(fake_mail, db)
