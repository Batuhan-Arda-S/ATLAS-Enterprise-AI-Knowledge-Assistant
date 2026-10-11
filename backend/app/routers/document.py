from fastapi import APIRouter,Query,Depends,UploadFile,File,Form,HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_session
from typing import Annotated
from app.services.document import document_service
from app.schemas.document import (DocumentCreate,
                                  DocumentUpdate,
                                  DocumentResponse,
                                  DocumentDeleteResponse,
                                  DocumentListResponse,
                                  DocumentUploadResponse)
from app.services.file_upload import file_upload_service
from app.dependencies.auth import require_admin
from app.models.document_chunk import DocumentChunk
from app.schemas.source import SourceResponse
from sqlalchemy import select,func
from app.models.conversation import Conversation

router = APIRouter(prefix="/documents",tags=["Documents"],dependencies=[Depends(require_admin)])


@router.post("/",status_code=201,response_model=DocumentResponse)
def create_document(document: DocumentCreate,session: Annotated[Session, Depends(get_session)]):
    document_data=document.model_dump()
    return document_service.create_document(session=session,document_data=document_data)


@router.get("/",response_model=DocumentListResponse)
def get_documents(session: Annotated[Session, Depends(get_session)],
                  offset:Annotated[int,Query(ge=0)]=0,
                  limit:Annotated[int,Query(ge=1,le=100)]=10):

   return document_service.get_documents(session=session,offset=offset, limit=limit)



@router.get("/{document_id}",response_model=DocumentResponse)
def get_document(document_id: int,session: Annotated[Session, Depends(get_session)]):

    return document_service.get_document(session=session,document_id=document_id)


@router.get("/{document_id}/chunks/{chunk_id}",response_model=SourceResponse)
def get_document_chunk(document_id: int,chunk_id: int,
                       session: Annotated[Session,Depends(get_session)]):
    chunk = session.get(DocumentChunk,chunk_id)
    if chunk is None or chunk.document_id != document_id:
        raise HTTPException(status_code=404,detail="Source not found")
    document = document_service.get_document(session=session,document_id=document_id)
    return SourceResponse(chunk_id=chunk.id,document_id=document.id,
                          chunk_index=chunk.chunk_index,content=chunk.content,
                          document_title=document.title,department=document.department)


@router.patch("/{document_id}",response_model=DocumentResponse)
def update_document(document_id: int, document_update: DocumentUpdate,session: Annotated[Session, Depends(get_session)]):

    update_data=document_update.model_dump(exclude_unset=True)

    return document_service.update_document(session=session,document_id=document_id, update_data=update_data)

@router.delete("/{document_id}",response_model=DocumentDeleteResponse)
def delete_document(document_id: int,session: Annotated[Session, Depends(get_session)]):
    if session.scalar(select(func.count(Conversation.id)).where(
            Conversation.document_id == document_id)):
        raise HTTPException(status_code=409,detail="Document has conversation history and cannot be deleted")
    deleted_document = document_service.delete_document(session=session,document_id=document_id)

    return {
        "message": "Document Deleted Successfully",
        "document": deleted_document
    }

@router.post("/upload",status_code=201,response_model=DocumentUploadResponse)
async def upload_document(title:Annotated[str,Form(min_length=1,max_length=225)],
                          department:Annotated[str,Form(min_length=1,max_length=100)],
                          file:Annotated[UploadFile,File(...)],
                          session:Annotated[Session,Depends(get_session)]):

    contents=await file_upload_service.validate_and_read(file)

    return document_service.create_uploaded_document(
        session=session,
        title=title,
        department=department,
        filename=file.filename,
        content_type=file.content_type,
        contents=contents,
    )


