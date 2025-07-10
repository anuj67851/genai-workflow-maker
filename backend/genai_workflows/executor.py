import json
import logging
from typing import Dict, Any, TYPE_CHECKING

from .workflow import Workflow, WorkflowStep
from .storage import WorkflowStorage
from .tools import ToolRegistry

# --- Import all the individual action classes ---
from .actions.agentic_tool_use_executor import AgenticToolUseAction
from .actions.condition_check_executor import ConditionCheckAction
from .actions.cross_encoder_rerank_executor import CrossEncoderRerankAction
from .actions.file_ingestion_executor import FileIngestionAction
from .actions.human_input_executor import HumanInputAction
from .actions.llm_response_executor import LlmResponseAction
from .actions.vector_db_ingestion_executor import VectorDbIngestionAction
from .actions.vector_db_query_executor import VectorDbQueryAction
from .actions.workflow_call_executor import WorkflowCallAction
from .actions.file_storage_executor import FileStorageAction
from .actions.http_request_executor import HttpRequestAction
from .actions.intelligent_router_executor import IntelligentRouterAction


if TYPE_CHECKING:
    from .core import WorkflowEngine


class WorkflowExecutor:
    """
    Executes a given workflow as a state machine. It handles the logic for each step,
    manages branching, and can pause execution to await external input.
    This executor is a dispatcher that delegates step execution to specific
    action classes.
    """

    def __init__(self, openai_client, tool_registry: ToolRegistry, storage: WorkflowStorage, engine: 'WorkflowEngine'):
        self.client = openai_client
        self.tool_registry = tool_registry
        self.storage = storage
        self.engine = engine # The engine itself, needed for sub-workflow calls
        self.logger = logging.getLogger(__name__)

        # --- The action registry maps action_type strings to their handler classes ---
        self.action_executors = {
            "agentic_tool_use": AgenticToolUseAction,
            "condition_check": ConditionCheckAction,
            "cross_encoder_rerank": CrossEncoderRerankAction,
            "file_storage": FileStorageAction,
            "file_ingestion": FileIngestionAction,
            "human_input": HumanInputAction,
            "llm_response": LlmResponseAction,
            "vector_db_ingestion": VectorDbIngestionAction,
            "vector_db_query": VectorDbQueryAction,
            "workflow_call": WorkflowCallAction,
            "http_request": HttpRequestAction,
            "intelligent_router": IntelligentRouterAction,
        }

    async def execute(self, workflow: Workflow, execution_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes or resumes a workflow from a given state.
        This method will run until the workflow completes, fails, or pauses for input.
        """
        self.logger.info(f"Executing workflow '{workflow.name}' from step '{execution_state['current_step_id']}'")

        try:
            while execution_state["current_step_id"] and execution_state["current_step_id"] != 'END':
                step = workflow.get_step(execution_state["current_step_id"])
                if not step:
                    error_msg = f"Step '{execution_state['current_step_id']}' not found in workflow '{workflow.name}'. Terminating."
                    self.logger.error(error_msg)
                    return {"status": "failed", "error": error_msg, "state": execution_state}

                # --- Delegate to the appropriate action class ---
                result = await self._execute_step(step, execution_state)

                # The rest of the loop logic remains the same...
                if result.get("status") in ["awaiting_input", "awaiting_file_upload"]:
                    response_payload = {
                        "status": "paused", "state": execution_state, "response": result.get("prompt"),
                        "output_key": result.get("output_key"), "pause_type": result.get("status")
                    }
                    if result.get("status") == "awaiting_file_upload":
                        response_payload["allowed_file_types"] = result.get("allowed_file_types")
                        response_payload["max_files"] = result.get("max_files")
                    return response_payload

                if step.output_key and result.get("success") and "output" in result:
                    execution_state["collected_inputs"][step.output_key] = result["output"]
                    self.logger.info(f"Step '{step.step_id}' output stored in 'collected_inputs' under key '{step.output_key}'.")

                execution_state["step_history"].append(result)

                if result.get("success"):
                    # Check for a dynamic override from the router first
                    if "next_step_override" in result and result["next_step_override"]:
                        execution_state["current_step_id"] = result["next_step_override"]
                    else:
                        # Fallback to the statically defined path
                        execution_state["current_step_id"] = step.on_success
                else: # Failed
                    if step.on_failure:
                        execution_state["current_step_id"] = step.on_failure
                    else:
                        error_msg = f"Step '{step.step_id}' failed with no 'on_failure' path. Terminating."
                        self.logger.error(error_msg)
                        return {"status": "failed", "error": result.get("error", error_msg), "state": execution_state}

            if not execution_state.get("final_response"):
                self.logger.info("Workflow ended without an explicit final response. Generating summary.")
                execution_state["final_response"] = await self._generate_final_response(execution_state)

            return {
                "status": "completed",
                "response": execution_state["final_response"],
                "state": execution_state
            }
        except Exception as e:
            self.logger.error(f"A critical error occurred during execution of workflow '{workflow.name}': {e}", exc_info=True)
            return {"status": "failed", "error": str(e), "state": execution_state}


    async def _execute_step(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        This method now finds the correct action class, instantiates it, and calls its execute method.
        """
        self.logger.info(f"Dispatching step '{step.step_id}' to handler for type '{step.action_type}'.")

        # Find the specific action class from our registry
        action_class = self.action_executors.get(step.action_type)

        if not action_class:
            self.logger.warning(f"No action executor found for type: {step.action_type}")
            return {"step_id": step.step_id, "success": False, "error": f"Unknown action type: {step.action_type}"}

        try:
            # Create an instance of the action class, passing all necessary dependencies
            action_instance = action_class(self.client, self.tool_registry, self.engine)
            # Call its execute method
            return await action_instance.execute(step, state)
        except Exception as e:
            self.logger.error(f"Error executing action for step '{step.step_id}': {e}", exc_info=True)
            return {"step_id": step.step_id, "success": False, "error": f"Critical error in action '{step.action_type}': {e}"}


    async def _generate_final_response(self, state: Dict[str, Any]) -> str:
        """This method remains as it's a general utility for the end of a workflow."""
        prompt = f"Based on the user's query '{state.get('query')}' and the actions taken, provide a concise final summary. History: {json.dumps(state.get('step_history', []), default=str)}"
        try:
            # Use a default model or get it from configuration
            default_model = "gpt-4o-mini"
            # Check if there's a default model configured in the engine
            if hasattr(self.engine, 'default_model') and self.engine.default_model:
                default_model = self.engine.default_model

            response = await self.client.chat.completions.create(
                model=default_model, 
                messages=[{"role": "user", "content": prompt}], 
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Final response generation failed: {e}", exc_info=True)
            return f"The workflow finished, but an error occurred during final response generation: {e}"
