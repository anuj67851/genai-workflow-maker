from typing import Dict, Callable, Any, Optional, List
import inspect

# Mapping Python types to JSON Schema types
TYPE_MAPPING = {
    "str": "string",
    "int": "integer",
    "float": "number",
    "bool": "boolean",
    "list": "array",
    "dict": "object",
    "Any": "any",
}

class ToolRegistry:
    """Registry for managing and describing workflow tools for LLM consumption."""

    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._tool_schemas: Dict[str, Dict[str, Any]] = {}

    def register(self, func: Callable = None, name: str = None):
        """Register a tool function. Can be used as a decorator."""
        def decorator(f: Callable):
            tool_name = name or f.__name__
            self._tools[tool_name] = f
            self._tool_schemas[tool_name] = self._generate_schema(f, tool_name)
            return f

        return decorator(func) if func else decorator

    def get_tool(self, name: str) -> Optional[Callable]:
        """Get a tool function by name."""
        return self._tools.get(name)

    def get_schema(self, name: str) -> Optional[Dict[str, Any]]:
        """Get the JSON schema for a single tool by name."""
        return self._tool_schemas.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools with their OpenAI-compatible schemas."""
        return list(self._tool_schemas.values())

    def get_tools_by_names(self, names: List[str]) -> List[Dict[str, Any]]:
        """Get a list of tool schemas for a given list of tool names."""
        return [schema for name, schema in self._tool_schemas.items() if name in names]

    def _generate_schema(self, func: Callable, name: str) -> Dict[str, Any]:
        """Generate OpenAI-compatible JSON schema from a function signature."""
        sig = inspect.signature(func)
        docstring = inspect.getdoc(func) or "No description provided."

        description = docstring.split('\n')[0]
        properties = {}
        required = []

        for param in sig.parameters.values():
            if param.name in ("self", "cls"):
                continue

            param_type_name = getattr(param.annotation, '__name__', 'string')
            param_type = TYPE_MAPPING.get(param_type_name, "string")
            properties[param.name] = {"type": param_type}

            for line in docstring.split('\n'):
                if line.strip().startswith(f":param {param.name}:"):
                    properties[param.name]["description"] = line.split(f":param {param.name}:")[1].strip()

            if param.default is inspect.Parameter.empty:
                required.append(param.name)

        # --- NEW: Parse return information ---
        return_info = {"description": "No return description provided."}
        if sig.return_annotation is not inspect.Signature.empty:
            return_type_name = getattr(sig.return_annotation, '__name__', 'any')
            return_info["type"] = TYPE_MAPPING.get(return_type_name, "any")

        for line in docstring.split('\n'):
            clean_line = line.strip()
            if clean_line.startswith(":return:") or clean_line.startswith(":returns:"):
                # Find the start of the description after the tag
                desc_start = clean_line.find(":") + 1
                return_info["description"] = clean_line[desc_start:].strip()
                break # Stop after finding the first return description

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
                "returns": return_info  # Add the parsed return info
            },
        }