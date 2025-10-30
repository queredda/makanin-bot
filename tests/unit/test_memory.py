import unittest
from unittest.mock import Mock, patch
import sys
import os
import time
from datetime import datetime, timedelta

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agent.memory import ContextManager, ConversationMemory


class TestConversationMemory(unittest.TestCase):
    """Unit tests for ConversationMemory"""

    def setUp(self):
        """Set up test fixtures"""
        # Mock Redis to avoid actual Redis dependency
        self.redis_patcher = patch('agent.memory.redis.Redis')
        self.mock_redis = self.redis_patcher.start()
        self.mock_client = Mock()
        self.mock_redis.return_value = self.mock_client

        self.memory = ConversationMemory()

    def tearDown(self):
        """Clean up test fixtures"""
        self.redis_patcher.stop()

    def test_create_session(self):
        """Test creating a new session"""
        session_id = self.memory.create_session("user123")

        self.assertIsNotNone(session_id)
        self.mock_client.hset.assert_called()
        self.mock_client.expire.assert_called()

    def test_get_session(self):
        """Test getting an existing session"""
        # Mock Redis response
        self.mock_client.hgetall.return_value = {
            b"user_id": b"user123",
            b"language": b"id",
            b"created_at": b"2023-01-01T00:00:00"
        }

        session = self.memory.get_session("session123")

        self.assertIsNotNone(session)
        self.assertEqual(session["user_id"], "user123")
        self.assertEqual(session["language"], "id")

    def test_get_session_not_found(self):
        """Test getting a non-existent session"""
        self.mock_client.hgetall.return_value = {}

        session = self.memory.get_session("nonexistent")

        self.assertIsNone(session)

    def test_update_session(self):
        """Test updating a session"""
        update_data = {"language": "en", "last_intent": "find_food"}

        result = self.memory.update_session("session123", update_data)

        self.assertTrue(result)
        self.mock_client.hset.assert_called()

    def test_get_conversation_history(self):
        """Test getting conversation history"""
        # Mock Redis list response
        self.mock_client.lrange.return_value = [
            b'{"role": "user", "content": "hello", "timestamp": "2023-01-01T00:00:00"}',
            b'{"role": "assistant", "content": "hi there!", "timestamp": "2023-01-01T00:00:01"}'
        ]

        history = self.memory.get_conversation_history("user123", 10)

        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["role"], "user")
        self.assertEqual(history[1]["role"], "assistant")

    def test_add_message(self):
        """Test adding a message to conversation history"""
        message = {
            "role": "user",
            "content": "test message",
            "timestamp": datetime.now().isoformat()
        }

        self.memory.add_message("user123", message)
        self.mock_client.lpush.assert_called()
        self.mock_client.ltrim.assert_called()

    def test_get_user_preferences(self):
        """Test getting user preferences"""
        # Mock Redis response
        self.mock_client.hgetall.return_value = {
            b"language": b"id",
            b"location_preference": b"Jakarta",
            b"dietary_restrictions": b"halal"
        }

        preferences = self.memory.get_user_preferences("user123")

        self.assertEqual(preferences["language"], "id")
        self.assertEqual(preferences["location_preference"], "Jakarta")
        self.assertEqual(preferences["dietary_restrictions"], "halal")

    def test_update_user_preferences(self):
        """Test updating user preferences"""
        preferences = {
            "language": "en",
            "location_preference": "Surabaya"
        }

        self.memory.update_user_preferences("user123", preferences)
        self.mock_client.hset.assert_called()

    def test_cleanup_old_sessions(self):
        """Test cleaning up old sessions"""
        # Mock Redis scan response
        self.mock_client.scan_iter.return_value = [b"session1", b"session2", b"session3"]
        # Mock session data
        self.mock_client.hgetall.side_effect = [
            {"created_at": "2023-01-01T00:00:00"},  # Old session
            {"created_at": datetime.now().isoformat()},  # New session
            {}  # Empty session
        ]

        cleaned_count = self.memory.cleanup_old_sessions(days_old=1)

        # Should clean 1 old session
        self.assertEqual(cleaned_count, 1)
        self.mock_client.delete.assert_called()


class TestContextManager(unittest.TestCase):
    """Unit tests for ContextManager"""

    def setUp(self):
        """Set up test fixtures"""
        self.redis_patcher = patch('agent.memory.redis.Redis')
        self.mock_redis = self.redis_patcher.start()
        self.mock_client = Mock()
        self.mock_redis.return_value = self.mock_client

        self.context_manager = ContextManager()

    def tearDown(self):
        """Clean up test fixtures"""
        self.redis_patcher.stop()

    def test_process_user_input(self):
        """Test processing user input"""
        # Mock Redis responses
        self.mock_client.hgetall.return_value = {}  # No existing session
        self.mock_client.hget.return_value = b"session123"  # Existing session ID

        context = self.context_manager.process_user_input("user123", "hello")

        self.assertIsNotNone(context)
        self.assertEqual(context["user_id"], "user123")
        self.assertIn("session_id", context)

    def test_process_assistant_response(self):
        """Test processing assistant response"""
        # Mock session data
        self.mock_client.hgetall.return_value = {
            "session_id": "session123",
            "user_id": "user123"
        }

        self.context_manager.process_assistant_response(
            "user123",
            "Hi there!",
            tools_used=["nlu", "conversation"]
        )

        # Verify message was added
        self.mock_client.lpush.assert_called()

    def test_record_tool_usage(self):
        """Test recording tool usage"""
        self.context_manager.record_tool_usage(
            "user123",
            "nlu",
            {"text": "hello"},
            {"intent": "chat"},
            True,
            0.5
        )

        # Verify tool usage was recorded
        self.mock_client.lpush.assert_called()

    def test_get_tool_usage_history(self):
        """Test getting tool usage history"""
        # Mock Redis response
        self.mock_client.lrange.return_value = [
            b'{"tool_name": "nlu", "success": true, "execution_time": 0.5}',
            b'{"tool_name": "tiktok_search", "success": false, "execution_time": 2.0}'
        ]

        history = self.context_manager.get_tool_usage_history("user123", 10)

        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["tool_name"], "nlu")
        self.assertEqual(history[1]["tool_name"], "tiktok_search")

    def test_update_user_preferences(self):
        """Test updating user preferences through context manager"""
        self.context_manager.update_user_preferences(
            "user123",
            language="en",
            last_intent="find_food"
        )

        # Verify preferences were updated
        self.mock_client.hset.assert_called()

    def test_get_context_summary(self):
        """Test getting context summary"""
        # Mock Redis responses
        self.mock_client.hgetall.return_value = {
            "language": "id",
            "last_intent": "find_food"
        }
        self.mock_client.lrange.return_value = [
            b'{"role": "user", "content": "cari bakso"}',
            b'{"role": "assistant", "content": "Baik, saya akan carikan bakso untuk Anda"}'
        ]

        summary = self.context_manager.get_context_summary("user123")

        self.assertIn("user_id", summary)
        self.assertIn("preferences", summary)
        self.assertIn("recent_messages", summary)
        self.assertEqual(summary["preferences"]["language"], "id")


if __name__ == '__main__':
    unittest.main()
