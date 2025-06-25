# Filename: app.py
import streamlit as st
import os
import json
import logging
import time
from genai_workflows.core import WorkflowEngine

# --- Page Configuration ---
st.set_page_config(
    page_title="GenAI Workflow Engine UI",
    page_icon="🤖",
    layout="wide"
)

# --- Logging Setup ---
# Ensures logs are visible in the console where you run streamlit.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Mock Tools (from your test.py for deterministic testing) ---
MOCK_ASSET_DB = {
    "j.doe": {"serial_number": "HW-1001", "name": "Laptop"},
    "a.smith": {"serial_number": "HW-2088", "name": "Desktop"},
}
MOCK_WARRANTY_DB = {
    "HW-1001": {"status": "Active", "expires": "2026-05-10"},
    "HW-2088": {"status": "Expired", "expires": "2024-01-20"},
}
MOCK_SOFTWARE_OUTAGES = ["VPN Service", "Email Server"]

def register_mock_tools(engine: WorkflowEngine):
    """Registers a suite of deterministic tools for testing the IT support workflow."""
    logger.info("Registering mock IT tools.")

    @engine.register_tool
    def triage_it_issue(problem_description: str):
        """
        Analyzes a user's problem description and categorizes it into 'Hardware', 'Software', or 'Access'.
        :param problem_description: The user's description of their IT problem.
        """
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
        if software_name in MOCK_SOFTWARE_OUTAGES:
            return {"status": "outage", "details": f"We are experiencing a system-wide outage for {software_name}."}
        return {"status": "operational"}

    @engine.register_tool
    def check_device_warranty(username: str):
        """
        Looks up a user's assigned device and checks its warranty status.
        :param username: The username of the employee (e.g., 'j.doe').
        """
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
        return {"status": "success", "ticket_id": ticket_id, "summary": issue_summary}


# --- Main Application Logic ---

def main():
    st.title("🤖 GenAI Workflow Engine Explorer")
    st.markdown("An interactive UI to create, test, and manage autonomous workflows.")

    # --- Sidebar for Configuration and Workflow Management ---
    with st.sidebar:
        st.header("⚙️ Configuration")
        api_key = st.text_input("OpenAI API Key", type="password", help="Your key is not stored. It is only held in memory for the session.")

        # Initialize engine only if API key is provided
        if api_key:
            db_path = "streamlit_workflows.db"
            # Use session state to keep the engine object alive across reruns
            if 'engine' not in st.session_state or st.session_state.engine is None:
                try:
                    engine = WorkflowEngine(openai_api_key=api_key, db_path=db_path)
                    register_mock_tools(engine)
                    st.session_state.engine = engine
                    st.success("Engine initialized.")
                except Exception as e:
                    st.error(f"Failed to initialize engine: {e}")
                    st.session_state.engine = None

            engine = st.session_state.engine
        else:
            st.session_state.engine = None
            st.warning("Please enter your OpenAI API key to begin.")

        # --- Workflow Management UI ---
        if st.session_state.get('engine'):
            st.divider()
            st.header("📚 Workflows")
            if st.button("Refresh List"):
                st.rerun()

            try:
                workflows = st.session_state.engine.list_workflows()
                if not workflows:
                    st.info("No workflows found. Create one in the 'Create Workflow' tab.")

                for wf in workflows:
                    with st.expander(f"**{wf['name']}** (ID: {wf['id']})"):
                        st.markdown(f"**Description:** {wf['description']}")
                        st.markdown(f"**Owner:** {wf['owner']}")

                        # Add a button to view the full workflow structure
                        if st.button("View Full Definition", key=f"view_{wf['id']}"):
                            full_wf = st.session_state.engine.get_workflow(wf['id'])
                            st.json(full_wf.to_dict())

                        # Add a delete button
                        if st.button("Delete Workflow", key=f"delete_{wf['id']}", type="primary"):
                            st.session_state.engine.delete_workflow(wf['id'])
                            st.success(f"Deleted workflow '{wf['name']}'.")
                            time.sleep(1) # Give a moment before rerunning
                            st.rerun()

            except Exception as e:
                st.error(f"Could not load workflows: {e}")


    # --- Main Panel for Interaction ---
    if not st.session_state.get('engine'):
        st.info("Enter your API key in the sidebar to activate the workflow engine.")
        return

    tab1, tab2 = st.tabs(["▶️ Execute Query", "➕ Create Workflow"])

    # --- Create Workflow Tab ---
    with tab1:
        st.header("▶️ Execute a Query")
        st.markdown(
            "Type a query below. The engine will use its **Router** to find the most appropriate "
            "workflow and then execute it."
        )

        query = st.text_area("User Query", height=100, placeholder="e.g., Hi, j.doe here. My laptop screen is cracked.")
        context = st.text_area(
            "Initial Context (JSON)",
            height=100,
            value='{"username": "j.doe"}',
            help="Provide optional context as a JSON object that can be used by the workflow."
        )

        if st.button("Execute", type="primary", use_container_width=True):
            if not query:
                st.warning("Please enter a query.")
            else:
                with st.spinner("Executing workflow..."):
                    try:
                        parsed_context = json.loads(context) if context else {}
                        result = st.session_state.engine.execute_query(query, parsed_context)

                        st.subheader("✅ Final Response")
                        st.markdown(result.get("response", "No response generated."))

                        with st.expander("Show Full Execution Trace"):
                            st.json(result)

                    except json.JSONDecodeError:
                        st.error("Invalid JSON in the 'Initial Context' field.")
                    except Exception as e:
                        st.error(f"An error occurred during execution: {e}")
                        logger.error("Execution failed", exc_info=True)


    # --- Execute Query Tab ---
    with tab2:
        st.header("➕ Create a New Workflow")
        st.markdown(
            "Define a workflow using natural language. The **Parser** will convert this into a "
            "structured plan that the **Executor** can run."
        )

        # Pre-fill with the complex example for convenience
        it_support_workflow_def = """
Your goal is to act as a helpful IT support agent. Follow these steps precisely.

1.  First, **use the triage tool** on the user's problem description to categorize it as 'Hardware', 'Software', or 'Access'. The user's problem is in the `{query}`.
2.  **IF the category from the last step is 'Software'**:
    a. First, **use the outage checking tool** to see if the software is down.
    b. If there IS an outage, use an `llm_response` to inform the user about the outage details from the history. Stop.
    c. If there is NO outage, **use the ticket creation tool** to create a 'Medium' priority ticket. Then, inform the user of the ticket number from the history.
3.  **IF the category from the last step is 'Hardware'**:
    a. First, **use the warranty checking tool** to get the device status for the user from the `{context}`.
    b. Next, **use the ticket creation tool** to create a 'High' priority ticket summarizing the issue.
    c. Finally, use an `llm_response` to inform the user of their device's serial number, warranty status, and the new ticket number, all from the `{history}`.
4.  **IF the category from the last step is 'Access'**:
    a. **Use the ticket creation tool** immediately to create a 'High' priority ticket.
    b. Inform the user of the ticket number from the `{history}`.
"""

        with st.form("create_workflow_form"):
            name = st.text_input("Workflow Name", "IT Support Ticket Agent")
            description = st.text_input("Description", "Triages IT issues, checks systems, and creates support tickets.")
            owner = st.text_input("Owner", "it.department")
            definition = st.text_area("Natural Language Definition", it_support_workflow_def, height=400)

            submitted = st.form_submit_button("Create Workflow", use_container_width=True)
            if submitted:
                if not all([name, description, definition]):
                    st.warning("Please fill out all fields.")
                else:
                    with st.spinner("Parsing definition and creating workflow..."):
                        try:
                            workflow_id = st.session_state.engine.create_workflow(
                                name=name,
                                description=description,
                                workflow_definition=definition,
                                owner=owner
                            )
                            st.success(f"Successfully created workflow '{name}' with ID: {workflow_id}")
                            st.info("Refresh the list in the sidebar to see the new workflow.")
                        except Exception as e:
                            st.error(f"Failed to create workflow: {e}")
                            logger.error("Creation failed", exc_info=True)

if __name__ == "__main__":
    main()