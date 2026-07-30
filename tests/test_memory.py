"""
Unit tests for session state, SQLite persistent store, vector search, and memory management.
"""

import unittest
import asyncio
from src.memory.memory_manager import MemoryManager
from src.memory.vector_store import SemanticVectorMemoryStore
from src.memory.context_compactor import ContextCompactor


class TestMemory(unittest.TestCase):

    def setUp(self):
        self.mgr = MemoryManager(db_path=":memory:")

    def test_session_state(self):
        session = self.mgr.get_or_create_session(session_id="test_s1", user_id="user_123")
        session.add_message("user", "Hello agent")
        session.add_message("assistant", "Hello! How can I help?")

        self.assertEqual(len(session.history), 2)
        self.assertEqual(session.user_id, "user_123")

    def test_long_term_memory_recall(self):
        self.mgr.store_long_term_memory("googl_earnings_q3", "Revenue grew 15% YoY with AI expansion")

        recalled = self.mgr.recall_long_term_memory("googl")
        self.assertGreaterEqual(len(recalled), 1)
        self.assertEqual(recalled[0]["key"], "googl_earnings_q3")

    def test_vector_memory_store_similarity(self):
        vstore = SemanticVectorMemoryStore()
        vstore.add_document("doc1", "Alphabet Cloud revenue accelerated by Gemini Enterprise API")
        vstore.add_document("doc2", "Semiconductor manufacturing equipment export restrictions")

        results = vstore.search_similar("Gemini Enterprise Cloud", top_k=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["key"], "doc1")
        self.assertGreater(results[0]["similarity_score"], 0.1)

    def test_context_compactor(self):
        compactor = ContextCompactor(token_threshold=50, keep_recent_turns=2)
        long_history = [
            {"role": "user", "content": f"Turn {i}: Detailed market inquiry regarding financial liquidity"}
            for i in range(10)
        ]
        compacted, metrics = compactor.compact_history(long_history, "Latest query")
        self.assertTrue(metrics["compacted"])
        self.assertIn("ADK COMPACTED CONTEXT SUMMARY", compacted)

    def test_pii_redaction_in_memory(self):
        session = self.mgr.get_or_create_session("pii_session")
        session.add_message("user", "My email is secret_investor@firm.com and phone is +1-555-839-2019")
        clean_content = session.history[-1]["content"]
        self.assertNotIn("secret_investor@firm.com", clean_content)
        self.assertIn("[EMAIL_REDACTED]", clean_content)
        self.assertIn("[PHONE_REDACTED]", clean_content)

    def test_format_context_prompt(self):
        self.mgr.store_long_term_memory("nvda_guidance", "NVIDIA projected $30B data center revenue")
        session = self.mgr.get_or_create_session("s_nvda")
        session.add_message("user", "What is NVDA outlook?")

        enriched = self.mgr.format_context_prompt("s_nvda", "Give me NVDA analysis")
        self.assertIn("NVDA", enriched)
        self.assertIn("NVIDIA", enriched)

    def test_async_memory_operations(self):
        async def run_async_test():
            session = await self.mgr.get_or_create_session_async("async_sess")
            await self.mgr.add_session_message_async("async_sess", "user", "Async message content")
            await self.mgr.store_long_term_memory_async("async_key", "Async memory value")
            results = await self.mgr.recall_long_term_memory_async("Async")
            return session, results

        session, results = asyncio.run(run_async_test())
        self.assertEqual(session.session_id, "async_sess")
        self.assertGreaterEqual(len(results), 1)


if __name__ == "__main__":
    unittest.main()
