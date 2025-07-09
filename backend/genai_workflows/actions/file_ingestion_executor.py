from typing import Dict, Any

from .base_executor import BaseActionExecutor
from ..workflow import WorkflowStep

class FileIngestionAction(BaseActionExecutor):
    async def execute(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generates a prompt for file upload and returns a pause signal."""
        prompt_for_user = self._fill_prompt_template(step.prompt_template, state)
        return {
            "status": "awaiting_file_upload",
            "prompt": prompt_for_user,
            "output_key": step.output_key,
            "allowed_file_types": step.allowed_file_types,
            "max_files": step.max_files,
        }