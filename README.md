# GraphRAG with Neo4j

## Overview
This project demonstrates a **GraphRAG (Graph-based Retrieval-Augmented Generation)** system using **Neo4j** and **LangChain**. It goes beyond simple vector search by extracting structured data (entities and relationships) from documents to build a knowledge graph. This allows for more context-aware retrieval and better answers to complex queries.

## Architecture

### 1. Ingestion Flow
The ingestion pipeline transforms raw documents into a structured graph:
1.  **Load**: Documents (PDF, DOCX, TXT) are loaded from the file system.
2.  **Split**: Text is split into manageable chunks.
3.  **Embed**: OpenAI embeddings are generated for each chunk.
4.  **Graph Construction**:
    -   **Structure**: Nodes are created for `Document` and `Chunk`, linked sequentially (`NEXT` relationship).
    -   **Entity Extraction**: An LLM analyzes each chunk to identify entities (e.g., `Person`, `Organization`, `Location`) and their relationships.
    -   **Graph Population**: These entities are stored in Neo4j and linked to their source chunks via `MENTIONED_IN` relationships.

### 2. Retrieval Flow
1.  **Query Embedding**: The user's question is embedded into a vector.
2.  **Vector Search**: The system queries the Neo4j vector index to find the most relevant `Chunk` nodes based on similarity.
3.  **Context Assembly**: The text from these chunks is retrieved. (Future enhancements can traverse the graph to pull in related entities).
4.  **Generation**: The retrieved context and the user's question are sent to an LLM to generate the final answer.

## Components
-   **`IngestionPipeline`** (`src/ingestion`): Orchestrates the loading, splitting, embedding, and entity extraction process.
-   **`GraphRetriever`** (`src/retrieval`): Handles vector search operations against the Neo4j database.
-   **`RAGGenerator`** (`src/retrieval`): Manages the LLM interaction to generate answers.
-   **`API`** (`src/retrieval/api.py`): A FastAPI server that exposes the ingestion and query capabilities.

## Prerequisites
-   **Python 3.12+**
-   **Neo4j Database**: You can use [Neo4j AuraDB](https://neo4j.com/cloud/platform/aura-graph-database/) (Free Tier available) or a local instance.
-   **OpenAI API Key**: Required for embeddings and entity extraction.

## Setup

1.  **Clone the repository**
    ```bash
    git clone https://github.com/subrahmaniank/graph-rag-neo4j-sample.git
    cd graph-rag-neo4j-sample
    ```

2.  **Install Dependencies**
    This project uses `uv` for dependency management, but standard `pip` works as well.
    ```bash
    # Using pip
    pip install -r requirements.txt
    
    # OR if you have uv installed
    uv sync
    ```

3.  **Configure Environment**
    Create a `.env` file in the root directory:
    ```env
    OPENAI_API_KEY=sk-your-key-here
    NEO4J_URI=bolt://localhost:7687
    NEO4J_USERNAME=neo4j
    NEO4J_PASSWORD=your-password
    ```

## Usage

The project includes a CLI `main.py` for easy interaction.

### 1. Initialize Schema
Set up the necessary vector indexes and constraints in Neo4j.
```bash
python main.py setup
```

### 2. Ingest Documents
Ingest a single file or a directory of files.
```bash
# Ingest a single file
python main.py ingest path/to/document.pdf

# Ingest a directory
python main.py ingest path/to/documents/
```

### 3. Query
Ask a question based on the ingested knowledge.
```bash
python main.py query "What are the key relationships mentioned in the documents?"
```

### 4. Start API Server
Run the FastAPI server to expose endpoints.
```bash
python main.py serve
```
The API will be accessible at `http://localhost:8000`.

## REST API

### Query Endpoint
**POST** `/query`

Query the knowledge graph with a question and receive an AI-generated answer with sources.

#### Request Body
```json
{
  "question": "Who are the ultimate beneficial owners of ACME Trading LLC? Show ownership chains, consolidated percent ownership, and cite the source document names and lines."
}
```

#### Response
```json
{
  "answer": "Based on the ingested documents...",
  "sources": [
    "Chunk text 1...",
    "Chunk text 2...",
    "Chunk text 3..."
  ]
}
```

#### Example with curl
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Who are the ultimate beneficial owners of ACME Trading LLC? Show ownership chains, consolidated percent ownership, and cite the source document names and lines."
  }'
```

#### Example with Python
```python
import requests

response = requests.post(
    "http://localhost:8000/query",
    json={
        "question": "Who are the ultimate beneficial owners of ACME Trading LLC? Show ownership chains, consolidated percent ownership, and cite the source document names and lines."
    }
)

result = response.json()
print(f"Answer: {result['answer']}")
print(f"Sources: {len(result['sources'])} chunks")
```

### API Documentation
Once the server is running, visit `http://localhost:8000/docs` for interactive API documentation (Swagger UI).

## Project Structure
```
├── config/             # Configuration settings
├── src/
│   ├── core/           # Database client and core utilities
│   ├── ingestion/      # Document processing and graph extraction logic
│   └── retrieval/      # Search and generation logic
├── main.py             # CLI entry point
├── pyproject.toml      # Project dependencies
└── README.md           # This file
```
