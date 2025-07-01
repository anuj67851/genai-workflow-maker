import os
import logging
import time
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from starlette.responses import JSONResponse

# Import the workflow engine and its components
from genai_workflows.core import WorkflowEngine
from genai_workflows.workflow import Workflow, WorkflowStep

# --- 1. Application Setup & Initialization ---

# Load environment variables from a .env file
load_dotenv()

# Basic logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Singleton Pattern for Workflow Engine ---
class EngineSingleton:
    _instance: Optional[WorkflowEngine] = None

    @classmethod
    def get_instance(cls) -> WorkflowEngine:
        if cls._instance is None:
            logger.info("Initializing WorkflowEngine singleton...")
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("FATAL: OPENAI_API_KEY environment variable not set.")

            db_file = "visual_workflows.db"
            cls._instance = WorkflowEngine(openai_api_key=api_key, db_path=db_file)
            register_mock_tools(cls._instance)
            logger.info("WorkflowEngine initialized successfully.")
        return cls._instance

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting up...")
    EngineSingleton.get_instance()
    yield
    logger.info("Application shutting down.")

app = FastAPI(
    title="GenAI Visual Workflow Engine API",
    description="An API for creating, managing, and executing AI-driven workflows.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def register_mock_tools(engine: WorkflowEngine):
    MOCK_ASSET_DB = {"j.doe": {"serial_number": "HW-1001"}, "a.smith": {"serial_number": "HW-2088"}}
    MOCK_WARRANTY_DB = {"HW-1001": {"status": "Active"}, "HW-2088": {"status": "Expired"}}

    @engine.register_tool
    def triage_it_issue(problem_description: str):
        """Analyzes a user's problem and categorizes it into 'Hardware', 'Software', or 'Access'."""
        desc = problem_description.lower()
        hardware_keywords = ["slow", "broken", "laptop", "screen", "won't turn on", "not working", "cracked", "keyboard", "mouse", "battery"]
        access_keywords = ["password", "access", "login", "can't log in", "locked out", "credentials"]
        software_keywords = ["software", "vpn", "email", "app", "application", "install", "error", "crashing"]

        if any(kw in desc for kw in hardware_keywords):
            return {"category": "Hardware"}
        if any(kw in desc for kw in access_keywords):
            return {"category": "Access"}
        if any(kw in desc for kw in software_keywords):
            return {"category": "Software"}
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
    id: Optional[int] = None

class ResumeExecutionRequest(BaseModel):
    execution_id: str
    user_input: Any

class StartExecutionByIdPayload(BaseModel):
    workflow_id: int
    query: str
    context: Optional[Dict[str, Any]] = None

# --- 3. Helper Functions ---

def convert_graph_to_workflow(graph_data: WorkflowGraph) -> Workflow:
    workflow = Workflow(id=graph_data.id, name=graph_data.name, description=graph_data.description, triggers=[graph_data.name.lower()])

    start_node = next((node for node in graph_data.nodes if node.type == 'startNode'), None)
    if not start_node: raise ValueError("Workflow has no start node.")

    start_edge = next((edge for edge in graph_data.edges if edge.source == start_node.id), None)
    if not start_edge: raise ValueError("Start node is not connected to any step.")
    workflow.start_step_id = start_edge.target

    edges_by_source = {edge.source: [] for edge in graph_data.edges}
    for edge in graph_data.edges:
        edges_by_source[edge.source].append(edge)

    for node in graph_data.nodes:
        if node.type in ['startNode', 'endNode']: continue

        on_success_target = 'END'
        on_failure_target = None
        source_edges = edges_by_source.get(node.id, [])
        for edge in source_edges:
            target = 'END' if edge.target == 'end' else edge.target
            if edge.sourceHandle == 'onSuccess' or node.type != 'condition_checkNode':
                on_success_target = target
            elif edge.sourceHandle == 'onFailure':
                on_failure_target = target

        # *** BUG FIX STARTS HERE ***
        # Correctly read all custom fields from the node's data payload.
        step = WorkflowStep(
            step_id=node.id,
            label=node.data.get('label'),
            description=node.data.get('description', ''),
            action_type=node.data.get('action_type', ''),
            prompt_template=node.data.get('prompt_template', ''),
            output_key=node.data.get('output_key'),
            tool_selection=node.data.get('tool_selection', 'auto'),
            tool_names=node.data.get('tool_names', []),
            on_success=on_success_target,
            on_failure=on_failure_target
        )
        # *** BUG FIX ENDS HERE ***
        workflow.add_step(step)
    return workflow

def convert_workflow_to_graph(workflow: Workflow) -> Dict[str, Any]:
    nodes, edges = [], []
    y_pos, x_pos = 50, 250
    nodes.append({"id": "start", "type": "startNode", "position": {"x": x_pos, "y": y_pos}, "data": {}})
    y_pos += 150
    if workflow.start_step_id:
        edges.append({"id": "e-start-connection", "source": "start", "target": workflow.start_step_id})

    for step_id, step in workflow.steps.items():
        nodes.append({
            "id": step.step_id, "type": f"{step.action_type}Node",
            "position": {"x": x_pos, "y": y_pos}, "data": step.to_dict()
        })
        y_pos += 150
        if step.on_success:
            edges.append({
                "id": f"e-{step.step_id}-success", "source": step.step_id,
                "target": "end" if step.on_success == "END" else step.on_success,
                "sourceHandle": "onSuccess" if step.action_type == "condition_check" else None
            })
        if step.on_failure:
            edges.append({
                "id": f"e-{step.step_id}-failure", "source": step.step_id,
                "target": "end" if step.on_failure == "END" else step.on_failure,
                "sourceHandle": "onFailure"
            })

    nodes.append({"id": "end", "type": "endNode", "position": {"x": x_pos, "y": y_pos}, "data": {}})
    return {"nodes": nodes, "edges": edges}

# --- 4. API Endpoints ---

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/tools")
def list_available_tools():
    engine = EngineSingleton.get_instance()
    return engine.tool_registry.list_tools()

@app.post("/api/workflows", status_code=201)
def save_workflow(graph: WorkflowGraph):
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
    engine = EngineSingleton.get_instance()
    return engine.list_workflows()

@app.get("/api/workflows/{workflow_id}")
def get_workflow_graph(workflow_id: int):
    engine = EngineSingleton.get_instance()
    workflow = engine.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    graph = convert_workflow_to_graph(workflow)
    return {"id": workflow.id, "name": workflow.name, "description": workflow.description, **graph}

@app.delete("/api/workflows/{workflow_id}", status_code=200)
def delete_workflow(workflow_id: int):
    engine = EngineSingleton.get_instance()
    if not engine.delete_workflow(workflow_id):
        raise HTTPException(status_code=404, detail="Workflow not found.")
    return {"status": "success", "message": f"Workflow {workflow_id} deleted."}

@app.post("/api/executions/start_by_id")
async def execute_workflow_by_id(payload: StartExecutionByIdPayload):
    try:
        engine = EngineSingleton.get_instance()
        result = engine.start_execution_by_id(
            workflow_id=payload.workflow_id, query=payload.query, context=payload.context
        )
        if result.get("status") == "failed":
            return JSONResponse(status_code=400, content={"detail": result.get("error", "Failed to start execution.")})
        return result
    except Exception as e:
        logger.error(f"Critical error starting execution for workflow_id {payload.workflow_id}: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"detail": "An internal server error occurred."})

@app.post("/api/executions/resume")
def resume_workflow_execution(request: ResumeExecutionRequest):
    try:
        engine = EngineSingleton.get_instance()
        result = engine.resume_execution(request.execution_id, request.user_input)
        return result
    except Exception as e:
        logger.error(f"Error resuming execution: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# --- Main entrypoint for running the server ---
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)