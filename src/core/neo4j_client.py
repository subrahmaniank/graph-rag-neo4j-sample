from neo4j import GraphDatabase
from config.settings import settings

class Neo4jClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Neo4jClient, cls).__new__(cls)
            cls._instance.driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
            )
        return cls._instance

    def close(self):
        if self.driver:
            self.driver.close()

    def execute_query(self, query, parameters=None, db=None):
        with self.driver.session(database=db) as session:
            result = session.run(query, parameters)
            return [record for record in result]

neo4j_client = Neo4jClient()
