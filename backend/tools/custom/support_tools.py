import random
from datetime import datetime, timedelta

from backend.tools.decorator import tool

FAKE_TICKET_DB = {
    "TKT-12345": {
        "status": "In Progress",
        "customer_email": "alice@example.com",
        "assigned_agent": "Bob",
        "last_update": "2024-05-20T10:00:00Z",
        "problem": "Cannot connect to the internet.",
        "notes": ["Customer rebooted router, no change."]
    },
    "TKT-67890": {
        "status": "Closed",
        "customer_email": "bob@example.com",
        "assigned_agent": "David",
        "last_update": "2024-05-19T15:30:00Z",
        "problem": "Printer is not working.",
        "notes": ["Resolved by sending customer new driver link."]
    }
}

FAKE_USER_PLANS_DB = {
    "alice@example.com": "Premium Plan",
    "bob@example.com": "Standard Plan",
    "david@example.com": "Premium Plan"
    # Note: A user like 'charlie@example.com' is not in this DB
    # to allow for testing the "user not found" case.
}

FAKE_WARRANTY_DB = {
    "SKU-XYZ-001": {"purchase_date": "2023-06-15", "warranty_months": 12},
    "SKU-ABC-002": {"purchase_date": "2022-01-10", "warranty_months": 24}
}

FAKE_SYSTEM_STATUS_DB = {
    "Website": "Operational",
    "API": "Operational",
    "Billing System": "Operational"
}
# ---------------------------------------------


@tool
def check_customer_plan(customer_email: str) -> str:
    """
    Checks the customer's current subscription plan (e.g., Standard or Premium).

    :param customer_email: The email address of the customer to look up.
    :return: A string indicating the customer's current plan, or a 'not found' message.
    """
    plan = FAKE_USER_PLANS_DB.get(customer_email)
    if not plan:
        return f"No customer account found for the email '{customer_email}'."
    return f"The customer with email '{customer_email}' is on the '{plan}'."


@tool
def lookup_ticket_status(ticket_id: str) -> str:
    """
    Looks up the current status and details of a specific support ticket.

    :param ticket_id: The unique identifier for the support ticket (e.g., 'TKT-12345').
    :return: A string summarizing the ticket's status, or a 'not found' message.
    """
    ticket = FAKE_TICKET_DB.get(ticket_id)
    if not ticket:
        return f"Sorry, I could not find a ticket with the ID '{ticket_id}'."

    return (
        f"Ticket {ticket_id} status: '{ticket['status']}'. "
        f"Assigned to: {ticket['assigned_agent']}. "
        f"Problem: {ticket['problem']}. "
        f"Notes: {' | '.join(ticket['notes'])}"
    )


@tool
def create_support_ticket(customer_email: str, problem_description: str, priority: str = "Medium") -> str:
    """
    Creates a new support ticket in the system.

    :param customer_email: The email address of the customer reporting the issue.
    :param problem_description: A detailed description of the problem the customer is facing.
    :param priority: The priority of the ticket. Can be 'Low', 'Medium', or 'High'. Defaults to 'Medium'.
    :return: A confirmation string with the new ticket ID.
    """
    new_ticket_id = f"TKT-{random.randint(10000, 99999)}"
    FAKE_TICKET_DB[new_ticket_id] = {
        "status": "Open",
        "customer_email": customer_email,
        "assigned_agent": "Unassigned",
        "last_update": datetime.now().isoformat(),
        "problem": problem_description,
        "priority": priority,
        "notes": [f"Ticket created with priority: {priority}"]
    }
    return f"I have successfully created a new support ticket for you. Your ticket ID is {new_ticket_id}."


@tool
def check_product_warranty(product_sku: str) -> str:
    """
    Checks the warranty status for a given product SKU.

    :param product_sku: The Stock Keeping Unit (SKU) of the product (e.g., 'SKU-XYZ-001').
    :return: A string describing the product's warranty status and expiration date.
    """
    warranty_info = FAKE_WARRANTY_DB.get(product_sku)
    if not warranty_info:
        return f"I could not find warranty information for product SKU '{product_sku}'."

    purchase_date = datetime.strptime(warranty_info["purchase_date"], "%Y-%m-%d")
    warranty_months = warranty_info["warranty_months"]
    expiration_date = purchase_date + timedelta(days=warranty_months * 30) # Approximate

    if datetime.now() > expiration_date:
        return f"The warranty for product {product_sku} expired on {expiration_date.strftime('%Y-%m-%d')}."
    else:
        return f"Product {product_sku} is under warranty until {expiration_date.strftime('%Y-%m-%d')}."


@tool
def check_system_outages() -> str:
    """
    Checks the operational status of all major internal systems.

    :return: A report of the system status.
    """
    report = []
    is_any_issue = False
    for service, status in FAKE_SYSTEM_STATUS_DB.items():
        report.append(f"- {service}: {status}")
        if status != "Operational":
            is_any_issue = True

    if is_any_issue:
        summary = "There are some ongoing system issues.\n"
    else:
        summary = "All systems are fully operational.\n"

    return summary + "\n".join(report)