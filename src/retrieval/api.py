from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.retrieval.search import GraphRetriever
from src.retrieval.generation import RAGGenerator

app = FastAPI(title="GraphRAG API")

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    sources: list

@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    try:
        retriever = GraphRetriever()
        generator = RAGGenerator()
        
        # 1. Retrieve
        results = retriever.search(request.question)
        if not results:
            return QueryResponse(answer="No relevant information found.", sources=[])

        # 2. Generate
        answer = generator.generate_answer(request.question, results)
        
        # Extract sources
        sources = [r['text'] for r in results]
        
        return QueryResponse(answer=answer, sources=sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
