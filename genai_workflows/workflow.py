from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class WorkflowStep:
    """
    Represents a single, atomic step in a workflow.
    It includes branching logic and support for pausing to get user input.
    """
    step_id: str  # Unique identifier for this step within the workflow
    description: str

    # ENHANCEMENT: Added 'human_input' to the list of official action types.
    action_type: str  # e.g., 'agentic_tool_use', 'llm_response', 'condition_check', 'human_input'

    # The prompt or instruction for this step.
    # For 'human_input', this is the question asked to the user.
    # For 'agentic_tool_use', this is the goal for the LLM.
    # For 'llm_response', this is the instruction for generating the final text.
    prompt_template: Optional[str] = None

    # Branching logic: defines the next step_id to execute. 'END' terminates a path.
    on_success: str = 'END'
    on_failure: Optional[str] = None # Jumps to this step_id if action fails or condition is false.

    # ENHANCEMENT: Added a field to store the result key for human input.
    # For 'human_input', this is the key under which the user's response will be
    # stored in the execution state's 'collected_inputs' dictionary.
    output_key: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the step object to a dictionary."""
        return {
            "step_id": self.step_id,
            "description": self.description,
            "action_type": self.action_type,
            "prompt_template": self.prompt_template,
            "on_success": self.on_success,
            "on_failure": self.on_failure,
            "output_key": self.output_key,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowStep':
        """Deserializes a dictionary into a WorkflowStep object."""
        return cls(
            step_id=data["step_id"],
            description=data["description"],
            action_type=data["action_type"],
            prompt_template=data.get("prompt_template"),
            on_success=data.get("on_success", 'END'),
            on_failure=data.get("on_failure"),
            output_key=data.get("output_key"),
        )

@dataclass
class Workflow:
    """
    Represents a complete, executable workflow. It contains all the steps,
    metadata, and the entry point for an execution.
    """
    # The database ID is assigned after saving.
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    owner: str = "default"

    # Triggers help the Router decide when to use this workflow.
    triggers: List[str] = field(default_factory=list)

    # Steps are stored in a dict for O(1) lookup by step_id during execution.
    steps: Dict[str, WorkflowStep] = field(default_factory=dict)

    # The original natural language definition provided by the user.
    raw_definition: str = ""

    # The ID of the first step to run when the workflow is triggered.
    start_step_id: Optional[str] = None

    created_at: Optional[str] = None
    updated_at: Optional[str] = None


    def add_step(self, step: WorkflowStep):
        """Adds a step to the workflow's step dictionary. If it's the first
        step added, it is automatically designated as the start step."""
        if not self.steps:
            self.start_step_id = step.step_id
        self.steps[step.step_id] = step

    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """Retrieves a step by its unique ID."""
        return self.steps.get(step_id)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the entire workflow object to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "owner": self.owner,
            "triggers": self.triggers,
            "steps": {step_id: step.to_dict() for step_id, step in self.steps.items()},
            "raw_definition": self.raw_definition,
            "start_step_id": self.start_step_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Workflow':
        """Deserializes a dictionary into a complete Workflow object."""
        workflow = cls(
            id=data.get("id"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            owner=data.get("owner", "default"),
            triggers=data.get("triggers", []),
            raw_definition=data.get("raw_definition", ""),
            start_step_id=data.get("start_step_id"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )

        steps_dict_data = data.get("steps", {})
        if isinstance(steps_dict_data, dict):
            for step_id, step_data in steps_dict_data.items():
                if isinstance(step_data, dict):
                    workflow.steps[step_id] = WorkflowStep.from_dict(step_data)

        return workflow