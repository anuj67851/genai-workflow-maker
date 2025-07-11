import re
import json
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, TYPE_CHECKING, List, Union

if TYPE_CHECKING:
    from ..core import WorkflowEngine
    from ...tools import ToolRegistry
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
        """Executes the logic for a specific workflow step."""
        pass

    def _get_value_from_state(self, placeholder: str, state: Dict[str, Any]) -> Any:
        """
        Helper to retrieve a value from state based on a placeholder string like '{input.var_name}'.
        """
        # Improved regex to handle various sources
        match = re.match(r'\{(state|context|input|env)\.([a-zA-Z0-9_]+)\}', placeholder)
        if not match:
            if placeholder == "{query}":
                return state.get("query")
            return None # Not a recognized placeholder format

        source, key = match.groups()
        if source == 'state':
            return state.get(key)
        if source == 'context':
            return state.get("initial_context", {}).get(key)
        if source == 'input':
            return state.get("collected_inputs", {}).get(key)
        if source == 'env':
            return os.getenv(key)
        return None

    def _recursive_fill(self, obj: Union[Dict, List, Any], state: Dict[str, Any]) -> Any:
        """
        Recursively traverses a Python object (from a parsed JSON template) and fills its values.
        """
        if isinstance(obj, dict):
            return {k: self._recursive_fill(v, state) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._recursive_fill(item, state) for item in obj]
        if isinstance(obj, str):
            # If the string is a placeholder, replace it. Otherwise, keep it as is.
            value = self._get_value_from_state(obj, state)
            return value if value is not None else obj
        return obj

    def _fill_json_template(self, template_str: str, state: Dict[str, Any]) -> Dict:
        """
        Parses a JSON template string and fills its values from the workflow state.
        This is the robust way to handle JSON structures for nodes like HTTP Request or Workflow Call.
        Returns a Python dictionary.
        """
        if not template_str:
            return {}
        try:
            template_obj = json.loads(template_str)
            return self._recursive_fill(template_obj, state)
        except json.JSONDecodeError:
            # This handles the case where the entire template_str is a single placeholder
            # like "{input.some_dict}" which resolves to a dictionary.
            value = self._get_value_from_state(template_str, state)
            if isinstance(value, dict):
                return value
            raise # Re-raise the JSONDecodeError if it's not a valid placeholder

    def _fill_prompt_template(self, template: str, state: Dict[str, Any]) -> str:
        """
        Utility method to replace placeholders in a simple text prompt.
        For filling JSON templates, use _fill_json_template.
        Returns a final string.
        """
        if not template:
            return ""

        # This regex finds all occurrences of {source.key} or {query}
        def replace_match(match):
            placeholder = match.group(0)
            value = self._get_value_from_state(placeholder, state)

            # If a placeholder's value is not found or is None, replace it with an empty string.
            if value is None:
                return ""

            # If the value is a list of strings (common from file ingestion), join them.
            if isinstance(value, list) and all(isinstance(i, str) for i in value):
                return "\n".join(value)

            # If the value is another complex type, represent it as a readable JSON string.
            if isinstance(value, (dict, list)):
                return json.dumps(value, indent=2, default=str)

            # For all other types (int, bool, str), just convert to a string.
            return str(value)

        filled_template = re.sub(r'\{[a-zA-Z0-9_.]+}', replace_match, template)

        return filled_template