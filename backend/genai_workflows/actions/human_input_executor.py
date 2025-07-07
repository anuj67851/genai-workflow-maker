from typing import Dict, Any
from .base_executor import BaseActionExecutor
from ..workflow import WorkflowStep

class HumanInputAction(BaseActionExecutor):
    def execute(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generates a prompt for the user and returns a pause signal for text input."""
        prompt_for_user = self._fill_prompt_template(step.prompt_template, state)
        return {
            "status": "awaiting_input",
            "prompt": prompt_for_user,
            "output_key": step.output_key
        }