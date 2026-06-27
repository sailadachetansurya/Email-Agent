from models.states import TaskState


class EmailTask:

    def __init__(self, email_text: str):
        self.email_text = email_text
        self.classification = None
        self.reply = "None"
        self._status = TaskState.PENDING
        self.Ticket_id = None
        self.db = None

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        if isinstance(value, str):
            try:
                self._status = TaskState(value)
            except ValueError:
                self._status = value
        else:
            self._status = value

    @property
    def status_str(self):
        return self._status.value if isinstance(self._status, TaskState) else self._status

    def to_dict(self):
        return {
            'email_text': self.email_text,
            'classification': self.classification,
            'reply': self.reply,
            'status': self.status_str,
            'Ticket_id': self.Ticket_id
        }

    @classmethod
    def from_dict(cls, data):
        email_task = cls(email_text=data['email_text'])
        email_task.classification = data.get('classification')
        email_task.reply = data.get('reply')
        email_task.status = data.get('status', 'pending')
        email_task.Ticket_id = data.get('Ticket_id')
        return email_task
