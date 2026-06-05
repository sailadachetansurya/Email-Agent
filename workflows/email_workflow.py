from agents import classifier_agent , reply_agent
from models.schemas import EmailTask
from tools import logger
from tools.ticket_manager import create_Ticket

def process_email(email_text):
    task = EmailTask(email_text)

    create_Ticket(task)

    task.classification = classifier_agent.classify(task.email_text)
    task.status = 'classified'

    if task.classification == 'urgent' :
        print("This email is classified as urgent. Immediate attention required.")
        task.reply = 'no reply waiting for human response'
        user_input = input("Do you want to generate a reply for this email? (yes/no): ")
        if user_input.lower() == 'yes':
            task.reply = reply_agent.generate_reply(task.email_text)
            print("Generated Reply: ", task.reply)
            task.status = 'completed'
        else:
            task.status = 'awaiting human response'
    else :
        task.reply = reply_agent.generate_reply(task.email_text)
        print("Generated Reply: ", task.reply)
        task.status = 'completed'
    print("Email to be classified : ", email_text)
    logger.log(task)
    task.status = 'logged & completed'
    print(task.classification)
    