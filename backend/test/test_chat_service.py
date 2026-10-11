from unittest.mock import Mock

import pytest

from types import SimpleNamespace
from app.services.chat import ChatService, ConversationNotFoundError


def test_other_user_cannot_read_messages():
    session = Mock()
    session.scalar.return_value = None

    chat_service = ChatService()

    with pytest.raises(ConversationNotFoundError):
        chat_service.get_messages(session,conversation_id=15,user_id=2)

    session.scalars.assert_not_called()

def test_other_user_cannot_add_message():
    session = Mock()
    session.scalar.return_value = None

    chat_service = ChatService()

    with pytest.raises(ConversationNotFoundError):
        chat_service.add_message(session,conversation_id=15,user_id=2,role="user",content="Hello")

    session.add.assert_not_called()

def test_chat_history_preserves_message_order():
    session = Mock()
    session.scalar.return_value = SimpleNamespace(id=15)

    session.scalars.return_value.all.return_value = [SimpleNamespace(id=7),
                                                     SimpleNamespace(id=6),
                                                     SimpleNamespace(id=5)]

    messages = ChatService().get_messages(session,conversation_id=15,user_id=1,limit=3)

    assert [message.id for message in messages] == [5,6,7]