import importlib.util
import logging
from pathlib import Path
from typing import List, Dict, Any

from .schema import SchemaGenerator

logger = logging.getLogger(__name__)


class ToolLoader:
    """
    Dynamically discovers and loads tools from specified directories.

    This class scans Python files, identifies functions decorated with @tool,
    and generates their schemas, making them ready for registration.
    """

    def __init__(self):
        self.schema_generator = SchemaGenerator()
        self.loaded_modules = {} # Cache to avoid re-importing unchanged files

    def load_tools_from_directories(self, tool_dirs: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Scans a list of directories for .py files and loads all discoverable tools.

        Args:
            tool_dirs: A list of paths to directories containing tool modules.

        Returns:
            A dictionary of all discovered tools, where keys are tool names
            and values are a dict containing the 'callable' and 'schema'.
        """
        all_tools = {}
        for directory in tool_dirs:
            path = Path(directory)
            if not path.is_dir():
                logger.warning(f"Tool directory not found, skipping: {directory}")
                continue

            logger.info(f"Scanning for tools in directory: {directory}")
            for file_path in path.glob("**/*.py"):
                if file_path.name == "__init__.py":
                    continue

                try:
                    tools_in_file = self._load_tools_from_file(file_path)
                    for tool_name, tool_data in tools_in_file.items():
                        if tool_name in all_tools:
                            logger.warning(f"Duplicate tool name '{tool_name}' found. Overwriting with definition from {file_path}.")
                        all_tools[tool_name] = tool_data
                except Exception as e:
                    logger.error(f"Failed to load tools from file {file_path}: {e}", exc_info=True)

        logger.info(f"Discovered {len(all_tools)} tools from {len(tool_dirs)} director(y/ies).")
        return all_tools

    def _load_tools_from_file(self, file_path: Path) -> Dict[str, Dict[str, Any]]:
        """
        Loads a single Python file as a module and extracts its tools.

        This uses `importlib` to dynamically load the module from its path
        without it needing to be in Python's standard path.
        """
        tools = {}
        # Create a unique module name from the file path to avoid conflicts.
        # e.g., 'backend/tools/custom/my_tool.py' -> 'tools.custom.my_tool'
        module_name = ".".join(file_path.with_suffix("").parts[-3:])

        # Use importlib to load the module from its file path
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if not spec:
            raise ImportError(f"Could not create module spec for {file_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Now, inspect the loaded module for functions with our decorator
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if callable(attr) and hasattr(attr, '_tool_spec'):
                tool_spec = attr._tool_spec
                tool_name = tool_spec['name']
                func = tool_spec['function']

                # Generate the full schema for the tool
                schema = self.schema_generator.generate_schema(func, tool_name)

                tools[tool_name] = {
                    "callable": func,
                    "schema": schema,
                }
        return tools