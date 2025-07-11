from typing import Callable

# This is a simple marker. The ToolLoader will scan modules and look for
# functions that have been "tagged" by this decorator.
# By attaching a spec to the function object itself, we keep the registration
# logic separate from the function's definition.

def tool(func: Callable = None, name: str = None) -> Callable:
    """
    A decorator to mark a function as a discoverable tool for the Workflow Engine.

    When the ToolLoader scans a module, it will identify any function
    decorated with @tool and prepare it for registration.

    Usage:

    @tool
    def my_simple_tool(arg1: str):
        ...

    @tool(name="custom_tool_name")
    def another_tool(arg1: int):
        ...

    Args:
        func: The function to be decorated (implicitly passed).
        name: An optional override for the tool's name. If not provided,
              the function's __name__ will be used.

    Returns:
        The decorated function, with an added '_tool_spec' attribute
        that the loader will use for discovery.
    """
    def decorator(f: Callable):
        tool_name = name or f.__name__
        # Attach a simple specification to the function object.
        # The ToolLoader will look for this attribute to identify tools.
        f._tool_spec = {
            "function": f,
            "name": tool_name
        }
        return f

    # This logic handles both @tool and @tool(name=...) syntaxes
    if func:
        return decorator(func)
    return decorator