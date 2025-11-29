import uuid
from src.core.neo4j_client import neo4j_client
from src.ingestion.loader import DocumentLoader
from src.ingestion.splitter import TextSplitter
from src.ingestion.embedder import EmbeddingGenerator
from src.ingestion.extractor import EntityExtractor

class IngestionPipeline:
    def __init__(self):
        self.loader = DocumentLoader()
        self.splitter = TextSplitter()
        self.embedder = EmbeddingGenerator()
        self.extractor = EntityExtractor()

    def setup_schema(self):
        # 1. Vector Index
        query = """
        CREATE VECTOR INDEX chunk_vector_index IF NOT EXISTS
        FOR (c:Chunk)
        ON (c.embedding)
        OPTIONS {indexConfig: {
            `vector.dimensions`: 1536,
            `vector.similarity_function`: 'cosine'
        }}
        """
        neo4j_client.execute_query(query)
        print("Vector index 'chunk_vector_index' created or already exists.")

        # 2. Constraints
        constraints = [
            "CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
            "CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT legal_entity_name IF NOT EXISTS FOR (e:LegalEntity) REQUIRE e.name IS UNIQUE",
            "CREATE CONSTRAINT person_name IF NOT EXISTS FOR (e:Person) REQUIRE e.name IS UNIQUE",
            "CREATE CONSTRAINT account_name IF NOT EXISTS FOR (e:Account) REQUIRE e.name IS UNIQUE",
            "CREATE CONSTRAINT facility_name IF NOT EXISTS FOR (e:Facility) REQUIRE e.name IS UNIQUE",
            "CREATE CONSTRAINT transaction_name IF NOT EXISTS FOR (e:Transaction) REQUIRE e.name IS UNIQUE",
            "CREATE CONSTRAINT branch_name IF NOT EXISTS FOR (e:Branch) REQUIRE e.name IS UNIQUE",
            "CREATE CONSTRAINT region_name IF NOT EXISTS FOR (e:Region) REQUIRE e.name IS UNIQUE",
            "CREATE CONSTRAINT instrument_name IF NOT EXISTS FOR (e:Instrument) REQUIRE e.name IS UNIQUE",
            "CREATE CONSTRAINT registry_name IF NOT EXISTS FOR (e:CompanyRegistry) REQUIRE e.name IS UNIQUE",
            "CREATE CONSTRAINT sanctions_name IF NOT EXISTS FOR (e:SanctionsList) REQUIRE e.name IS UNIQUE",
            "CREATE CONSTRAINT event_name IF NOT EXISTS FOR (e:Event) REQUIRE e.name IS UNIQUE",
            "CREATE CONSTRAINT product_name IF NOT EXISTS FOR (e:Product) REQUIRE e.name IS UNIQUE"
        ]

        for constraint in constraints:
            try:
                neo4j_client.execute_query(constraint)
                print(f"Constraint created: {constraint.split('REQUIRE')[1].strip()}")
            except Exception as e:
                print(f"Error creating constraint: {e}")

    def run(self, file_path: str):
        print(f"Starting ingestion for: {file_path}")
        
        # 1. Load
        docs = self.loader.load_document(file_path)
        print(f"Loaded {len(docs)} documents.")

        # 2. Split
        chunks = self.splitter.split_documents(docs)
        print(f"Split into {len(chunks)} chunks.")

        # 3. Embed, Extract and Store
        
        # Create Document Node
        doc_id = str(uuid.uuid4())
        file_name = file_path.split('\\')[-1]
        
        create_doc_query = """
        MERGE (d:Document {fileName: $fileName})
        ON CREATE SET d.id = $docId, d.createdAt = datetime()
        RETURN d
        """
        neo4j_client.execute_query(create_doc_query, {"fileName": file_name, "docId": doc_id})

        prev_chunk_id = None

        for i, chunk in enumerate(chunks):
            chunk_id = str(uuid.uuid4())
            text = chunk.page_content
            embedding = self.embedder.embed_query(text)
            
            # Create Chunk Node first (so we have it even if extraction fails)
            create_chunk_query = """
            MATCH (d:Document {id: $docId})
            CREATE (c:Chunk {id: $chunkId, text: $text, embedding: $embedding, index: $index})
            MERGE (d)-[:HAS_CHUNK]->(c)
            RETURN c
            """
            neo4j_client.execute_query(create_chunk_query, {
                "docId": doc_id,
                "chunkId": chunk_id,
                "text": text,
                "embedding": embedding,
                "index": i
            })

            # Extract Entities
            print(f"Extracting entities from chunk {i}...")
            try:
                extraction = self.extractor.extract(text)

                # Store Entities and Relationships
                for entity in extraction.entities:
                    # Sanitize label
                    label = entity.type.replace(" ", "")
                    
                    # Convert properties list to dict
                    props = {p.key: p.value for p in entity.properties}
                    
                    # Create Entity Node
                    create_entity_query = f"""
                    MERGE (e:{label} {{name: $name}})
                    SET e += $properties
                    WITH e
                    MATCH (c:Chunk {{id: $chunkId}})
                    MERGE (e)-[:MENTIONED_IN]->(c)
                    """
                    neo4j_client.execute_query(create_entity_query, {
                        "name": entity.name,
                        "properties": props,
                        "chunkId": chunk_id
                    })

                for rel in extraction.relationships:
                    # Create Relationship between Entities
                    # We assume entities are identified by name (simplification)
                    rel_type = rel.type.upper().replace(" ", "_")
                    
                    # Convert properties list to dict
                    props = {p.key: p.value for p in rel.properties}
                    
                    create_rel_query = f"""
                    MATCH (a {{name: $source}}), (b {{name: $target}})
                    MERGE (a)-[r:{rel_type}]->(b)
                    SET r += $properties
                    """
                    neo4j_client.execute_query(create_rel_query, {
                        "source": rel.source,
                        "target": rel.target,
                        "properties": props
                    })
                    
            except Exception as e:
                print(f"Error extracting/storing entities for chunk {i}: {e}")

            # Connect to previous chunk
            if prev_chunk_id:
                connect_chunks_query = """
                MATCH (c1:Chunk {id: $prevId}), (c2:Chunk {id: $currId})
                MERGE (c1)-[:NEXT]->(c2)
                """
                neo4j_client.execute_query(connect_chunks_query, {"prevId": prev_chunk_id, "currId": chunk_id})
            
            prev_chunk_id = chunk_id
            
        print(f"Ingestion complete for {file_name}")
