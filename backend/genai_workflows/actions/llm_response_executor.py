import json
import logging
from typing import Dict, Any

from .base_executor import BaseActionExecutor
from ..workflow import WorkflowStep
from ...config import settings

logger = logging.getLogger(__name__)

class LlmResponseAction(BaseActionExecutor):
    async def execute(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # 1. Get the intelligently prepared prompt from our new helper.
            llm_input = self._prepare_llm_input(step, state)
            final_prompt = llm_input["final_prompt"]

            # 2. Make the API call with the optimized prompt.
            messages = [{"role": "user", "content": final_prompt}]
            model = step.model_name or settings.DEFAULT_MODEL
            response = await self.client.chat.completions.create(model=model, messages=messages, temperature=0.5)
            llm_output = response.choices[0].message.content

            return {"step_id": step.step_id, "success": True, "type": "llm_response", "output": llm_output}
        except Exception as e:
            logger.error(f"LLM response step '{step.step_id}' failed: {e}", exc_info=True)
            return {"step_id": step.step_id, "success": False, "error": str(e)}
