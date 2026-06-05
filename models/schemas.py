class EmailTask:

    def __init__(self, email_text: str):

        self.email_text = email_text
        self.classification = None
        self.reply = None
        self.status = 'pending'
        self.Ticket_id = None