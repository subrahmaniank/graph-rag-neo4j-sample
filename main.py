import argparse
import sys
from src.ingestion.pipeline import IngestionPipeline
from src.retrieval.search import GraphRetriever
from src.retrieval.generation import RAGGenerator
from src.core.neo4j_client import neo4j_client

def setup():
    print("Setting up Neo4j schema...")
    pipeline = IngestionPipeline()
    pipeline.setup_schema()
    print("Setup complete.")

import os

def ingest(path):
    pipeline = IngestionPipeline()
    
    if os.path.isdir(path):
        print(f"Ingesting directory: {path}")
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.lower().endswith('.pdf'):
                    file_path = os.path.join(root, file)
                    print(f"Processing file: {file_path}")
                    try:
                        pipeline.run(file_path)
                    except Exception as e:
                        print(f"Failed to ingest {file_path}: {e}")
    else:
        print(f"Ingesting file: {path}")
        pipeline.run(path)

def query(question):
    print(f"Querying: {question}")
    retriever = GraphRetriever()
    generator = RAGGenerator()
    
    # 1. Retrieve
    results = retriever.search(question)
    if not results:
        print("No relevant information found.")
        return

    print(f"Found {len(results)} relevant chunks.")
    
    # 2. Generate
    answer = generator.generate_answer(question, results)
    print("\nAnswer:")
    print(answer)

def main():
    parser = argparse.ArgumentParser(description="GraphRAG CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Setup command
    subparsers.add_parser("setup", help="Initialize Neo4j schema and indexes")

    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest a document")
    ingest_parser.add_argument("file", help="Path to the file to ingest (PDF, DOCX, TXT)")

    # Query command
    query_parser = subparsers.add_parser("query", help="Ask a question")
    query_parser.add_argument("question", help="The question to ask")

    # Serve command
    subparsers.add_parser("serve", help="Start the REST API server")

    args = parser.parse_args()

    try:
        if args.command == "setup":
            setup()
        elif args.command == "ingest":
            ingest(args.file)
        elif args.command == "query":
            query(args.question)
        elif args.command == "serve":
            import uvicorn
            print("Starting API server on http://localhost:8000")
            uvicorn.run("src.retrieval.api:app", host="0.0.0.0", port=8000, reload=True)
        else:
            parser.print_help()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Only close if not serving, as uvicorn needs the connection? 
        # Actually, neo4j_client is a singleton, so closing it here might affect the running server if it was initialized before.
        # But for 'serve', the loop runs inside uvicorn.run, so we reach finally only after stopping server.
        neo4j_client.close()

if __name__ == "__main__":
    main()
