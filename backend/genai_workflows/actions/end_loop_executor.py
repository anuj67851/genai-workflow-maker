import logging
from typing import Dict, Any

from .base_executor import BaseActionExecutor
from ..workflow import WorkflowStep

logger = logging.getLogger(__name__)

class EndLoopAction(BaseActionExecutor):
    """
    A simple executor that signals the end of a single loop iteration
    and passes back a specified value for aggregation.
    """

    async def execute(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determines which value to return from the iteration. If a 'value_to_return'
        template is provided, it resolves it. Otherwise, it defaults to the
        output of the previous step. It then returns the 'loop_iteration_complete'
        status.
        """
        logger.info(f"Reached end of loop iteration at step '{step.step_id}'.")
        if step.value_to_return:
            try:
                # Use the template filler to get the specific value from the state
                iteration_output = self._fill_prompt_template(step.value_to_return, state)
                logger.info(f"EndLoop returning configured value from '{step.value_to_return}'.")
            except Exception as e:
                logger.error(f"Could not resolve 'value_to_return' template '{step.value_to_return}': {e}", exc_info=True)
                iteration_output = {"error": f"Failed to resolve return value: {e}"}
        else:
            # Fallback to the original behavior if no value is specified
            last_history_entry = state.get("step_history", [])[-1] if state.get("step_history") else {}
            iteration_output = last_history_entry.get("output", f"Iteration completed at {step.step_id}")
            logger.info("EndLoop returning output from the previous step as no specific value was configured.")

        return {
            "step_id": step.step_id,
            "success": True,
            "status": "loop_iteration_complete",
            "type": "end_loop",
            "output": iteration_output # This is the value that will be aggregated
        }