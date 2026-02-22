"""
Tests for Conversation Memory module.
"""
import pytest
from datetime import datetime, timezone
from src.llm.memory import Message, Conversation, ConversationMemory, get_memory


class TestMessage:
    """Tests for the Message dataclass."""

    def test_message_creation(self):
        msg = Message(role="user", content="Merhaba")
        assert msg.role == "user"
        assert msg.content == "Merhaba"
        assert isinstance(msg.timestamp, datetime)
        assert msg.metadata == {}

    def test_message_with_metadata(self):
        meta = {"source": "web", "lang": "tr"}
        msg = Message(role="assistant", content="Hoşgeldiniz", metadata=meta)
        assert msg.metadata == meta

    def test_message_timestamp_is_utc(self):
        msg = Message(role="user", content="test")
        assert msg.timestamp.tzinfo == timezone.utc


class TestConversation:
    """Tests for the Conversation dataclass."""

    def test_conversation_creation(self):
        conv = Conversation(id="test-123")
        assert conv.id == "test-123"
        assert conv.messages == []
        assert conv.context == {}

    def test_add_message(self):
        conv = Conversation(id="c1")
        conv.add_message("user", "Selam")
        assert len(conv.messages) == 1
        assert conv.messages[0].role == "user"
        assert conv.messages[0].content == "Selam"

    def test_add_message_with_metadata(self):
        conv = Conversation(id="c1")
        conv.add_message("assistant", "Yanıt", metadata={"model": "groq"})
        assert conv.messages[0].metadata == {"model": "groq"}

    def test_get_history(self):
        conv = Conversation(id="c1")
        conv.add_message("user", "Soru 1")
        conv.add_message("assistant", "Cevap 1")
        conv.add_message("user", "Soru 2")

        history = conv.get_history()
        assert len(history) == 3
        assert history[0] == {"role": "user", "content": "Soru 1"}
        assert history[1] == {"role": "assistant", "content": "Cevap 1"}

    def test_get_history_with_limit(self):
        conv = Conversation(id="c1")
        for i in range(20):
            conv.add_message("user", f"Mesaj {i}")

        history = conv.get_history(limit=5)
        assert len(history) == 5
        assert history[0]["content"] == "Mesaj 15"

    def test_get_context_prompt_empty(self):
        conv = Conversation(id="c1")
        assert conv.get_context_prompt() == ""

    def test_get_context_prompt(self):
        conv = Conversation(id="c1")
        conv.add_message("user", "Telefon öner")
        conv.add_message("assistant", "Samsung S24 iyi bir seçenek")

        prompt = conv.get_context_prompt()
        assert "Kullanıcı: Telefon öner" in prompt
        assert "Asistan: Samsung S24 iyi bir seçenek" in prompt


class TestConversationMemory:
    """Tests for the ConversationMemory manager."""

    def test_get_or_create_new(self):
        mem = ConversationMemory()
        conv = mem.get_or_create("new-conv")
        assert conv.id == "new-conv"
        assert len(conv.messages) == 0

    def test_get_or_create_existing(self):
        mem = ConversationMemory()
        conv1 = mem.get_or_create("conv-1")
        conv1.add_message("user", "test")
        conv2 = mem.get_or_create("conv-1")
        assert len(conv2.messages) == 1

    def test_add_exchange(self):
        mem = ConversationMemory()
        mem.add_exchange("conv-1", "Merhaba", "Hoşgeldiniz!")
        conv = mem.get_or_create("conv-1")
        assert len(conv.messages) == 2
        assert conv.messages[0].role == "user"
        assert conv.messages[1].role == "assistant"

    def test_get_context(self):
        mem = ConversationMemory()
        mem.add_exchange("conv-1", "Telefon öner", "Samsung S24 Ultra önerilir")
        context = mem.get_context("conv-1")
        assert "Telefon öner" in context

    def test_get_context_empty(self):
        mem = ConversationMemory()
        context = mem.get_context("nonexistent")
        assert context == ""

    def test_clear(self):
        mem = ConversationMemory()
        mem.add_exchange("conv-1", "test", "response")
        mem.clear("conv-1")
        context = mem.get_context("conv-1")
        assert context == ""

    def test_set_and_get_context_var(self):
        mem = ConversationMemory()
        mem.set_context("conv-1", "product_id", "iphone-16-pro")
        val = mem.get_context_var("conv-1", "product_id")
        assert val == "iphone-16-pro"

    def test_get_context_var_default(self):
        mem = ConversationMemory()
        val = mem.get_context_var("conv-1", "missing", default="none")
        assert val == "none"

    def test_multiple_conversations(self):
        mem = ConversationMemory()
        mem.add_exchange("conv-1", "Q1", "A1")
        mem.add_exchange("conv-2", "Q2", "A2")
        assert "Q1" in mem.get_context("conv-1")
        assert "Q2" in mem.get_context("conv-2")
        assert "Q1" not in mem.get_context("conv-2")
