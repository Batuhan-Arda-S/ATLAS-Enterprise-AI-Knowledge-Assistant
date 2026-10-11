from app.database.session import SessionFactory
from app.models.conversation import Conversation
from app.models.document import Document
from app.models.message import Message
from app.models.user import User
import app.models.document_chunk

from app.services.chat import ChatService, ConversationNotFoundError


conversation_id = None
chat_service = ChatService()

try:
    with SessionFactory() as session:
        with session.begin():
            if session.get(User,1) is None or session.get(Document,12) is None:
                raise RuntimeError("Test user or document was not found")

            conversation = chat_service.create_conversation(session,user_id=1,
                                                            document_id=12,
                                                            title="Remote work")

            conversation_id = conversation.id

            chat_service.add_message(session,
                                     conversation_id,
                                     user_id=1,
                                     role="user",
                                     content="How many days may I work remotely?")

            chat_service.add_message(session,
                                     conversation_id,
                                     user_id=1,
                                     role="assistant",
                                     content="Up to two days per week. [[chunk:1]]",
                                     answer_status="answered",cited_chunk_ids=[1])


    with SessionFactory() as session:
        conversation = chat_service.get_conversation(session,conversation_id,user_id=1)
        messages = chat_service.get_messages(session,conversation_id,user_id=1)

        print("Conversation ID:",conversation.id)
        print("Title:",conversation.title)

        for message in messages:
            print("Role:",message.role)
            print("Content:",message.content)
            print("Answer status:",message.answer_status)
            print("Cited chunks:",message.cited_chunk_ids)

        try:
            chat_service.get_messages(session,conversation_id,user_id=2)
        except ConversationNotFoundError:
            print("Other-user access blocked")
        else:
            raise AssertionError("Other-user access was not blocked")

finally:
    if conversation_id is not None:
        with SessionFactory() as session:
            with session.begin():
                conversation = session.get(Conversation,conversation_id)

                if conversation is not None:
                    session.delete(conversation)