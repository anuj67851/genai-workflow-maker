import json
import logging
import re
from typing import Dict, Any

from .base_executor import BaseActionExecutor
from ..workflow import WorkflowStep

logger = logging.getLogger(__name__)

class ConditionCheckAction(BaseActionExecutor):
    async def execute(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        filled_prompt = self._fill_prompt_template(step.prompt_template, state)
        prompt = f"""
        Analyze the following execution history and context to determine if a specific condition is met.
        **Execution History & Context:**
        ---
        {json.dumps(state, indent=2, default=str)}
        ---
        **Condition to Evaluate:**
        "{filled_prompt}"
        **Your Task:**
        1. Carefully read the history and context.
        2. Evaluate the condition based on the provided information.
        3. Provide your reasoning in a <reasoning> XML tag.
        4. Provide your final answer in a <final_answer> XML tag. The answer must be ONLY the word TRUE or FALSE.
        """
        try:
            response = await self.client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}], temperature=0.0)
            result_text = response.choices[0].message.content
            match = re.search(r'<final_answer>\s*(TRUE|FALSE)\s*</final_answer>', result_text, re.IGNORECASE)

            if not match:
                is_true = "TRUE" in result_text.upper()
                logger.warning(f"Could not find <final_answer> tag in condition check. Falling back to simple string search. Result: {is_true}")
            else:
                is_true = match.group(1).upper() == 'TRUE'

            logger.info(f"Condition '{step.prompt_template}' evaluated to: {is_true}")
            return {"step_id": step.step_id, "success": is_true, "type": "condition_check", "output": is_true}
        except Exception as e:
            logger.error(f"Condition check step '{step.step_id}' failed: {e}", exc_info=True)
            return {"step_id": step.step_id, "success": False, "error": str(e)}