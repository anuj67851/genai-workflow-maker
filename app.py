import streamlit as st
import os
import logging
import time
from dotenv import load_dotenv

# Import the necessary components from your library
from genai_workflows.core import WorkflowEngine
from genai_workflows.workflow import Workflow, WorkflowStep

# Import the mermaid component for visualization
from streamlit_mermaid import st_mermaid

# --- 1. App Configuration and Setup ---

st.set_page_config(
    page_title="GenAI Workflow Engine UI",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load environment variables (for OPENAI_API_KEY)
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# --- 2. Mock Tools and Pre-built Workflow (WITH MODIFICATIONS) ---

# Mock Asset DBs (unchanged)
MOCK_ASSET_DB = {
    "j.doe": {"serial_number": "HW-1001", "name": "Laptop"},
    "a.smith": {"serial_number": "HW-2088", "name": "Desktop"},
}
MOCK_WARRANTY_DB = {
    "HW-1001": {"status": "Active", "expires": "2026-05-10"},
    "HW-2088": {"status": "Expired", "expires": "2024-01-20"},
}
MOCK_SOFTWARE_OUTAGES = ["VPN Service", "Email Server"]

# NEW: Mock Ticket Database, lives in session_state to be persistent
if "MOCK_TICKET_DB" not in st.session_state:
    st.session_state.MOCK_TICKET_DB = {}


def register_mock_tools(engine: WorkflowEngine):
    """Registers a set of deterministic tools for the IT support demo."""
    if "tools_registered" in st.session_state:
        return

    @engine.register_tool
    def triage_it_issue(problem_description: str):
        """Analyzes a user's problem and categorizes it into 'Hardware', 'Software', or 'Access'."""
        desc = problem_description.lower()
        if any(kw in desc for kw in ["slow", "broken", "won't turn on", "cracked", "laptop", "mouse"]):
            return {"category": "Hardware"}
        if any(kw in desc for kw in ["can't log in", "password", "locked out", "access"]):
            return {"category": "Access"}
        if any(kw in desc for kw in ["software", "application", "vpn", "email", "not loading"]):
            return {"category": "Software"}
        return {"category": "Unknown"}

    @engine.register_tool
    def check_known_outages(software_name: str):
        """Checks if a specific software is on the list of current system outages."""
        if software_name in MOCK_SOFTWARE_OUTAGES:
            return {"status": "outage", "details": f"System-wide outage for {software_name}."}
        return {"status": "operational"}

    @engine.register_tool
    def check_device_warranty(username: str):
        """Looks up a user's device and checks its warranty status."""
        if username not in MOCK_ASSET_DB:
            return {"status": "error", "reason": "User not found."}
        serial = MOCK_ASSET_DB[username]["serial_number"]
        warranty_info = MOCK_WARRANTY_DB.get(serial, {"status": "Not Found"})
        return {"serial_number": serial, "warranty": warranty_info}

    # MODIFIED: The ticket creation tool now takes a detailed description
    # and saves the ticket to our mock database.
    @engine.register_tool
    def create_support_ticket(username: str, problem_description: str, priority: str = "Medium"):
        """
        Creates a new support ticket and saves it to the database.
        :param username: The username of the person with the issue.
        :param problem_description: A detailed description of the issue provided by the user.
        :param priority: The priority of the ticket (High, Medium, Low).
        """
        ticket_id = f"IT-{int(time.time()) % 10000}"
        ticket_details = {
            "ticket_id": ticket_id,
            "username": username,
            "description": problem_description,
            "priority": priority,
            "status": "Open",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        # Save to our mock "DB"
        st.session_state.MOCK_TICKET_DB[ticket_id] = ticket_details
        logger.info(f"Saved ticket to DB: {ticket_details}")
        return {"status": "success", "ticket_id": ticket_id, "summary": problem_description}

    st.session_state.tools_registered = True
    logger.info("Mock tools registered successfully.")


def create_demo_it_workflow(engine: WorkflowEngine):
    """
    Manually defines and saves the complex, multi-branch IT Support workflow
    so it's available for execution and visualization in the app.
    (This function is heavily modified to add the new steps).
    """
    if "demo_workflow_created" in st.session_state:
        return

    logger.info("Creating and saving the MODIFIED demo IT Support workflow...")
    it_workflow = Workflow(
        name="IT Support Ticket Agent",
        description="A multi-branch workflow that triages IT issues, asks for details, checks systems, and creates support tickets.",
        owner="it.department",
        triggers=["it support", "computer problem", "locked out", "email down"]
    )

    # Core Triage (unchanged)
    it_workflow.add_step(WorkflowStep(
        step_id="triage_issue", description="Triage the user's problem into Hardware, Software, or Access.",
        action_type="agentic_tool_use", prompt_template="Triage this IT issue: {query}", on_success="check_category"))
    it_workflow.add_step(WorkflowStep(
        step_id="check_category", description="Check if the issue category is Software.", action_type="condition_check",
        prompt_template="Based on the history, is the category 'Software'? Look at the output of the 'triage_issue' step.",
        on_success="ask_for_software_name", on_failure="check_if_hardware"))
    it_workflow.add_step(WorkflowStep(
        step_id="check_if_hardware", description="Check if the issue category is Hardware.", action_type="condition_check",
        prompt_template="Based on the history, is the category 'Hardware'? Look at the output of the 'triage_issue' step.",
        on_success="check_warranty", on_failure="ask_for_details")) # Access issues go straight to asking for details

    # Software Branch (unchanged up to outage check)
    it_workflow.add_step(WorkflowStep(
        step_id="ask_for_software_name", description="Ask user for the name of the problematic software.",
        action_type="human_input",
        prompt_template="I understand you're having a software issue. To check for outages, could you please tell me the exact name of the application?",
        output_key="software_name", on_success="check_for_outages"))
    it_workflow.add_step(WorkflowStep(
        step_id="check_for_outages", description="Check for known software outages.", action_type="agentic_tool_use",
        prompt_template="Check for outages for the following software: {input.software_name}",
        on_success="check_outage_result"))
    it_workflow.add_step(WorkflowStep(
        step_id="check_outage_result", description="Check if there was an outage.", action_type="condition_check",
        prompt_template="Based on the history, did the 'check_for_outages' step find an 'outage' status?",
        on_success="inform_user_of_outage", on_failure="ask_for_details")) # If no outage, we need to ask for details
    it_workflow.add_step(WorkflowStep(
        step_id="inform_user_of_outage", description="Inform user about the outage.", action_type="llm_response",
        prompt_template="Politely inform the user about the system-wide outage for {input.software_name}. State that a ticket is not needed.",
        on_success="END"))

    # Hardware Branch (unchanged)
    it_workflow.add_step(WorkflowStep(
        step_id="check_warranty", description="Check the user's device warranty.", action_type="agentic_tool_use",
        prompt_template="Check the device warranty for user: {context.username}", on_success="ask_for_details")) # After checking warranty, ask for details

    # --- NEW & CONSOLIDATED STEPS ---
    # NEW: This is the new human_input step that all branches will lead to if a ticket is needed.
    it_workflow.add_step(WorkflowStep(
        step_id="ask_for_details",
        description="Ask the user for more details about their issue.",
        action_type="human_input",
        prompt_template="Okay, I will create a ticket for you. Could you please provide a one or two sentence description of the problem so I can include it in the ticket?",
        output_key="issue_description",
        on_success="create_final_ticket"
    ))

    # CONSOLIDATED: Replaces the three old create_*_ticket steps with one smart one.
    it_workflow.add_step(WorkflowStep(
        step_id="create_final_ticket",
        description="Create a support ticket with the user's provided details.",
        action_type="agentic_tool_use",
        prompt_template="Create a support ticket for user '{context.username}'. The detailed problem description is: '{input.issue_description}'. Review the full conversation history to determine the issue category (Hardware, Software, Access) and set the priority accordingly (High for Hardware/Access, Medium for Software).",
        on_success="inform_user_of_ticket_number"
    ))

    # Common End Step (unchanged)
    it_workflow.add_step(WorkflowStep(
        step_id="inform_user_of_ticket_number", description="Inform user of their new ticket number.", action_type="llm_response",
        prompt_template="Politely inform the user that a ticket has been created. Provide them with the ticket ID from the previous step's output and confirm the details they provided have been included.",
        on_success="END"))

    engine.save_workflow(it_workflow)
    st.session_state.demo_workflow_created = True
    logger.info("Demo IT Support workflow saved successfully.")

# --- 3. Main Application Logic ---

def initialize_app():
    """One-time setup for the Streamlit application using st.session_state."""
    if "engine" in st.session_state:
        return st.session_state.engine

    logger.info("Performing first-time app initialization...")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("FATAL: OPENAI_API_KEY environment variable not set. Please set it in a `.env` file or as a system variable.")
        st.stop()

    db_file = "app_workflows.db"
    # To ensure a clean slate for the demo, we only delete the DB if it exists during the very first initialization.
    if os.path.exists(db_file):
        os.remove(db_file)

    engine = WorkflowEngine(openai_api_key=api_key, db_path=db_file)
    st.session_state.engine = engine

    # Initialize mock DB here as well
    st.session_state.MOCK_TICKET_DB = {}

    register_mock_tools(engine)
    create_demo_it_workflow(engine)

    logger.info("First-time app initialization complete.")
    return engine

# --- 4. UI Rendering Functions ---

def render_run_workflow_page(engine: WorkflowEngine):
    """UI for executing workflows, now with chat and resume capabilities."""
    st.header("🏃‍♂️ Run a Workflow")
    st.markdown("Enter a query to start a workflow. If it needs more information, it will ask you here.")

    # UI to display created tickets from our mock DB
    with st.expander("🎫 View Created Tickets (Mock DB)", expanded=False):
        if not st.session_state.MOCK_TICKET_DB:
            st.info("No tickets have been created in this session yet.")
        else:
            st.json(st.session_state.MOCK_TICKET_DB)

    if "run_messages" not in st.session_state:
        st.session_state.run_messages = []
    if "current_execution_id" not in st.session_state:
        st.session_state.current_execution_id = None

    for message in st.session_state.run_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What is your IT issue? Or provide the requested info..."):
        st.session_state.run_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                if st.session_state.current_execution_id:
                    result = engine.resume_execution(st.session_state.current_execution_id, prompt)
                else:
                    context = {}
                    if "j.doe" in prompt.lower(): context["username"] = "j.doe"
                    elif "a.smith" in prompt.lower(): context["username"] = "a.smith"
                    result = engine.start_execution(prompt, context=context)

                if result.get("status") == "completed":
                    response_text = result.get("response")
                    st.markdown(response_text)
                    st.session_state.run_messages.append({"role": "assistant", "content": response_text})
                    st.session_state.current_execution_id = None
                    st.success("✅ Workflow Completed!", icon="🎉")
                    # --- THIS IS THE FIX ---
                    # Force the page to re-run from the top to refresh the ticket list.
                    st.rerun()

                elif result.get("status") == "awaiting_input":
                    response_text = result.get("response")
                    st.markdown(response_text)
                    st.session_state.run_messages.append({"role": "assistant", "content": response_text})
                    st.session_state.current_execution_id = result.get("execution_id")
                    st.info("🤔 Workflow is waiting for your input.", icon="👆")

                else: # failed or no workflow found
                    error_msg = result.get("error", "I'm not sure how to handle that.")
                    st.markdown(error_msg)
                    st.session_state.run_messages.append({"role": "assistant", "content": error_msg})
                    st.session_state.current_execution_id = None

    if st.button("🔄 Start New Conversation"):
        st.session_state.run_messages = []
        st.session_state.current_execution_id = None
        st.session_state.MOCK_TICKET_DB = {} # Clear the mock DB on new conversation
        st.rerun()

def render_create_workflow_page(engine: WorkflowEngine):
    """UI for the interactive workflow builder."""
    st.header("🛠️ Create a Workflow Interactively")
    st.markdown("Build a workflow step-by-step by talking to the AI assistant.")

    if "interactive_parser" not in st.session_state:
        st.session_state.interactive_parser = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if st.session_state.interactive_parser is None:
        with st.form("new_workflow_form"):
            wf_name = st.text_input("Workflow Name", placeholder="e.g., 'Customer Onboarding'")
            wf_desc = st.text_area("Description", placeholder="A brief description of what this workflow does.")
            submitted = st.form_submit_button("Start Building")

            if submitted and wf_name and wf_desc:
                parser = engine.create_workflow_interactively(name=wf_name, description=wf_desc)
                st.session_state.interactive_parser = parser
                initial_prompt = "OK, I've started a new workflow for you. **What is the very first step?** (e.g., 'Ask the user for their email address')"
                st.session_state.chat_history = [{"role": "assistant", "content": initial_prompt}]
                st.rerun()
    else:
        st.info(f"Building workflow: **{st.session_state.interactive_parser.workflow_in_progress.name}**")

        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if user_input := st.chat_input("Describe the next step, or say 'I'm done'...", key="creator_input"):
            parser = st.session_state.interactive_parser
            st.session_state.chat_history.append({"role": "user", "content": user_input})

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    assistant_response = parser.handle_user_response(user_input)
                    st.markdown(assistant_response)

            st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})

            if parser.is_finished:
                final_workflow = parser.get_final_workflow()
                if final_workflow:
                    workflow_id = engine.save_workflow(final_workflow)
                    st.success(f"🎉 Workflow '{final_workflow.name}' has been finalized and saved with ID {workflow_id}!")
                    del st.session_state.interactive_parser
                    del st.session_state.chat_history
            st.rerun()

def render_manage_workflows_page(engine: WorkflowEngine):
    """UI for listing and visualizing workflows using a dropdown."""
    st.header("📚 Manage & Visualize Workflows")

    workflows = engine.list_workflows()
    if not workflows:
        st.warning("No workflows found in the database. Please create one first.")
        return

    # Create a list of display names for the dropdown
    workflow_display_names = [f"{wf['name']} (ID: {wf['id']})" for wf in workflows]

    # The selectbox will return the selected string
    selected_display_name = st.selectbox(
        "Select a workflow to visualize:",
        options=workflow_display_names
    )

    if selected_display_name:
        # Find the corresponding workflow info from the original list
        selected_wf_info = next((wf for wf in workflows if f"{wf['name']} (ID: {wf['id']})" == selected_display_name), None)

        if not selected_wf_info:
            st.error("An error occurred while selecting the workflow.")
            return

        workflow_id = selected_wf_info['id']
        wf = engine.get_workflow(workflow_id)

        if not wf:
            st.error(f"Could not retrieve full workflow with ID {workflow_id}.")
            return

        st.divider()
        st.subheader(f"Details for: `{wf.name}`")
        st.markdown(f"**Description:** *{wf.description}*")

        with st.spinner("Generating diagram..."):
            mermaid_code = engine.visualize_workflow(workflow_id)

        if mermaid_code:
            # Display the generated Mermaid code first
            st.subheader("Generated Mermaid Code")
            st.code(mermaid_code, language="mermaid")

            # Then display the rendered diagram
            st.subheader("Workflow Diagram")
            try:
                st_mermaid(mermaid_code, height="800px")
            except Exception as e:
                st.error(f"Failed to render Mermaid diagram. The syntax above is likely invalid. Error: {e}")
        else:
            st.error("Could not generate a visualization for this workflow.")


# --- Main App Execution ---
if __name__ == "__main__":
    st.title("🤖 GenAI Workflow Engine")

    engine = initialize_app()

    with st.sidebar:
        st.header("Navigation")
        app_mode = st.radio(
            "Choose a mode:",
            ("🏃‍♂️ Run Workflow", "🛠️ Create New Workflow", "📚 Manage & Visualize")
        )

    if app_mode == "🏃‍♂️ Run Workflow":
        render_run_workflow_page(engine)
    elif app_mode == "🛠️ Create New Workflow":
        render_create_workflow_page(engine)
    elif app_mode == "📚 Manage & Visualize":
        render_manage_workflows_page(engine)