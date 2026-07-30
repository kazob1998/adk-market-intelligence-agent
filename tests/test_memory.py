"""
Unit tests for session state and memory management.
"""

import unittest
from src.memory.memory_manager import MemoryManager


class TestMemory(unittest.TestCase):

    def test_session_state(self):
        mgr = MemoryManager()
        session = mgr.get_or_create_session(session_id="test_s1", user_id="user_123")
        session.add_message("user", "Hello agent")
        session.add_message("assistant", "Hello! How can I help?")

        self.assertEqual(len(session.history), 2)
        self.assertEqual(session.user_id, "user_123")

    def test_long_term_memory_recall(self):
        mgr = MemoryManager()
        mgr.store_long_term_memory("googl_earnings_q3", "Revenue grew 15% YoY with AI expansion")

        recalled = mgr.recall_long_term_memory("googl")
        self.assertEqual(len(recalled), 1)
        self.assertEqual(recalled[0]["key"], "googl_earnings_q3")

    def test_format_context_prompt(self):
        mgr = MemoryManager()
        mgr.store_long_term_memory("nvda_guidance", "NVIDIA projected $30B data center revenue")
        session = mgr.get_or_create_session("s_nvda")
        session.add_message("user", "What is NVDA outlook?")

        enriched = mgr.format_context_prompt("s_nvda", "Give me NVDA analysis")
        self.assertIn("NVDA", enriched)
        self.assertIn("NVIDIA", enriched)


if __name__ == "__main__":
    unittest.main()
