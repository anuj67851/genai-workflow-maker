import os
import logging
import time
from typing import List, Dict, Any, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Import the workflow engine and its components
# Note: You must place the `genai_workflows` package in the `backend` directory
from genai_workflows.core import WorkflowEngine
from genai_workflows.workflow import Workflow, WorkflowStep

# --- 1. Application Setup & Initialization ---

# Load environment variables from a .env file
load_dotenv()

# Basic logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create the FastAPI app instance
app = FastAPI(
    title="GenAI Visual Workflow Engine API",
    description="An API for creating, managing, and executing AI-driven workflows.",
    version="1.0.0"
)

# Configure CORS (Cross-Origin Resource Sharing)
# This allows the React frontend (running on a different port) to communicate with the backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], # The origin of the React app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Singleton Pattern for Workflow Engine ---
# This ensures we initialize the engine (and its DB) only once.
class EngineSingleton:
    _instance: Optional[WorkflowEngine] = None

    @classmethod
    def get_instance(cls) -> WorkflowEngine:
        if cls._instance is None:
            logger.info("Initializing WorkflowEngine singleton...")
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("FATAL: OPENAI_API_KEY environment variable not set.")

            # Ensure a clean slate for the demo by removing the old DB file on startup
            db_file = "visual_workflows.db"
            # if os.path.exists(db_file):
            #     os.remove(db_file)
            #     logger.info(f"Removed existing database file: {db_file}")

            cls._instance = WorkflowEngine(openai_api_key=api_key, db_path=db_file)
            register_mock_tools(cls._instance) # Register tools on first init
            logger.info("WorkflowEngine initialized successfully.")
        return cls._instance

# --- Mock Tools (Adapted from your app.py) ---
# We register these directly so the backend is self-contained.

def register_mock_tools(engine: WorkflowEngine):
    """Registers a set of deterministic tools for the IT support demo."""
    MOCK_ASSET_DB = {"j.doe": {"serial_number": "HW-1001"}, "a.smith": {"serial_number": "HW-2088"}}
    MOCK_WARRANTY_DB = {"HW-1001": {"status": "Active"}, "HW-2088": {"status": "Expired"}}

    @engine.register_tool
    def triage_it_issue(problem_description: str):
        """Analyzes a user's problem and categorizes it into 'Hardware', 'Software', or 'Access'."""
        desc = problem_description.lower()
        if any(kw in desc for kw in ["slow", "broken", "laptop"]): return {"category": "Hardware"}
        if any(kw in desc for kw in ["password", "access"]): return {"category": "Access"}
        if any(kw in desc for kw in ["software", "vpn", "email"]): return {"category": "Software"}
        return {"category": "Unknown"}

    @engine.register_tool
    def check_device_warranty(username: str):
        """Looks up a user's device and checks its warranty status."""
        if username not in MOCK_ASSET_DB: return {"status": "error", "reason": "User not found."}
        serial = MOCK_ASSET_DB[username]["serial_number"]
        warranty_info = MOCK_WARRANTY_DB.get(serial, {"status": "Not Found"})
        return {"serial_number": serial, "warranty": warranty_info}

    @engine.register_tool
    def create_support_ticket(username: str, problem_description: str):
        """Creates a new support ticket."""
        ticket_id = f"IT-{int(time.time()) % 10000}"
        return {"status": "success", "ticket_id": ticket_id, "summary": problem_description}

    logger.info("Mock IT tools registered.")


# --- 2. Pydantic Models for API Data Validation ---

class NodeData(BaseModel):
    id: str
    type: str
    position: Dict[str, float]
    data: Dict[str, Any]

class EdgeData(BaseModel):
    id: str
    source: str
    target: str
    sourceHandle: Optional[str] = None

class WorkflowGraph(BaseModel):
    name: str
    description: str
    nodes: List[NodeData]
    edges: List[EdgeData]
    id: Optional[int] = None # Include ID for updates

class StartExecutionRequest(BaseModel):
    workflow_id: int
    query: str
    context: Optional[Dict[str, Any]] = None

class ResumeExecutionRequest(BaseModel):
    execution_id: str
    user_input: Any


# --- 3. Helper Functions ---


def convert_graph_to_workflow(graph_data: WorkflowGraph) -> Workflow:
    """
    Translates the node-edge graph from React Flow into an executable Workflow object.
    """
    workflow = Workflow(id=graph_data.id, name=graph_data.name, description=graph_data.description, triggers=[graph_data.name.lower()])
    target_node_ids = {edge.target for edge in graph_data.edges}
    start_nodes = [node for node in graph_data.nodes if node.id not in target_node_ids and node.type == 'startNode']
    if not start_nodes: raise ValueError("Workflow has no start node.")

    # The true start step is the one connected to the 'startNode'
    start_edge = next((edge for edge in graph_data.edges if edge.source == start_nodes[0].id), None)
    if not start_edge: raise ValueError("Start node is not connected to any step.")
    workflow.start_step_id = start_edge.target

    edges_by_source = {}
    for edge in graph_data.edges:
        if edge.source not in edges_by_source: edges_by_source[edge.source] = []
        edges_by_source[edge.source].append(edge)

    for node in graph_data.nodes:
        if node.type in ['startNode', 'endNode']: continue

        on_success_target = 'END' # Default to END if not connected
        on_failure_target = None

        source_edges = edges_by_source.get(node.id, [])
        for edge in source_edges:
            # *** THIS IS THE CRITICAL FIX ***
            # If the target is the special UI node 'end', set the target to the string 'END'
            # which the engine understands as a termination signal.
            target = 'END' if edge.target == 'end' else edge.target

            if edge.sourceHandle == 'onSuccess' or node.type != 'condition_checkNode':
                on_success_target = target
            elif edge.sourceHandle == 'onFailure':
                on_failure_target = target

        step = WorkflowStep(
            step_id=node.id,
            description=node.data.get('description', ''),
            action_type=node.data.get('action_type', ''),
            prompt_template=node.data.get('prompt_template', ''),
            output_key=node.data.get('output_key', None),
            on_success=on_success_target,
            on_failure=on_failure_target
        )
        workflow.add_step(step)
    return workflow


def convert_workflow_to_graph(workflow: Workflow) -> Dict[str, Any]:
    """
    Translates a saved Workflow object back into a graph structure for React Flow.
    This version correctly creates START/END nodes and maps connections.
    """
    nodes = []
    edges = []

    # Simple layout positioning
    y_pos = 50
    x_pos = 250

    # Add the essential START node for the UI
    nodes.append({"id": "start", "type": "startNode", "position": {"x": x_pos, "y": y_pos}, "data": {}})
    y_pos += 150

    # If there's a defined start step, connect the START node to it
    if workflow.start_step_id:
        edges.append({"id": "e-start-connection", "source": "start", "target": workflow.start_step_id})

    # Create a UI node for every step in the workflow
    for step_id, step in workflow.steps.items():
        nodes.append({
            "id": step.step_id,
            "type": f"{step.action_type}Node",
            "position": {"x": x_pos, "y": y_pos}, # Use a simple vertical layout for now
            "data": step.to_dict()
        })
        y_pos += 150

        # Create the success edge
        if step.on_success:
            # Map the special 'END' keyword back to the UI's 'end' node ID
            target_id = "end" if step.on_success == "END" else step.on_success
            edges.append({
                "id": f"e-{step.step_id}-success",
                "source": step.step_id,
                "target": target_id,
                # Add the specific source handle for condition nodes for correct rendering
                "sourceHandle": "onSuccess" if step.action_type == "condition_check" else None
            })

        # Create the failure edge if it exists
        if step.on_failure:
            target_id = "end" if step.on_failure == "END" else step.on_failure
            edges.append({
                "id": f"e-{step.step_id}-failure",
                "source": step.step_id,
                "target": target_id,
                "sourceHandle": "onFailure"
            })

    # Add the essential END node for the UI
    nodes.append({"id": "end", "type": "endNode", "position": {"x": x_pos, "y": y_pos}, "data": {}})

    return {"nodes": nodes, "edges": edges}


# --- 4. API Endpoints ---

@app.on_event("startup")
async def startup_event():
    """On startup, initialize the engine and register tools."""
    EngineSingleton.get_instance()
    logger.info("Application startup complete.")

@app.get("/api/health")
def health_check():
    """Simple endpoint to check if the API is running."""
    return {"status": "ok"}

@app.get("/api/tools")
def list_available_tools():
    """Returns a list of all registered tools the workflows can use."""
    engine = EngineSingleton.get_instance()
    return engine.tool_registry.list_tools()

@app.post("/api/workflows", status_code=201)
def save_workflow(graph: WorkflowGraph):
    """
    Receives a workflow graph from the frontend, converts it, and saves it.
    """
    try:
        engine = EngineSingleton.get_instance()
        workflow_obj = convert_graph_to_workflow(graph)
        workflow_id = engine.save_workflow(workflow_obj)
        logger.info(f"Saved workflow '{graph.name}' with ID: {workflow_id}")
        return {"id": workflow_id, "name": graph.name}
    except Exception as e:
        logger.error(f"Error saving workflow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/workflows")
def list_saved_workflows():
    """Returns a list of all saved workflows."""
    engine = EngineSingleton.get_instance()
    return engine.list_workflows()

@app.get("/api/workflows/{workflow_id}")
def get_workflow_graph(workflow_id: int):
    """
    Retrieves a specific workflow and converts it into a React Flow-compatible graph.
    """
    engine = EngineSingleton.get_instance()
    workflow = engine.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    graph = convert_workflow_to_graph(workflow)
    return {
        "id": workflow.id,
        "name": workflow.name,
        "description": workflow.description,
        **graph
    }

@app.post("/api/executions/start")
def start_workflow_execution(request: StartExecutionRequest):
    """Starts a new execution of a specified workflow."""
    try:
        engine = EngineSingleton.get_instance()
        # Find the workflow by name, as the UI might not have the ID for the first run
        workflows = engine.list_workflows()
        matching_wf = next((wf for wf in workflows if wf['id'] == request.workflow_id), None)

        if not matching_wf:
            # Fallback to the router if not found by ID (though it should be)
            all_workflows = engine.storage.get_all_workflows()
            found_workflow = engine.router.find_matching_workflow(request.query, all_workflows)
        else:
            found_workflow = engine.get_workflow(request.workflow_id)

        if not found_workflow:
            raise HTTPException(status_code=404, detail="No matching workflow found for the query.")

        result = engine.start_execution(request.query, context=request.context)
        return result
    except Exception as e:
        logger.error(f"Error starting execution: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/executions/resume")
def resume_workflow_execution(request: ResumeExecutionRequest):
    """Resumes a paused workflow execution with user-provided input."""
    try:
        engine = EngineSingleton.get_instance()
        result = engine.resume_execution(request.execution_id, request.user_input)
        return result
    except Exception as e:
        logger.error(f"Error resuming execution: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/workflows/{workflow_id}", status_code=200)
def delete_workflow(workflow_id: int):
    """Deletes a workflow by its ID."""
    engine = EngineSingleton.get_instance()
    success = engine.delete_workflow(workflow_id)
    if not success:
        raise HTTPException(status_code=404, detail="Workflow not found or could not be deleted.")
    logger.info(f"Successfully deleted workflow with ID: {workflow_id}")
    return {"status": "success", "message": f"Workflow {workflow_id} deleted."}

# --- Main entrypoint for running the server ---
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)