import json
import logging
import re
import os
from typing import Dict, Any, List, TYPE_CHECKING
import numpy as np

# RAG-specific imports
try:
    import faiss
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from sentence_transformers import CrossEncoder
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False


from .workflow import Workflow, WorkflowStep
from .tools import ToolRegistry
from .storage import WorkflowStorage

if TYPE_CHECKING:
    from .core import WorkflowEngine


class WorkflowExecutor:
    """
    Executes a given workflow as a state machine. It handles the logic for each step,
    manages branching, and can pause execution to await external input.
    """

    def __init__(self, openai_client, tool_registry: ToolRegistry, storage: WorkflowStorage, engine: 'WorkflowEngine'):
        self.client = openai_client
        self.tool_registry = tool_registry
        self.storage = storage
        self.engine = engine
        self.logger = logging.getLogger(__name__)
        # Create a directory for vector stores if it doesn't exist
        os.makedirs("vector_stores", exist_ok=True)

    def execute(self, workflow: Workflow, execution_state: Dict[str, Any]) -> Dict[str, Any]:
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

                result = self._execute_step(step, execution_state)

                if result.get("status") in ["awaiting_input", "awaiting_file_upload"]:
                    self.logger.info(f"Workflow paused. Awaiting external input for step '{step.step_id}'.")
                    # The response payload is now dynamic based on the pause type
                    response_payload = {
                        "status": "paused",
                        "state": execution_state,
                        "response": result.get("prompt"),
                        "output_key": result.get("output_key"),
                        "pause_type": result.get("status") # e.g., 'awaiting_input' or 'awaiting_file_upload'
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
                    execution_state["current_step_id"] = step.on_success
                    if step.on_success == 'END' and result.get("type") == "llm_response":
                        execution_state["final_response"] = result.get("output")
                else:
                    if step.on_failure:
                        self.logger.warning(f"Step '{step.step_id}' failed. Branching to: '{step.on_failure}'.")
                        execution_state["current_step_id"] = step.on_failure
                    else:
                        error_msg = f"Step '{step.step_id}' failed with no 'on_failure' path. Terminating."
                        self.logger.error(error_msg)
                        return {"status": "failed", "error": result.get("error", error_msg), "state": execution_state}

            if not execution_state.get("final_response"):
                self.logger.info("Workflow ended without an explicit final response. Generating summary.")
                execution_state["final_response"] = self._generate_final_response(execution_state)

            return {
                "status": "completed",
                "response": execution_state["final_response"],
                "state": execution_state
            }
        except Exception as e:
            self.logger.error(f"A critical error occurred during execution of workflow '{workflow.name}': {e}", exc_info=True)
            return {"status": "failed", "error": str(e), "state": execution_state}

    def _execute_step(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches execution to the correct method based on the step's action type."""
        self.logger.info(f"Executing step '{step.step_id}' of type '{step.action_type}'.")

        action_map = {
            "agentic_tool_use": self._execute_agentic_tool_use,
            "llm_response": self._execute_llm_response,
            "condition_check": self._execute_condition_check,
            "human_input": self._execute_human_input,
            "workflow_call": self._execute_workflow_call,
            "file_ingestion": self._execute_file_ingestion,
            "vector_db_ingestion": self._execute_vector_db_ingestion,
            "vector_db_query": self._execute_vector_db_query,
            "cross_encoder_rerank": self._execute_cross_encoder_rerank,
        }

        executor_func = action_map.get(step.action_type)
        if executor_func:
            return executor_func(step, state)
        else:
            self.logger.warning(f"Unknown action type encountered: {step.action_type}")
            return {"step_id": step.step_id, "success": False, "error": f"Unknown action type: {step.action_type}"}

    def _execute_human_input(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generates a prompt for the user and returns a pause signal for text input."""
        prompt_for_user = self._fill_prompt_template(step.prompt_template, state)
        return {
            "status": "awaiting_input",
            "prompt": prompt_for_user,
            "output_key": step.output_key
        }

    def _execute_file_ingestion(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generates a prompt for file upload and returns a pause signal."""
        prompt_for_user = self._fill_prompt_template(step.prompt_template, state)
        return {
            "status": "awaiting_file_upload",
            "prompt": prompt_for_user,
            "output_key": step.output_key,
            "allowed_file_types": step.allowed_file_types,
            "max_files": step.max_files,
        }

    def _execute_workflow_call(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        """Loads and executes a sub-workflow, then returns its final result."""
        self.logger.info(f"Executing sub-workflow for step '{step.step_id}'.")
        target_id = step.target_workflow_id
        if not target_id:
            return {"step_id": step.step_id, "success": False, "error": "Step is missing a 'target_workflow_id'."}

        sub_workflow = self.storage.get_workflow(target_id)
        if not sub_workflow:
            return {"step_id": step.step_id, "success": False, "error": f"Sub-workflow with ID {target_id} not found."}

        # Pass the parent's state down as the initial context for the sub-workflow.
        # This makes parent outputs available to the child.
        sub_context = state.get("collected_inputs", {}).copy()
        sub_context["parent_query"] = state.get("query")
        sub_context["parent_execution_id"] = state.get("execution_id")

        # The sub-workflow is started with the parent's original query.
        query = state.get("query")

        # We use the main engine's execution entry point to run the sub-workflow.
        result = self.engine._init_and_run(sub_workflow, query, sub_context)

        if result.get("status") == "completed":
            self.logger.info(f"Sub-workflow '{sub_workflow.name}' completed successfully.")
            return {"step_id": step.step_id, "success": True, "type": "workflow_call", "output": result.get("response")}

        elif result.get("status") == "awaiting_input":
            error_msg = f"Sub-workflow '{sub_workflow.name}' paused for human input, which is not supported in a sub-call."
            self.logger.error(error_msg)
            return {"step_id": step.step_id, "success": False, "error": error_msg}

        else: # failed
            error_details = result.get("error", "Sub-workflow failed without a specific error.")
            self.logger.error(f"Sub-workflow '{sub_workflow.name}' failed: {error_details}")
            return {"step_id": step.step_id, "success": False, "error": f"Sub-workflow failed: {error_details}"}

    def _fill_prompt_template(self, template: str, state: Dict[str, Any]) -> str:
        """
        Replaces placeholders in a prompt template with values from the execution state.
        Handles {query}, {history}, {input.key}, and {context.key}.
        """
        if not template:
            return ""

        # First, handle the direct replacement of special placeholders
        filled_template = template.replace("{query}", str(state.get("query", "")))

        # Handle history replacement, which can be large
        if "{history}" in filled_template:
            history_json = json.dumps(state.get("step_history", []), indent=2, default=str)
            filled_template = filled_template.replace("{history}", history_json)

        # Now, handle structured placeholders like {input.key} and {context.key}
        def replace_placeholder(match):
            full_match = match.group(0)
            source = match.group(1)
            key = match.group(2)

            if source == 'context':
                value = state.get("initial_context", {}).get(key)
            elif source == 'input':
                value = state.get("collected_inputs", {}).get(key)
            else:
                return full_match # Should not happen with the given regex

            if value is None:
                self.logger.warning(f"Placeholder '{full_match}' resolved to None. Replacing with empty string.")
                return ""

            # If the value is a dictionary or list, serialize it to a JSON string
            if isinstance(value, (dict, list)):
                return json.dumps(value, default=str)

            return str(value)

        # This regex looks for {input.some_key} or {context.some_key}
        filled_template = re.sub(r'\{(context|input)\.([a-zA-Z0-9_]+)}', replace_placeholder, filled_template)

        return filled_template

    def _execute_agentic_tool_use(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        filled_prompt = self._fill_prompt_template(step.prompt_template, state)
        system_message = "You are an assistant that must achieve a goal. Analyze the user's query and the goal."
        available_tools: List[Dict[str, Any]] = []

        if step.tool_selection == 'auto':
            system_message += " You can use any of the available tools to help you."
            available_tools = self.tool_registry.list_tools()
        elif step.tool_selection == 'manual' and step.tool_names:
            system_message += " You must use one of the specifically provided tools to achieve your goal."
            available_tools = self.tool_registry.get_tools_by_names(step.tool_names)
        elif step.tool_selection == 'none':
            system_message += " You must respond directly without using any tools."

        messages = [{"role": "system", "content": system_message}, {"role": "user", "content": filled_prompt}]
        completion_kwargs = {"model": "gpt-4o-mini", "messages": messages}
        if available_tools:
            completion_kwargs["tools"] = available_tools
            completion_kwargs["tool_choice"] = "auto"

        try:
            response = self.client.chat.completions.create(**completion_kwargs)
            response_message = response.choices[0].message

            if response_message.tool_calls:
                tool_call = response_message.tool_calls[0]
                tool_name = tool_call.function.name
                tool_func = self.tool_registry.get_tool(tool_name)
                if not tool_func:
                    return {"step_id": step.step_id, "success": False, "error": f"Tool '{tool_name}' not found."}

                tool_args = json.loads(tool_call.function.arguments)
                tool_result = tool_func(**tool_args)
                return {"step_id": step.step_id, "success": True, "type": "tool_call", "tool_name": tool_name, "tool_args": tool_args, "output": tool_result}

            if step.tool_selection in ['auto', 'manual']:
                error_msg = "Agent failed to select a required tool. The prompt may be missing context or is too vague."
                return {"step_id": step.step_id, "success": False, "error": error_msg}

            llm_output = response_message.content
            return {"step_id": step.step_id, "success": True, "type": "llm_response", "output": llm_output}
        except Exception as e:
            self.logger.error(f"Agentic tool use step '{step.step_id}' failed: {e}", exc_info=True)
            return {"step_id": step.step_id, "success": False, "error": str(e)}

    def _execute_condition_check(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        filled_prompt = self._fill_prompt_template(step.prompt_template, state)
        prompt = f"""
        Analyze the following execution history and context to determine if a specific condition is met.
        **Execution History & Context:**
        ---
        {json.dumps(state, indent=2, default=str)}
        ---
        **Condition to Evaluate:**
        "{filled_prompt}"
        **Your Task:**
        1. Carefully read the history and context.
        2. Evaluate the condition based on the provided information.
        3. Provide your reasoning in a <reasoning> XML tag.
        4. Provide your final answer in a <final_answer> XML tag. The answer must be ONLY the word TRUE or FALSE.
        """
        try:
            response = self.client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}], temperature=0.0)
            result_text = response.choices[0].message.content
            match = re.search(r'<final_answer>\s*(TRUE|FALSE)\s*</final_answer>', result_text, re.IGNORECASE)

            if not match:
                is_true = "TRUE" in result_text.upper()
                self.logger.warning(f"Could not find <final_answer> tag in condition check. Falling back to simple string search. Result: {is_true}")
            else:
                is_true = match.group(1).upper() == 'TRUE'

            self.logger.info(f"Condition '{step.prompt_template}' evaluated to: {is_true}")
            return {"step_id": step.step_id, "success": is_true, "type": "condition_check", "output": is_true}
        except Exception as e:
            self.logger.error(f"Condition check step '{step.step_id}' failed: {e}", exc_info=True)
            return {"step_id": step.step_id, "success": False, "error": str(e)}

    def _execute_llm_response(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        filled_prompt = self._fill_prompt_template(step.prompt_template, state)
        structured_prompt = f"""
        You are an assistant generating a user-facing response based on the instruction: "{filled_prompt}".
        Synthesize information from the execution history provided below.
        Original user query: "{state.get('query', '')}"

        Execution History:
        ---
        {json.dumps(state.get('step_history', []), indent=2, default=str)}
        ---
        Generate a polite and complete response that directly follows the instruction.
        """
        messages = [{"role": "user", "content": structured_prompt}]
        try:
            response = self.client.chat.completions.create(model="gpt-4o-mini", messages=messages, temperature=0.5)
            llm_output = response.choices[0].message.content
            return {"step_id": step.step_id, "success": True, "type": "llm_response", "output": llm_output}
        except Exception as e:
            self.logger.error(f"LLM response step '{step.step_id}' failed: {e}", exc_info=True)
            return {"step_id": step.step_id, "success": False, "error": str(e)}

    def _generate_final_response(self, state: Dict[str, Any]) -> str:
        """Generates a final summary if a workflow ends without a specific llm_response step."""
        prompt = self._fill_prompt_template(
            "Based on the user's query and the actions taken, provide a concise and helpful final summary. "
            "User Query: {query}. History: {history}",
            state
        )
        try:
            response = self.client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}], temperature=0.7)
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Final response generation failed: {e}", exc_info=True)
            return f"The workflow finished, but an error occurred during final response generation: {e}"

    def _execute_vector_db_ingestion(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        """Splits text, gets embeddings, and saves to a FAISS vector store."""
        if not FAISS_AVAILABLE:
            return {"step_id": step.step_id, "success": False, "error": "RAG dependencies (faiss, langchain) are not installed."}

        try:
            collection_name = step.collection_name
            if not collection_name:
                return {"step_id": step.step_id, "success": False, "error": "Missing 'collection_name' for ingestion step."}

            input_text = self._fill_prompt_template(step.prompt_template, state)
            if not input_text:
                return {"step_id": step.step_id, "success": False, "error": "Ingestion step received no input text."}

            text_splitter = RecursiveCharacterTextSplitter(chunk_size=step.chunk_size, chunk_overlap=step.chunk_overlap)
            documents = text_splitter.split_text(input_text)

            self.logger.info(f"Splitting text into {len(documents)} chunks.")

            embedding_model = step.embedding_model or "text-embedding-3-small"
            response = self.client.embeddings.create(input=documents, model=embedding_model)
            embeddings = [item.embedding for item in response.data]

            dimension = len(embeddings[0])
            index = faiss.IndexFlatL2(dimension)
            index.add(np.array(embeddings, dtype=np.float32))

            vector_store_dir = "vector_stores"
            faiss.write_index(index, f"{vector_store_dir}/{collection_name}.faiss")

            # Save the text documents separately, linked by index
            with open(f"{vector_store_dir}/{collection_name}.json", 'w') as f:
                json.dump(documents, f)

            output_message = f"Successfully ingested {len(documents)} chunks into collection '{collection_name}'."
            self.logger.info(output_message)
            return {"step_id": step.step_id, "success": True, "type": "vector_db_ingestion", "output": output_message}

        except Exception as e:
            error_msg = f"Vector DB ingestion failed: {e}"
            self.logger.error(error_msg, exc_info=True)
            return {"step_id": step.step_id, "success": False, "error": error_msg}


    def _execute_vector_db_query(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        """Queries a FAISS vector store to find similar documents."""
        if not FAISS_AVAILABLE:
            return {"step_id": step.step_id, "success": False, "error": "RAG dependencies (faiss, langchain) are not installed."}

        try:
            collection_name = step.collection_name
            if not collection_name:
                return {"step_id": step.step_id, "success": False, "error": "Missing 'collection_name' for query step."}

            vector_store_dir = "vector_stores"
            faiss_path = f"{vector_store_dir}/{collection_name}.faiss"
            docs_path = f"{vector_store_dir}/{collection_name}.json"

            if not os.path.exists(faiss_path) or not os.path.exists(docs_path):
                return {"step_id": step.step_id, "success": False, "error": f"Collection '{collection_name}' not found."}

            query_text = self._fill_prompt_template(step.prompt_template, state)
            if not query_text:
                return {"step_id": step.step_id, "success": False, "error": "Query step received no query text."}

            index = faiss.read_index(faiss_path)
            with open(docs_path, 'r') as f:
                documents = json.load(f)

            embedding_model = step.embedding_model or "text-embedding-3-small"
            query_embedding = self.client.embeddings.create(input=[query_text], model=embedding_model).data[0].embedding

            top_k = step.top_k or 5
            distances, indices = index.search(np.array([query_embedding], dtype=np.float32), top_k)

            retrieved_docs = [documents[i] for i in indices[0]]

            output = {"query": query_text, "retrieved_docs": retrieved_docs}
            self.logger.info(f"Retrieved {len(retrieved_docs)} documents from '{collection_name}'.")

            return {"step_id": step.step_id, "success": True, "type": "vector_db_query", "output": output}

        except Exception as e:
            error_msg = f"Vector DB query failed: {e}"
            self.logger.error(error_msg, exc_info=True)
            return {"step_id": step.step_id, "success": False, "error": error_msg}


    def _execute_cross_encoder_rerank(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        """Re-ranks retrieved documents using a cross-encoder model for better relevance."""
        if not FAISS_AVAILABLE:
            return {"step_id": step.step_id, "success": False, "error": "RAG dependencies (sentence-transformers) are not installed."}

        try:
            # The input to this step is expected to be the output from the query step
            input_data_str = self._fill_prompt_template(step.prompt_template, state)

            # The filled template might be a JSON string, so we parse it.
            # It could also be a direct reference to a python object.
            if isinstance(input_data_str, str):
                try:
                    input_data = json.loads(input_data_str)
                except json.JSONDecodeError:
                    # Fallback for if the input isn't a valid JSON string
                    return {"step_id": step.step_id, "success": False, "error": f"Rerank step received invalid input. Expected JSON object but got: {input_data_str[:100]}..."}
            elif isinstance(input_data_str, dict):
                input_data = input_data_str # It was already a dict
            else:
                return {"step_id": step.step_id, "success": False, "error": f"Rerank step received unexpected input type: {type(input_data_str)}"}


            query = input_data.get("query")
            retrieved_docs = input_data.get("retrieved_docs")

            if not query or not retrieved_docs:
                return {"step_id": step.step_id, "success": False, "error": "Rerank step input missing 'query' or 'retrieved_docs'."}

            model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            sentence_pairs = [[query, doc] for doc in retrieved_docs]

            scores = model.predict(sentence_pairs)

            # Combine docs with scores, sort, and return top N
            scored_docs = list(zip(scores, retrieved_docs))
            scored_docs.sort(key=lambda x: x[0], reverse=True)

            rerank_top_n = step.rerank_top_n or 3
            reranked_docs = [doc for score, doc in scored_docs[:rerank_top_n]]

            self.logger.info(f"Re-ranked {len(retrieved_docs)} documents down to {len(reranked_docs)}.")

            return {"step_id": step.step_id, "success": True, "type": "cross_encoder_rerank", "output": reranked_docs}

        except Exception as e:
            error_msg = f"Cross-encoder re-ranking failed: {e}"
            self.logger.error(error_msg, exc_info=True)
            return {"step_id": step.step_id, "success": False, "error": error_msg}