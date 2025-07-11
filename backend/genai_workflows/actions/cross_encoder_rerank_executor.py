import logging
from typing import Dict, Any

from .base_executor import BaseActionExecutor
from ..workflow import WorkflowStep

try:
    from sentence_transformers import CrossEncoder
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

logger = logging.getLogger(__name__)

class CrossEncoderRerankAction(BaseActionExecutor):
    async def execute(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        """Re-ranks retrieved documents using a cross-encoder model for better relevance."""
        if not RAG_AVAILABLE:
            return {"step_id": step.step_id, "success": False, "error": "RAG dependencies (sentence-transformers) are not installed."}

        try:
            # The prompt_template for this node should just be the placeholder, e.g., "{input.query_results}"
            # The _get_value_from_state helper will retrieve the actual dictionary.
            input_data = self._get_value_from_state(step.prompt_template, state)

            if not isinstance(input_data, dict):
                # This can happen if the placeholder wasn't found or returned an unexpected type.
                filled_str = self._fill_prompt_template(step.prompt_template, state)
                return {"step_id": step.step_id, "success": False, "error": f"Rerank step did not receive a valid dictionary. Check the source variable. Value was: {str(filled_str)[:200]}"}

            if 'query' not in input_data or 'retrieved_docs' not in input_data:
                return {"step_id": step.step_id, "success": False, "error": "Rerank step input dictionary is missing 'query' or 'retrieved_docs' keys."}

            query = input_data.get("query")
            retrieved_docs = input_data.get("retrieved_docs")

            if not retrieved_docs:
                logger.warning("Rerank step received no documents to process. Returning empty list.")
                return {"step_id": step.step_id, "success": True, "type": "cross_encoder_rerank", "output": []}

            if not isinstance(retrieved_docs, list) or not all(isinstance(doc, str) for doc in retrieved_docs):
                return {"step_id": step.step_id, "success": False, "error": "The 'retrieved_docs' key must contain a list of strings."}

            model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            sentence_pairs = [[query, doc] for doc in retrieved_docs]
            scores = model.predict(sentence_pairs)

            scored_docs = list(zip(scores, retrieved_docs))
            scored_docs.sort(key=lambda x: x[0], reverse=True)
            rerank_top_n = step.rerank_top_n or 3
            reranked_docs = [doc for score, doc in scored_docs[:rerank_top_n]]

            logger.info(f"Re-ranked {len(retrieved_docs)} documents down to {len(reranked_docs)}.")

            return {"step_id": step.step_id, "success": True, "type": "cross_encoder_rerank", "output": reranked_docs}

        except Exception as e:
            error_msg = f"Cross-encoder re-ranking failed: {e}"
            logger.error(error_msg, exc_info=True)
            return {"step_id": step.step_id, "success": False, "error": error_msg}