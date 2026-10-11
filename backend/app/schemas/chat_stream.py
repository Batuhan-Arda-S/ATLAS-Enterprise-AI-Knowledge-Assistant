from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints


class ChatStreamRequest(BaseModel):
    question: Annotated[str,StringConstraints(strip_whitespace=True,min_length=1,max_length=1000)]
    limit: int = Field(default=3,ge=1,le=10)

