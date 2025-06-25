import os
import logging
from dotenv import load_dotenv
from genai_workflows.core import WorkflowEngine

# --- Setup ---
# Load environment variables (for OPENAI_API_KEY)
load_dotenv()
# Configure logging to see the engine's internal workings
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def run_comprehensive_demo():
    """
    A full demonstration of the enhanced workflow system, covering all new features.
    """
    print("🚀 STARTING COMPREHENSIVE DEMO 🚀")

    # --- 1. Initialization ---
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logging.fatal("FATAL: OPENAI_API_KEY environment variable not set.")
        return

    db_file = "comprehensive_demo.db"
    if os.path.exists(db_file):
        os.remove(db_file) # Start with a clean slate for the demo

    engine = WorkflowEngine(openai_api_key=api_key, db_path=db_file)
    print("\n✅ Engine Initialized")

    # --- 2. Register Mock Tools ---
    @engine.register_tool
    def get_employee_details(username: str):
        """Looks up an employee's full name and department from their username."""
        logging.info(f"TOOL: Looking up details for '{username}'")
        MOCK_USERS = {"j.doe": {"full_name": "Jane Doe", "department": "Engineering"}}
        return MOCK_USERS.get(username, {"error": "User not found"})

    @engine.register_tool
    def create_leave_request(full_name: str, leave_date: str, reason: str):
        """Creates an official leave request in the HR system."""
        logging.info(f"TOOL: Creating leave request for {full_name} on {leave_date}")
        return {"status": "success", "request_id": f"LR-{hash(full_name + leave_date) % 1000}"}

    print("✅ Tools Registered")

    # --- 3. INTERACTIVE WORKFLOW CREATION ---
    print("\n--- 🗣️ Part 1: Interactive Workflow Creation ---\n")

    # Start the interactive builder
    parser = engine.create_workflow_interactively(
        name="HR Leave Request Assistant",
        description="A workflow to handle employee leave requests by asking for details."
    )

    # Simulate the conversation to build the workflow
    conversation = [
        "First, ask the user for their username.",
        "Then, use the employee's username to get their full name and department.",
        "Next, ask the user for the reason they are requesting leave.",
        "After that, use the full name and the reason for leave to create the request. For the date, just use today's date.",
        "Finally, confirm to the user that the leave request has been created and provide the request ID."
    ]

    for i, turn in enumerate(conversation):
        print(f"User > {turn}")
        bot_response = parser.handle_user_response(turn)
        print(f"Bot  > {bot_response}\n")

    # Finalize the creation process
    print("User > I'm done.")
    bot_response = parser.handle_user_response("I'm done.")
    print(f"Bot  > {bot_response}\n")

    # Get the final workflow object
    new_workflow = parser.get_final_workflow()
    if new_workflow:
        workflow_id = engine.save_workflow(new_workflow)
        print(f"✅ Workflow '{new_workflow.name}' created and saved with ID: {workflow_id}")
    else:
        logging.error("Failed to create workflow.")
        return

    # --- 4. VISUALIZATION ---
    print("\n--- 📊 Part 2: Workflow Visualization ---\n")

    mermaid_diagram = engine.visualize_workflow(workflow_id)
    print("Generated Mermaid.js Diagram:")
    print("-----------------------------------")
    print(mermaid_diagram)
    print("-----------------------------------")
    print("(You can paste this into a Mermaid.js renderer to see the flowchart)\n")

    # --- 5. EXECUTION WITH HUMAN-IN-THE-LOOP ---
    print("\n--- 🏃 Part 3: Running the Workflow ---\n")

    # Step 5.1: Start the execution
    query = "I need to request a day off."
    print(f"User > {query}")
    result = engine.start_execution(query=query)

    # Step 5.2: Handle the pause for human input
    if result.get("status") == "awaiting_input":
        question_from_bot = result.get("response")
        execution_id = result.get("execution_id")
        print(f"Bot  > {question_from_bot}")
        print(f"(Workflow is now paused, waiting for input. Execution ID: {execution_id})\n")

        # Step 5.3: User provides the first piece of information
        user_response_1 = "j.doe"
        print(f"User > {user_response_1}")

        # Step 5.4: Resume the workflow
        result = engine.resume_execution(execution_id, user_response_1)

    # Step 5.5: Handle the second pause
    if result.get("status") == "awaiting_input":
        question_from_bot = result.get("response")
        execution_id = result.get("execution_id")
        print(f"Bot  > {question_from_bot}")
        print(f"(Workflow paused again for the next question. Execution ID: {execution_id})\n")

        # Step 5.6: User provides the second piece of information
        user_response_2 = "Doctor's appointment"
        print(f"User > {user_response_2}")

        # Step 5.7: Resume the workflow for the final time
        final_result = engine.resume_execution(execution_id, user_response_2)

        # --- 6. FINAL OUTPUT ---
        print("\n--- ✅ Part 4: Final Result ---\n")
        if final_result.get("status") == "completed":
            print(f"Bot  > {final_result.get('response')}")
        else:
            logging.error("Workflow did not complete successfully.")
            print(final_result)
    else:
        logging.error("Workflow did not pause as expected or failed.")
        print(result)

    print("\n\n🎉 DEMO COMPLETED SUCCESSFULLY 🎉")


if __name__ == "__main__":
    run_comprehensive_demo()