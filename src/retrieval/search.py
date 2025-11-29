from src.core.neo4j_client import neo4j_client
from src.ingestion.embedder import EmbeddingGenerator

class GraphRetriever:
    def __init__(self):
        self.embedder = EmbeddingGenerator()

    def search(self, query: str, k: int = 3):
        """
        Performs vector search to find relevant chunks.
        """
        query_embedding = self.embedder.embed_query(query)
        
        cypher_query = """
        CALL db.index.vector.queryNodes('chunk_vector_index', $k, $embedding)
        YIELD node, score
        RETURN node.text AS text, score, node.id AS id
        """
        
        results = neo4j_client.execute_query(cypher_query, {
            "k": k,
            "embedding": query_embedding
        })
        
        return results

    def get_context_window(self, chunk_id: str):
        """
        Retrieves previous and next chunks for a given chunk ID.
        """
        cypher_query = """
        MATCH (c:Chunk {id: $chunkId})
        OPTIONAL MATCH (prev)-[:NEXT]->(c)
        OPTIONAL MATCH (c)-[:NEXT]->(next)
        RETURN prev.text AS prev_text, c.text AS curr_text, next.text AS next_text
        """
        
        results = neo4j_client.execute_query(cypher_query, {"chunkId": chunk_id})
        if not results:
            return None
            
        record = results[0]
        return {
            "prev": record["prev_text"],
            "curr": record["curr_text"],
            "next": record["next_text"]
        }
