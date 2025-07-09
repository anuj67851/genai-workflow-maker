import json
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
            input_data_str = self._fill_prompt_template(step.prompt_template, state)

            if isinstance(input_data_str, str):
                try:
                    input_data = json.loads(input_data_str)
                except json.JSONDecodeError:
                    return {"step_id": step.step_id, "success": False, "error": f"Rerank step received invalid JSON input: {input_data_str[:100]}..."}
            elif isinstance(input_data_str, dict):
                input_data = input_data_str
            else:
                return {"step_id": step.step_id, "success": False, "error": f"Rerank step received unexpected input type: {type(input_data_str)}"}

            if 'query' not in input_data or 'retrieved_docs' not in input_data:
                return {"step_id": step.step_id, "success": False, "error": "Rerank step input missing 'query' or 'retrieved_docs' keys."}

            query = input_data.get("query")
            retrieved_docs = input_data.get("retrieved_docs")

            # If there are no documents to rerank, just pass through the empty list.
            if not retrieved_docs:
                logger.warning("Rerank step received no documents to process. Returning empty list.")
                return {"step_id": step.step_id, "success": True, "type": "cross_encoder_rerank", "output": []}

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