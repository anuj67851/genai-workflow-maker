import openai
import logging
from typing import Dict, List, Optional, Any
from .workflow import Workflow
from .storage import WorkflowStorage
from .tools import ToolRegistry
from .parser import WorkflowParser
from .router import WorkflowRouter
from .executor import WorkflowExecutor

class WorkflowEngine:
    """Main facade for the GenAI workflow automation system."""

    def __init__(self, openai_api_key: str, db_path: str = "workflows.db"):
        """Initializes all components of the workflow system."""
        self.client = openai.OpenAI(api_key=openai_api_key)
        self.storage = WorkflowStorage(db_path)
        self.tool_registry = ToolRegistry()

        # Initialize the new modular components
        self.parser = WorkflowParser(self.client)
        self.router = WorkflowRouter(self.client)
        self.executor = WorkflowExecutor(self.client, self.tool_registry)

        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        self._register_builtin_tools()

    def create_workflow(self, name: str, description: str, workflow_definition: str, owner: str = "default") -> int:
        """Creates a new workflow by parsing the definition and saving it to storage."""
        self.logger.info(f"Received request to create workflow: '{name}'")
        workflow = self.parser.parse_definition(workflow_definition, name, description, owner)

        workflow_id = self.storage.save_workflow(workflow)
        self.logger.info(f"Successfully created and stored workflow '{name}' with ID {workflow_id}")
        return workflow_id

    def execute_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Executes a user query by routing to the best workflow and executing it."""
        context = context or {}
        all_workflows = self.storage.get_all_workflows()

        matching_workflow = self.router.find_matching_workflow(query, all_workflows)

        if not matching_workflow:
            self.logger.warning(f"No matching workflow found for query: '{query}'. Generating fallback.")
            return {
                "success": False,
                "message": "No matching workflow found.",
                "response": self._generate_fallback_response(query)
            }

        try:
            return self.executor.execute(matching_workflow, query, context)
        except Exception as e:
            self.logger.error(f"Critical error during workflow execution for '{matching_workflow.name}': {e}", exc_info=True)
            return {"success": False, "error": str(e), "workflow_name": matching_workflow.name}

    def list_workflows(self) -> List[Dict[str, Any]]:
        return self.storage.list_workflows()

    def get_workflow(self, workflow_id: int) -> Optional[Workflow]:
        return self.storage.get_workflow(workflow_id)

    def delete_workflow(self, workflow_id: int) -> bool:
        return self.storage.delete_workflow(workflow_id)

    def register_tool(self, func: callable, name: str = None):
        """Registers a custom tool function."""
        return self.tool_registry.register(func, name)

    def _generate_fallback_response(self, query: str) -> str:
        """Generates a direct LLM response when no workflows match."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": f"Please provide a helpful answer to the following query: {query}"}],
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Fallback response generation failed: {e}")
            return "I'm sorry, I couldn't find a way to handle your request and encountered an error trying to generate a direct response."

    def _register_builtin_tools(self):
        """Registers built-in tools."""

        @self.register_tool
        def get_current_time():
            """
            Gets the current date and time.
            """
            from datetime import datetime
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        @self.register_tool
        def simple_calendar_check(date: str):
            """
            Checks calendar availability for a specific date. A real implementation would connect to a calendar API.
            :param date: The date to check in YYYY-MM-DD format.
            """
            import random
            is_available = random.choice([True, False])
            if is_available:
                return f"The calendar is open on {date}. Suggested times are 2:00 PM, 3:30 PM, and 4:00 PM."
            else:
                return f"The calendar is fully booked on {date}."