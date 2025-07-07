import json
import logging
import numpy as np
from typing import Dict, Any

from .base_executor import BaseActionExecutor
from ..workflow import WorkflowStep

try:
    import faiss
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

logger = logging.getLogger(__name__)

class VectorDbIngestionAction(BaseActionExecutor):
    def execute(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        """Splits text, gets embeddings, and saves to a FAISS vector store."""
        if not RAG_AVAILABLE:
            return {"step_id": step.step_id, "success": False, "error": "RAG dependencies (faiss, langchain) are not installed."}

        try:
            collection_name = step.collection_name
            if not collection_name:
                return {"step_id": step.step_id, "success": False, "error": "Missing 'collection_name' for ingestion step."}

            input_text = self._fill_prompt_template(step.prompt_template, state)
            if not input_text:
                return {"step_id": step.step_id, "success": False, "error": "Ingestion step received no input text."}

            text_splitter = RecursiveCharacterTextSplitter(chunk_size=step.chunk_size, chunk_overlap=step.chunk_overlap)
            documents = text_splitter.split_text(input_text)

            logger.info(f"Splitting text into {len(documents)} chunks.")

            embedding_model = step.embedding_model or "text-embedding-3-small"
            response = self.client.embeddings.create(input=documents, model=embedding_model)
            embeddings = [item.embedding for item in response.data]

            dimension = len(embeddings[0])
            index = faiss.IndexFlatL2(dimension)
            index.add(np.array(embeddings, dtype=np.float32))

            vector_store_dir = "vector_stores"
            faiss.write_index(index, f"{vector_store_dir}/{collection_name}.faiss")

            # Save the text documents separately, linked by index
            with open(f"{vector_store_dir}/{collection_name}.json", 'w') as f:
                json.dump(documents, f)

            output_message = f"Successfully ingested {len(documents)} chunks into collection '{collection_name}'."
            logger.info(output_message)
            return {"step_id": step.step_id, "success": True, "type": "vector_db_ingestion", "output": output_message}

        except Exception as e:
            error_msg = f"Vector DB ingestion failed: {e}"
            logger.error(error_msg, exc_info=True)
            return {"step_id": step.step_id, "success": False, "error": error_msg}