# A more sophisticated example usage and testing script for the refactored workflow system.
from dotenv import load_dotenv
import os
import logging
import time

from genai_workflows.core import WorkflowEngine

# --- Setup Logging ---
# Ensures logs from the engine are displayed, which is crucial for debugging.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# --- Deterministic Mock Tools for Predictable Testing ---

# A hardcoded database of users and their assets for our mock tools.
MOCK_ASSET_DB = {
    "j.doe": {"serial_number": "HW-1001", "name": "Laptop"},
    "a.smith": {"serial_number": "HW-2088", "name": "Desktop"},
}
MOCK_WARRANTY_DB = {
    "HW-1001": {"status": "Active", "expires": "2026-05-10"},
    "HW-2088": {"status": "Expired", "expires": "2024-01-20"},
}
MOCK_SOFTWARE_OUTAGES = ["VPN Service", "Email Server"]


# --- Main Example ---
def sophisticated_example():
    """
    Demonstrates creating and executing a complex, multi-branch workflow
    for an IT support system with deterministic tools.
    """
    load_dotenv()
    # --- Initialization ---
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("FATAL: OPENAI_API_KEY environment variable not set.")
        return

    db_file = "it_support_workflows.db"
    if os.path.exists(db_file):
        os.remove(db_file) # Start with a clean slate for this test run.

    engine = WorkflowEngine(openai_api_key=api_key, db_path=db_file)

    # --- Registering the Deterministic Toolset ---

    @engine.register_tool
    def triage_it_issue(problem_description: str):
        """
        Analyzes a user's problem description and categorizes it into 'Hardware', 'Software', or 'Access'.
        :param problem_description: The user's description of their IT problem.
        """
        logging.info(f"TOOL: Triaging issue: '{problem_description}'")
        desc = problem_description.lower()
        if any(keyword in desc for keyword in ["slow", "broken", "won't turn on", "cracked", "laptop", "mouse"]):
            return {"category": "Hardware"}
        if any(keyword in desc for keyword in ["can't log in", "password", "locked out", "access"]):
            return {"category": "Access"}
        if any(keyword in desc for keyword in ["software", "application", "vpn", "email", "not loading"]):
            return {"category": "Software"}
        return {"category": "Unknown"}

    @engine.register_tool
    def check_known_outages(software_name: str):
        """
        Checks if a specific software is on the official list of current system outages.
        :param software_name: The name of the software to check (e.g., 'VPN Service').
        """
        logging.info(f"TOOL: Checking outages for '{software_name}'")
        if software_name in MOCK_SOFTWARE_OUTAGES:
            return {"status": "outage", "details": f"We are experiencing a system-wide outage for {software_name}. Engineers are working on it."}
        return {"status": "operational"}

    @engine.register_tool
    def check_device_warranty(username: str):
        """
        Looks up a user's assigned device and checks its warranty status.
        :param username: The username of the employee (e.g., 'j.doe').
        """
        logging.info(f"TOOL: Checking warranty for user '{username}'")
        if username not in MOCK_ASSET_DB:
            return {"status": "error", "reason": "User not found in asset database."}

        serial = MOCK_ASSET_DB[username]["serial_number"]
        warranty_info = MOCK_WARRANTY_DB.get(serial, {"status": "Not Found"})
        return {"serial_number": serial, "warranty": warranty_info}

    @engine.register_tool
    def create_support_ticket(username: str, issue_summary: str, priority: str = "Medium"):
        """
        Creates a new support ticket in the system.
        :param username: The username of the person reporting the issue.
        :param issue_summary: A brief summary of the problem.
        :param priority: The priority of the ticket ('High', 'Medium', 'Low').
        """
        ticket_id = f"IT-{int(time.time()) % 10000}"
        logging.info(f"TOOL: Creating ticket {ticket_id} for {username} with summary: '{issue_summary}'")
        return {"status": "success", "ticket_id": ticket_id, "summary": issue_summary}

    # --- Defining a Complex, Multi-Branch Workflow ---
    it_support_workflow_def = """
    When a user reports an IT problem, your job is to act as a helpful IT support agent.
    
    1.  First, triage the user's problem description to determine if it is a 'Hardware', 'Software', or 'Access' issue.
    2.  **If it's a 'Software' issue**:
        a. Check for any known system outages related to the software they mentioned.
        b. If there IS an outage, inform the user about the outage and that engineers are working on it. Do not create a ticket.
        c. If there is NO outage, create a support ticket with a 'Medium' priority and inform the user of the ticket number.
    3.  **If it's a 'Hardware' issue**:
        a. Check the warranty status for the user's assigned device.
        b. Inform the user of their device's serial number and warranty status, then create a 'High' priority ticket and provide the ticket number.
    4.  **If it's an 'Access' issue**:
        a. Immediately create a 'High' priority support ticket for a password reset and inform the user of the ticket number.
    5.  Always be polite and provide the generated ticket number to the user when a ticket is created. The user's name or username will be in the query.
    """

    print("--- Creating IT Support Workflow ---")
    workflow_id = engine.create_workflow(
        name="IT Support Ticket Agent",
        description="A multi-branch workflow that triages IT issues, checks systems, and creates support tickets.",
        workflow_definition=it_support_workflow_def,
        owner="it.department"
    )
    print(f"Created workflow with ID: {workflow_id}\n")

    # --- Test Cases for Each Workflow Branch ---

    def run_test_case(name: str, query: str, context: dict):
        print("\n" + "="*25 + f" RUNNING TEST: {name} " + "="*25)
        result = engine.execute_query(query, context)

        print("\n--- Final User-Facing Response ---")
        print(result.get("response"))

        # This provides a full trace to see which steps and tools were used.
        # print("\n--- Full Execution Trace ---")
        # print(json.dumps(result, indent=2))
        print("="*75 + "\n")

    # Test Case 1: Software issue with a known outage (Should not create a ticket)
    run_test_case(
        "Software - Known Outage",
        "Hi, this is a.smith. My Email Server application is not loading at all.",
        {"username": "a.smith", "department": "Finance"}
    )
    time.sleep(1) # sleep to ensure unique ticket IDs if creation happens fast

    # Test Case 2: Software issue with no outage (Should create a ticket)
    run_test_case(
        "Software - No Outage",
        "Hello, my name is a.smith. The analytics software is crashing on startup.",
        {"username": "a.smith", "department": "Finance"}
    )
    time.sleep(1)

    # Test Case 3: Hardware issue for a user with an active warranty
    run_test_case(
        "Hardware - Active Warranty",
        "Hi, j.doe here. My laptop screen is cracked.",
        {"username": "j.doe", "department": "Engineering"}
    )
    time.sleep(1)

    # Test Case 4: Simple access issue that should go directly to ticket creation
    run_test_case(
        "Access Issue",
        "Help, I'm locked out of my account. My username is j.doe.",
        {"username": "j.doe", "department": "Engineering"}
    )


if __name__ == "__main__":
    sophisticated_example()