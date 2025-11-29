import os
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader

class DocumentLoader:
    @staticmethod
    def load_document(file_path: str):
        """
        Loads a document based on its file extension.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        if ext == '.pdf':
            loader = PyPDFLoader(file_path)
        elif ext == '.docx':
            loader = Docx2txtLoader(file_path)
        elif ext == '.txt':
            loader = TextLoader(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        return loader.load()
