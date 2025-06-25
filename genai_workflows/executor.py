import json
import logging
from typing import Dict, Any, List
from .workflow import Workflow, WorkflowStep
from .tools import ToolRegistry

class WorkflowExecutor:
    """Executes a given workflow, handling state and branching logic."""

    def __init__(self, openai_client, tool_registry: ToolRegistry):
        self.client = openai_client
        self.tool_registry = tool_registry
        self.logger = logging.getLogger(__name__)

    def execute(self, workflow: Workflow, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Executes a workflow from its start step."""
        execution_state = {
            "query": query,
            "initial_context": context,
            "step_history": [],
            "current_step_id": workflow.start_step_id,
            "final_response": None
        }
        self.logger.info(f"Starting execution of workflow '{workflow.name}' for query: '{query}'")

        while execution_state["current_step_id"] and execution_state["current_step_id"] != 'END':
            step = workflow.get_step(execution_state["current_step_id"])
            if not step:
                self.logger.error(f"Step '{execution_state['current_step_id']}' not found. Ending.")
                break

            result = self._execute_step(step, execution_state)
            execution_state["step_history"].append(result)

            if result.get("success"):
                execution_state["current_step_id"] = step.on_success
                if step.on_success == 'END' and result.get("type") == "llm_response":
                    execution_state["final_response"] = result.get("output")
            else:
                if step.on_failure:
                    self.logger.warning(f"Step '{step.step_id}' failed/returned false. Branching to: '{step.on_failure}'.")
                    execution_state["current_step_id"] = step.on_failure
                else:
                    self.logger.error(f"Step '{step.step_id}' failed with no 'on_failure' path. Ending.")
                    break

        if not execution_state["final_response"]:
            self.logger.info("Workflow ended without an explicit response. Generating final summary.")
            execution_state["final_response"] = self._generate_final_response(execution_state)

        return {
            "success": True, "workflow_name": workflow.name, "response": execution_state["final_response"],
            "execution_details": execution_state["step_history"]
        }

    def _execute_step(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        self.logger.info(f"Executing step '{step.step_id}': {step.description}")

        if step.action_type == "agentic_tool_use":
            return self._execute_agentic_tool_use(step, state)
        elif step.action_type == "llm_response":
            return self._execute_llm_response(step, state)
        elif step.action_type == "condition_check":
            return self._execute_condition_check(step, state)
        else:
            self.logger.warning(f"Unknown action type: {step.action_type}")
            return {"step_id": step.step_id, "success": False, "error": f"Unknown action type"}

    def _execute_condition_check(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        history_json = self._fill_prompt_template("{history}", state)
        prompt = f"""
        Based on the execution history provided below, evaluate if the following condition is true or false.
        Condition: "{step.prompt_template}"
        Execution History:
        {history_json}
        Respond with only the word TRUE or FALSE.
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=5
            )
            result_text = response.choices[0].message.content.strip().upper()
            is_true = "TRUE" in result_text
            self.logger.info(f"Condition '{step.prompt_template}' evaluated to: {is_true}")
            return {"step_id": step.step_id, "success": is_true, "type": "condition_check", "output": is_true}
        except Exception as e:
            self.logger.error(f"Condition check step '{step.step_id}' failed: {e}", exc_info=True)
            return {"step_id": step.step_id, "success": False, "error": str(e)}

    def _execute_agentic_tool_use(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        filled_prompt = self._fill_prompt_template(step.prompt_template, state)
        messages = [
            {"role": "system", "content": "You are an assistant that must achieve a goal by using the correct tool. Analyze the user's query and the goal, then call the appropriate tool with the correct parameters."},
            {"role": "user", "content": filled_prompt}
        ]
        try:
            response = self.client.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=self.tool_registry.list_tools(), tool_choice="auto")
            response_message = response.choices[0].message
            if not response_message.tool_calls:
                # Add context to the error
                error_message = f"LLM did not choose a tool for the goal: '{step.prompt_template}'. This often happens when required parameters (like a username) are missing from the context."
                self.logger.warning(error_message)
                return {"step_id": step.step_id, "success": False, "error": error_message}

            tool_call = response_message.tool_calls[0]
            tool_name = tool_call.function.name
            tool_func = self.tool_registry.get_tool(tool_name)
            if not tool_func:
                return {"step_id": step.step_id, "success": False, "error": f"Tool '{tool_name}' not found."}

            tool_args = json.loads(tool_call.function.arguments)
            tool_result = tool_func(**tool_args)
            return {"step_id": step.step_id, "success": True, "type": "tool_call", "tool_name": tool_name, "tool_args": tool_args, "output": tool_result}
        except Exception as e:
            return {"step_id": step.step_id, "success": False, "error": str(e)}

    def _execute_llm_response(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes an LLM response step with a more robust, context-aware prompt.
        """
        history_str = json.dumps(state["step_history"], indent=2, default=str)

        # Construct a new, more reliable prompt that forces the LLM to use the history.
        structured_prompt = f"""
        You are an assistant generating a user-facing response. Your assigned task is to follow this specific instruction:
        **Instruction:** "{step.prompt_template}"

        To fulfill this instruction, you MUST synthesize information from the execution history provided below.
        Read the history carefully to find all the necessary data (e.g., ticket numbers, status, names).
        Do not use placeholders like '[value]' in your final answer; extract the real data from the history.
        The original user query was: "{state['query']}"

        **Execution History:**
        ---
        {history_str}
        ---

        Now, generate a polite, professional, and complete response to the user that directly addresses the instruction.
        """

        messages = [
            {"role": "system", "content": "You are a helpful assistant. Your job is to generate a final, user-facing response by synthesizing information from a provided history log according to a specific instruction."},
            {"role": "user", "content": structured_prompt}
        ]

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.5 # A little less creative for factual responses
            )
            llm_output = response.choices[0].message.content
            return {"step_id": step.step_id, "success": True, "type": "llm_response", "output": llm_output}
        except Exception as e:
            return {"step_id": step.step_id, "success": False, "error": str(e)}

    def _fill_prompt_template(self, template: str, state: Dict[str, Any]) -> str:
        history_str = json.dumps(state["step_history"], indent=2, default=str)
        template = template.replace("{query}", state["query"])
        template = template.replace("{context}", json.dumps(state.get("initial_context", {})))
        template = template.replace("{history}", history_str)
        return template

    def _generate_final_response(self, state: Dict[str, Any]) -> str:
        prompt = self._fill_prompt_template(
            "Based on the user's query and the actions taken, provide a concise and helpful final response. "
            "Synthesize the key results from the history into a summary for the user. "
            "User Query: {query}. History: {history}",
            state
        )
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"The workflow finished, but an error occurred during final response generation: {e}"