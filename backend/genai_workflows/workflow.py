from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class WorkflowStep:
    """Represents a single, atomic step in a workflow."""
    step_id: str
    description: str
    action_type: str  # 'agentic_tool_use', 'llm_response', 'condition_check', 'human_input', 'workflow_call', 'file_ingestion', 'vector_db_ingestion', 'vector_db_query', 'cross_encoder_rerank', 'file_storage', 'http_request', 'intelligent_router'
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
