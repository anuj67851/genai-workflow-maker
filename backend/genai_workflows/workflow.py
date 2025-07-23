from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class WorkflowStep:
    """Represents a single, atomic step in a workflow."""
    step_id: str
    description: str
    action_type: str  # 'agentic_tool_use', 'llm_response', 'condition_check', 'human_input', 'workflow_call', 'file_ingestion', 'vector_db_ingestion', 'vector_db_query', 'cross_encoder_rerank', 'file_storage', 'http_request', 'intelligent_router', 'direct_tool_call', 'display_message'
    prompt_template: Optional[str] = None
    on_success: str = 'END'
    on_failure: Optional[str] = None
    output_key: Optional[str] = None
    label: Optional[str] = None

    # Fields for 'agentic_tool_use'
    tool_selection: str = 'auto'  # 'auto', 'manual', 'none'
    tool_names: Optional[List[str]] = field(default_factory=list)

    # --- Field for 'workflow_call' ---
    target_workflow_id: Optional[int] = None
    input_mappings: Optional[str] = None # A JSON string template. E.g., '{"child_key": "{input.parent_key}"}'

    # --- Fields for 'file_ingestion' ---
    allowed_file_types: Optional[List[str]] = field(default_factory=list)  # e.g., ['.pdf', '.txt']
    max_files: int = 1

    # --- Fields for RAG nodes ---
    collection_name: Optional[str] = None  # For ingestion and query
    embedding_model: Optional[str] = None  # For ingestion
    chunk_size: Optional[int] = 1000  # For ingestion
    chunk_overlap: Optional[int] = 200  # For ingestion
    top_k: Optional[int] = 5  # For query
    rerank_top_n: Optional[int] = 3  # For rerank

    # --- Field for LLM model selection ---
    model_name: Optional[str] = None  # For LLM-based actions

    # --- Field for 'file_storage' ---
    storage_path: Optional[str] = None  # e.g., 'tickets/attachments'

    # --- Fields for 'http_request' ---
    http_method: Optional[str] = 'GET' # e.g., GET, POST, PUT, DELETE
    url_template: Optional[str] = None
    headers_template: Optional[str] = None # JSON string
    body_template: Optional[str] = None # JSON string

    # --- Fields for 'intelligent_router' ---
    # Stores a mapping of route names to target step_ids. E.g., {"billing": "ask_billing_question", "technical": "create_tech_ticket"}
    routes: Optional[Dict[str, str]] = field(default_factory=dict)

    # --- Fields for Database nodes ---
    table_name: Optional[str] = None
    primary_key_columns: Optional[List[str]] = field(default_factory=list)
    data_template: Optional[str] = None # JSON string template for save node
    query_template: Optional[str] = None # SQL string template for query node

    # --- Fields for 'direct_tool_call' ---
    target_tool_name: Optional[str] = None

    # --- Fields for 'start_loop' ---
    input_collection_variable: Optional[str] = None
    current_item_output_key: Optional[str] = None
    loop_body_start_step_id: Optional[str] = None # This will be populated by from_graph

    # --- Field for 'end_loop' ---
    value_to_return: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        # Exclude fields with default or None values for cleaner serialization, if desired.
        # For now, a simple conversion is robust.
        return {k: v for k, v in self.__dict__.items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowStep':
        # Use dictionary unpacking for simplicity, ensures all fields are mapped.
        # This is robust to new fields being added to the dataclass.
        return cls(**data)


@dataclass
class Workflow:
    """Represents a complete, executable workflow."""
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    owner: str = "default"
    triggers: List[str] = field(default_factory=list)
    steps: Dict[str, WorkflowStep] = field(default_factory=dict)
    raw_definition: str = ""
    start_step_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def add_step(self, step: WorkflowStep):
        if not self.steps:
            self.start_step_id = step.step_id
        self.steps[step.step_id] = step

    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        return self.steps.get(step_id)

    def to_dict(self) -> Dict[str, Any]:
        # Create a copy to avoid modifying the original object's __dict__
        d = self.__dict__.copy()
        # Ensure nested steps are also serialized to dictionaries
        d["steps"] = {sid: s.to_dict() for sid, s in self.steps.items()}
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Workflow':
        """
        Deserializes a dictionary into a complete Workflow object.
        """
        # Create an empty instance of the Workflow class.
        steps_data = data.pop('steps', {})

        # Create the workflow instance using only the simple fields.
        # This avoids any type mismatch errors with the dataclass constructor.
        workflow = cls(**data)

        # Now, manually iterate through the separated steps data and reconstruct
        # the WorkflowStep objects, populating the new workflow's 'steps' dictionary.
        if isinstance(steps_data, dict):
            for step_id, step_dict in steps_data.items():
                workflow.steps[step_id] = WorkflowStep.from_dict(step_dict)

        return workflow

    @classmethod
    def from_graph(
            cls, name: str, description: str, raw_definition: str, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]
    ) -> 'Workflow':
        """
        Constructs a Workflow object from frontend graph data (nodes and edges).
        """
        node_types_by_id = {node['id']: node.get('type', '').replace('Node', '') for node in nodes}

        edges_by_source = {}
        for edge in edges:
            source_id = edge.get("source")
            source_handle = edge.get("sourceHandle") or "default"
            source_node_type = node_types_by_id.get(source_id)

            if source_id not in edges_by_source:
                edges_by_source[source_id] = {}

            # Special handling for our start_loop node's unique handles
            if source_node_type == 'start_loop':
                if source_handle == 'loopBody':
                    # This handle defines the start of the loop's body.
                    edges_by_source[source_id]['loopBody'] = edge.get("target")
                elif source_handle == 'onSuccess':
                    # This handle defines the path after the loop completes.
                    edges_by_source[source_id]['onSuccess'] = edge.get("target")
                elif source_handle == 'onFailure':
                    # The standard failure path
                    edges_by_source[source_id]['onFailure'] = edge.get("target")
            else:
                # Standard handle processing for all other nodes
                edges_by_source[source_id][source_handle] = edge.get("target")


        backend_steps = {}
        for node in nodes:
            node_id = node.get("id")
            # The frontend node type has "Node" appended, e.g., "condition_checkNode"
            # The backend action_type is just "condition_check"
            node_type = node.get("type", "").replace("Node", "")
            if node_type in ["start", "end"]:
                continue

            # The frontend passes all the step data inside the `data` key.
            step_data = node.get("data", {})
            step_data["step_id"] = node_id

            # For most nodes, the frontend may not have an action_type in its data block,
            # so we derive it from the node's main `type` field.
            if "action_type" not in step_data:
                step_data["action_type"] = node_type

            connections = edges_by_source.get(node_id, {})

            if node_type == "start_loop":
                step_data["loop_body_start_step_id"] = connections.get("loopBody", "END")
                step_data["on_success"] = connections.get("onSuccess", "END")
                step_data["on_failure"] = connections.get("onFailure") # Can be None
            elif node_type == "intelligent_router":
                # Get the routes dict from the node's data (e.g., {"query": "END", "create": "END"})
                current_routes = step_data.get('routes', {})
                updated_routes = {}
                # For each defined route name, find its actual connection target from the edges
                for route_name in current_routes.keys():
                    # The edge's sourceHandle IS the route name. Find its target.
                    target_node_id = connections.get(route_name, "END")
                    updated_routes[route_name] = target_node_id
                step_data['routes'] = updated_routes
            elif node_type == "condition_check":
                # Explicit handles for condition nodes
                step_data["on_success"] = connections.get("onSuccess", "END")
                step_data["on_failure"] = connections.get("onFailure", "END")
            else:
                # Default handle for all other nodes
                step_data["on_success"] = connections.get("default", "END")
                # Optional failure path
                if "onFailure" in connections:
                    step_data["on_failure"] = connections.get("onFailure")

            # Normalize 'end' to 'END' for consistency
            if step_data.get("on_success") == "end": step_data["on_success"] = "END"
            if step_data.get("on_failure") == "end": step_data["on_failure"] = "END"
            if step_data.get("loop_body_start_step_id") == "end": step_data["loop_body_start_step_id"] = "END"


            # Remove any frontend-specific helper properties
            step_data.pop('_version', None)

            backend_steps[node_id] = WorkflowStep.from_dict(step_data)

        start_step_id = edges_by_source.get("start", {}).get("default")
        if not start_step_id:
            raise ValueError("Workflow must have a connection from the START node.")

        return cls(
            name=name,
            description=description,
            steps=backend_steps,
            start_step_id=start_step_id,
            raw_definition=raw_definition
        )
