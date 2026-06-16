import sqlite3
import json 

class DataBase :
    def __init__(self, db_name) :
        self.db_name = db_name
        db_path = db_name
        self.conn = sqlite3.connect(db_path)

    def save_workflow_state(self, workflow_id, state) :
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS workflow_state (
                    workflow_id TEXT PRIMARY KEY,
                    state TEXT
                )
            ''')
            self.conn.execute('''
                INSERT OR REPLACE INTO workflow_state (workflow_id, state)
                VALUES (?, ?)
            ''', (workflow_id, json.dumps(state)))
    def get_workflow_state(self, workflow_id) :
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT state FROM workflow_state WHERE workflow_id = ?
        ''', (workflow_id,))
        result = cursor.fetchone()
        return json.loads(result[0]) if result else None