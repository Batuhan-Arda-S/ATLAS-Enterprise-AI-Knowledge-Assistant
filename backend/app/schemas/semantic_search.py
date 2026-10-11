from pydantic import BaseModel, Field, field_validator


class SemanticSearchRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    limit: int = Field(default=3, ge=1, le=10)

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Question cannot be blank")

        return value


class SemanticSearchHit(BaseModel):
    chunk_id: int
    chunk_index: int
    content: str
    cosine_similarity: float


class SemanticSearchResponse(BaseModel):
    document_id: int
    retrieval_status: str
    results: list[SemanticSearchHit]