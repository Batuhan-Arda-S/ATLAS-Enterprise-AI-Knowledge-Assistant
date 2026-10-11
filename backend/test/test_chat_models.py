from app.models.conversation import Conversation
from app.models.message import Message


def test_conversation_contains_messages():
    conversation = Conversation(user_id=1,document_id=12,title="Remote work")

    user_message = Message(role="user",content="How many days can I work remotely?")
    assistant_message = Message(role="assistant",
                                content="Up to two days. [[chunk:1]]",
                                answer_status="answered",
                                cited_chunk_ids=[1])

    conversation.messages.extend([user_message,assistant_message])

    assert len(conversation.messages) == 2
    assert user_message.conversation is conversation
    assert assistant_message.conversation is conversation
    assert assistant_message.cited_chunk_ids == [1]

def test_conversation_foreign_keys():
    user_fk = next(iter(Conversation.__table__.c.user_id.foreign_keys))
    document_fk = next(iter(Conversation.__table__.c.document_id.foreign_keys))
    conversation_fk = next(iter(Message.__table__.c.conversation_id.foreign_keys))

    assert user_fk.target_fullname == "users.id"
    assert document_fk.target_fullname == "documents.id"
    assert conversation_fk.target_fullname == "conversations.id"