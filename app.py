import streamlit as st
import os
import time
import base64
from dotenv import load_dotenv

# Import all necessary components from your library
from genai_workflows.core import WorkflowEngine
from genai_workflows.workflow import Workflow, WorkflowStep

# --- Page Configuration ---
st.set_page_config(
    page_title="GenAI Workflow Engine",
    page_icon="🤖",
    layout="wide"
)

# --- App State & Demo Initialization ---
def initialize_state():
    """Initializes session state and creates the demo workflow if it doesn't exist."""
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("FATAL: OPENAI_API_KEY environment variable not set. Please create a .env file.")
        st.stop()

    if "engine" not in st.session_state:
        db_file = "ui_workflows.db"
        st.session_state.engine = WorkflowEngine(openai_api_key=api_key, db_path=db_file)
        st.toast("Workflow Engine Initialized!")
        create_it_support_demo_if_not_exists(st.session_state.engine)

    # Initialize all necessary state variables to prevent errors
    for key in ["run_messages", "builder_messages", "wf_builder_name", "wf_builder_desc"]:
        if key not in st.session_state:
            st.session_state[key] = [] if "messages" in key else ""

    if "execution_id" not in st.session_state: st.session_state.execution_id = None
    if "builder_parser" not in st.session_state: st.session_state.builder_parser = None


def create_it_support_demo_if_not_exists(engine: WorkflowEngine):
    # This function is unchanged and correct.
    # For brevity, its content is omitted here, but it should be copied from the previous response.
    workflows = engine.list_workflows()
    if any(wf['name'] == "IT Support Agent" for wf in workflows): return
    MOCK_ASSET_DB = {"j.doe": "Laptop-SN1001", "a.smith": "Desktop-SN2088"}
    MOCK_WARRANTY_DB = {"Laptop-SN1001": "Active until 2026", "Desktop-SN2088": "Expired"}
    MOCK_SOFTWARE_OUTAGES = ["VPN Service"]
    @engine.register_tool
    def triage_it_issue(problem_description: str):
        desc=problem_description.lower();[a,b,c]=["Hardware","Software","Access"];d=any
        if d(kw in desc for kw in["slow","broken","cracked","laptop"]):return{"category":a}
        if d(kw in desc for kw in["software","vpn","email","not loading"]):return{"category":b}
        if d(kw in desc for kw in["password","locked out","access"]):return{"category":c}
        return{"category":"Unknown"}
    @engine.register_tool
    def check_known_outages(software_name: str):
        if software_name in MOCK_SOFTWARE_OUTAGES:return{"status":"outage","details":f"We have a system-wide outage for {software_name}."}
        return{"status":"operational"}
    @engine.register_tool
    def check_device_warranty(username: str):
        serial = MOCK_ASSET_DB.get(username, "Unknown Device");status = MOCK_WARRANTY_DB.get(serial, "No Warranty Info")
        return{"serial_number":serial,"warranty_status":status}
    @engine.register_tool
    def create_support_ticket(username: str, summary: str, priority: str="Medium"):
        return{"status":"success","ticket_id":f"IT-{int(time.time()%10000)}","summary":summary}
    wf=Workflow(name="IT Support Agent",description="Triages IT issues, checks systems, and creates tickets.")
    s=WorkflowStep
    wf.add_step(s(step_id="triage_issue",description="Triage user's problem.",action_type="agentic_tool_use",prompt_template="Triage the user's problem described in their query: {query}",on_success="is_software_check"))
    wf.add_step(s(step_id="is_software_check",description="Check if category is 'Software'.",action_type="condition_check",prompt_template="The output of 'triage_issue' contains 'Software'",on_success="ask_for_software_name",on_failure="is_hardware_check"))
    wf.add_step(s(step_id="is_hardware_check",description="Check if category is 'Hardware'.",action_type="condition_check",prompt_template="The output of 'triage_issue' contains 'Hardware'",on_success="check_warranty",on_failure="create_access_ticket"))
    wf.add_step(s(step_id="ask_for_software_name",description="Ask for software name.",action_type="human_input",prompt_template="I see you have a software issue. Which application is causing problems (e.g., 'VPN Service')?",output_key="software_name",on_success="check_for_outage"))
    wf.add_step(s(step_id="check_for_outage",description="Check for known outages.",action_type="agentic_tool_use",prompt_template="Check for outages for the software named: {input.software_name}",on_success="is_outage_check"))
    wf.add_step(s(step_id="is_outage_check",description="Check if there was an outage.",action_type="condition_check",prompt_template="The output of 'check_for_outage' contains 'outage'",on_success="report_outage",on_failure="create_software_ticket"))
    wf.add_step(s(step_id="report_outage",description="Inform user about the outage.",action_type="llm_response",prompt_template="Inform the user about the known outage based on the history. Do not create a ticket.",on_success="END"))
    wf.add_step(s(step_id="create_software_ticket",description="Create medium priority software ticket.",action_type="agentic_tool_use",prompt_template="Create a support ticket for user {context.username} about the software issue: {input.software_name}",on_success="report_ticket_creation"))
    wf.add_step(s(step_id="check_warranty",description="Check device warranty.",action_type="agentic_tool_use",prompt_template="Check the device warranty for user {context.username}",on_success="create_hardware_ticket"))
    wf.add_step(s(step_id="create_hardware_ticket",description="Create high priority hardware ticket.",action_type="agentic_tool_use",prompt_template="Create a 'High' priority ticket for user {context.username} regarding their hardware issue. Mention warranty status from history.",on_success="report_ticket_creation"))
    wf.add_step(s(step_id="create_access_ticket",description="Create ticket for access/unknown issues.",action_type="agentic_tool_use",prompt_template="Create a 'High' priority ticket for user {context.username} for the issue: {query}",on_success="report_ticket_creation"))
    wf.add_step(s(step_id="report_ticket_creation",description="Confirm ticket creation.",action_type="llm_response",prompt_template="Politely inform the user that a ticket has been created and provide the ticket ID from the history.",on_success="END"))
    engine.save_workflow(wf);st.toast("✅ Created Sophisticated 'IT Support Agent' Demo!")


def draw_sidebar():
    """Draws the sidebar for building and managing workflows."""
    with st.sidebar:
        st.title("Workflow Controls")

        st.subheader("Build a Workflow")
        with st.expander("Builder & Demo", expanded=False):

            # --- FIX: Use a callback to set state BEFORE the UI is redrawn ---
            def load_demo_defaults():
                st.session_state.wf_builder_name = "IT Support Agent (Copy)"
                st.session_state.wf_builder_desc = "Triages IT issues, checks systems, and creates tickets."

            st.button("Load 'IT Support Agent' Demo", on_click=load_demo_defaults)

            with st.form("new_workflow_form"):
                st.text_input("Workflow Name", key="wf_builder_name")
                st.text_area("Description", key="wf_builder_desc")
                submitted = st.form_submit_button("Start Building")
                if submitted:
                    name = st.session_state.wf_builder_name
                    desc = st.session_state.wf_builder_desc
                    if name:
                        parser = st.session_state.engine.create_workflow_interactively(name, desc)
                        st.session_state.builder_parser = parser
                        st.session_state.builder_messages = [{"role": "assistant", "content": f"Let's build '{name}'. What is the first step?"}]
                        # Clear form values after submission
                        st.session_state.wf_builder_name = ""
                        st.session_state.wf_builder_desc = ""
                        st.rerun()

        st.subheader("Existing Workflows")
        workflows = st.session_state.engine.list_workflows()
        if not workflows: st.caption("No workflows created yet.")
        else:
            for wf in workflows:
                with st.container(border=True):
                    st.write(f"**{wf['name']}**")
                    st.caption(f"ID: {wf['id']}")
                    if st.button("Delete", key=f"delete_{wf['id']}", type="secondary"):
                        st.session_state.engine.delete_workflow(wf['id'])
                        st.toast(f"Deleted workflow {wf['id']}")
                        st.rerun()

def draw_main_content():
    st.header("GenAI Workflow Engine")
    run_tab, build_tab, visualize_tab = st.tabs(["▶️ Run Workflow", "🛠️ Build Workflow", "📊 Visualize & Details"])

    with run_tab:
        # This tab is correct and needs no changes
        st.subheader("Automatic Workflow Execution")
        if st.button("🔄 New Chat"):
            st.session_state.run_messages, st.session_state.execution_id = [], None
            st.rerun()
        st.info("Enter a query below. The AI will automatically select and run the best workflow.", icon="💡")
        for msg in st.session_state.run_messages:
            with st.chat_message(msg["role"]): st.write(msg["content"])
        if prompt := st.chat_input("What can I help you with today?"):
            st.session_state.run_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.write(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Processing..."):
                    engine, exec_id = st.session_state.engine, st.session_state.execution_id
                    if exec_id: result = engine.resume_execution(exec_id, prompt)
                    else:
                        context = {}; u = prompt.lower()
                        if "j.doe" in u: context = {"username": "j.doe"}
                        if "a.smith" in u: context = {"username": "a.smith"}
                        result = engine.start_execution(query=prompt, context=context)
                    status, response = result.get("status"), result.get("response", result.get("error", "..."))
                    st.session_state.execution_id = result.get("execution_id")
                    st.write(response)
                    st.session_state.run_messages.append({"role": "assistant", "content": response})
                    if status in ['completed', 'failed']: st.info("Workflow finished.", icon="🏁")

    with build_tab:
        # This tab is correct and needs no changes
        st.subheader("Interactive Workflow Builder")
        if not st.session_state.builder_parser: st.info("Start building via the sidebar.")
        else:
            for msg in st.session_state.builder_messages:
                with st.chat_message(msg["role"]):st.write(msg["content"])
            if prompt := st.chat_input("Describe the next step..."):
                st.session_state.builder_messages.append({"role":"user","content":prompt});
                with st.chat_message("user"):st.write(prompt)
                parser=st.session_state.builder_parser;
                with st.spinner("Thinking..."):bot_response=parser.handle_user_response(prompt)
                st.session_state.builder_messages.append({"role":"assistant","content":bot_response});
                with st.chat_message("assistant"):st.write(bot_response)
                if parser.is_finished:
                    final_workflow=parser.get_final_workflow()
                    if final_workflow:
                        st.session_state.engine.save_workflow(final_workflow);st.success(f"Workflow '{final_workflow.name}' saved!");
                        st.session_state.builder_parser=None;st.session_state.builder_messages=[]

    with visualize_tab:
        st.subheader("Workflow Diagram & Details")
        workflows = st.session_state.engine.list_workflows()
        if not workflows: st.info("No workflows to visualize. Go to the 'Build' tab to create one.")
        else:
            workflow_options = {f"{wf['name']} (ID: {wf['id']})": wf['id'] for wf in workflows}
            selected_option = st.selectbox("Select a workflow to visualize:", options=workflow_options.keys())
            if selected_option:
                wf_id = workflow_options[selected_option]
                workflow = st.session_state.engine.get_workflow(wf_id)
                st.write(f"**Name:** {workflow.name}")
                st.write(f"**Description:** {workflow.description}")
                st.divider()
                with st.spinner("Generating diagram..."):
                    diagram = st.session_state.engine.visualize_workflow(wf_id)
                    if diagram:
                        # --- FIX: Use a robust, web-based image rendering method ---
                        st.write("### Workflow Diagram")
                        graph_bytes = diagram.encode("utf8")
                        base64_bytes = base64.b64encode(graph_bytes)
                        base64_string = base64_bytes.decode("ascii")
                        img_url = f"https://mermaid.ink/img/{base64_string}"
                        st.image(img_url, caption="Workflow Diagram rendered via mermaid.ink")
                    else:
                        st.error("Could not generate diagram for this workflow.")

if __name__ == "__main__":
    initialize_state()
    draw_sidebar()
    draw_main_content()