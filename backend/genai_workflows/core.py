import openai
import logging
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
import random

from .workflow import Workflow
from .storage import WorkflowStorage
from .tools import ToolRegistry
from .router import WorkflowRouter
from .executor import WorkflowExecutor
from .visualization import WorkflowVisualizer
from .interactive_parser import InteractiveWorkflowParser


class WorkflowEngine:
    """
    Main facade for the GenAI workflow automation system.
    Orchestrates creation, execution, visualization, and state management.
    """

    def __init__(self, openai_api_key: str, db_path: str = "workflows.db"):
        """Initializes all components of the workflow system."""
        self.client = openai.OpenAI(api_key=openai_api_key)
        self.storage = WorkflowStorage(db_path)
        self.tool_registry = ToolRegistry()
        self.router = WorkflowRouter(self.client)
        self.executor = WorkflowExecutor(self.client, self.tool_registry)
        self.visualizer = WorkflowVisualizer()
        self.interactive_parser = InteractiveWorkflowParser(self.client, self.tool_registry)

        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        self._register_builtin_tools()

    # --- 1. Workflow Definition & Creation ---

    def create_workflow_interactively(self, name: str, description: str, owner: str = "default") -> InteractiveWorkflowParser:
        """
        Starts a new interactive session to build a workflow conversationally.
        Returns the parser instance which manages the conversation.
        """
        self.logger.info(f"Starting interactive session for new workflow: '{name}'")
        self.interactive_parser.start_new_workflow(name, description, owner)
        return self.interactive_parser

    def save_workflow(self, workflow: Workflow) -> int:
        """Saves a completed workflow object to the database."""
        workflow_id = self.storage.save_workflow(workflow)
        self.logger.info(f"Successfully saved workflow '{workflow.name}' with ID {workflow_id}")
        return workflow_id

    # --- 2. Workflow Execution & State Management ---

    def start_execution(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Finds the best workflow for a query and starts a new execution.
        The workflow may complete in one go or pause if it requires human input.
        """
        context = context or {}
        all_workflows = self.storage.get_all_workflows()
        matching_workflow = self.router.find_matching_workflow(query, all_workflows)

        if not matching_workflow:
            self.logger.warning(f"No matching workflow found for query: '{query}'.")
            return { "status": "failed", "error": "No matching workflow found." }

        # Create the initial state for a brand new execution
        execution_id = str(uuid.uuid4())
        initial_state = {
            "execution_id": execution_id,
            "workflow_id": matching_workflow.id,
            "query": query,
            "initial_context": context,
            "collected_inputs": {},
            "step_history": [],
            "current_step_id": matching_workflow.start_step_id,
            "final_response": None
        }

        return self._run_execution_loop(matching_workflow, initial_state)

    def resume_execution(self, execution_id: str, user_input: Any) -> Dict[str, Any]:
        """Resumes a paused workflow with the provided human input."""
        paused_state = self.storage.get_execution_state(execution_id)
        if not paused_state:
            return {"status": "failed", "error": "Execution ID not found or has already completed."}

        workflow = self.storage.get_workflow(paused_state["workflow_id"])
        if not workflow:
            return {"status": "failed", "error": f"Associated workflow ID {paused_state['workflow_id']} could not be found."}

        # 1. Find the step that was paused
        paused_step_id = paused_state.get("current_step_id")
        paused_step = workflow.get_step(paused_step_id)
        if not paused_step:
            error_msg = f"State is corrupt. Paused step ID '{paused_step_id}' not found in workflow."
            self.logger.error(error_msg)
            return {"status": "failed", "error": error_msg}

        # 2. Inject the user's input into the state, as before
        last_history_entry = paused_state["step_history"][-1]
        output_key = last_history_entry.get("output_key")
        if output_key:
            paused_state["collected_inputs"][output_key] = user_input
            self.logger.info(f"Resuming execution {execution_id}. Stored input '{user_input}' under key '{output_key}'.")
            # Also add a simple history entry for the input itself for better traceability
            paused_state["step_history"].append({
                'step_id': paused_step_id, 'type': 'human_input_provided',
                'input': user_input
            })
        else:
            self.logger.warning(f"Resuming execution {execution_id}, but the paused step had no output_key.")

        # 3. Manually advance the state to the next step BEFORE re-entering the loop.
        # The 'human_input' step is considered successfully completed by the user providing input.
        next_step_id = paused_step.on_success
        paused_state["current_step_id"] = next_step_id
        self.logger.info(f"Advancing state from '{paused_step_id}' to next step: '{next_step_id}'.")

        return self._run_execution_loop(workflow, paused_state)

    def _run_execution_loop(self, workflow: Workflow, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Internal method that calls the executor and handles the result,
        managing state persistence in the database.
        """
        try:
            result = self.executor.execute(workflow, state)
            status = result["status"]
            execution_id = result["state"]["execution_id"]

            if status == "paused":
                # Save the paused state to the DB for later resumption
                paused_step = workflow.get_step(result['state']['current_step_id'])
                # Add a record of the pause itself to the history
                result['state']['step_history'].append({
                    'step_id': paused_step.step_id, 'type': 'human_input_pending',
                    'prompt': result['response'], 'output_key': result['output_key']
                })
                self.storage.save_execution_state(execution_id, workflow.id, "paused", result["state"])
                self.logger.info(f"Execution {execution_id} paused and state saved to DB.")
                return {
                    "status": "awaiting_input",
                    "execution_id": execution_id,
                    "response": result["response"]
                }

            # If completed or failed, the execution is over. Remove the state from the DB.
            self.storage.delete_execution_state(execution_id)
            if status == "completed":
                self.logger.info(f"Execution {execution_id} completed successfully.")
                return {"status": "completed", "response": result["response"]}
            else: # status == "failed"
                self.logger.error(f"Execution {execution_id} failed: {result.get('error')}")
                return {"status": "failed", "error": result.get("error", "An unknown error occurred.")}

        except Exception as e:
            self.logger.error(f"Critical error in execution loop for workflow '{workflow.name}': {e}", exc_info=True)
            # Try to clean up any state if a critical error occurs
            if 'state' in locals() and 'execution_id' in state:
                self.storage.delete_execution_state(state['execution_id'])
            return {"status": "failed", "error": f"A critical system error occurred: {e}"}

    # --- 3. Introspection and Management ---

    def visualize_workflow(self, workflow_id: int) -> Optional[str]:
        """Generates a Mermaid.js diagram for a specified workflow."""
        workflow = self.storage.get_workflow(workflow_id)
        if not workflow:
            self.logger.warning(f"Visualize request failed: Workflow ID {workflow_id} not found.")
            return None
        return self.visualizer.generate_mermaid_diagram(workflow)

    def list_workflows(self) -> List[Dict[str, Any]]:
        """Returns a list of all defined workflows."""
        return self.storage.list_workflows()

    def get_workflow(self, workflow_id: int) -> Optional[Workflow]:
        """Retrieves a full workflow object by its ID."""
        return self.storage.get_workflow(workflow_id)

    def delete_workflow(self, workflow_id: int) -> bool:
        """Deletes a workflow and all associated paused states from the database."""
        return self.storage.delete_workflow(workflow_id)

    # --- 4. Tool and Utility Methods ---

    def register_tool(self, func: callable, name: str = None):
        """Registers a custom Python function as a tool the LLM can use."""
        self.tool_registry.register(func, name)

    def _register_builtin_tools(self):
        """Registers a set of simple, built-in tools for demonstration."""
        @self.register_tool
        def get_current_time():
            """
            Gets the current date and time.
            """
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        @self.register_tool
        def simple_calendar_check(date: str):
            """
            Checks calendar availability for a specific date. A real implementation would connect to a calendar API.
            :param date: The date to check in YYYY-MM-DD format.
            """
            is_available = random.choice([True, False])
            if is_available:
                return f"The calendar is open on {date}. Suggested times are 2:00 PM and 4:00 PM."
            else:
                return f"The calendar is fully booked on {date}."