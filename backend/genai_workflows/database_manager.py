import sqlite3
import logging
from typing import List, Dict, Any, Tuple

from ..config import settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Handles all database operations for the application's structured data."""

    def __init__(self, db_path: str = settings.DATA_DB_PATH):
        """
        Initializes the DatabaseManager.
        :param db_path: Path to the SQLite database file.
        """
        self.db_path = db_path
        logger.info(f"DatabaseManager initialized for database at: {self.db_path}")

    def _get_connection(self):
        """Creates and returns a new database connection."""
        conn = sqlite3.connect(self.db_path)
        # Use Row factory to get rows as dictionary-like objects
        conn.row_factory = sqlite3.Row
        return conn

    def execute_query(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """
        Executes a SELECT query and returns the results as a list of dictionaries.
        :param query: The SQL SELECT statement to execute.
        :param params: A tuple of parameters to safely bind to the query.
        :return: A list of dictionaries, where each dictionary represents a row.
        """
        logger.info(f"Executing query: {query} with params: {params}")
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()
                # Convert sqlite3.Row objects to standard dictionaries
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Database query failed: {e}", exc_info=True)
            # Re-raise the exception so the caller can handle it
            raise e

    def upsert_data(self, table_name: str, data: Dict[str, Any], primary_key_columns: List[str]):
        """
        Inserts a new row or updates an existing one based on the primary key.
        :param table_name: The name of the table to upsert into.
        :param data: A dictionary where keys are column names and values are the data to be inserted/updated.
        :param primary_key_columns: A list of column names that form the primary key.
        """
        if not primary_key_columns:
            raise ValueError("Primary key columns must be specified for an upsert operation.")

        columns = list(data.keys())
        values_placeholder = ", ".join(["?"] * len(columns))
        columns_str = ", ".join(f'"{c}"' for c in columns)
        pk_str = ", ".join(f'"{c}"' for c in primary_key_columns)

        # Columns to update are all columns that are NOT part of the primary key
        update_columns = [col for col in columns if col not in primary_key_columns]
        update_placeholder = ", ".join([f'"{col}" = excluded."{col}"' for col in update_columns])

        # If there's nothing to update (all keys are PKs), the update clause is empty
        if not update_placeholder:
            # A simple INSERT OR IGNORE is sufficient if there are no non-PK fields to update
            sql = f'INSERT OR IGNORE INTO "{table_name}" ({columns_str}) VALUES ({values_placeholder});'
        else:
            sql = (
                f'INSERT INTO "{table_name}" ({columns_str}) VALUES ({values_placeholder}) '
                f'ON CONFLICT({pk_str}) DO UPDATE SET {update_placeholder};'
            )

        params = tuple(data.values())
        logger.info(f"Executing upsert: {sql} with params: {params}")

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                conn.commit()
                rows_affected = cursor.rowcount
                guaranteed_rows_affected = max(0, rows_affected) if rows_affected is not None else 0

                logger.info(f"Upsert successful for table '{table_name}'. Driver rowcount: {rows_affected}, Guaranteed rows_affected: {guaranteed_rows_affected}")
                return guaranteed_rows_affected
        except sqlite3.Error as e:
            logger.error(f"Database upsert failed: {e}", exc_info=True)
            raise e

    def list_tables_and_schema(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieves a list of all tables and their schemas in the database.
        :return: A dictionary where keys are table names and values are lists of column info.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Get list of tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row['name'] for row in cursor.fetchall()]

            schema_info = {}
            for table_name in tables:
                # Get schema for each table
                cursor.execute(f'PRAGMA table_info("{table_name}");')
                columns = cursor.fetchall()
                schema_info[table_name] = [dict(col) for col in columns]

            return schema_info

    def execute_admin_command(self, sql: str) -> Dict[str, Any]:
        """
        Executes a raw SQL command, intended for admin purposes like CREATE/DROP TABLE.
        Can also return results for SELECT statements.
        :param sql: The raw SQL command to execute.
        :return: A dictionary containing status and results/error message.
        """
        logger.warning(f"Executing admin SQL command: {sql}")
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Use executescript for multi-statement commands
                cursor.executescript(sql)
                conn.commit()

                # Try to fetch results if it was a SELECT-like query
                # This is a bit tricky with executescript, so we'll re-execute the last statement
                # This part is simplified and might not capture all results perfectly, but works for single statements.
                try:
                    # Re-run the command to fetch potential output
                    cursor.execute(sql)
                    rows = cursor.fetchall()
                    return {
                        "status": "success",
                        "message": "Command executed successfully.",
                        "results": [dict(row) for row in rows]
                    }
                except (sqlite3.Error, TypeError):
                    # This will happen on non-SELECT statements (CREATE, INSERT, etc.)
                    return {
                        "status": "success",
                        "message": "Command executed successfully. No results to display.",
                        "results": []
                    }

        except sqlite3.Error as e:
            logger.error(f"Admin SQL command failed: {e}", exc_info=True)
            return {"status": "error", "message": str(e), "results": []}