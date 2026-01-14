from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Any


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
