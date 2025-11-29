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
    type: str = Field(..., description="Type of the entity (LegalEntity, Person, Account, Facility, Transaction, Branch, Region, Instrument, CompanyRegistry, SanctionsList, Event, Product)")
    properties: List[Property] = Field(default_factory=list, description="Additional properties like id, status, balance, etc.")

class Relationship(BaseModel):
    source: str = Field(..., description="Name of the source entity")
    target: str = Field(..., description="Name of the target entity")
    type: str = Field(..., description="Type of relationship (HAS_ACCOUNT, IS_SIGNATORY_OF, OWNS, BORROWER_OF, HAS_EXPOSURE, FROM, TO, REGISTERED_AT, HAS_ALIAS, RELATED_TO)")
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
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert financial analyst. Extract entities and relationships from the text based on the following schema:
            
            Node Types:
            - LegalEntity: corporates, subsidiaries, SPVs
            - Person: signatories, UBOs, employees
            - Account: bank accounts
            - Facility: credit facilities, loans
            - Transaction: high-value transactions
            - Branch/Region: organizational units
            - Instrument: securities, derivatives
            - CompanyRegistry: DUNS, LEI
            - SanctionsList: sanctions entries
            - Event: alerts, investigations
            - Product: trade finance, FX
            
            Relationship Types:
            - HAS_ACCOUNT, IS_SIGNATORY_OF, OWNS, BORROWER_OF, HAS_EXPOSURE
            - FROM, TO, REGISTERED_AT, HAS_ALIAS, RELATED_TO
            
            Extract properties like IDs, amounts, percentages where available.
            """),
            ("human", "{text}")
        ])
        
        self.chain = self.prompt | self.llm.with_structured_output(ExtractionResult)

    def extract(self, text: str) -> ExtractionResult:
        return self.chain.invoke({"text": text})
