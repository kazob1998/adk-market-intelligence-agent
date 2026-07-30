"""
Persistent Storage Engine for Google ADK Agent.
Provides production-grade SQLite session state and memory persistence with both
synchronous and non-blocking asynchronous execution.
"""

import sqlite3
import json
import time
import os
import asyncio
from typing import Dict, List, Any, Optional
from src.compat import BaseModel, Field


class PersistentSessionRecord(BaseModel):
    session_id: str
    user_id: str = "default_user"
    state: Dict[str, Any] = Field(default_factory=dict)
    history: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)


class SQLiteSessionStore:
    """
    SQLite persistent storage backend for ADK session states, messages, and long-term memory.
    Supports file-backed databases and in-memory test databases.
    """

    def __init__(self, db_path: str = "data/sessions.db"):
        self.db_path = db_path
        if db_path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        else:
            self._conn = sqlite3.connect(":memory:", check_same_thread=False)
            
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        cursor = self._conn.cursor()
        if self.db_path != ":memory:":
            cursor.execute("PRAGMA journal_mode=WAL;")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                state_json TEXT NOT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp REAL NOT NULL,
                FOREIGN KEY(session_id) REFERENCES sessions(session_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS long_term_memory (
                key TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                created_at REAL NOT NULL
            )
        """)
        self._conn.commit()

    # --- Synchronous CRUD Operations ---

    def save_session(self, session: PersistentSessionRecord):
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT INTO sessions (session_id, user_id, state_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                state_json=excluded.state_json,
                updated_at=excluded.updated_at
            """,
            (
                session.session_id,
                session.user_id,
                json.dumps(session.state),
                session.created_at,
                session.updated_at
            )
        )
        cursor.execute("DELETE FROM messages WHERE session_id = ?", (session.session_id,))
        for msg in session.history:
            cursor.execute(
                "INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (
                    session.session_id,
                    msg.get("role", "user"),
                    msg.get("content", ""),
                    float(msg.get("timestamp", time.time()))
                )
            )
        self._conn.commit()

    def load_session(self, session_id: str) -> Optional[PersistentSessionRecord]:
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        if not row:
            return None

        cursor.execute("SELECT role, content, timestamp FROM messages WHERE session_id = ? ORDER BY id ASC", (session_id,))
        msg_rows = cursor.fetchall()
        history = [{"role": m["role"], "content": m["content"], "timestamp": m["timestamp"]} for m in msg_rows]

        return PersistentSessionRecord(
            session_id=row["session_id"],
            user_id=row["user_id"],
            state=json.loads(row["state_json"]),
            history=history,
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    def save_long_term_memory(self, key: str, content: Any, metadata: Optional[Dict[str, Any]] = None):
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT INTO long_term_memory (key, content, metadata_json, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                content=excluded.content,
                metadata_json=excluded.metadata_json,
                created_at=excluded.created_at
            """,
            (
                key,
                json.dumps(content) if not isinstance(content, str) else content,
                json.dumps(metadata or {}),
                time.time()
            )
        )
        self._conn.commit()

    def get_all_long_term_memories(self) -> List[Dict[str, Any]]:
        cursor = self._conn.cursor()
        cursor.execute("SELECT key, content, metadata_json, created_at FROM long_term_memory ORDER BY created_at DESC")
        rows = cursor.fetchall()
        results = []
        for r in rows:
            content_raw = r["content"]
            try:
                content_val = json.loads(content_raw)
            except Exception:
                content_val = content_raw
            results.append({
                "key": r["key"],
                "content": content_val,
                "metadata": json.loads(r["metadata_json"]),
                "created_at": r["created_at"]
            })
        return results

    # --- Asynchronous Non-Blocking Operations ---

    async def save_session_async(self, session: PersistentSessionRecord):
        await asyncio.to_thread(self.save_session, session)

    async def load_session_async(self, session_id: str) -> Optional[PersistentSessionRecord]:
        return await asyncio.to_thread(self.load_session, session_id)

    async def save_long_term_memory_async(self, key: str, content: Any, metadata: Optional[Dict[str, Any]] = None):
        await asyncio.to_thread(self.save_long_term_memory, key, content, metadata)

    async def get_all_long_term_memories_async(self) -> List[Dict[str, Any]]:
        return await asyncio.to_thread(self.get_all_long_term_memories)
