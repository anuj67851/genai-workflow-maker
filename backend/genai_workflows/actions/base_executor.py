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
        # This regex now correctly captures the source and the key as two separate groups.
        match = re.match(r'\{(state|context|input|env)\.(.+?)}', placeholder.strip())
        if not match:
            if placeholder.strip() == "{query}":
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
            # This logic is now simpler and correct. It uses the same template filling
            # for all strings, which handles both full replacement and embedded replacement.
            return self._fill_prompt_template(obj, state)
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
            # The _recursive_fill will handle all template replacements now.
            template_obj = json.loads(template_str)
            return self._recursive_fill(template_obj, state)
        except json.JSONDecodeError:
            # This handles the case where the entire template_str is a single placeholder
            # like "{input.some_dict}" which resolves to a dictionary.
            value = self._get_value_from_state(template_str, state)
            if isinstance(value, dict):
                return value
            raise ValueError(f"Template string is not valid JSON and not a valid placeholder for a dictionary: {template_str}")
        except Exception as e:
            # Catch other potential errors during filling
            raise ValueError(f"Failed to process JSON template: {e}")


    def _fill_prompt_template(self, template: str, state: Dict[str, Any]) -> str:
        """
        Utility method to replace all placeholders in a template string.
        """
        if not template:
            return ""

        # The regex to find all valid placeholders
        placeholder_regex = r'\{(?:state|context|input|env)\.[a-zA-Z0-9_]+_?\}|\{query\}'

        def replace_match(match):
            placeholder = match.group(0)
            value = self._get_value_from_state(placeholder, state)

            # If a placeholder's value is not found or is None, replace it with an empty string
            # to avoid 'None' appearing in the final string.
            if value is None:
                return ""

            # If the value is a complex type (not a string), represent it as a JSON string.
            # This is important for cases where a whole dict might be injected into a larger string.
            if not isinstance(value, str):
                return json.dumps(value, default=str)

            # If it's a simple string, return it directly.
            return value

        # Check if the entire template is just one placeholder.
        # This is important to correctly return non-string types without converting them to JSON.
        if re.fullmatch(placeholder_regex, template.strip()):
            value = self._get_value_from_state(template, state)
            # If a value is found, return it directly, preserving its type (e.g., dict, list, int).
            # If not found, return the original template string.
            return value if value is not None else template

        # If we are here, the template is a string with embedded placeholders.
        # We use re.sub to replace all occurrences.
        return re.sub(placeholder_regex, replace_match, template)