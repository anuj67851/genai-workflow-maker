import re
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..core import WorkflowEngine
    from ..tools import ToolRegistry
    from ..workflow import WorkflowStep

class BaseActionExecutor(ABC):
    """
    Abstract base class for all action executors.
    Defines the contract for executing a single workflow step.
    """
    def __init__(self, openai_client, tool_registry: 'ToolRegistry', engine: 'WorkflowEngine'):
        self.client = openai_client
        self.tool_registry = tool_registry
        self.engine = engine

    @abstractmethod
    async def execute(self, step: 'WorkflowStep', state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the logic for a specific workflow step.

        Args:
            step: The WorkflowStep object with its configuration.
            state: The current execution state of the workflow.

        Returns:
            A dictionary containing the result of the execution (e.g., success status, output, error).
        """
        pass

    def _fill_prompt_template(self, template: str, state: Dict[str, Any]) -> str:
        """
        Utility method to replace placeholders in a prompt template with values from the execution state.
        This is provided here as a convenience for all subclasses.
        """
        if not template:
            return ""

        filled_template = template.replace("{query}", str(state.get("query", "")))

        if "{history}" in filled_template:
            history_json = json.dumps(state.get("step_history", []), indent=2, default=str)
            filled_template = filled_template.replace("{history}", history_json)

        def replace_placeholder(match):
            full_match = match.group(0)
            source = match.group(1)
            key = match.group(2)

            if source == 'context':
                value = state.get("initial_context", {}).get(key)
            elif source == 'input':
                value = state.get("collected_inputs", {}).get(key)
            else:
                return full_match

            if value is None:
                return ""

            if isinstance(value, (dict, list)):
                return json.dumps(value, default=str)

            return str(value)

        filled_template = re.sub(r'\{(context|input)\.([a-zA-Z0-9_]+)}', replace_placeholder, filled_template)

        return filled_template