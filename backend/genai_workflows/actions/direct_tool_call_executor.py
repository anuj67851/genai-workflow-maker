import logging
from typing import Dict, Any

from .base_executor import BaseActionExecutor
from ..workflow import WorkflowStep

logger = logging.getLogger(__name__)

class DirectToolCallAction(BaseActionExecutor):
    """
    Executes a specific tool from the registry without any LLM-based decision making.
    This is a deterministic, direct function call.
    """

    async def execute(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        target_tool_name = step.target_tool_name
        if not target_tool_name:
            return {"step_id": step.step_id, "success": False, "error": "Direct Tool Call node is missing 'target_tool_name'."}

        tool_func = self.tool_registry.get_tool(target_tool_name)
        if not tool_func:
            return {"step_id": step.step_id, "success": False, "error": f"Tool '{target_tool_name}' not found in the registry."}

        try:
            # Use the robust JSON template filler to prepare the arguments for the tool.
            # The 'data_template' holds the JSON string mapping arguments to workflow variables.
            # e.g., '{ "customer_email": "{input.email}", "problem_description": "{query}" }'
            tool_args = self._fill_json_template(step.data_template, state) if step.data_template else {}

            if not isinstance(tool_args, dict):
                raise ValueError("The resolved 'data_template' must result in a dictionary (JSON object) of arguments.")

            # Execute the tool function with the prepared arguments
            logger.info(f"Executing direct tool call to '{target_tool_name}' with args: {tool_args}")
            tool_result = tool_func(**tool_args)

            return {
                "step_id": step.step_id,
                "success": True,
                "type": "direct_tool_call",
                "output": tool_result
            }

        except ValueError as ve:
            # Catches errors from template filling or argument mismatches
            error_msg = f"Error preparing arguments for tool '{target_tool_name}': {ve}"
            logger.error(f"Step '{step.step_id}': {error_msg}", exc_info=True)
            return {"step_id": step.step_id, "success": False, "error": error_msg}
        except TypeError as te:
            # Catches errors if the wrong arguments are passed to the function
            error_msg = f"Argument mismatch for tool '{target_tool_name}': {te}. Check the data_template."
            logger.error(f"Step '{step.step_id}': {error_msg}", exc_info=True)
            return {"step_id": step.step_id, "success": False, "error": error_msg}
        except Exception as e:
            # Catch-all for any other exceptions during tool execution
            error_msg = f"An unexpected error occurred during execution of tool '{target_tool_name}': {e}"
            logger.error(f"Step '{step.step_id}': {error_msg}", exc_info=True)
            return {"step_id": step.step_id, "success": False, "error": error_msg}