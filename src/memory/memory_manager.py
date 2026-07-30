"""
Context & Memory Management for Google ADK Agent.
Provides persistent SQLite session state storage, semantic vector memory recall,
robust context compaction, and non-blocking asynchronous execution.
"""

from typing import Dict, List, Any, Optional
import json
import time
import os
import asyncio
from src.compat import BaseModel, Field

from src.memory.persistent_store import SQLiteSessionStore, PersistentSessionRecord
from src.memory.vector_store import SemanticVectorMemoryStore
from src.memory.context_compactor import context_compactor
from src.observability.pii_redactor import pii_redactor
from src.observability.logger import logger


class MemoryItem(BaseModel):
    key: str
    content: Any
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)


class SessionState(BaseModel):
    session_id: str
    user_id: str = "default_user"
    history: List[Dict[str, Any]] = Field(default_factory=list)
    state: Dict[str, Any] = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)

    def add_message(self, role: str, content: str):
        # Automatically redact PII before adding to session state
        clean_content = pii_redactor.redact_text(content)
        self.history.append({
            "role": role,
            "content": clean_content,
            "timestamp": time.time()
        })
        self.updated_at = time.time()

    def get_recent_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self.history[-limit:]


class MemoryManager:
    """
    Production-grade Memory Manager for ADK Multi-Agent System.
    Integrates persistent SQLite storage, semantic vector retrieval,
    and ADK context compaction.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.getenv("SESSION_DB_PATH", "data/sessions.db")
        self.store = SQLiteSessionStore(db_path=self.db_path)
        self.vector_store = SemanticVectorMemoryStore()
        self.compactor = context_compactor
        self._cache: Dict[str, SessionState] = {}
        self._init_warmup()

    def _init_warmup(self):
        """Loads persistent memories from SQLite into vector index on startup."""
        try:
            stored_memories = self.store.get_all_long_term_memories()
            for mem in stored_memories:
                self.vector_store.add_document(
                    key=mem["key"],
                    content=str(mem["content"]),
                    metadata=mem["metadata"]
                )
        except Exception as e:
            logger.warning(f"Memory warmup notice: {e}")

    # --- Synchronous Session Operations ---

    def get_or_create_session(self, session_id: str, user_id: str = "default_user") -> SessionState:
        """Retrieves session from cache or SQLite persistent store, or initializes new."""
        if session_id in self._cache:
            return self._cache[session_id]

        record = self.store.load_session(session_id)
        if record:
            session = SessionState(
                session_id=record.session_id,
                user_id=record.user_id,
                history=record.history,
                state=record.state,
                created_at=record.created_at,
                updated_at=record.updated_at
            )
        else:
            session = SessionState(session_id=session_id, user_id=user_id)
            self._persist_session(session)

        self._cache[session_id] = session
        return session

    def _persist_session(self, session: SessionState):
        record = PersistentSessionRecord(
            session_id=session.session_id,
            user_id=session.user_id,
            state=session.state,
            history=session.history,
            created_at=session.created_at,
            updated_at=session.updated_at
        )
        self.store.save_session(record)

    def update_session_state(self, session_id: str, key: str, value: Any):
        """Updates a state key inside persistent session context."""
        session = self.get_or_create_session(session_id)
        session.state[key] = pii_redactor.redact_object(value)
        session.updated_at = time.time()
        self._persist_session(session)

    def add_session_message(self, session_id: str, role: str, content: str):
        """Appends a message to session and persists to SQLite."""
        session = self.get_or_create_session(session_id)
        session.add_message(role, content)
        self._persist_session(session)

    def store_long_term_memory(self, key: str, content: Any, metadata: Optional[Dict[str, Any]] = None):
        """Stores a factual item into both persistent SQLite and the semantic vector store."""
        clean_content = pii_redactor.redact_object(content)
        meta = metadata or {}
        # 1. Save to SQLite
        self.store.save_long_term_memory(key=key, content=clean_content, metadata=meta)
        # 2. Index into Vector Store for semantic similarity search
        self.vector_store.add_document(key=key, content=str(clean_content), metadata=meta)

    def recall_long_term_memory(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Recalls items from memory using semantic vector similarity ranking.
        Falls back to keyword matching if vector store returns no matches.
        """
        if not query.strip():
            return self.store.get_all_long_term_memories()[:top_k]

        # 1. Vector Search
        vector_results = self.vector_store.search_similar(query=query, top_k=top_k, similarity_threshold=0.10)
        if vector_results:
            return vector_results

        # 2. Keyword Fallback
        all_memories = self.store.get_all_long_term_memories()
        query_tokens = [t.lower() for t in query.split() if len(t) > 2]
        matched = []
        for item in all_memories:
            key_lower = item["key"].lower()
            content_lower = str(item["content"]).lower()
            if any(tok in key_lower or tok in content_lower for tok in query_tokens):
                matched.append(item)
        return matched[:top_k]

    def format_context_prompt(self, session_id: str, current_prompt: str) -> str:
        """
        Builds a contextually enriched prompt using ADK Context Compaction
        and semantic vector memory retrieval.
        """
        session = self.get_or_create_session(session_id)

        # 1. Robust Context Compaction on History
        compacted_history, comp_metrics = self.compactor.compact_history(
            history=session.history,
            current_query=current_prompt
        )

        # 2. Semantic Vector Memory Recall
        memory_results = self.recall_long_term_memory(current_prompt, top_k=3)
        memory_snippet = ""
        if memory_results:
            memory_snippet = "Relevant Long-Term Memories (Vector Search):\n" + "\n".join(
                [f"- [{m.get('key')}]: {m.get('content')}" for m in memory_results]
            )

        context_blocks = []
        if compacted_history:
            context_blocks.append(f"Conversation Context:\n{compacted_history}")
        if memory_snippet:
            context_blocks.append(memory_snippet)
        if session.state:
            context_blocks.append(f"Session State Variables: {json.dumps(session.state)}")

        if context_blocks:
            prefix = "\n---\n".join(context_blocks)
            return f"Context:\n{prefix}\n\nCurrent User Request:\n{current_prompt}"

        return current_prompt

    # --- Asynchronous Non-Blocking Operations ---

    async def get_or_create_session_async(self, session_id: str, user_id: str = "default_user") -> SessionState:
        return await asyncio.to_thread(self.get_or_create_session, session_id, user_id)

    async def add_session_message_async(self, session_id: str, role: str, content: str):
        session = await self.get_or_create_session_async(session_id)
        session.add_message(role, content)
        await asyncio.to_thread(self._persist_session, session)

    async def store_long_term_memory_async(self, key: str, content: Any, metadata: Optional[Dict[str, Any]] = None):
        await asyncio.to_thread(self.store_long_term_memory, key, content, metadata)

    async def recall_long_term_memory_async(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        return await asyncio.to_thread(self.recall_long_term_memory, query, top_k)

    async def format_context_prompt_async(self, session_id: str, current_prompt: str) -> str:
        return await asyncio.to_thread(self.format_context_prompt, session_id, current_prompt)


# Global Memory Singleton with persistent storage
memory_manager = MemoryManager()
