import os
import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Use relative import for the package
from .genai_workflows import WorkflowEngine, Workflow, WorkflowStep

# Load environment variables from a .env file
load_dotenv()

# --- Lifespan Management ---
# This is the modern way to handle startup/shutdown logic.
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup Logic ---
    logging.info("Application starting up...")
    # Initialize the WorkflowEngine and attach it to the app's state
    # This ensures a single instance is created and shared.
    app.state.engine = WorkflowEngine(
        openai_api_key=os.getenv("OPENAI_API_KEY", "your-api-key-here"),
        db_path="workflows.db"
    )
    logging.info("WorkflowEngine initialized.")

    yield # The application runs here

    # --- Shutdown Logic ---
    logging.info("Application shutting down...")
    # Add any cleanup logic here if needed in the future

# --- FastAPI App Initialization ---
app = FastAPI(
    title="GenAI Visual Workflows API",
    description="API for creating, managing, and executing GenAI workflows.",
    version="3.0.0",
    lifespan=lifespan # Use the lifespan manager
)

# --- Pydantic Models ---
class WorkflowSaveRequest(BaseModel):
    name: str; description: Optional[str] = ""; nodes: List[Dict[str, Any]]; edges: List[Dict[str, Any]]
class ExecutionRequest(BaseModel):
    query: str; context: Optional[Dict[str, Any]] = None
class ExecutionByIdRequest(ExecutionRequest):
    workflow_id: int
class ResumeRequest(BaseModel):
    execution_id: str; user_input: Any

# --- Dependency Injection for Engine ---
# This function now gets the engine instance from the application state.
def get_engine(request: Request) -> WorkflowEngine:
    return request.app.state.engine

# --- API Endpoints ---
@app.get("/api/workflows", summary="List all workflows")
def list_workflows_endpoint(eng: WorkflowEngine = Depends(get_engine)):
    return eng.list_workflows()

@app.post("/api/workflows", summary="Save or update a workflow")
def save_workflow_endpoint(payload: WorkflowSaveRequest, eng: WorkflowEngine = Depends(get_engine)):
    try:
        nodes, edges = payload.nodes, payload.edges
        edges_by_source = {}
        for edge in edges:
            source_id, source_handle = edge.get("source"), edge.get("sourceHandle") or "default"
            if source_id not in edges_by_source: edges_by_source[source_id] = {}
            edges_by_source[source_id][source_handle] = edge.get("target")
        backend_steps = {}
        for node in nodes:
            node_id, node_type = node.get("id"), node.get("type", "").replace("Node", "")
            if node_type in ["start", "end"]: continue
            step_data = node.get("data", {}); step_data["step_id"] = node_id
            connections = edges_by_source.get(node_id, {})
            if node_type == "condition_check":
                step_data["on_success"] = connections.get("onSuccess", "END")
                step_data["on_failure"] = connections.get("onFailure", "END")
            else:
                step_data["on_success"] = connections.get("default", "END")
            if step_data.get("on_success") == "end": step_data["on_success"] = "END"
            if step_data.get("on_failure") == "end": step_data["on_failure"] = "END"
            backend_steps[node_id] = WorkflowStep.from_dict(step_data)
        start_step_id = edges_by_source.get("start", {}).get("default")
        if not start_step_id: raise ValueError("Workflow must have a connection from the START node.")
        workflow_to_save = Workflow(
            name=payload.name, description=payload.description, steps=backend_steps,
            start_step_id=start_step_id, raw_definition=payload.model_dump_json()
        )
        workflow_id = eng.save_workflow(workflow_to_save)
        return {"id": workflow_id, "name": workflow_to_save.name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process workflow graph: {e}")

@app.get("/api/workflows/{workflow_id}", summary="Get a single workflow for the builder")
def get_workflow_endpoint(workflow_id: int, eng: WorkflowEngine = Depends(get_engine)):
    workflow = eng.get_workflow(workflow_id)
    if not workflow: raise HTTPException(status_code=404, detail="Workflow not found")
    if workflow.raw_definition:
        try:
            graph_data = json.loads(workflow.raw_definition)
            return {"id": workflow.id, "name": workflow.name, "description": workflow.description, "nodes": graph_data.get("nodes", []), "edges": graph_data.get("edges", [])}
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Could not parse stored workflow definition.")
    raise HTTPException(status_code=404, detail="No valid graph definition found for this workflow.")

@app.delete("/api/workflows/{workflow_id}", status_code=204, summary="Delete a workflow")
def delete_workflow_endpoint(workflow_id: int, eng: WorkflowEngine = Depends(get_engine)):
    if not eng.delete_workflow(workflow_id): raise HTTPException(status_code=404, detail="Workflow not found")
    return {}

@app.post("/api/executions/start_by_id", summary="Start a workflow by its ID")
async def start_by_id_endpoint(req: ExecutionByIdRequest, eng: WorkflowEngine = Depends(get_engine)):
    result = await eng.start_execution_by_id(req.workflow_id, req.query, req.context)
    if result.get("status") == "failed": raise HTTPException(status_code=400, detail=result.get("error", "Execution failed"))
    return result

@app.post("/api/executions/resume", summary="Resume a paused workflow with text input")
async def resume_endpoint(req: ResumeRequest, eng: WorkflowEngine = Depends(get_engine)):
    result = await eng.resume_execution(req.execution_id, req.user_input)
    if result.get("status") == "failed": raise HTTPException(status_code=400, detail=result.get("error", "Resume failed"))
    return result

@app.post("/api/executions/resume_with_file", summary="Resume a paused workflow with file(s)")
async def resume_with_file_endpoint(
        execution_id: str = Form(...),
        files: List[UploadFile] = File(...),
        eng: WorkflowEngine = Depends(get_engine)
):
    return await eng.resume_execution_with_files(execution_id, files)

@app.get("/api/tools", tags=["Tools"])
def get_available_tools(eng: WorkflowEngine = Depends(get_engine)):
    """
    Returns a list of all currently loaded and available tools with their schemas.
    This is used by the frontend to populate the node inspector.
    """
    try:
        # The list_tools() method on our new registry already returns the
        # exact format the frontend will need.
        return eng.tool_registry.list_tools()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An internal error occurred while fetching tools: {e}"
        )

@app.post("/api/tools/rescan", tags=["Tools"])
def rescan_tools(eng: WorkflowEngine = Depends(get_engine)):
    """
    Triggers a dynamic rescan of the tool directories (`builtin` and `custom`).
    This allows for hot-reloading new or updated tools without restarting the server.
    """
    try:
        # This calls the method we created in the WorkflowEngine
        result = eng.rescan_and_load_tools()
        return result
    except Exception as e:
        # Log the exception for debugging
        logging.error(f"Failed during tool rescan: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An internal error occurred during tool rescanning: {e}"
        )

# --- Static Files Mounting (with conditional check) ---
class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope: Dict):
        try: return await super().get_response(path, scope)
        except HTTPException as ex:
            if ex.status_code == 404: return await super().get_response("index.html", scope)
            raise ex

static_files_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
if os.path.exists(static_files_path):
    app.mount("/", SPAStaticFiles(directory=static_files_path, html=True), name="static")
    logging.info(f"Serving static files from {static_files_path}")
else:
    logging.warning(f"Static files directory not found at {static_files_path}. The API will run, but the UI will not be served. Run 'npm run dev' in the frontend directory.")