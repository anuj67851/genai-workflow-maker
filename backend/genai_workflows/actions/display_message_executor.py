import logging
from typing import Dict, Any

from .base_executor import BaseActionExecutor
from ..workflow import WorkflowStep

logger = logging.getLogger(__name__)

class DisplayMessageAction(BaseActionExecutor):
    """
    An executor that prepares a message for display in the UI's execution log.
    This action is synchronous and does not pause the workflow.
    """

    async def execute(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fills the message template and returns it as the step's output.
        """
        logger.info(f"Executing display_message step '{step.step_id}'.")

        try:
            # Use the existing helper to fill variables into the message template.
            filled_message = self._fill_prompt_template(step.prompt_template, state)

            # Return a standard success result. The 'output' will be stored
            # in the step_history and can be displayed by the frontend.
            return {
                "step_id": step.step_id,
                "success": True,
                "type": "display_message",
                "output": filled_message
            }
        except Exception as e:
            error_msg = f"Failed to fill template for display_message step '{step.step_id}': {e}"
            logger.error(error_msg, exc_info=True)
            return {"step_id": step.step_id, "success": False, "error": error_msg}