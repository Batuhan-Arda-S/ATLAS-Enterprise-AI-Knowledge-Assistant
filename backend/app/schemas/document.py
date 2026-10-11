from pydantic import BaseModel,ConfigDict,StringConstraints,model_validator
from datetime import datetime
from typing import Annotated

TitleText=Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=225,
    )]

DepartmentText=Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=100,
    )
]

ContentText=Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=200_000,
    )
]

class DocumentCreate(BaseModel):
    title: TitleText
    department: DepartmentText
    content: ContentText


class DocumentUpdate(BaseModel):
    title: TitleText | None = None
    department: DepartmentText | None = None
    content: ContentText | None = None

    @model_validator(mode="after")
    def validate_update_request(self):
        if not self.model_fields_set:
            raise ValueError("For the update requires at least 1 field")

        null_fields=[
            field_name
            for field_name in self.model_fields_set
            if getattr(self,field_name) is None
        ]

        if null_fields:
            raise ValueError(f"That fields can not be null:{','.join(null_fields)}")

        return self


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:int
    title:str
    department:str
    content:str
    filename:str | None = None
    content_type:str | None = None
    file_size:int | None = None
    processing_status:str = "processed"
    created_at:datetime
    updated_at:datetime

class DocumentListResponse(BaseModel):
    items:list[DocumentResponse]
    total:int
    offset:int
    limit:int

class DocumentDeleteResponse(BaseModel):
    message:str
    document:DocumentResponse

class DocumentUploadResponse(BaseModel):
    model_config=ConfigDict(from_attributes=True)

    id:int
    title:str
    department:str

    filename: str | None
    content_type: str | None
    file_size: int | None

    processing_status: str
