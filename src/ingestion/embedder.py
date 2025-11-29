from langchain_openai import OpenAIEmbeddings
from config.settings import settings

class EmbeddingGenerator:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY
        )

    def embed_documents(self, texts):
        """
        Generates embeddings for a list of texts.
        """
        return self.embeddings.embed_documents(texts)

    def embed_query(self, text):
        """
        Generates embedding for a single query text.
        """
        return self.embeddings.embed_query(text)
