import json
import logging
from typing import Dict, Any

from .base_executor import BaseActionExecutor
from ..workflow import WorkflowStep

logger = logging.getLogger(__name__)

class WorkflowCallAction(BaseActionExecutor):
    async def execute(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        """Loads and executes a sub-workflow, then returns its final result."""
        logger.info(f"Executing sub-workflow for step '{step.step_id}'.")
        target_id = step.target_workflow_id
        if not target_id:
            return {"step_id": step.step_id, "success": False, "error": "Step is missing a 'target_workflow_id'."}

        sub_workflow = self.engine.storage.get_workflow(target_id)
        if not sub_workflow:
            return {"step_id": step.step_id, "success": False, "error": f"Sub-workflow with ID {target_id} not found."}

        sub_context = {}
        if step.input_mappings:
            try:
                # This helper now returns a ready-to-use Python dictionary.
                sub_context = self._fill_json_template(step.input_mappings, state)
                logger.info(f"Passing mapped context to sub-workflow: {sub_context}")
            except json.JSONDecodeError as e:
                # This error means the user's template itself is malformed JSON.
                error_msg = f"Invalid JSON structure in 'input_mappings' for step '{step.step_id}': {e}"
                logger.error(error_msg, exc_info=True)
                return {"step_id": step.step_id, "success": False, "error": error_msg}
            except Exception as e:
                error_msg = f"Failed to process 'input_mappings': {e}"
                logger.error(error_msg, exc_info=True)
                return {"step_id": step.step_id, "success": False, "error": error_msg}

        query = sub_context.get("query", state.get("query"))
        result = await self.engine._init_and_run(sub_workflow, query, sub_context)

        if result.get("status") == "completed":
            logger.info(f"Sub-workflow '{sub_workflow.name}' completed successfully.")
            return {"step_id": step.step_id, "success": True, "type": "workflow_call", "output": result.get("response")}

        elif result.get("status") == "awaiting_input":
            error_msg = f"Sub-workflow '{sub_workflow.name}' paused for human input, which is not supported in a sub-call."
            logger.error(error_msg)
            return {"step_id": step.step_id, "success": False, "error": error_msg}

        else: # failed
            error_details = result.get("error", "Sub-workflow failed without a specific error.")
            logger.error(f"Sub-workflow '{sub_workflow.name}' failed: {error_details}")
            return {"step_id": step.step_id, "success": False, "error": f"Sub-workflow failed: {error_details}"}