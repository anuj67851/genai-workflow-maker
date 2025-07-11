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
    async def execute(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        """Splits text, gets embeddings, and saves to a FAISS vector store."""
        if not RAG_AVAILABLE:
            return {"step_id": step.step_id, "success": False, "error": "RAG dependencies (faiss, langchain) are not installed."}

        try:
            # Step 1: Use the main helper to fill the entire template.
            # This can now handle any combination of variables from context or input.
            if not step.prompt_template:
                return {"step_id": step.step_id, "success": False, "error": "Ingestion node is missing its prompt_template / data source."}

            input_data = self._fill_prompt_template(step.prompt_template, state)

            if not input_data:
                return {"step_id": step.step_id, "success": False, "error": "Ingestion step received no data after filling the template. Check if the source variables exist and have content."}

            # The result of _fill_prompt_template for complex types (like a list from File Ingestion)
            # is a JSON string, so we should try to parse it.
            try:
                potential_list = json.loads(input_data)
                if isinstance(potential_list, list):
                    input_data = potential_list
            except (json.JSONDecodeError, TypeError):
                # This is expected if the template resulted in a plain string. We can safely ignore it.
                pass

            # === Step 2: Initialize the text splitter ===
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=step.chunk_size,
                chunk_overlap=step.chunk_overlap
            )

            # === Step 3: Process input based on its type ===
            documents = []
            if isinstance(input_data, list):
                # Handles cases where the input variable was a list of strings (e.g., from file ingestion).
                logger.info(f"Processing {len(input_data)} document(s) from input list.")
                # We need to ensure all items in the list are strings.
                string_docs = [str(doc) for doc in input_data]
                langchain_docs = text_splitter.create_documents(string_docs)
                documents = text_splitter.split_documents(langchain_docs)
            elif isinstance(input_data, str):
                # Handles cases where the template resulted in a single block of text.
                logger.info("Processing a single text block input.")
                split_texts = text_splitter.split_text(input_data)
                documents = [d for d in split_texts]
            else:
                return {"step_id": step.step_id, "success": False, "error": f"Unsupported input type for ingestion: {type(input_data)}"}

            if not documents:
                return {"step_id": step.step_id, "success": False, "error": "Text splitting resulted in zero documents. Check input content and chunk settings."}

            logger.info(f"Splitting successful. Total chunks created: {len(documents)}")

            doc_contents = [doc.page_content if hasattr(doc, 'page_content') else doc for doc in documents]

            # === Step 4: Embed and Ingest ===
            embedding_model = step.embedding_model or "text-embedding-3-small"
            response = await self.client.embeddings.create(input=doc_contents, model=embedding_model)
            embeddings = [item.embedding for item in response.data]

            dimension = len(embeddings[0])
            index = faiss.IndexFlatL2(dimension)
            index.add(np.array(embeddings, dtype=np.float32))

            # Also allow the collection name to be sourced from any state variable.
            collection_name = self._fill_prompt_template(step.collection_name, state)
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