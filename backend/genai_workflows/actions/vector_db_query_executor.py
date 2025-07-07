import os
import json
import logging
import numpy as np
from typing import Dict, Any

from .base_executor import BaseActionExecutor
from ..workflow import WorkflowStep

try:
    import faiss
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

logger = logging.getLogger(__name__)

class VectorDbQueryAction(BaseActionExecutor):
    def execute(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        """Queries a FAISS vector store to find similar documents."""
        if not RAG_AVAILABLE:
            return {"step_id": step.step_id, "success": False, "error": "RAG dependencies (faiss) are not installed."}

        try:
            collection_name = step.collection_name
            if not collection_name:
                return {"step_id": step.step_id, "success": False, "error": "Missing 'collection_name' for query step."}

            query_text = self._fill_prompt_template(step.prompt_template, state)
            if not query_text:
                return {"step_id": step.step_id, "success": False, "error": "Query step received no query text."}

            vector_store_dir = "vector_stores"
            faiss_path = f"{vector_store_dir}/{collection_name}.faiss"
            docs_path = f"{vector_store_dir}/{collection_name}.json"

            if not os.path.exists(faiss_path) or not os.path.exists(docs_path):
                logger.warning(f"Collection '{collection_name}' not found. Returning empty search results.")
                # Instead of failing, we return a successful result with an empty list.
                # This prevents the workflow from crashing.
                return {
                    "step_id": step.step_id,
                    "success": True,
                    "type": "vector_db_query",
                    "output": {"query": query_text, "retrieved_docs": []}
                }

            index = faiss.read_index(faiss_path)
            with open(docs_path, 'r') as f:
                documents = json.load(f)

            embedding_model = step.embedding_model or "text-embedding-3-small"
            query_embedding = self.client.embeddings.create(input=[query_text], model=embedding_model).data[0].embedding

            top_k = step.top_k or 5
            distances, indices = index.search(np.array([query_embedding], dtype=np.float32), top_k)

            retrieved_docs = [documents[i] for i in indices[0]]

            output = {"query": query_text, "retrieved_docs": retrieved_docs}
            logger.info(f"Retrieved {len(retrieved_docs)} documents from '{collection_name}'.")

            return {"step_id": step.step_id, "success": True, "type": "vector_db_query", "output": output}

        except Exception as e:
            error_msg = f"Vector DB query failed: {e}"
            logger.error(error_msg, exc_info=True)
            return {"step_id": step.step_id, "success": False, "error": error_msg}