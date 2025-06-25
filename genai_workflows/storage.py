import sqlite3
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from .workflow import Workflow

class WorkflowStorage:
    """Manages persistent storage for workflows and their execution states using SQLite."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initializes the database schema, creating tables for workflows and execution states."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Table for storing workflow definitions
            cursor.execute("""
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
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_workflows_name ON workflows(name)")

            # ENHANCEMENT: New table to store the state of paused workflows
            cursor.execute("""
                           CREATE TABLE IF NOT EXISTS execution_states (
                                                                           execution_id TEXT PRIMARY KEY, -- A UUID for the execution
                                                                           workflow_id INTEGER NOT NULL,
                                                                           status TEXT NOT NULL,          -- e.g., 'paused', 'completed', 'failed'
                                                                           state_json TEXT NOT NULL,      -- The full execution state as a JSON blob
                                                                           created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                                                           updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                                                           FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE
                               )
                           """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_execution_states_status ON execution_states(status)")
            conn.commit()

    def save_workflow(self, workflow: Workflow) -> int:
        """Saves a new workflow or updates an existing one based on its name.
        Returns the workflow's database ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            steps_json = json.dumps({step_id: step.to_dict() for step_id, step in workflow.steps.items()})
            triggers_json = json.dumps(workflow.triggers)

            # Use INSERT...ON CONFLICT for an atomic upsert operation.
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

            # Retrieve the ID of the inserted or updated workflow to ensure accuracy.
            cursor.execute("SELECT id FROM workflows WHERE name = ?", (workflow.name,))
            workflow_id = cursor.fetchone()[0]
            conn.commit()
            return workflow_id

    def get_workflow(self, workflow_id: int) -> Optional[Workflow]:
        """Retrieves a single workflow by its primary key ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM workflows WHERE id = ?", (workflow_id,))
            row = cursor.fetchone()
            return self._row_to_workflow(row)

    def get_all_workflows(self) -> List[Workflow]:
        """Retrieves all workflows from the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM workflows ORDER BY name ASC")
            rows = cursor.fetchall()
            return [self._row_to_workflow(row) for row in rows]

    def list_workflows(self) -> List[Dict[str, Any]]:
        """Provides a lightweight list of workflows with basic information."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, description, owner, created_at FROM workflows ORDER BY name ASC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def delete_workflow(self, workflow_id: int) -> bool:
        """Deletes a workflow by ID. Cascading delete removes associated execution states."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM workflows WHERE id = ?", (workflow_id,))
            conn.commit()
            return cursor.rowcount > 0

    def _row_to_workflow(self, row: sqlite3.Row) -> Optional[Workflow]:
        """Converts a database row into a fully-formed Workflow object."""
        if not row:
            return None

        workflow_data = dict(row)

        # This ensures that what we pass to Workflow.from_dict is correctly typed.
        workflow_data["triggers"] = json.loads(workflow_data["triggers"]) if workflow_data.get("triggers") else []
        workflow_data["steps"] = json.loads(workflow_data["steps"]) if workflow_data.get("steps") else {}

        return Workflow.from_dict(workflow_data)

    def save_execution_state(self, execution_id: str, workflow_id: int, status: str, state_dict: Dict[str, Any]):
        """Saves or updates the state of a running/paused workflow execution."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            state_json = json.dumps(state_dict, default=str)

            cursor.execute("""
                           INSERT INTO execution_states (execution_id, workflow_id, status, state_json, created_at, updated_at)
                           VALUES (?, ?, ?, ?, ?, ?)
                               ON CONFLICT(execution_id) DO UPDATE SET
                               status=excluded.status,
                                                                state_json=excluded.state_json,
                                                                updated_at=excluded.updated_at
                           """, (execution_id, workflow_id, status, state_json, now, now))
            conn.commit()

    def get_execution_state(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a paused execution state by its ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT state_json FROM execution_states WHERE execution_id = ? AND status = 'paused'", (execution_id,))
            row = cursor.fetchone()
            return json.loads(row[0]) if row else None

    def delete_execution_state(self, execution_id: str) -> bool:
        """Deletes an execution state, typically after completion or failure."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM execution_states WHERE execution_id = ?", (execution_id,))
            conn.commit()
            return cursor.rowcount > 0