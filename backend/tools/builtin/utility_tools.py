from backend.tools.decorator import tool
from datetime import datetime

@tool(name="get_current_time")
def get_current_time(timezone: str = "UTC") -> str:
    """
    Returns the current date and time in a specified timezone.

    :param timezone: The timezone to use, e.g., 'UTC', 'America/New_York'.
                     Defaults to UTC if not provided.
    :return: A string representing the current date and time.
    """
    # Note: This is a simplified example. A real implementation would use
    # a library like 'pytz' or 'zoneinfo' for proper timezone handling.
    now = datetime.now()
    return f"The current time in {timezone} is approximately {now.strftime('%Y-%m-%d %H:%M:%S')}."


@tool(name="simple_calculator")
def simple_calculator(expression: str) -> str:
    """
    Evaluates a simple mathematical expression (addition, subtraction, multiplication, division).

    This tool is for demonstration purposes and uses Python's eval(),
    which can be insecure. DO NOT use this in a real production environment
    without proper sandboxing and input validation.

    :param expression: A string containing the mathematical expression to evaluate, like "5 * (10 + 2)".
    :return: A string containing the result of the calculation or an error message.
    """
    try:
        # WARNING: eval() is dangerous and should not be used with untrusted input.
        # This is for demonstration only.
        allowed_chars = "0123456789+-*/(). "
        if not all(char in allowed_chars for char in expression):
            return "Error: Expression contains invalid characters."

        result = eval(expression)
        return f"The result of '{expression}' is {result}."
    except Exception as e:
        return f"Error evaluating expression: {e}"