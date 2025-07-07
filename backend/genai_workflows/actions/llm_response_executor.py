import json
import logging
from typing import Dict, Any

from .base_executor import BaseActionExecutor
from ..workflow import WorkflowStep

logger = logging.getLogger(__name__)

class LlmResponseAction(BaseActionExecutor):
    def execute(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        filled_prompt = self._fill_prompt_template(step.prompt_template, state)
        structured_prompt = f"""
        You are an assistant generating a user-facing response based on the instruction: "{filled_prompt}".
        Synthesize information from the execution history provided below.
        Original user query: "{state.get('query', '')}"

        Execution History:
        ---
        {json.dumps(state.get('step_history', []), indent=2, default=str)}
        ---
        Generate a polite and complete response that directly follows the instruction.
        """
        messages = [{"role": "user", "content": structured_prompt}]
        try:
            response = self.client.chat.completions.create(model="gpt-4o-mini", messages=messages, temperature=0.5)
            llm_output = response.choices[0].message.content
            return {"step_id": step.step_id, "success": True, "type": "llm_response", "output": llm_output}
        except Exception as e:
            logger.error(f"LLM response step '{step.step_id}' failed: {e}", exc_info=True)
            return {"step_id": step.step_id, "success": False, "error": str(e)}