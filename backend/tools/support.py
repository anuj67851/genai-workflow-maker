import logging
import random
from typing import Dict, Any

# Get a logger for this specific module
logger = logging.getLogger(__name__)

def check_customer_plan(email: str) -> str:
    """
    Checks the support plan level for a customer based on their email.
    In a real system, this would query a database or CRM.
    :param email: The customer's email address.
    :return: The customer's plan level, e.g., 'Standard' or 'Premium'.
    """
    logger.info(f"Checking plan for: {email}")
    # Mock database of customers
    premium_customers = ["admin@example.com", "vip@example.com"]
    if email.lower() in premium_customers:
        return "Premium"
    return "Standard"

def create_support_ticket(details: str) -> Dict[str, Any]:
    """
    Creates a new support ticket in the ticketing system.
    In a real system, this would make an API call to Zendesk, Jira, etc.
    :param details: A summary of the ticket details, including user info and the problem.
    :return: A dictionary containing the new ticket's ID and status.
    """
    logger.info(f"Creating ticket with details: {details}")
    # Mock ticket creation
    ticket_id = f"TICKET-{random.randint(1000, 9999)}"
    status = "Open"
    logger.info(f"Generated ticket {ticket_id}")
    return {"ticket_id": ticket_id, "status": status, "summary": "Ticket created successfully in the system."}