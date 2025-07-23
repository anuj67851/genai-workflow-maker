import logging
from typing import Dict, Any

from .base_executor import BaseActionExecutor
from ..workflow import WorkflowStep

logger = logging.getLogger(__name__)

class StartLoopAction(BaseActionExecutor):
    """
    Manages the execution of a loop. It is a stateful executor that handles
    initializing the loop, executing each iteration, aggregating results,
    and terminating the loop.
    """

    async def execute(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the logic for the start_loop action.
        This involves three main phases managed via a state object:
        1. Initialization: Set up the loop state on the first run.
        2. Iteration: For each item, set the current item variable and trigger the loop body sub-graph.
        3. Completion: Once all items are processed, return the aggregated results.
        """
        loop_state_key = f"__loop_state_{step.step_id}"

        # --- Phase 1: Initialization or Resumption ---
        if loop_state_key not in state["collected_inputs"]:
            # This is the first time we've hit this node in this execution.
            input_collection = self._get_value_from_state(step.input_collection_variable, state)

            if not isinstance(input_collection, list):
                error_msg = f"Loop input variable '{step.input_collection_variable}' is not a list or could not be found."
                logger.error(f"Step '{step.step_id}': {error_msg}")
                # Return success=False to trigger the node's 'on_failure' path.
                return {"step_id": step.step_id, "success": False, "error": error_msg}

            # Create and save the initial state for this loop.
            state["collected_inputs"][loop_state_key] = {
                "collection": input_collection,
                "index": 0,
                "results": [],
            }
            logger.info(f"Initialized loop '{step.step_id}' with {len(input_collection)} items.")

        # Retrieve the current state of the loop.
        loop_state = state["collected_inputs"][loop_state_key]
        current_index = loop_state["index"]
        collection = loop_state["collection"]

        # --- Phase 2: Check for Loop Completion ---
        if current_index >= len(collection):
            logger.info(f"Loop '{step.step_id}' completed.")
            final_results = loop_state["results"]

            # Clean up the loop state from collected_inputs.
            del state["collected_inputs"][loop_state_key]

            # Return the aggregated results and signal success to follow the 'on_success' path.
            return {
                "step_id": step.step_id,
                "success": True,
                "type": "start_loop_complete",
                "output": final_results
            }

        # --- Phase 3: Process the Next Iteration ---

        # If we are resuming from a completed iteration, aggregate its result.
        last_history_entry = state["step_history"][-1] if state.get("step_history") else {}
        if last_history_entry.get("type") == "end_loop":
            loop_state["results"].append(last_history_entry.get("output"))
            logger.info(f"Loop '{step.step_id}': Aggregated result from iteration {current_index -1}.")

        # Prepare the state for the current iteration.
        current_item = collection[current_index]
        state["collected_inputs"][step.current_item_output_key] = current_item
        logger.info(f"Loop '{step.step_id}': Starting iteration {current_index}. Current item key '{step.current_item_output_key}' is set.")

        # Crucially, advance the index *before* starting the sub-graph.
        loop_state["index"] += 1
        state["collected_inputs"][loop_state_key] = loop_state

        # Return a special status to the main executor.
        # This tells the executor to start a sub-graph execution at the 'loop_body_start_step_id'
        # and to return control here once it hits an 'end_loop' node.
        return {
            "step_id": step.step_id,
            "success": True,
            "status": "start_loop_iteration",
            "type": "start_loop_iteration",
            "next_step_override": step.loop_body_start_step_id
        }