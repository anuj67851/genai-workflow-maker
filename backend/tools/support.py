import logging
import random
import os
from datetime import datetime
from typing import Dict, Any

# Get a logger for this specific module
logger = logging.getLogger(__name__)

# --- NEW: Define a directory for ticket outputs ---
TICKET_OUTPUT_DIR = "./ticket_outputs"
# Ensure the directory exists when the module is loaded
os.makedirs(TICKET_OUTPUT_DIR, exist_ok=True)


def check_customer_plan(email: str) -> str:
    """
    Checks the support plan level for a customer based on their email.
    In a real system, this would query a database or CRM.
    :param email: The customer's email address.
    :return: The customer's plan level, e.g., 'Standard' or 'Premium'.
    """
    logger.info(f"Checking plan for: {email}")
    premium_customers = ["admin@example.com", "vip@example.com"]
    if email.lower() in premium_customers:
        return "Premium"
    return "Standard"

def create_support_ticket(details: str) -> Dict[str, Any]:
    """
    Creates a new support ticket in the ticketing system and logs it to a file.
    In a real system, this would make an API call to Zendesk, Jira, etc.
    :param details: A summary of the ticket details, including user info and the problem.
    :return: A dictionary containing the new ticket's ID and status.
    """
    logger.info(f"Creating ticket with details: {details}")
    # Mock ticket creation
    ticket_id = f"TICKET-{random.randint(1000, 9999)}"
    status = "Open"
    logger.info(f"Generated ticket {ticket_id}")

    # --- NEW: File Writing Logic ---
    try:
        # 1. Format the content for the file
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file_content = (
            f"--- Support Ticket Log ---\n\n"
            f"Ticket ID:    {ticket_id}\n"
            f"Status:       {status}\n"
            f"Generated At: {timestamp}\n\n"
            f"--- Full Details Provided to Ticketing System ---\n"
            f"{details}\n"
        )

        # 2. Define the output file path
        file_path = os.path.join(TICKET_OUTPUT_DIR, f"{ticket_id}.txt")

        # 3. Write the content to the file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(file_content)

        logger.info(f"Successfully wrote ticket info to {file_path}")

    except Exception as e:
        # Log an error if file writing fails, but don't crash the tool
        logger.error(f"Failed to write ticket file for {ticket_id}: {e}")

    # The tool's return value to the workflow remains unchanged.
    return {"ticket_id": ticket_id, "status": status, "summary": "Ticket created successfully in the system."}