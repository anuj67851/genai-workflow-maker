import logging
import sys

# Configure logging as soon as the package is imported.
# This ensures all modules get the same configuration.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout  # Explicitly log to standard output.
)


from .core import WorkflowEngine
from .workflow import Workflow, WorkflowStep
from .storage import WorkflowStorage
from .router import WorkflowRouter
from .executor import WorkflowExecutor

from .interactive_parser import InteractiveWorkflowParser
from .visualization import WorkflowVisualizer

__version__ = "3.0.0"

__all__ = [
    # Core Components
    "WorkflowEngine",
    "Workflow",
    "WorkflowStep",

    # Major Sub-systems
    "InteractiveWorkflowParser",
    "WorkflowExecutor",
    "WorkflowVisualizer",
    "WorkflowStorage",
    "WorkflowRouter",
]