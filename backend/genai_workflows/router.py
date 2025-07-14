import logging
from typing import List, Optional
from .workflow import Workflow
from ..config import settings

class WorkflowRouter:
    """Selects the best workflow to handle a user query."""

    def __init__(self, openai_client):
        self.client = openai_client
        self.logger = logging.getLogger(__name__)

    def find_matching_workflow(self, query: str, workflows: List[Workflow]) -> Optional[Workflow]:
        """
        Finds the best matching workflow from a list using an LLM.

        Note: This approach can be slow with many workflows. For production,
        consider replacing this with a vector embedding search for better performance.
        """
        if not workflows:
            return None

        workflow_summaries = "\n".join(
            [f"ID: {wf.name} - Triggers: {', '.join(wf.triggers)} - Description: {wf.description}" for wf in workflows]
        )

        match_prompt = f"""
        User Query: "{query}"

        Available Workflows:
        ---
        {workflow_summaries}
        ---
        
        Based on the user's query, which workflow ID is the most appropriate to handle this request?
        Consider the triggers and description for semantic relevance.
        Respond with ONLY the workflow ID (e.g., "Professor Meeting Scheduler"). If no workflow is a clear match, respond with "NONE".
        """

        try:
            # Use the global settings object for the default model
            response = self.client.chat.completions.create(
                model=settings.DEFAULT_MODEL,
                messages=[{"role": "user", "content": match_prompt}],
                temperature=0.0,
                max_tokens=50
            )

            best_match_name = response.choices[0].message.content.strip()

            if best_match_name == "NONE":
                self.logger.info(f"No matching workflow found for query: '{query}'")
                return None

            for workflow in workflows:
                if workflow.name == best_match_name:
                    self.logger.info(f"Matched query to workflow: '{workflow.name}'")
                    return workflow

            return None

        except Exception as e:
            self.logger.error(f"Error during workflow matching: {e}")
            return None