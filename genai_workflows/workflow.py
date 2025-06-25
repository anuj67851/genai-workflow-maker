from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class WorkflowStep:
    """Represents a single step in a workflow, now with branching."""
    step_id: str  # Unique identifier for this step within the workflow
    description: str
    action_type: str  # e.g., 'agentic_tool_use', 'llm_response', 'condition_check'

    # For action_type='llm_response' or 'agentic_tool_use'
    prompt_template: Optional[str] = None

    # For branching logic
    # Can be a step_id, 'END', or 'RESPOND'
    on_success: str = 'END'
    on_failure: Optional[str] = None # Jumps to this step_id if action fails

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "description": self.description,
            "action_type": self.action_type,
            "prompt_template": self.prompt_template,
            "on_success": self.on_success,
            "on_failure": self.on_failure,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowStep':
        return cls(
            step_id=data["step_id"],
            description=data["description"],
            action_type=data["action_type"],
            prompt_template=data.get("prompt_template"),
            on_success=data.get("on_success", 'END'),
            on_failure=data.get("on_failure"),
        )

@dataclass
class Workflow:
    """Represents a complete workflow with a dictionary of steps for easy lookup."""
    name: str = ""
    description: str = ""
    owner: str = "default"
    # Triggers help the Router decide when to use this workflow
    triggers: List[str] = field(default_factory=list)
    # Steps are stored in a dict for easy branching using step_id
    steps: Dict[str, WorkflowStep] = field(default_factory=dict)
    raw_definition: str = ""
    start_step_id: Optional[str] = None
    created_at: Optional[str] = None

    def add_step(self, step: WorkflowStep):
        """Add a step to the workflow. Set the start_step_id if it's the first."""
        if not self.start_step_id:
            self.start_step_id = step.step_id
        self.steps[step.step_id] = step

    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        return self.steps.get(step_id)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "owner": self.owner,
            "triggers": self.triggers,
            "steps": {step_id: step.to_dict() for step_id, step in self.steps.items()},
            "raw_definition": self.raw_definition,
            "start_step_id": self.start_step_id,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Workflow':
        workflow = cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            owner=data.get("owner", "default"),
            triggers=data.get("triggers", []),
            raw_definition=data.get("raw_definition", ""),
            start_step_id=data.get("start_step_id"),
            created_at=data.get("created_at")
        )

        steps_dict_data = data.get("steps", {})
        for step_id, step_data in steps_dict_data.items():
            # This check is a safeguard, but step_data should always be a dict here.
            if isinstance(step_data, dict):
                workflow.steps[step_id] = WorkflowStep.from_dict(step_data)

        return workflow