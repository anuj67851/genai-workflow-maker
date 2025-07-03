from ..genai_workflows.tools import ToolRegistry
from . import builtin
from . import support

def register_all_tools(registry: ToolRegistry):
    """
    Discovers and registers all available tools into the given registry.
    This is the single entry point for making tools available to the engine.

    To add new tools, simply create a new module in this package
    and add its registration calls here.
    """
    # Register built-in tools
    registry.register(builtin.get_current_time)

    # Register support tools
    registry.register(support.check_customer_plan)
    registry.register(support.create_support_ticket)

    # To extend, add new registrations here:
    # from . import my_new_module
    # registry.register(my_new_module.my_cool_tool)