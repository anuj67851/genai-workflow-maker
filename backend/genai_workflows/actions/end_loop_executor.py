import logging
from typing import Dict, Any

from .base_executor import BaseActionExecutor
from ..workflow import WorkflowStep

logger = logging.getLogger(__name__)

class EndLoopAction(BaseActionExecutor):
    """
    A simple executor that signals the end of a single loop iteration.
    """

    async def execute(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        This executor does not perform any action itself. Its sole purpose is to
        return a unique status that the main WorkflowExecutor can intercept.
        This signals that the current sub-graph execution for a loop iteration
        is complete and control should return to the calling StartLoopAction.
        """
        logger.info(f"Reached end of loop iteration at step '{step.step_id}'. Signaling completion of iteration.")

        # The 'output' key can hold the final value from the last step of the loop,
        # which the StartLoopAction can then aggregate. For now, we return a simple message.
        last_step_history = state.get("step_history", [])[-1] if state.get("step_history") else {}
        last_output = last_step_history.get("output", f"Iteration completed at {step.step_id}")

        return {
            "step_id": step.step_id,
            "success": True,
            "status": "loop_iteration_complete",
            "type": "end_loop",
            "output": last_output
        }