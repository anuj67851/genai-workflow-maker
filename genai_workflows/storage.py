import sqlite3
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from .workflow import Workflow, WorkflowStep

class WorkflowStorage:
    """SQLite storage for workflows."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                         CREATE TABLE IF NOT EXISTS workflows (
                                                                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                                  name TEXT NOT NULL UNIQUE,
                                                                  description TEXT,
                                                                  owner TEXT DEFAULT 'default',
                                                                  triggers TEXT,         -- JSON array of strings
                                                                  steps TEXT,            -- JSON blob of the steps dictionary
                                                                  raw_definition TEXT,
                                                                  start_step_id TEXT,    -- The entry point of the workflow
                                                                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                                                  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                         )
                         """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_workflows_owner ON workflows(owner)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_workflows_name ON workflows(name)")

    def save_workflow(self, workflow: Workflow) -> int:
        """Saves or updates a workflow and returns its ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()

            steps_json = json.dumps({step_id: step.to_dict() for step_id, step in workflow.steps.items()})
            triggers_json = json.dumps(workflow.triggers)

            cursor.execute("""
                           INSERT INTO workflows (name, description, owner, triggers, steps, raw_definition, start_step_id, created_at, updated_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                               ON CONFLICT(name) DO UPDATE SET
                               description=excluded.description,
                                                        owner=excluded.owner,
                                                        triggers=excluded.triggers,
                                                        steps=excluded.steps,
                                                        raw_definition=excluded.raw_definition,
                                                        start_step_id=excluded.start_step_id,
                                                        updated_at=excluded.updated_at
                           """, (
                               workflow.name, workflow.description, workflow.owner, triggers_json, steps_json,
                               workflow.raw_definition, workflow.start_step_id, now, now
                           ))
            return cursor.lastrowid

    def get_workflow(self, workflow_id: int) -> Optional[Workflow]:
        """Gets a workflow by its primary ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM workflows WHERE id = ?", (workflow_id,))
            row = cursor.fetchone()
            return self._row_to_workflow(row) if row else None

    def get_all_workflows(self) -> List[Workflow]:
        """Gets all workflows from the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM workflows ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [self._row_to_workflow(row) for row in rows]

    def list_workflows(self) -> List[Dict[str, Any]]:
        """Lists workflows with basic info."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, description, owner, created_at FROM workflows ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def delete_workflow(self, workflow_id: int) -> bool:
        """Deletes a workflow by its ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM workflows WHERE id = ?", (workflow_id,))
            return cursor.rowcount > 0

    def _row_to_workflow(self, row: sqlite3.Row) -> Workflow:
        """Converts a database row into a Workflow object."""
        workflow_data = dict(row)
        # Deserialize JSON fields
        workflow_data["triggers"] = json.loads(row["triggers"]) if row["triggers"] else []

        # Reconstruct the steps dictionary in the workflow_data
        workflow_data["steps"] = json.loads(row["steps"]) if row["steps"] else {}

        return Workflow.from_dict(workflow_data)