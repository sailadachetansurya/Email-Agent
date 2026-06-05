
from time import time


def create_Ticket(Task):
    Ticket_id = "TICKET-" + str(int(time.time()))
    Task.Ticket_id = Ticket_id
    print("Ticket created successfully.")
