import logging
from typing import Callable, Dict, Any, List, Optional

from .loader import ToolLoader

logger = logging.getLogger(__name__)

class ToolRegistry:
    """
    A central registry for managing all discoverable workflow tools.

    This class holds the tools loaded by the ToolLoader and provides
    interfaces for the rest of the application (like the WorkflowExecutor)
    to access them. It supports dynamic rescanning of tool directories.
    """

    def __init__(self, tool_dirs: List[str]):
        """
        Initializes the registry and performs an initial scan for tools.

        Args:
            tool_dirs: A list of directory paths to scan for tool modules.
        """
        self._tool_dirs = tool_dirs
        self._loader = ToolLoader()
        self._tools: Dict[str, Callable] = {}
        self._tool_schemas: Dict[str, Dict[str, Any]] = {}
        self.rescan_tools() # Perform initial scan on startup

    def rescan_tools(self) -> int:
        """
        Clears the current toolset and re-scans the tool directories.

        This allows for hot-reloading of tools without a server restart.
        It's the primary method for dynamically updating the available tools.

        Returns:
            The total number of tools loaded.
        """
        logger.info("Rescanning tool directories...")
        loaded_tools = self._loader.load_tools_from_directories(self._tool_dirs)

        # Clear existing tools before reloading
        self._tools.clear()
        self._tool_schemas.clear()

        for name, tool_data in loaded_tools.items():
            self._tools[name] = tool_data["callable"]
            self._tool_schemas[name] = tool_data["schema"]

        count = len(self._tools)
        logger.info(f"Rescan complete. {count} tools are now registered.")
        return count

    def get_tool(self, name: str) -> Optional[Callable]:
        """
        Retrieves a tool's callable function by its registered name.

        Args:
            name: The name of the tool.

        Returns:
            The callable function, or None if the tool is not found.
        """
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        Returns a list of all available tool schemas.

        This is used to provide the LLM with the context of what tools
        it can choose from.

        Returns:
            A list of OpenAI-compatible tool schemas.
        """
        # Return a list of the function schemas
        return [data['function'] for data in self._tool_schemas.values()]

    def get_tools_by_names(self, names: List[str]) -> List[Dict[str, Any]]:
        """

        Retrieves a list of tool schemas for a given list of tool names.

        Args:
            names: A list of tool names to retrieve schemas for.

        Returns:
            A list of matching OpenAI-compatible tool schemas.
        """
        # Filter the schemas and return the function part
        return [
            data['function'] for name, data in self._tool_schemas.items()
            if name in names
        ]