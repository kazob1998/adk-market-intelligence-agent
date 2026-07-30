"""
Context & Memory Management for Google ADK Agent.
Provides session state persistence, conversation history tracking, and a long-term memory store
for cross-session context recall.
"""

from typing import Dict, List, Any, Optional
import json
import time
from pydantic import BaseModel, Field


class MemoryItem(BaseModel):
    key: str
    content: Any
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)


class SessionState(BaseModel):
    session_id: str
    user_id: str = "default_user"
    history: List[Dict[str, str]] = Field(default_factory=list)
    state: Dict[str, Any] = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)

    def add_message(self, role: str, content: str):
        self.history.append({"role": role, "content": content, "timestamp": str(time.time())})
        self.updated_at = time.time()

    def get_recent_history(self, limit: int = 10) -> List[Dict[str, str]]:
        return self.history[-limit:]


class MemoryManager:
    """
    Manages short-term session state and long-term memory store for ADK Agents.
    Supports in-memory persistence and JSON file backup.
    """

    def __init__(self):
        self._sessions: Dict[str, SessionState] = {}
        self._long_term_memory: Dict[str, MemoryItem] = {}

    def get_or_create_session(self, session_id: str, user_id: str = "default_user") -> SessionState:
        """Retrieves an existing session or creates a new session state."""
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionState(session_id=session_id, user_id=user_id)
        return self._sessions[session_id]

    def update_session_state(self, session_id: str, key: str, value: Any):
        """Updates a state key inside session context."""
        session = self.get_or_create_session(session_id)
        session.state[key] = value
        session.updated_at = time.time()

    def store_long_term_memory(self, key: str, content: Any, metadata: Optional[Dict[str, Any]] = None):
        """Stores a factual item in long-term memory for future retrieval."""
        item = MemoryItem(key=key, content=content, metadata=metadata or {})
        self._long_term_memory[key] = item

    def recall_long_term_memory(self, query: str) -> List[Dict[str, Any]]:
        """
        Recalls items from long-term memory matching any query terms or tokens.
        """
        results = []
        if not query.strip():
            return [{"key": item.key, "content": item.content, "metadata": item.metadata} for item in self._long_term_memory.values()]

        query_tokens = [t.lower() for t in query.split() if len(t) > 2]
        for key, item in self._long_term_memory.items():
            key_lower = key.lower()
            content_lower = str(item.content).lower()
            if any(token in key_lower or token in content_lower for token in query_tokens):
                results.append({"key": item.key, "content": item.content, "metadata": item.metadata})
        return results

    def format_context_prompt(self, session_id: str, current_prompt: str) -> str:
        """
        Builds a contextually enriched prompt combining session history, current state,
        and relevant long-term memory.
        """
        session = self.get_or_create_session(session_id)
        history_snippet = ""
        recent = session.get_recent_history(limit=4)
        if recent:
            history_lines = [f"{msg['role'].upper()}: {msg['content']}" for msg in recent]
            history_snippet = "\n".join(history_lines)

        memory_results = self.recall_long_term_memory(current_prompt)
        memory_snippet = ""
        if memory_results:
            memory_snippet = "Relevant Long-Term Memory:\n" + "\n".join(
                [f"- {m['key']}: {m['content']}" for m in memory_results]
            )

        context_blocks = []
        if history_snippet:
            context_blocks.append(f"Recent Conversation History:\n{history_snippet}")
        if memory_snippet:
            context_blocks.append(memory_snippet)
        if session.state:
            context_blocks.append(f"Current Session State Variables: {json.dumps(session.state)}")

        if context_blocks:
            prefix = "\n---\n".join(context_blocks)
            return f"Context:\n{prefix}\n\nCurrent User Request:\n{current_prompt}"
        
        return current_prompt


# Global Memory Singleton
memory_manager = MemoryManager()
