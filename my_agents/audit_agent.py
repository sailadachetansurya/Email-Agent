import json
import time
from tools.hash import hash_string


class AuditAgent:
    def __init__(self, db):
        self.db = db
        self._ensure_table()

    def _ensure_table(self):
        self.db.conn.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id TEXT,
                action TEXT,
                details TEXT,
                timestamp REAL,
                hash TEXT
            )
        ''')
        self.db.conn.commit()

    def log_action(self, ticket_id, action, details=None):
        timestamp = time.time()
        payload = f"{ticket_id}:{action}:{timestamp}"
        entry_hash = hash_string(payload)

        self.db.conn.execute(
            "INSERT INTO audit_log (ticket_id, action, details, timestamp, hash) VALUES (?, ?, ?, ?, ?)",
            (ticket_id, action, json.dumps(details) if details else None, timestamp, entry_hash)
        )
        self.db.conn.commit()
        return entry_hash

    def get_history(self, ticket_id):
        cursor = self.db.conn.execute(
            "SELECT action, details, timestamp, hash FROM audit_log WHERE ticket_id = ? ORDER BY timestamp",
            (ticket_id,)
        )
        return cursor.fetchall()

    def verify_integrity(self, ticket_id):
        rows = self.get_history(ticket_id)
        for action, details, timestamp, stored_hash in rows:
            payload = f"{ticket_id}:{action}:{timestamp}"
            expected = hash_string(payload)
            if expected != stored_hash:
                return False
        return True


def audit(task, action, details=None):
    from memory.sqlite_store import DataBase
    from workflows.config import WORKFLOW_DB
    db = DataBase(WORKFLOW_DB)
    agent = AuditAgent(db)
    agent.log_action(task.Ticket_id, action, details)
