import httpx
import app.models.document_chunk

from app.database.session import SessionFactory
from app.models.conversation import Conversation
from app.models.document import Document
from app.models.user import User
from app.services.chat import ChatService
from app.services.llm import LLMService
from app.services.rag import RAGService
from app.services.semantic_search import semantic_search_service


conversation_id = None
chat_service = ChatService()

first_question = "How many days may I work remotely?"
followup_question = "Does my manager need to approve it?"

try:
    with httpx.Client(base_url="http://127.0.0.1:11434",timeout=120.0) as client:
        llm_service = LLMService(client=client,model="qwen3:4b-instruct")

        rag_service = RAGService(session_factory=SessionFactory,
                                 search_service=semantic_search_service,
                                 llm_service=llm_service)

        first_result = rag_service.answer(document_id=12,question=first_question)

        if first_result.answer_status != "answered":
            raise RuntimeError("The first question was not answered")

        with SessionFactory() as session:
            with session.begin():
                if session.get(User,1) is None or session.get(Document,12) is None:
                    raise RuntimeError("Test user or document was not found")

                conversation = chat_service.create_conversation(session,user_id=1,document_id=12,title="Remote work")

                conversation_id = conversation.id

                chat_service.add_message(
                    session,conversation_id,user_id=1,role="user",content=first_question)

                chat_service.add_message(session,
                                         conversation_id,
                                         user_id=1,
                                         role="assistant",
                                         content=first_result.answer,
                                         answer_status=first_result.answer_status,
                                         cited_chunk_ids=[source.chunk_id for source in first_result.cited_sources])

        with SessionFactory() as session:
            saved_messages = chat_service.get_messages(session,conversation_id,user_id=1,limit=6)

            history = [{"role":message.role,"content":message.content} for message in saved_messages if message.content]

        second_result = rag_service.answer(document_id=12,question=followup_question,history=history)

        print("First answer:",first_result.answer)
        print("History:",history)
        print("Follow-up:",followup_question)
        print("Second answer:",second_result.answer)
        print("Answer status:",second_result.answer_status)
        print("Cited IDs:",[source.chunk_id for source in second_result.cited_sources])

finally:
    if conversation_id is not None:
        with SessionFactory() as session:
            with session.begin():
                conversation = session.get(Conversation,conversation_id)

                if conversation is not None:
                    session.delete(conversation)