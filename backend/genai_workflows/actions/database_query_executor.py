import logging
import re
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
            # Find all placeholders like {input.var} in the template
            placeholders = re.findall(r'(\{(?:state|context|input|env)\..+?}|\{query})', query_template)

            # Get the values for these placeholders from the state
            params = tuple(self._get_value_from_state(p, state) for p in placeholders)

            # Replace the placeholders in the template with standard SQL '?' placeholders
            sanitized_query = re.sub(r'\{(?:state|context|input|env)\..+?}|\{query}', '?', query_template)

            # Execute the sanitized query with safe parameters
            query_results = self.db_manager.execute_query(sanitized_query, params)

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