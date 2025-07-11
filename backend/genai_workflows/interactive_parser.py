import json
import logging
from typing import Dict, Any, List, Optional
from .workflow import Workflow, WorkflowStep
from ..tools.registry import ToolRegistry

class InteractiveWorkflowParser:
    """
    Builds a Workflow object through a step-by-step conversation with a user.
    """

    def __init__(self, openai_client, tool_registry: ToolRegistry):
        self.client = openai_client
        self.tool_registry = tool_registry
        self.logger = logging.getLogger(__name__)
        self._reset_state()

    def _reset_state(self):
        """Initializes or resets the internal state for a new workflow build."""
        self.workflow_in_progress: Optional[Workflow] = None
        self.conversation_history: List[Dict[str, str]] = []
        self.last_added_step_id: Optional[str] = None
        self.is_finished: bool = False

    def start_new_workflow(self, name: str, description: str, owner: str = "default"):
        """Begins a new workflow creation session."""
        self._reset_state()
        self.workflow_in_progress = Workflow(name=name, description=description, owner=owner)
        self.logger.info(f"Started interactive build for workflow: {name}")

    def handle_user_response(self, user_response: str) -> str:
        """

        Processes the user's latest message, attempts to add a step to the workflow,
        and returns the next question for the user.

        Args:
            user_response: The natural language input from the user.

        Returns:
            A string containing the next prompt for the user.
        """
        if not self.workflow_in_progress:
            return "Error: Please start a new workflow first with `start_new_workflow()`."

        if user_response.lower().strip() in ["undo", "undo last step", "go back"]:
            return self._undo_last_step()

        self.conversation_history.append({"role": "user", "content": user_response})

        try:
            # The core of the parser: use an LLM to turn user text into a structured step
            tool_call_response = self._get_llm_tool_call()
            message = tool_call_response.choices[0].message

            if not message.tool_calls:
                # The LLM decided the user is done or didn't provide a valid step.
                self.is_finished = True
                self.logger.info("LLM indicated workflow is complete.")
                return "I believe the workflow is complete. I will now finalize it. You can save it to the database."

            # Process the structured step returned by the LLM
            tool_call = message.tool_calls[0]
            function_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            # Add the new step to our workflow object
            self.last_added_step_id = args.get("step_id")
            new_step = WorkflowStep.from_dict(args)
            self.workflow_in_progress.add_step(new_step)

            self.logger.info(f"Added step '{new_step.step_id}' of type '{new_step.action_type}'.")

            # Generate the next guiding question for the user
            next_prompt = f"OK, I've added the step: '{new_step.description}'. What should happen next? (You can also say 'undo' or 'I'm done')."
            self.conversation_history.append({"role": "assistant", "content": next_prompt})
            return next_prompt

        except Exception as e:
            self.logger.error(f"Error during interactive parsing: {e}", exc_info=True)
            return "I'm sorry, I had trouble understanding that. Could you please rephrase? Or you can say 'I'm done' to finish."

    def _undo_last_step(self) -> str:
        """Removes the most recently added step from the workflow."""
        if not self.last_added_step_id or not self.workflow_in_progress:
            return "There's nothing to undo."

        removed_step = self.workflow_in_progress.steps.pop(self.last_added_step_id, None)
        if removed_step:
            # Reset start step if we removed the very first step
            if self.workflow_in_progress.start_step_id == self.last_added_step_id:
                self.workflow_in_progress.start_step_id = None
                # If other steps exist, make the first one the new start
                if self.workflow_in_progress.steps:
                    self.workflow_in_progress.start_step_id = next(iter(self.workflow_in_progress.steps))

            self.logger.info(f"Undid the last step: {self.last_added_step_id}")
            self.last_added_step_id = None # Clear it
            return f"OK, I've removed the step: '{removed_step.description}'. What would you like to do instead?"
        return "There was an issue undoing the last step."

    def get_final_workflow(self) -> Optional[Workflow]:
        """Returns the completed workflow object if the process is finished."""
        if self.is_finished:
            # Set triggers based on the workflow name and description as a default
            if not self.workflow_in_progress.triggers:
                self.workflow_in_progress.triggers = [self.workflow_in_progress.name.lower()]
            return self.workflow_in_progress
        return None

    def _get_llm_tool_call(self):
        """Makes the LLM call with the conversation history and function definitions."""
        system_prompt = self._get_system_prompt()
        messages = [{"role": "system", "content": system_prompt}] + self.conversation_history

        parsing_tools = self._get_parsing_tools()

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=parsing_tools,
            tool_choice="auto", # Let the model decide if it should call a tool or not
            temperature=0.1,
        )
        return response

    def _get_system_prompt(self) -> str:
        """Constructs the master system prompt for the interactive builder LLM."""
        # --- MODIFIED: Get tools directly from the new registry ---
        # The list_tools() method now returns the correct OpenAI format.
        available_tools = self.tool_registry.list_tools()
        tools_json_str = json.dumps(available_tools, indent=2)

        return f"""
        You are an expert system that helps a user build a logical workflow, one step at a time.
        Your job is to interpret the user's latest instruction and convert it into a single, structured workflow step by calling the `add_step` function.

        **Workflow So Far:**
        {json.dumps(self.workflow_in_progress.to_dict() if self.workflow_in_progress else {}, indent=2)}
        
        **Available Tools for the Workflow:**
        The workflow can use any of these tools. When the user mentions an action, match it to one of these tools.
        {tools_json_str}

        **Your Task:**
        1.  Analyze the user's most recent message based on the conversation history.
        2.  Decide what kind of step they are describing (`tool_use`, `human_input`, `condition_check`, or `llm_response`).
        3.  Generate a concise, unique `step_id` (e.g., 'check_user_warranty', 'ask_for_name').
        4.  Fill in all the parameters for the `add_step` function.
        5.  **VERY IMPORTANT**: If the user says they are "done", "finished", or something similar, DO NOT call a tool. Just respond with a confirmation message. This signals the end of the process.

        **Branching Logic:**
        - For `on_success` and `on_failure`, you MUST specify the `step_id` of a future step. It's okay if that step doesn't exist yet. The user will define it next.
        - To end a branch, use the special string 'END'.
        - You must always provide an `on_success` path.
        """

    def _get_parsing_tools(self) -> List[Dict[str, Any]]:
        """Defines the function calling schema for the `add_step` action."""
        step_schema = {
            "type": "function",
            "function": {
                "name": "add_step",
                "description": "Adds a single step to the workflow being built.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "step_id": {"type": "string", "description": "A short, unique, descriptive ID for the step (e.g., 'check_inventory', 'ask_for_ticket_id')."},
                        "description": {"type": "string", "description": "A user-facing sentence describing what this step does."},
                        "action_type": {
                            "type": "string",
                            "enum": ["agentic_tool_use", "llm_response", "condition_check", "human_input"],
                            "description": "The category of action for this step."
                        },
                        "prompt_template": {"type": "string", "description": "The detailed instruction for this step. For tools, the goal. For humans, the question. For conditions, the evaluation criteria."},
                        "output_key": {"type": "string", "description": "For 'human_input' only. The variable name to store the user's answer (e.g., 'user_name', 'ticket_number')."},
                        "on_success": {"type": "string", "description": "The step_id to go to on success or if a condition is true. Use 'END' to finish this path."},
                        "on_failure": {"type": "string", "description": "Optional: The step_id to go to on failure or if a condition is false."},
                    },
                    "required": ["step_id", "description", "action_type", "prompt_template", "on_success"],
                },
            },
        }
        return [step_schema]