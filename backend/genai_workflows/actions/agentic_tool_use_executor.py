import json
import logging
from typing import Dict, Any, List

from .base_executor import BaseActionExecutor
from ..workflow import WorkflowStep

logger = logging.getLogger(__name__)

class AgenticToolUseAction(BaseActionExecutor):
    async def execute(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        filled_prompt = self._fill_prompt_template(step.prompt_template, state)
        system_message = "You are an assistant that must achieve a goal. Analyze the user's query and the goal."
        available_tools: List[Dict[str, Any]] = []

        if step.tool_selection == 'auto':
            system_message += " You can use any of the available tools to help you."
            available_tools = self.tool_registry.list_tools()
        elif step.tool_selection == 'manual' and step.tool_names:
            system_message += " You must use one of the specifically provided tools to achieve your goal."
            available_tools = self.tool_registry.get_tools_by_names(step.tool_names)
        elif step.tool_selection == 'none':
            system_message += " You must respond directly without using any tools."

        messages = [{"role": "system", "content": system_message}, {"role": "user", "content": filled_prompt}]
        completion_kwargs = {"model": "gpt-4o-mini", "messages": messages}
        if available_tools:
            completion_kwargs["tools"] = available_tools
            completion_kwargs["tool_choice"] = "auto"

        try:
            response = await self.client.chat.completions.create(**completion_kwargs)
            response_message = response.choices[0].message

            if response_message.tool_calls:
                tool_call = response_message.tool_calls[0]
                tool_name = tool_call.function.name
                tool_func = self.tool_registry.get_tool(tool_name)
                if not tool_func:
                    return {"step_id": step.step_id, "success": False, "error": f"Tool '{tool_name}' not found."}

                tool_args = json.loads(tool_call.function.arguments)
                tool_result = tool_func(**tool_args)
                return {"step_id": step.step_id, "success": True, "type": "tool_call", "tool_name": tool_name, "tool_args": tool_args, "output": tool_result}

            if step.tool_selection in ['auto', 'manual']:
                error_msg = "Agent failed to select a required tool. The prompt may be missing context or is too vague."
                return {"step_id": step.step_id, "success": False, "error": error_msg}

            llm_output = response_message.content
            return {"step_id": step.step_id, "success": True, "type": "llm_response", "output": llm_output}
        except Exception as e:
            logger.error(f"Agentic tool use step '{step.step_id}' failed: {e}", exc_info=True)
            return {"step_id": step.step_id, "success": False, "error": str(e)}