from .workflow import Workflow, WorkflowStep

class WorkflowVisualizer:
    """Generates professional, readable Mermaid.js diagrams with maximum compatibility."""

    def generate_mermaid_diagram(self, workflow: Workflow) -> str:
        """
        Creates a Mermaid.js graph definition string from a workflow.
        This version uses a professional color palette and ensures text wrapping
        using the universally compatible newline character (`\n`).
        """
        if not workflow or not workflow.steps:
            return "graph TD;\n    A[Empty Workflow];"

        diagram_parts = ["graph TD;"]

        # 1. Define a professional color palette and styles
        diagram_parts.extend([
            "    classDef tool fill:#cde4ff,stroke:#333,stroke-width:2px,color:#333;",
            "    classDef condition fill:#fff2cc,stroke:#333,stroke-width:2px,color:#333;",
            "    classDef human fill:#d4edda,stroke:#333,stroke-width:2px,color:#333;",
            "    classDef response fill:#d1ecf1,stroke:#333,stroke-width:2px,color:#333;",
            "    classDef startEnd fill:#f8f9fa,stroke:#333,stroke-width:2px,color:#333;"
        ])

        # 2. Define Start and End Nodes with styling
        start_node_id = "START"
        end_node_id = "END"
        diagram_parts.append(f'    {start_node_id}(("Start")):::startEnd')
        if workflow.start_step_id:
            diagram_parts.append(f'    {start_node_id} --> {workflow.start_step_id}')
        diagram_parts.append(f'    {end_node_id}(("End")):::startEnd')

        # 3. Define all Workflow Step nodes
        for step in workflow.steps.values():
            node_definition = self._format_node_for_compatibility(step)
            diagram_parts.append(f"    {node_definition}")

        # 4. Define all connections
        for step_id, step in workflow.steps.items():
            target_on_success = end_node_id if step.on_success == 'END' else step.on_success
            if step.action_type == "condition_check":
                diagram_parts.append(f'    {step_id} -->|"True"| {target_on_success}')
            else:
                diagram_parts.append(f'    {step_id} --> {target_on_success}')

            if step.on_failure:
                target_on_failure = end_node_id if step.on_failure == 'END' else step.on_failure
                diagram_parts.append(f'    {step_id} -->|"False"| {target_on_failure}')

        return "\n".join(diagram_parts)

    def _format_node_for_compatibility(self, step: WorkflowStep) -> str:
        """
        Formats a node using simple quotes and the \n character for wrapping.
        This is the most reliable method for all Mermaid renderers.
        """
        # Sanitize the description to escape any double quotes within the text.
        sanitized_description = step.description.replace('"', '"')

        # Create multi-line text using the \n newline character.
        # This is the key change for reliable text wrapping.
        text_content = f"{step.step_id}\\n{sanitized_description}"

        # Use a simple, standard double-quoted string.
        node_text_block = f'"{text_content}"'

        # Define the node shape and text
        if step.action_type == "agentic_tool_use":
            node_definition = f'{step.step_id}>{node_text_block}]'
            class_name = ":::tool"
        elif step.action_type == "condition_check":
            node_definition = f'{step.step_id}{{{node_text_block}}}'
            class_name = ":::condition"
        elif step.action_type == "human_input":
            node_definition = f'{step.step_id}({node_text_block})'
            class_name = ":::human"
        elif step.action_type == "llm_response":
            node_definition = f'{step.step_id}(({node_text_block}))'
            class_name = ":::response"
        else:
            node_definition = f'{step.step_id}[{node_text_block}]'
            class_name = ""

        return f"{node_definition}{class_name}"