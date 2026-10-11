from app.database.session import SessionFactory
from app.services.semantic_search import semantic_search_service
from app.services.prompt_builder import build_context


question = ("How many days per week may full-time employees " "work remotely?")

with SessionFactory() as session:
    matches = semantic_search_service.search(session=session,document_id=12,question=question,limit=3)

    context = build_context(matches)

print(context)