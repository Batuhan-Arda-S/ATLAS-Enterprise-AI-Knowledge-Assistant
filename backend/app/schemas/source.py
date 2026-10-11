from pydantic import BaseModel


class SourceResponse(BaseModel):
    chunk_id: int
    document_id: int
    chunk_index: int
    content: str
    document_title: str
    department: str
