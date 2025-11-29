from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from config.settings import settings

class RAGGenerator:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o", # Or gpt-3.5-turbo
            openai_api_key=settings.OPENAI_API_KEY
        )

    def generate_answer(self, query: str, context: list):
        """
        Generates an answer based on the query and retrieved context.
        """
        # Combine context
        context_str = "\n\n".join([c['text'] for c in context])
        
        system_prompt = """You are a helpful assistant. Use the following pieces of context to answer the user's question.
        If you don't know the answer, just say that you don't know, don't try to make up an answer.
        """
        
        user_prompt = f"Context:\n{context_str}\n\nQuestion: {query}"
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = self.llm.invoke(messages)
        return response.content
