import inspect
from typing import Callable, Dict, Any

# Mapping Python types to JSON Schema types for function parameters
TYPE_MAPPING = {
    "str": "string",
    "int": "integer",
    "float": "number",
    "bool": "boolean",
    "list": "array",
    "dict": "object",
    "Any": "any",  # 'any' is not standard JSON schema, but useful for our context
}


class SchemaGenerator:
    """
    Generates an OpenAI-compatible JSON schema from a Python function.

    This class introspects a function's signature and docstring to build
    a structured representation that an LLM can use to understand how to
    call the function.
    """

    def generate_schema(self, func: Callable, name: str) -> Dict[str, Any]:
        """
        Creates the full tool schema for a given function.

        It parses the main description, parameters, and return value details
        from the function's docstring.

        Args:
            func: The tool function to inspect.
            name: The name to assign to the tool in the schema.

        Returns:
            A dictionary representing the OpenAI-compatible function schema.
        """
        sig = inspect.signature(func)
        docstring = inspect.getdoc(func) or "No description provided."

        # The main description is the first part of the docstring.
        description = self._parse_main_description(docstring)

        # Parse parameters from signature and docstring
        properties, required = self._parse_parameters(sig, docstring)

        # Parse return information from signature and docstring
        return_info = self._parse_return_info(sig, docstring)

        return {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
                "returns": return_info
            },
        }

    def _parse_main_description(self, docstring: str) -> str:
        """Extracts the primary description from the docstring."""
        # The description is the text before the first 'Args:', ':param', or similar section.
        lines = docstring.split('\n')
        description_lines = []
        for line in lines:
            if line.strip().lower().startswith(('args:', ':param', ':return', ':returns:')):
                break
            description_lines.append(line.strip())
        return " ".join(description_lines).strip()

    def _parse_parameters(self, sig: inspect.Signature, docstring: str):
        """Extracts and describes the function's parameters."""
        properties = {}
        required = []

        docstring_params = self._parse_docstring_params(docstring)

        for param in sig.parameters.values():
            # Skip 'self' and 'cls' for class methods
            if param.name in ("self", "cls"):
                continue

            # Determine parameter type from type hint, default to 'string'
            param_type_name = getattr(param.annotation, '__name__', 'string')
            param_type = TYPE_MAPPING.get(param_type_name.lower(), "string")

            properties[param.name] = {
                "type": param_type,
                "description": docstring_params.get(param.name, "No description provided.")
            }

            # If the parameter has no default value, it's required.
            if param.default is inspect.Parameter.empty:
                required.append(param.name)

        return properties, required

    def _parse_return_info(self, sig: inspect.Signature, docstring: str):
        """Extracts and describes the function's return value."""
        return_info = {"description": "No return description provided."}

        # Determine return type from type hint
        if sig.return_annotation is not inspect.Signature.empty:
            return_type_name = getattr(sig.return_annotation, '__name__', 'any')
            return_info["type"] = TYPE_MAPPING.get(return_type_name.lower(), "any")

        # Find the return description in the docstring
        for line in docstring.split('\n'):
            clean_line = line.strip()
            if clean_line.startswith((":return:", ":returns:")):
                # Find the start of the description after the tag
                desc_start = clean_line.find(":") + 1
                return_info["description"] = clean_line[desc_start:].strip()
                break  # Stop after finding the first return description

        return return_info

    def _parse_docstring_params(self, docstring: str) -> Dict[str, str]:
        """Parses all :param descriptions from a docstring."""
        params = {}
        for line in docstring.split('\n'):
            line = line.strip()
            if line.startswith(":param"):
                parts = line.split(":", 2)
                if len(parts) == 3:
                    param_name = parts[1].strip().split()[1]
                    param_desc = parts[2].strip()
                    params[param_name] = param_desc
        return params