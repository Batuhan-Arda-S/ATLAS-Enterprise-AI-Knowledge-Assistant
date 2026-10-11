from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.database.session import get_session
from app.dependencies.auth import get_current_user
from app.evaluation.retrieval_assessment import assess_retrieval
from app.models.document import Document
from app.models.user import User
from app.schemas.semantic_search import SemanticSearchRequest,SemanticSearchResponse,SemanticSearchHit
from app.services.semantic_search import semantic_search_service


router = APIRouter(prefix="/documents",tags=["semantic-search"])

@router.post("/{document_id}/search",response_model=SemanticSearchResponse)
def search_document(payload: SemanticSearchRequest,document_id: int = Path(ge=1),
                    session: Session = Depends(get_session),
                    current_user: User = Depends(get_current_user)):

    role = getattr(current_user.role, "value", current_user.role)

    if str(role).lower() != "admin":
        raise HTTPException(status_code=403,detail="Document search is not permitted")

    document = session.get(Document, document_id)

    if document is None:
        raise HTTPException(status_code=404,detail="Document not found")

    matches = semantic_search_service.search(session=session,
                                             document_id=document.id,
                                             question=payload.question,
                                             limit=payload.limit)

    assessment = assess_retrieval(distances=[distance for _, distance in matches])

    hits = [SemanticSearchHit(chunk_id=chunk.id,chunk_index=chunk.chunk_index,content=chunk.content,cosine_similarity=1.0 - distance) for chunk, distance in matches]

    return SemanticSearchResponse(document_id=document.id,retrieval_status=assessment.status,results=hits)