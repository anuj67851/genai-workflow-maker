import os
import shutil
import logging
import io
from typing import List

from fastapi import UploadFile

# Import necessary libraries for text extraction, handling potential import errors
try:
    import PyPDF2
    from PIL import Image
    import pytesseract
    import docx
    EXTRACTION_LIBS_AVAILABLE = True
except ImportError:
    EXTRACTION_LIBS_AVAILABLE = False
    logging.warning("Optional libraries for file text extraction (PyPDF2, Pillow, pytesseract, python-docx) are not installed. File Ingestion will be limited.")


class FileProcessor:
    """
    Handles the logic for processing uploaded files, including text extraction
    and saving to disk.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def extract_text_from_files(self, files: List[UploadFile]) -> List[str]:
        """
        Extracts text content from a list of uploaded files.
        Supports PDF, common image formats, DOCX, and TXT.
        """
        if not EXTRACTION_LIBS_AVAILABLE:
            raise ImportError("Cannot extract text because required libraries are missing.")

        extracted_content = []
        for file in files:
            file_content = await file.read()
            file_extension = os.path.splitext(file.filename)[1].lower()
            text = ""

            try:
                if file_extension == '.pdf':
                    pdf_file = io.BytesIO(file_content)
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    text = "".join(page.extract_text() for page in pdf_reader.pages)
                elif file_extension in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
                    image = Image.open(io.BytesIO(file_content))
                    text = pytesseract.image_to_string(image)
                elif file_extension == '.docx':
                    doc = docx.Document(io.BytesIO(file_content))
                    text = "\n".join([p.text for p in doc.paragraphs])
                elif file_extension == '.txt':
                    text = file_content.decode('utf-8')
                else:
                    text = f"[Unsupported file type: {file_extension}]"
                    self.logger.warning(f"Unsupported file type '{file_extension}' for text extraction from file '{file.filename}'.")
            except Exception as e:
                error_msg = f"Failed to extract text from {file.filename}: {e}"
                self.logger.error(error_msg, exc_info=True)
                text = f"[Error processing file: {file.filename}]"

            extracted_content.append(text)

        self.logger.info(f"Extracted text from {len(extracted_content)} file(s).")
        return extracted_content

    async def save_files(
            self,
            files: List[UploadFile],
            base_storage_dir: str,
            custom_path: str,
            execution_id: str
    ) -> List[str]:
        """Saves a list of files to a designated storage path."""
        target_dir = os.path.join(base_storage_dir, custom_path, execution_id)
        os.makedirs(target_dir, exist_ok=True)

        saved_file_paths = []
        for file in files:
            file_location = os.path.join(target_dir, file.filename)
            with open(file_location, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_file_paths.append(file_location)
            self.logger.info(f"Successfully saved file to: {file_location}")

        return saved_file_paths