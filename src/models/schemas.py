from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Any, Dict


class RequirementRule(BaseModel):
    category: str = Field(
        ..., description="Category: Vergabe, Bericht, Ausgaben, Formular"
    )
    rule: str = Field(..., description="Short description of the rule")
    value: Optional[Any] = Field(
        None, description="Specific threshold or deadline if present"
    )


class RequirementRuleResult(BaseModel):
    rules: List[RequirementRule]


class ChunkMetadata(BaseModel):
    id: str
    doc_id: str
    text: str
    context_hierarchy: List[str]
    source_url: Optional[HttpUrl] = None
    page_number: Optional[int] = None
    rules: List[RequirementRule] = []


# --- GraphRAG Expansion ModelsAsString ---


class ExpandContextRequest(BaseModel):
    context_label: str = Field(
        ..., description="Label for the context, e.g. 'Guidelines_Drone_2024'"
    )
    text_chunks: List[str] = Field(
        ..., description="List of text chunks from the guideline"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional metadata like agency, year"
    )


class MappedRule(BaseModel):
    rule_id: str
    content: str
    relevance_reason: str


class MappedRegulation(BaseModel):
    category: str
    source_doc: str
    doc_id: Optional[str] = None
    rules: List[MappedRule]


class ExpandContextResponse(BaseModel):
    compliance_context_id: str
    mapped_regulations: List[MappedRegulation]


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []
    uploaded_doc_id: Optional[str] = None
