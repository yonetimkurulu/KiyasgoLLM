"""
Conversation Memory
Çoklu-tur konuşma hafızası.
"""
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json


@dataclass
class Message:
    """A single message in conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict = field(default_factory=dict)


@dataclass
class Conversation:
    """A conversation with message history."""
    id: str
    messages: list[Message] = field(default_factory=list)
    context: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def add_message(self, role: str, content: str, metadata: dict = None):
        """Add a message to the conversation."""
        self.messages.append(Message(
            role=role,
            content=content,
            metadata=metadata or {},
        ))
    
    def get_history(self, limit: int = 10) -> list[dict]:
        """Get recent messages as list of dicts."""
        recent = self.messages[-limit:]
        return [
            {"role": m.role, "content": m.content}
            for m in recent
        ]
    
    def get_context_prompt(self) -> str:
        """Build context prompt from history."""
        if not self.messages:
            return ""
        
        history = self.get_history(6)  # Last 6 messages
        lines = []
        for msg in history:
            prefix = "Kullanıcı" if msg["role"] == "user" else "Asistan"
            lines.append(f"{prefix}: {msg['content'][:200]}")
        
        return "\n".join(lines)


class ConversationMemory:
    """
    Manage multiple conversations.
    In-memory implementation (can be extended to Redis/DB).
    """
    
    def __init__(self):
        self._conversations: dict[str, Conversation] = {}
    
    def get_or_create(self, conversation_id: str) -> Conversation:
        """Get existing or create new conversation."""
        if conversation_id not in self._conversations:
            self._conversations[conversation_id] = Conversation(id=conversation_id)
        return self._conversations[conversation_id]
    
    def add_exchange(
        self,
        conversation_id: str,
        user_message: str,
        assistant_response: str,
    ):
        """Add a user/assistant exchange."""
        conv = self.get_or_create(conversation_id)
        conv.add_message("user", user_message)
        conv.add_message("assistant", assistant_response)
    
    def get_context(self, conversation_id: str) -> str:
        """Get conversation context for prompts."""
        conv = self.get_or_create(conversation_id)
        return conv.get_context_prompt()
    
    def clear(self, conversation_id: str):
        """Clear a conversation."""
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
    
    def set_context(self, conversation_id: str, key: str, value):
        """Set context variable for conversation."""
        conv = self.get_or_create(conversation_id)
        conv.context[key] = value
    
    def get_context_var(self, conversation_id: str, key: str, default=None):
        """Get context variable from conversation."""
        conv = self.get_or_create(conversation_id)
        return conv.context.get(key, default)


# Singleton
_memory = None

def get_memory() -> ConversationMemory:
    """Get singleton conversation memory."""
    global _memory
    if _memory is None:
        _memory = ConversationMemory()
    return _memory
