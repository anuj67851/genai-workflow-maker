import json
import logging
from typing import Dict, Any

from .base_executor import BaseActionExecutor
from ..workflow import WorkflowStep

logger = logging.getLogger(__name__)

class IntelligentRouterAction(BaseActionExecutor):
    """
    Uses an LLM to decide which of several paths to take based on the current state.
    """

    async def execute(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        # --- 1. Configuration Validation ---
        if not step.routes or not isinstance(step.routes, dict) or len(step.routes) == 0:
            return {"step_id": step.step_id, "success": False, "error": "Intelligent Router node has no routes configured."}

        if not step.prompt_template:
            return {"step_id": step.step_id, "success": False, "error": "Intelligent Router node is missing its prompt/instruction."}

        # --- 2. Construct the Choice-Forcing Prompt ---
        filled_prompt = self._fill_prompt_template(step.prompt_template, state)
        available_choices = list(step.routes.keys())

        system_prompt = f"""
You are a routing expert in a complex workflow. Your task is to analyze the user's query and the workflow history to decide which path to take next.
You MUST choose one of the following options and only one. Do not provide any other explanation or commentary.

Available Options:
{json.dumps(available_choices)}
"""

        user_prompt = f"""
**Instruction:**
{filled_prompt}

**Workflow Context:**
---
{json.dumps(state, indent=2, default=str)}
---

Based on the instruction and the context, which of the available options is the most appropriate next step?
Respond with ONLY the name of your chosen option from the list.
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # --- 3. Execute LLM Call and Parse the Choice ---
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini", # A fast and cheap model is good for routing
                messages=messages,
                temperature=0.0,
            )

            chosen_route_name = response.choices[0].message.content.strip().replace('"', '').replace("'", "")
            logger.info(f"Intelligent Router chose route: '{chosen_route_name}'")

            # --- 4. Determine the Next Step ---
            if chosen_route_name in step.routes:
                next_step_id = step.routes[chosen_route_name]
                # We dynamically set the next step by returning it in the result.
                # The executor will use this to override the default on_success path.
                return {
                    "step_id": step.step_id,
                    "success": True,
                    "type": "intelligent_router",
                    "output": {"chosen_route": chosen_route_name, "next_step_id": next_step_id},
                    "next_step_override": next_step_id # Special key for the executor
                }
            else:
                error_msg = f"LLM chose an invalid route '{chosen_route_name}', which is not in the configured options: {available_choices}"
                logger.error(f"Step '{step.step_id}': {error_msg}")
                # We treat this as a failure, so it can go to a fallback path if configured.
                return {"step_id": step.step_id, "success": False, "error": error_msg}

        except Exception as e:
            error_msg = f"An unexpected error occurred during intelligent routing: {e}"
            logger.error(f"Step '{step.step_id}': {error_msg}", exc_info=True)
            return {"step_id": step.step_id, "success": False, "error": error_msg}