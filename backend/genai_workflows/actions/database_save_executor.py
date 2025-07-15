import logging
from typing import Dict, Any, TYPE_CHECKING

from .base_executor import BaseActionExecutor
from ..workflow import WorkflowStep
from ..database_manager import DatabaseManager

if TYPE_CHECKING:
    from ...tools import ToolRegistry
    from ..core import WorkflowEngine

logger = logging.getLogger(__name__)

class DatabaseSaveAction(BaseActionExecutor):
    """Executes a database upsert operation."""

    def __init__(self, openai_client, tool_registry: 'ToolRegistry', engine: 'WorkflowEngine'):
        super().__init__(openai_client, tool_registry, engine)
        self.db_manager = DatabaseManager()

    async def execute(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Executing database_save step '{step.step_id}'.")

        table_name = step.table_name
        data_template = step.data_template
        pk_columns = step.primary_key_columns

        if not table_name:
            return {"step_id": step.step_id, "success": False, "error": "Database Save node is missing 'table_name'."}
        if not data_template:
            return {"step_id": step.step_id, "success": False, "error": "Database Save node is missing 'data_template'."}
        if not pk_columns:
            return {"step_id": step.step_id, "success": False, "error": "Database Save node is missing 'primary_key_columns'."}

        try:
            # Use the robust JSON template filler to create the data payload
            data_to_save = self._fill_json_template(data_template, state)
            if not isinstance(data_to_save, dict):
                raise ValueError("The resolved 'data_template' must be a dictionary (JSON object).")

            # Perform the upsert operation
            self.db_manager.upsert_data(table_name, data_to_save, pk_columns)

            output_message = f"Successfully saved data to table '{table_name}'."
            return {
                "step_id": step.step_id,
                "success": True,
                "type": "database_save",
                "output": output_message
            }

        except ValueError as ve:
            # Catches errors from template filling
            error_msg = f"Error processing data_template for step '{step.step_id}': {ve}"
            logger.error(error_msg, exc_info=True)
            return {"step_id": step.step_id, "success": False, "error": error_msg}
        except Exception as e:
            # Catches database errors from the manager
            error_msg = f"Database save operation failed for step '{step.step_id}': {e}"
            logger.error(error_msg, exc_info=True)
            return {"step_id": step.step_id, "success": False, "error": error_msg}