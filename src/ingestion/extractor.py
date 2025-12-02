import json
import os
from pydantic import BaseModel, Field
from typing import List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from config.settings import settings

# Define the schema for extraction
class Property(BaseModel):
    key: str = Field(..., description="Property key")
    value: str = Field(..., description="Property value")

class Entity(BaseModel):
    name: str = Field(..., description="Name of the entity")
    type: str = Field(..., description="Type of the entity as defined in the schema")
    properties: List[Property] = Field(default_factory=list, description="Additional properties like id, status, balance, etc.")

class Relationship(BaseModel):
    source: str = Field(..., description="Name of the source entity")
    target: str = Field(..., description="Name of the target entity")
    type: str = Field(..., description="Type of relationship as defined in the schema")
    properties: List[Property] = Field(default_factory=list, description="Relationship properties like pct, amount, type")

class ExtractionResult(BaseModel):
    entities: List[Entity]
    relationships: List[Relationship]

class EntityExtractor:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # Load schema and prompt
        self._load_config()
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", "{text}")
        ])
        
        self.chain = self.prompt | self.llm.with_structured_output(ExtractionResult)

    def _load_config(self):
        # Load graph schema
        schema_path = os.path.join(os.path.dirname(__file__), "../../config/graph_schema.json")
        with open(schema_path, "r") as f:
            self.schema = json.load(f)
            
        # Load prompt template
        prompt_path = os.path.join(os.path.dirname(__file__), "../../config/extraction_prompt.txt")
        with open(prompt_path, "r") as f:
            prompt_template = f.read()
            
        # Format schema for prompt
        node_types = "\n".join([f"- {n['label']}: {n['description']}" for n in self.schema['nodes']])
        rel_types = "- " + ", ".join(self.schema['relationships'])
        
        self.system_prompt = prompt_template.format(
            node_schema=node_types,
            rel_schema=rel_types
        )

    def extract(self, text: str) -> ExtractionResult:
        return self.chain.invoke({"text": text})
