from datetime import datetime

def get_current_time():
    """Gets the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")