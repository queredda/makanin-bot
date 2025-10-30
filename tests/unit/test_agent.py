import unittest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os
import asyncio

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agent.agent import MakaninAgent


class TestMakaninAgent(unittest.TestCase):
    """Unit tests for MakaninAgent"""

    def setUp(self):
        """Set up test fixtures"""
        with patch('google.generativeai.config'):
            with patch('google.generativeai.GenerativeModel'):
                self.agent = MakaninAgent()

    def test_agent_initialization(self):
        """Test agent initialization"""
        self.assertIsNotNone(self.agent.tool_registry)
        self.assertIsNotNone(self.agent.tool_executor)
        self.assertIsNotNone(self.agent.context_manager)
        self.assertIsNotNone(self.agent.reasoning_model)

    def test_handle_error_indonesian(self):
        """Test error handling in Indonesian"""
        error_message = self.agent._handle_error("Test Error", "Something went wrong", "id")
        self.assertIn("maaf", error_message.lower())
        self.assertIn("kesalahan", error_message.lower())

    def test_handle_error_english(self):
        """Test error handling in English"""
        error_message = self.agent._handle_error("Test Error", "Something went wrong", "en")
        self.assertIn("oops", error_message.lower())
        self.assertIn("wrong", error_message.lower())

    def test_get_used_tools(self):
        """Test getting list of used tools"""
        # Mock execution history
        self.agent.tool_executor.get_execution_history = Mock(return_value=[
            Mock(tool_name="nlu"),
            Mock(tool_name="tiktok_search")
        ])

        used_tools = self.agent._get_used_tools()
        self.assertEqual(used_tools, ["nlu", "tiktok_search"])

    def test_get_tool_status(self):
        """Test getting tool status"""
        # Mock components
        self.agent.tool_registry.list_tools = Mock(return_value=["nlu", "tiktok_search"])
        self.agent.tool_executor.get_execution_history = Mock(return_value=[Mock(), Mock()])
        self.agent.context_manager.memory.sessions = {"user1": {}, "user2": {}}

        status = self.agent.get_tool_status()

        self.assertIn("available_tools", status)
        self.assertIn("recent_executions", status)
        self.assertIn("active_sessions", status)
        self.assertEqual(status["available_tools"], ["nlu", "tiktok_search"])
        self.assertEqual(status["recent_executions"], 2)
        self.assertEqual(status["active_sessions"], 2)

    @patch('agent.agent.genai.GenerativeModel')
    def test_create_tool_plan_success(self, mock_model):
        """Test successful tool plan creation"""
        # Mock Gemini response
        mock_response = Mock()
        mock_response.text = '{"reasoning": "Test reasoning", "tool_plan": [], "expected_outcome": "Test outcome"}'
        mock_model_instance = Mock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_model_instance

        # Recreate agent with mocked model
        with patch('google.generativeai.config'):
            agent = MakaninAgent()

        plan = asyncio.run(agent.create_tool_plan("find bakso in jogja", "user123"))

        self.assertIn("reasoning", plan)
        self.assertIn("tool_plan", plan)
        self.assertIn("expected_outcome", plan)

    @patch('agent.agent.genai.GenerativeModel')
    def test_create_tool_plan_fallback(self, mock_model):
        """Test tool plan creation with fallback on error"""
        # Mock model that raises exception
        mock_model_instance = Mock()
        mock_model_instance.generate_content.side_effect = Exception("API Error")
        mock_model.return_value = mock_model_instance

        with patch('google.generativeai.config'):
            agent = MakaninAgent()

        plan = asyncio.run(agent.create_tool_plan("test message", "user123"))

        # Should return fallback plan
        self.assertIn("reasoning", plan)
        self.assertIn("tool_plan", plan)
        self.assertIn("expected_outcome", plan)
        self.assertIn("Failed to generate plan", plan["reasoning"])

    def test_register_tools(self):
        """Test tool registration"""
        # Test that _register_tools doesn't raise exceptions
        try:
            self.agent._register_tools()
        except Exception as e:
            self.fail(f"_register_tools raised {e} unexpectedly!")


if __name__ == '__main__':
    unittest.main()
