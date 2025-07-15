import logging
from typing import Dict, Any, TYPE_CHECKING

from .base_executor import BaseActionExecutor
from ..workflow import WorkflowStep
from ..database_manager import DatabaseManager

if TYPE_CHECKING:
    from ...tools import ToolRegistry
    from ..core import WorkflowEngine

logger = logging.getLogger(__name__)

class DatabaseQueryAction(BaseActionExecutor):
    """Executes a database SELECT query."""

    def __init__(self, openai_client, tool_registry: 'ToolRegistry', engine: 'WorkflowEngine'):
        super().__init__(openai_client, tool_registry, engine)
        self.db_manager = DatabaseManager()

    async def execute(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Executing database_query step '{step.step_id}'.")

        query_template = step.query_template
        if not query_template:
            return {"step_id": step.step_id, "success": False, "error": "Database Query node is missing 'query_template'."}

        try:
            # Fill the SQL template with values from the state
            # Note: For production systems with untrusted inputs, it's safer to parse
            # the template and pass variables as `params`. For this trusted environment,
            # filling the template is acceptable.
            filled_query = self._fill_prompt_template(query_template, state)

            # Execute the query
            query_results = self.db_manager.execute_query(filled_query)

            logger.info(f"Database query for step '{step.step_id}' returned {len(query_results)} rows.")

            return {
                "step_id": step.step_id,
                "success": True,
                "type": "database_query",
                "output": query_results
            }

        except Exception as e:
            # Catches database errors from the manager
            error_msg = f"Database query operation failed for step '{step.step_id}': {e}"
            logger.error(error_msg, exc_info=True)
            return {"step_id": step.step_id, "success": False, "error": error_msg}