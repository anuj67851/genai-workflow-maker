import json
import logging
import re
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
    async def execute(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        """Splits text, gets embeddings, and saves to a FAISS vector store."""
        if not RAG_AVAILABLE:
            return {"step_id": step.step_id, "success": False, "error": "RAG dependencies (faiss, langchain) are not installed."}

        try:
            # === Step 1: Get the input data correctly ===
            if not step.prompt_template or not re.search(r'\{input\.([a-zA-Z0-9_]+)}', step.prompt_template):
                return {"step_id": step.step_id, "success": False, "error": "Ingestion prompt_template must contain an {input.variable_name} placeholder."}

            input_variable_name = re.search(r'\{input\.([a-zA-Z0-9_]+)}', step.prompt_template).group(1)
            input_data = state.get("collected_inputs", {}).get(input_variable_name)

            if not input_data:
                return {"step_id": step.step_id, "success": False, "error": f"Ingestion step received no data from input variable '{input_variable_name}'."}

            # === Step 2: Initialize the text splitter ===
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=step.chunk_size,
                chunk_overlap=step.chunk_overlap
            )

            # === Step 3: Process input based on its type ===
            documents = []
            if isinstance(input_data, list):
                # This handles the File Ingestion case, where input_data is a list of strings.
                # Each string is a full document.
                logger.info(f"Processing {len(input_data)} document(s) from input list.")
                # We use split_documents, which is designed to take a list of docs and chunk each one.
                # Langchain expects "Document" objects, so we create them first.
                langchain_docs = text_splitter.create_documents(input_data)
                documents = text_splitter.split_documents(langchain_docs)
            elif isinstance(input_data, str):
                # This handles the Human Input case, where input_data is a single string.
                logger.info("Processing a single text block input.")
                # We use split_text for a single string.
                split_texts = text_splitter.split_text(input_data)
                documents = [d for d in split_texts] # Ensure output is a list of strings
            else:
                return {"step_id": step.step_id, "success": False, "error": f"Unsupported input type for ingestion: {type(input_data)}"}

            if not documents:
                return {"step_id": step.step_id, "success": False, "error": "Text splitting resulted in zero documents. Check input content and chunk settings."}

            logger.info(f"Splitting successful. Total chunks created: {len(documents)}")

            # Langchain's split_documents returns Document objects, we need the text content
            doc_contents = [doc.page_content if hasattr(doc, 'page_content') else doc for doc in documents]

            # === Step 4: Embed and Ingest ===
            embedding_model = step.embedding_model or "text-embedding-3-small"
            response = await self.client.embeddings.create(input=doc_contents, model=embedding_model)
            embeddings = [item.embedding for item in response.data]

            dimension = len(embeddings[0])
            index = faiss.IndexFlatL2(dimension)
            index.add(np.array(embeddings, dtype=np.float32))

            collection_name = step.collection_name
            if not collection_name:
                return {"step_id": step.step_id, "success": False, "error": "Missing 'collection_name' for ingestion step."}

            vector_store_dir = "vector_stores"
            faiss.write_index(index, f"{vector_store_dir}/{collection_name}.faiss")

            with open(f"{vector_store_dir}/{collection_name}.json", 'w') as f:
                json.dump(doc_contents, f)

            output_message = f"Successfully ingested {len(doc_contents)} chunks into collection '{collection_name}'."
            logger.info(output_message)
            return {"step_id": step.step_id, "success": True, "type": "vector_db_ingestion", "output": output_message}

        except Exception as e:
            error_msg = f"Vector DB ingestion failed: {e}"
            logger.error(error_msg, exc_info=True)
            return {"step_id": step.step_id, "success": False, "error": error_msg}