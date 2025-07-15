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
            # 1. Define the core pattern for finding placeholders like {input.var}
            core_placeholder_pattern = r'\{(?:state|context|input|env)\.[a-zA-Z0-9_]+?\}|\{query\}'

            # 2. Find all placeholders to get their corresponding values for the params tuple
            placeholders_to_fill = re.findall(core_placeholder_pattern, query_template)
            params = tuple(self._get_value_from_state(p, state) for p in placeholders_to_fill)

            # 3. Define a new, more robust pattern for substitution.
            # This pattern finds the placeholder AND any surrounding single/double quotes.
            # This is what prevents the ... = '?' error.
            substitution_pattern = rf"['\"]?({core_placeholder_pattern})['\"]?"

            # 4. Replace the full pattern (e.g., '{input.var}') with a single '?'
            sanitized_query = re.sub(substitution_pattern, '?', query_template)

            # 5. Execute the sanitized query with safe parameters
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