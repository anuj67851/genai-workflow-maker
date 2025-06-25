import html
from .workflow import Workflow, WorkflowStep

class WorkflowVisualizer:
    """Generates Mermaid.js diagrams from Workflow objects for easy visualization."""

    def generate_mermaid_diagram(self, workflow: Workflow) -> str:
        """
        Creates a Mermaid.js graph definition string from a workflow.

        Args:
            workflow: The Workflow object to visualize.

        Returns:
            A string containing the complete Mermaid.js syntax for the diagram.
        """
        if not workflow or not workflow.steps:
            return "graph TD;\n    subgraph Empty Workflow\n        A[No steps defined];\n    end"

        diagram_parts = ["graph TD;"] # TD = Top Down graph

        # --- Define Styles for Icons (optional but improves readability) ---
        # Note: You need Font Awesome loaded where you render this for icons to appear.
        diagram_parts.append("    classDef tool fill:#f9f,stroke:#333,stroke-width:2px;")
        diagram_parts.append("    classDef condition fill:#ccf,stroke:#333,stroke-width:2px;")
        diagram_parts.append("    classDef human fill:#fcf,stroke:#333,stroke-width:2px;")
        diagram_parts.append("    classDef response fill:#cff,stroke:#333,stroke-width:2px;")


        # --- Define Nodes ---
        # Add a clear start node
        start_node_id = f"START_{workflow.name.replace(' ', '_')}"
        diagram_parts.append(f'\n    {start_node_id}((Start))')
        if workflow.start_step_id:
            diagram_parts.append(f'    {start_node_id} --> {workflow.start_step_id}')

        # Define a single, clear end node
        end_node_id = f"END_{workflow.name.replace(' ', '_')}"
        diagram_parts.append(f'    {end_node_id}((End))')


        for step_id, step in workflow.steps.items():
            node_definition = self._format_node(step)
            diagram_parts.append(f"    {node_definition}")

        # --- Define Links ---
        for step_id, step in workflow.steps.items():
            # On Success Path
            if step.on_success:
                label = "Success / True" if step.action_type == "condition_check" else "Success"
                target = end_node_id if step.on_success == 'END' else step.on_success
                diagram_parts.append(f'    {step_id} -- "{label}" --> {target}')

            # On Failure Path
            if step.on_failure:
                label = "Failure / False"
                target = end_node_id if step.on_failure == 'END' else step.on_failure
                diagram_parts.append(f'    {step_id} -- "{label}" --> {target}')

        return "\n".join(diagram_parts)

    def _format_node(self, step: WorkflowStep) -> str:
        """Formats a single step into a Mermaid node definition string."""

        # Sanitize content for Mermaid diagram
        step_id = html.escape(step.step_id)
        description = html.escape(step.description)

        # Use icons for better readability (requires Font Awesome)
        icon = ""
        node_class = ""
        # Choose shape and icon based on action type
        if step.action_type == "agentic_tool_use":
            icon = "fa:fa-cogs"
            shape_start, shape_end = ('["', '"]')
            node_class = ":::tool"
        elif step.action_type == "condition_check":
            icon = "fa:fa-diamond"
            shape_start, shape_end = ('{', '}')
            node_class = ":::condition"
        elif step.action_type == "human_input":
            icon = "fa:fa-user-plus"
            shape_start, shape_end = ('[', ']')
            node_class = ":::human"
        elif step.action_type == "llm_response":
            icon = "fa:fa-robot"
            shape_start, shape_end = ('([', '])')
            node_class = ":::response"
        else: # Default shape
            shape_start, shape_end = ('[', ']')

        # Assemble the node content with the step_id and description
        node_content = f"'{icon} <b>{step_id}</b><br/>{description}'"

        return f"{step_id}{shape_start}{node_content}{shape_end} {node_class}"