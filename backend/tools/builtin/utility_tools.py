import shlex
from typing import List

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

@tool(name="split_string_to_list")
def split_string_to_list(input_string: str, delimiter: str = ',') -> List[str]:
    """
    Splits a string into a list of strings based on a delimiter.
    It also cleans up whitespace and handles quoted text.

    :param input_string: The string to be split (e.g., "Alice, Bob, 'Charlie Day'").
    :param delimiter: The character to split the string by. Defaults to a comma.
    :return: A list of clean strings.
    """
    # Use shlex for robust splitting that handles quotes
    splitter = shlex.shlex(input_string, posix=True)
    splitter.whitespace = delimiter
    splitter.whitespace_split = True
    return [s.strip() for s in splitter]

@tool(name="greet_person_tool")
def greet(name: str) -> str:
    """
    Generates a simple greeting for a given name.

    :param name: The name of the person to greet.
    :return: A greeting string.
    """
    return f"Hello, {name}! Welcome to the workflow."