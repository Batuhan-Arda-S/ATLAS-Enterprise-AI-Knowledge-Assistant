from types import SimpleNamespace

import app.models.document_chunk

from fastapi.testclient import TestClient

from app.main import app
from app.database.session import SessionFactory
from app.dependencies.auth import get_current_user
from app.models.conversation import Conversation
from app.models.document import Document
from app.models.user import User
from app.services.chat import ChatService


chat_service = ChatService()
conversation_id = None

try:
    with SessionFactory() as session:
        with session.begin():
            if session.get(User,1) is None or session.get(Document,12) is None:
                raise RuntimeError("Test user or document was not found")

            conversation = chat_service.create_conversation(session,user_id=1,
                                                            document_id=12,title="Streaming test")

            conversation_id = conversation.id

    app.dependency_overrides[get_current_user] = lambda:SimpleNamespace(id=1,role="admin")

    with TestClient(app) as client:
        with client.stream("POST",f"/chat/{conversation_id}/stream",json={"question":"How many days per week may I work remotely?",
                                                                          "limit":3}) as response:

            print("HTTP status:",response.status_code)

            for line in response.iter_lines():
                if line:
                    print(line)

    with SessionFactory() as session:
        messages = chat_service.get_messages(session,conversation_id,user_id=1)

        print("\nSaved messages:",len(messages))

        for message in messages:
            print("Role:",message.role)
            print("Content:",message.content)
            print("Answer status:",message.answer_status)

finally:
    app.dependency_overrides.pop(get_current_user,None)

    if conversation_id is not None:
        with SessionFactory() as session:
            with session.begin():
                conversation = session.get(Conversation,conversation_id)

                if conversation is not None:
                    session.delete(conversation)