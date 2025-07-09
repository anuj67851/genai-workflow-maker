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

        # Pass the parent's state down as the initial context for the sub-workflow.
        # This makes parent outputs available to the child.
        sub_context = state.get("collected_inputs", {}).copy()
        sub_context["parent_query"] = state.get("query")
        sub_context["parent_execution_id"] = state.get("execution_id")

        # The sub-workflow is started with the parent's original query.
        query = state.get("query")

        # We use the main engine's execution entry point to run the sub-workflow.
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