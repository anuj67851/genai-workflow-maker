import os
import shutil

import openai
import logging
import uuid
from typing import Dict, List, Optional, Any

from fastapi import UploadFile

from .workflow import Workflow
from .storage import WorkflowStorage
from .tools import ToolRegistry
from .router import WorkflowRouter
from .executor import WorkflowExecutor
from .visualization import WorkflowVisualizer
from .interactive_parser import InteractiveWorkflowParser
from .. import tools


class WorkflowEngine:
    """
    Main facade for the GenAI workflow automation system.
    Orchestrates creation, execution, visualization, and state management.
    """

    def __init__(self, openai_api_key: str, db_path: str = "workflows.db", default_model: str = "gpt-4o-mini"):
        """Initializes all components of the workflow system."""
        self.client = openai.AsyncOpenAI(api_key=openai_api_key)
        self.storage = WorkflowStorage(db_path)
        self.tool_registry = ToolRegistry()
        self.router = WorkflowRouter(self.client)
        # Pass storage and self (engine) to executor for sub-workflow calls
        self.executor = WorkflowExecutor(self.client, self.tool_registry, self.storage, self)
        self.visualizer = WorkflowVisualizer()
        self.interactive_parser = InteractiveWorkflowParser(self.client, self.tool_registry)

        # Default model to use for LLM operations if not specified in the step
        self.default_model = default_model

        self.logger = logging.getLogger(__name__)

        # Ensure required directories exist
        os.makedirs("vector_stores", exist_ok=True)
        os.makedirs("file_attachments", exist_ok=True)

        tools.register_all_tools(self.tool_registry)
        self.logger.info(f"Registered {len(self.tool_registry.list_tools())} tools.")

    async def resume_execution_with_files(self, execution_id: str, files: List[UploadFile]) -> Dict[str, Any]:
        """
        Handles file uploads by checking the paused step's action type.
        - For 'file_ingestion', it extracts text content.
        - For 'file_storage', it saves the file and returns its path.
        """
        self.logger.info(f"Resuming execution {execution_id} with {len(files)} file(s).")

        # First, we need to know what kind of step paused for this upload.
        paused_state = self.storage.get_execution_state(execution_id)
        if not paused_state:
            return {"status": "failed", "error": "Execution ID not found."}
        workflow = self.storage.get_workflow(paused_state["workflow_id"])
        paused_step = workflow.get_step(paused_state.get("current_step_id"))
        if not paused_step:
            return {"status": "failed", "error": "Could not find the paused step in the workflow."}

        # This will hold the final output for the step (either content or paths)
        final_output = []

        if paused_step.action_type == 'file_ingestion':
            # --- Text Extraction Logic ---
            self.logger.info("Handling as 'file_ingestion': Extracting text content.")

            try:
                # Import necessary libraries for text extraction
                import PyPDF2
                from PIL import Image
                import pytesseract
                import docx

                for file in files:
                    file_content = await file.read()
                    file_extension = os.path.splitext(file.filename)[1].lower()

                    if file_extension == '.pdf':
                        # Extract text from PDF
                        import io
                        pdf_file = io.BytesIO(file_content)
                        pdf_reader = PyPDF2.PdfReader(pdf_file)
                        text = ""
                        for page_num in range(len(pdf_reader.pages)):
                            text += pdf_reader.pages[page_num].extract_text()
                        final_output.append(text)

                    elif file_extension in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
                        # Extract text from image using OCR
                        import io
                        image = Image.open(io.BytesIO(file_content))
                        text = pytesseract.image_to_string(image)
                        final_output.append(text)

                    elif file_extension == '.docx':
                        # Extract text from Word document
                        import io
                        doc = docx.Document(io.BytesIO(file_content))
                        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                        final_output.append(text)

                    elif file_extension == '.txt':
                        # Extract text from plain text file
                        text = file_content.decode('utf-8')
                        final_output.append(text)

                    else:
                        # For unsupported file types, add a placeholder
                        final_output.append(f"[Unsupported file type: {file_extension}]")

                if not final_output:
                    return {"status": "failed", "error": "No text could be extracted from the uploaded files."}

            except Exception as e:
                error_msg = f"Text extraction failed: {e}"
                self.logger.error(error_msg, exc_info=True)
                return {"status": "failed", "error": error_msg}

        elif paused_step.action_type == 'file_storage':
            # --- Save and Reference Logic ---
            self.logger.info("Handling as 'file_storage': Saving files and returning paths.")
            base_storage_dir = "file_attachments"
            # Use a subdirectory specified in the node, or a default
            custom_path = paused_step.storage_path or 'general'
            target_dir = os.path.join(base_storage_dir, custom_path, execution_id)
            os.makedirs(target_dir, exist_ok=True)

            saved_file_paths = []
            for file in files:
                try:
                    # Create a secure path to save the file
                    file_location = os.path.join(target_dir, file.filename)
                    with open(file_location, "wb") as buffer:
                        shutil.copyfileobj(file.file, buffer)
                    saved_file_paths.append(file_location)
                    self.logger.info(f"Successfully saved file to: {file_location}")
                except Exception as e:
                    error_msg = f"Failed to save file {file.filename}: {e}"
                    self.logger.error(error_msg, exc_info=True)
                    return {"status": "failed", "error": error_msg}
            final_output = saved_file_paths

        else:
            # Should not happen if the workflow is designed correctly
            return {"status": "failed", "error": f"Workflow paused for file upload on an unsupported step type: {paused_step.action_type}"}

        # Call the standard resume logic with the correctly prepared output
        return await self.resume_execution(execution_id, final_output)

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

    async def start_execution(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Finds the best workflow for a query via the router and starts a new execution.
        """
        all_workflows = self.storage.get_all_workflows()
        matching_workflow = self.router.find_matching_workflow(query, all_workflows)

        if not matching_workflow:
            self.logger.warning(f"No matching workflow found for query: '{query}'.")
            return { "status": "failed", "error": "No matching workflow found." }

        return await self._init_and_run(matching_workflow, query, context)

    async def start_execution_by_id(self, workflow_id: int, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Starts a new execution for a specific workflow ID, bypassing the router.
        """
        workflow = self.storage.get_workflow(workflow_id)
        if not workflow:
            self.logger.error(f"Execution start failed: Workflow with ID {workflow_id} not found.")
            return { "status": "failed", "error": f"Workflow with ID {workflow_id} not found."}

        return await self._init_and_run(workflow, query, context)

    async def _init_and_run(self, workflow: Workflow, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Private helper to initialize state and start the execution loop for a given workflow.
        """
        context = context or {}
        execution_id = str(uuid.uuid4())
        initial_state = {
            "execution_id": execution_id,
            "workflow_id": workflow.id,
            "query": query,
            "initial_context": context,
            "collected_inputs": {},
            "step_history": [],
            "current_step_id": workflow.start_step_id,
            "final_response": None
        }

        self.logger.info(f"Starting new execution {execution_id} for workflow '{workflow.name}' (ID: {workflow.id})")
        return await self._run_execution_loop(workflow, initial_state)

    async def resume_execution(self, execution_id: str, user_input: Any) -> Dict[str, Any]:
        """Resumes a paused workflow with the provided human input (text or file)."""
        paused_state = self.storage.get_execution_state(execution_id)
        if not paused_state:
            return {"status": "failed", "error": "Execution ID not found or has already completed."}

        workflow = self.storage.get_workflow(paused_state["workflow_id"])
        if not workflow:
            return {"status": "failed", "error": f"Associated workflow ID {paused_state['workflow_id']} could not be found."}

        paused_step_id = paused_state.get("current_step_id")
        paused_step = workflow.get_step(paused_step_id)
        if not paused_step:
            error_msg = f"State is corrupt. Paused step ID '{paused_step_id}' not found in workflow."
            self.logger.error(error_msg)
            return {"status": "failed", "error": error_msg}

        last_history_entry = paused_state["step_history"][-1]
        output_key = last_history_entry.get("output_key")
        if output_key:
            paused_state["collected_inputs"][output_key] = user_input

            input_summary = str(user_input)
            if isinstance(user_input, list) and len(user_input) > 0:
                input_summary = f"[{len(user_input)} document(s)]"
            elif len(input_summary) > 100:
                input_summary = input_summary[:100] + "..."

            self.logger.info(f"Resuming execution {execution_id}. Stored input '{input_summary}' under key '{output_key}'.")
            paused_state["step_history"].append({
                'step_id': paused_step_id, 'type': 'human_input_provided',
                'input_summary': str(user_input) # Avoid logging large file content
            })
        else:
            self.logger.warning(f"Resuming execution {execution_id}, but the paused step had no output_key.")

        next_step_id = paused_step.on_success
        paused_state["current_step_id"] = next_step_id
        self.logger.info(f"Advancing state from '{paused_step_id}' to next step: '{next_step_id}'.")

        return await self._run_execution_loop(workflow, paused_state)

    async def _run_execution_loop(self, workflow: Workflow, state: Dict[str, Any]) -> Dict[str, Any]:
        """

        Internal method that calls the executor and handles the result,
        managing state persistence in the database.
        """
        try:
            result = await self.executor.execute(workflow, state)
            status = result["status"]
            execution_id = result["state"]["execution_id"]

            if status == "paused":
                paused_step = workflow.get_step(result['state']['current_step_id'])
                # Record what kind of pause this is
                pause_type = result.get("pause_type", "awaiting_input")
                result['state']['step_history'].append({
                    'step_id': paused_step.step_id,
                    'type': f'pause_{pause_type}',
                    'prompt': result['response'],
                    'output_key': result['output_key']
                })
                self.storage.save_execution_state(execution_id, workflow.id, "paused", result["state"])
                self.logger.info(f"Execution {execution_id} paused for {pause_type} and state saved to DB.")

                # Construct response for the frontend
                response_payload = {
                    "status": "awaiting_input", # Generic status for client
                    "execution_id": execution_id,
                    "response": result["response"],
                    "pause_type": pause_type,
                }
                if pause_type == 'awaiting_file_upload':
                    response_payload["allowed_file_types"] = result.get("allowed_file_types")
                    response_payload["max_files"] = result.get("max_files")
                return response_payload

            self.storage.delete_execution_state(execution_id)
            if status == "completed":
                self.logger.info(f"Execution {execution_id} completed successfully.")
                return {"status": "completed", "response": result["response"]}
            else: # status == "failed"
                self.logger.error(f"Execution {execution_id} failed: {result.get('error')}")
                return {"status": "failed", "error": result.get("error", "An unknown error occurred.")}

        except Exception as e:
            self.logger.error(f"Critical error in execution loop for workflow '{workflow.name}': {e}", exc_info=True)
            if 'state' in locals() and 'execution_id' in state:
                self.storage.delete_execution_state(state['execution_id'])
            return {"status": "failed", "error": f"A critical system error occurred: {e}"}

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

    def register_tool(self, func: callable, name: str = None):
        """Registers a custom Python function as a tool the LLM can use."""
        self.tool_registry.register(func, name)
