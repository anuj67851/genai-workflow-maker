from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class WorkflowStep:
    """Represents a single, atomic step in a workflow."""
    step_id: str
    description: str
    action_type: str
    prompt_template: Optional[str] = None
    on_success: str = 'END'
    on_failure: Optional[str] = None
    output_key: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        # This is correct
        return self.__dict__

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowStep':
        # This is correct
        # Use dictionary unpacking for simplicity, ensures all fields are mapped.
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
        # This is correct
        if not self.steps:
            self.start_step_id = step.step_id
        self.steps[step.step_id] = step

    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        # This is correct
        return self.steps.get(step_id)

    def to_dict(self) -> Dict[str, Any]:
        # This is correct
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