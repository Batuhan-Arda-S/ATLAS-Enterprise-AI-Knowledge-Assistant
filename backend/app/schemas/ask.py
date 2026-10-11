from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.semantic_search import SemanticSearchRequest


class AskRequest(SemanticSearchRequest):
    document_id: int = Field(gt=0)


class SourceResponse(BaseModel):
    chunk_id: int
    document_id: int
    chunk_index: int


class AskResponse(BaseModel):
    answer: str | None
    answer_status: Literal["answered","no_candidates","insufficient_evidence"]
    retrieval_status: str
    retrieved_sources: list[SourceResponse]
    cited_sources: list[SourceResponse]