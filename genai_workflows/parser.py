import json
import logging
from .workflow import Workflow, WorkflowStep

class WorkflowParser:
    """Parses natural language definitions into structured Workflow objects."""

    def __init__(self, openai_client):
        self.client = openai_client
        self.logger = logging.getLogger(__name__)

    def parse_definition(self, definition: str, name: str, description: str, owner: str) -> Workflow:
        """
        Uses an LLM with function calling to parse a definition into a structured workflow.
        """
        parsing_tool_schema = {
            "type": "function",
            "function": {
                "name": "create_workflow_structure",
                "description": "Creates a structured, branching workflow from a natural language definition.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "triggers": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "A list of phrases or intents that should trigger this workflow.",
                        },
                        "steps": {
                            "type": "array",
                            "description": "The sequence of steps that define the workflow's logic.",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "step_id": {"type": "string", "description": "Unique ID for the step (e.g., 'check_calendar', 'create_ticket')."},
                                    "description": {"type": "string", "description": "A brief summary of what this step does."},
                                    "action_type": {
                                        "type": "string",
                                        "enum": ["agentic_tool_use", "llm_response", "condition_check"],
                                        "description": "The type of action for this step."
                                    },
                                    "prompt_template": {
                                        "type": "string",
                                        "description": "For 'agentic_tool_use', a goal. For 'llm_response', a directive. For 'condition_check', the condition."
                                    },
                                    "on_success": {"type": "string", "description": "Next step_id on success or if condition is TRUE. Use 'END' to finish."},
                                    "on_failure": {"type": "string", "description": "Optional: Next step_id on failure or if condition is FALSE."},
                                },
                                "required": ["step_id", "description", "action_type", "prompt_template", "on_success"],
                            },
                        },
                    },
                    "required": ["triggers", "steps"],
                },
            },
        }

        # --- GENERIC AND ABSTRACT PROMPT ---
        prompt = f"""
        You are an expert system for designing logical workflows. Your task is to convert a user's definition into a structured JSON plan.

        **CRITICAL RULE FOR "IF/ELSE IF/ELSE" LOGIC:**
        To create branching logic, you MUST build a sequential chain of `condition_check` steps. The `on_failure` of one check must lead to the `step_id` of the next check.

        **Abstract Example:**
        1. A tool `categorize_request` runs first.
        2. A step `check_if_type_A` runs next.
           - `action_type`: "condition_check"
           - `prompt_template`: "The output of the 'categorize_request' step was 'Type A'"
           - `on_success`: "start_type_A_branch"  // Jumps to the first step for handling Type A.
           - `on_failure`: "check_if_type_B"     // **KEY**: If not A, it MUST jump to the next condition check.
        3. A step `check_if_type_B` runs next.
           - `action_type`: "condition_check"
           - `prompt_template`: "The output of 'categorize_request' was 'Type B'"
           - `on_success`: "start_type_B_branch"
           - `on_failure`: "fallback_step" // Can go to another check or a default/error step.

        **OTHER RULES:**
        - **TOOLS FIRST:** Prioritize `agentic_tool_use` for any action. Use `llm_response` only to communicate a final result at the end of a branch.
        - **USE PLACEHOLDERS:** The `prompt_template` must use `{{query}}`, `{{context}}`, and `{{history}}` to access data. Ensure tool steps get the data they need (e.g., "Use the username from `{{context}}`").

        **Your Task:**
        Parse the following definition into a sequence of steps using the `create_workflow_structure` tool, following the abstract branching pattern EXACTLY.
        ---
        Workflow Definition: "{definition}"
        ---
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                tools=[parsing_tool_schema],
                tool_choice={"type": "function", "function": {"name": "create_workflow_structure"}},
                temperature=0.0,
            )
            message = response.choices[0].message
            if not message.tool_calls:
                self.logger.error("LLM failed to generate a tool call for parsing. Falling back.")
                self.logger.error(f"LLM Response Content: {message.content}")
                return self._create_fallback_workflow(definition, name, description, owner)
            tool_call = message.tool_calls[0]
            if tool_call.function.name == "create_workflow_structure":
                parsed_args = json.loads(tool_call.function.arguments)
                workflow = Workflow(name=name, description=description, owner=owner, triggers=parsed_args.get("triggers", []), raw_definition=definition)
                for step_data in parsed_args.get("steps", []):
                    step = WorkflowStep.from_dict(step_data)
                    workflow.add_step(step)
                self.logger.info(f"Successfully parsed workflow '{name}' with LLM.")
                return workflow
        except (json.JSONDecodeError, IndexError, KeyError) as e:
            self.logger.error(f"Failed to parse workflow with LLM: {e}. Falling back to simple workflow.")
            return self._create_fallback_workflow(definition, name, description, owner)

    def _create_fallback_workflow(self, definition: str, name: str, description: str, owner: str) -> Workflow:
        workflow = Workflow(name=name, description=description, owner=owner, triggers=[name.lower(), description.lower()], raw_definition=definition)
        fallback_step = WorkflowStep(step_id="fallback_response", description="Generate a direct response.", action_type="llm_response", prompt_template="Respond to the query: {query}", on_success='END')
        workflow.add_step(fallback_step)
        return workflow