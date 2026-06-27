import sqlite3
import json


class DataBase:
    def __init__(self, db_name):
        self.db_name = db_name
        db_path = db_name
        self.conn = sqlite3.connect(db_path, timeout=10)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._ensure_tables()

    def _ensure_tables(self):
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS workflow_state (
                workflow_id TEXT PRIMARY KEY,
                state TEXT
            )
        ''')
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                ticket_id TEXT PRIMARY KEY,
                email_text TEXT,
                classification TEXT,
                reply TEXT,
                status TEXT
            )
        ''')
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id TEXT,
                chunk_text TEXT,
                embedding TEXT
            )
        ''')
        self.conn.commit()

    def save_workflow_state(self, workflow_id, state):
        with self.conn:
            self.conn.execute('''
                INSERT OR REPLACE INTO workflow_state (workflow_id, state)
                VALUES (?, ?)
            ''', (workflow_id, json.dumps(state)))
            ticket_id = state.get("Ticket_id")
            if ticket_id:
                self.conn.execute('''
                    INSERT OR REPLACE INTO tasks (ticket_id, email_text, classification, reply, status)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    ticket_id,
                    state.get("email_text"),
                    state.get("classification"),
                    state.get("reply"),
                    state.get("status")
                ))

    def get_workflow_state(self, workflow_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT state FROM workflow_state WHERE workflow_id = ?
        ''', (workflow_id,))
        result = cursor.fetchone()
        return json.loads(result[0]) if result else None

    def create_chunks_table(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_id TEXT,
                    chunk_text TEXT,
                    embedding TEXT
                );
            ''')

    def add_chunk(self, doc_id, chunk_text, embedding):
        self.conn.execute(
            "INSERT INTO chunks (doc_id, chunk_text, embedding) VALUES (?, ?, ?)",
            (doc_id, chunk_text, json.dumps(embedding))
        )
        self.conn.commit()
