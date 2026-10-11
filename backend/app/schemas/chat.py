from datetime import datetime

from pydantic import BaseModel,ConfigDict,Field


class ConversationCreate(BaseModel):
    document_id: int = Field(ge=1)
    title: str | None = Field(default=None,min_length=1,max_length=200)


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    title: str | None
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str | None
    answer_status: str | None
    cited_chunk_ids: list[int] | None
    created_at: datetime


class ConversationDetail(ConversationResponse):
    messages: list[MessageResponse]
