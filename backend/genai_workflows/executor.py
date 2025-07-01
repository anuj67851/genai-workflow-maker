import json
import logging
import re
from typing import Dict, Any, List
from .workflow import Workflow, WorkflowStep
from .tools import ToolRegistry

class WorkflowExecutor:
    """
    Executes a given workflow as a state machine. It handles the logic for each step,
    manages branching, and can pause execution to await external input.
    """

    def __init__(self, openai_client, tool_registry: ToolRegistry):
        self.client = openai_client
        self.tool_registry = tool_registry
        self.logger = logging.getLogger(__name__)

    def execute(self, workflow: Workflow, execution_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes or resumes a workflow from a given state.
        This method will run until the workflow completes, fails, or pauses for input.

        Args:
            workflow: The workflow object to execute.
            execution_state: The current state of the execution, including the next step to run.

        Returns:
            A dictionary indicating the outcome: 'completed', 'paused', or 'failed',
            along with the final or intermediate state.
        """
        self.logger.info(f"Executing workflow '{workflow.name}' from step '{execution_state['current_step_id']}'")

        try:
            while execution_state["current_step_id"] and execution_state["current_step_id"] != 'END':
                step = workflow.get_step(execution_state["current_step_id"])
                if not step:
                    error_msg = f"Step '{execution_state['current_step_id']}' not found in workflow '{workflow.name}'. Terminating."
                    self.logger.error(error_msg)
                    return {"status": "failed", "error": error_msg, "state": execution_state}

                result = self._execute_step(step, execution_state)

                if result.get("status") == "awaiting_input":
                    self.logger.info(f"Workflow paused. Awaiting human input for step '{step.step_id}'.")
                    return {
                        "status": "paused",
                        "state": execution_state,
                        "response": result.get("prompt"),
                        "output_key": result.get("output_key")
                    }

                # Save the output of the step to the collected_inputs if an output_key is defined
                if step.output_key and result.get("success") and "output" in result:
                    execution_state["collected_inputs"][step.output_key] = result["output"]
                    self.logger.info(f"Step '{step.step_id}' output stored in 'collected_inputs' under key '{step.output_key}'.")


                execution_state["step_history"].append(result)

                if result.get("success"):
                    execution_state["current_step_id"] = step.on_success
                    if step.on_success == 'END' and result.get("type") == "llm_response":
                        execution_state["final_response"] = result.get("output")
                else: # Handle failure
                    if step.on_failure:
                        self.logger.warning(f"Step '{step.step_id}' failed. Branching to: '{step.on_failure}'.")
                        execution_state["current_step_id"] = step.on_failure
                    else:
                        error_msg = f"Step '{step.step_id}' failed with no 'on_failure' path. Terminating."
                        self.logger.error(error_msg)
                        return {"status": "failed", "error": result.get("error", error_msg), "state": execution_state}

            if not execution_state.get("final_response"):
                self.logger.info("Workflow ended without an explicit final response. Generating summary.")
                execution_state["final_response"] = self._generate_final_response(execution_state)

            return {
                "status": "completed",
                "response": execution_state["final_response"],
                "state": execution_state
            }
        except Exception as e:
            self.logger.error(f"A critical error occurred during execution of workflow '{workflow.name}': {e}", exc_info=True)
            return {"status": "failed", "error": str(e), "state": execution_state}

    def _execute_step(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches execution to the correct method based on the step's action type."""
        self.logger.info(f"Executing step '{step.step_id}' of type '{step.action_type}'.")

        action_map = {
            "agentic_tool_use": self._execute_agentic_tool_use,
            "llm_response": self._execute_llm_response,
            "condition_check": self._execute_condition_check,
            "human_input": self._execute_human_input,
        }

        executor_func = action_map.get(step.action_type)
        if executor_func:
            return executor_func(step, state)
        else:
            self.logger.warning(f"Unknown action type encountered: {step.action_type}")
            return {"step_id": step.step_id, "success": False, "error": f"Unknown action type: {step.action_type}"}

    def _execute_human_input(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generates a prompt for the user and returns a pause signal."""
        prompt_for_user = self._fill_prompt_template(step.prompt_template, state)
        return {
            "status": "awaiting_input",
            "prompt": prompt_for_user,
            "output_key": step.output_key
        }

    def _fill_prompt_template(self, template: str, state: Dict[str, Any]) -> str:
        """
        Replaces placeholders in a prompt template with values from the execution state.
        Handles {query}, {history}, {input.key}, and {context.key}.
        """
        if not template:
            return ""
        filled_template = template

        def replace_placeholder(match):
            full_match = match.group(0)
            source = match.group(1)
            key = match.group(2)

            if source == 'context':
                value = state.get("initial_context", {}).get(key, f"'{key}' not found in context")
            elif source == 'input':
                value = state.get("collected_inputs", {}).get(key, f"'{key}' not found in inputs")
            else:
                return full_match

            return str(value)

        filled_template = re.sub(r'\{(context|input)\.([a-zA-Z0-9_]+)}', replace_placeholder, filled_template)

        filled_template = filled_template.replace("{query}", state.get("query", ""))
        filled_template = filled_template.replace("{history}", json.dumps(state.get("step_history", []), indent=2, default=str))

        return filled_template


    def _execute_agentic_tool_use(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        filled_prompt = self._fill_prompt_template(step.prompt_template, state)

        system_message = "You are an assistant that must achieve a goal. Analyze the user's query and the goal."
        available_tools: List[Dict[str, Any]] = []

        if step.tool_selection == 'auto':
            system_message += " You can use any of the available tools to help you."
            available_tools = self.tool_registry.list_tools()
            self.logger.info(f"Step '{step.step_id}' is in 'auto' mode. Providing all tools.")
        elif step.tool_selection == 'manual' and step.tool_names:
            system_message += " You must use one of the specifically provided tools to achieve your goal."
            available_tools = self.tool_registry.get_tools_by_names(step.tool_names)
            self.logger.info(f"Step '{step.step_id}' is in 'manual' mode. Constraining to: {step.tool_names}")
        elif step.tool_selection == 'none':
            system_message += " You must respond directly without using any tools."
            self.logger.info(f"Step '{step.step_id}' is in 'none' mode. No tools will be provided.")

        messages = [{"role": "system", "content": system_message}, {"role": "user", "content": filled_prompt}]

        completion_kwargs = {"model": "gpt-4o-mini", "messages": messages}
        if available_tools:
            completion_kwargs["tools"] = available_tools
            completion_kwargs["tool_choice"] = "auto"

        try:
            response = self.client.chat.completions.create(**completion_kwargs)
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

            # *** BUG FIX STARTS HERE ***
            # If we expected a tool call ('auto' or 'manual' mode) but didn't get one, it's an error.
            if step.tool_selection in ['auto', 'manual']:
                error_msg = "Agent failed to select a required tool. The prompt may be missing context (e.g., `{query}`) or is too vague."
                self.logger.error(f"Step '{step.step_id}': {error_msg}")
                return {"step_id": step.step_id, "success": False, "error": error_msg}

            # Otherwise (i.e., in 'none' mode), a text response is the expected successful outcome.
            llm_output = response_message.content
            return {"step_id": step.step_id, "success": True, "type": "llm_response", "output": llm_output}
            # *** BUG FIX ENDS HERE ***

        except Exception as e:
            self.logger.error(f"Agentic tool use step '{step.step_id}' failed: {e}", exc_info=True)
            return {"step_id": step.step_id, "success": False, "error": str(e)}

    def _execute_condition_check(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
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
        1. Carefully read the history and context. Pay close attention to user queries, tool outputs, and collected inputs.
        2. Evaluate the condition based on the provided information.
        3. Provide your reasoning in a <reasoning> XML tag. Explain step-by-step how you arrived at your conclusion.
        4. Provide your final answer in a <final_answer> XML tag. The answer must be ONLY the word TRUE or FALSE.

        Example:
        <reasoning>
        The user's query mentions a "broken screen", which is a hardware issue. The last tool output confirms a hardware fault was detected. Therefore, a hardware-related condition is true.
        </reasoning>
        <final_answer>TRUE</final_answer>
        """
        try:
            response = self.client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}], temperature=0.0)
            result_text = response.choices[0].message.content

            self.logger.debug(f"Condition check raw response for step '{step.step_id}':\n{result_text}")

            match = re.search(r'<final_answer>\s*(TRUE|FALSE)\s*</final_answer>', result_text, re.IGNORECASE)

            if not match:
                is_true = "TRUE" in result_text.upper()
                self.logger.warning(f"Could not find <final_answer> tag. Falling back to simple string search. Result: {is_true}")
            else:
                is_true = match.group(1).upper() == 'TRUE'

            self.logger.info(f"Condition '{step.prompt_template}' evaluated to: {is_true}")
            return {"step_id": step.step_id, "success": is_true, "type": "condition_check", "output": is_true}
        except Exception as e:
            self.logger.error(f"Condition check step '{step.step_id}' failed: {e}", exc_info=True)
            return {"step_id": step.step_id, "success": False, "error": str(e)}

    def _execute_llm_response(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        filled_prompt = self._fill_prompt_template(step.prompt_template, state)
        structured_prompt = f"""
        You are an assistant generating a user-facing response based on the instruction: "{filled_prompt}".
        To do this, synthesize information from the execution history provided below.
        Extract all necessary data (e.g., ticket numbers, status) from the history. Do not use placeholders.
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
            self.logger.error(f"LLM response step '{step.step_id}' failed: {e}", exc_info=True)
            return {"step_id": step.step_id, "success": False, "error": str(e)}

    def _generate_final_response(self, state: Dict[str, Any]) -> str:
        """Generates a final summary if a workflow ends without a specific llm_response step."""
        prompt = self._fill_prompt_template(
            "Based on the user's query and the actions taken, provide a concise and helpful final summary. "
            "Synthesize the key results from the history for the user. "
            "User Query: {query}. History: {history}",
            state
        )
        try:
            response = self.client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}], temperature=0.7)
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Final response generation failed: {e}", exc_info=True)
            return f"The workflow finished, but an error occurred during final response generation: {e}"