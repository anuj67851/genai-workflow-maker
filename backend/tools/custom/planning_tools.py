from backend.tools.decorator import tool

@tool(name="create_calendar_event")
def create_calendar_event(event_title: str, start_time: str, attendees_str: str) -> str:
    """
    Schedules a new event in a calendar. This is a mock tool.

    It takes the event details and returns a confirmation message.

    :param event_title: The title or name of the event.
    :param start_time: The start time for the event, in ISO format (e.g., '2025-09-15T10:00:00Z').
    :param attendees_str: A comma-separated string of attendee email addresses.
    :return: A string confirming the event was scheduled.
    """

    if not event_title or not start_time:
        return "Error: Event title and start time cannot be empty."

    # Split the attendee string into a clean list
    attendees = [email.strip() for email in attendees_str.split(',') if email.strip()]

    if not attendees:
        return f"Successfully scheduled event '{event_title}' at {start_time}. There are no attendees."

    return f"Successfully scheduled event '{event_title}' at {start_time} with attendees: {', '.join(attendees)}."