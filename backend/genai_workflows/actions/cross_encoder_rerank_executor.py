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
    def execute(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        """Re-ranks retrieved documents using a cross-encoder model for better relevance."""
        if not RAG_AVAILABLE:
            return {"step_id": step.step_id, "success": False, "error": "RAG dependencies (sentence-transformers) are not installed."}

        try:
            # The input to this step is expected to be the output from the query step
            input_data_str = self._fill_prompt_template(step.prompt_template, state)

            # The filled template might be a JSON string, so we parse it.
            # It could also be a direct reference to a python object.
            if isinstance(input_data_str, str):
                try:
                    input_data = json.loads(input_data_str)
                except json.JSONDecodeError:
                    # Fallback for if the input isn't a valid JSON string
                    return {"step_id": step.step_id, "success": False, "error": f"Rerank step received invalid input. Expected JSON object but got: {input_data_str[:100]}..."}
            elif isinstance(input_data_str, dict):
                input_data = input_data_str # It was already a dict
            else:
                return {"step_id": step.step_id, "success": False, "error": f"Rerank step received unexpected input type: {type(input_data_str)}"}


            query = input_data.get("query")
            retrieved_docs = input_data.get("retrieved_docs")

            if not query or not retrieved_docs:
                return {"step_id": step.step_id, "success": False, "error": "Rerank step input missing 'query' or 'retrieved_docs'."}

            model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            sentence_pairs = [[query, doc] for doc in retrieved_docs]

            scores = model.predict(sentence_pairs)

            # Combine docs with scores, sort, and return top N
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