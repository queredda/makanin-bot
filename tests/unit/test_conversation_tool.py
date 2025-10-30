import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tools.conversation_tool import ConversationTool
from agent.tools import ToolInput


class TestConversationTool(unittest.TestCase):
    """Unit tests for ConversationTool"""

    def setUp(self):
        """Set up test fixtures"""
        with patch('google.generativeai.config'):
            with patch('google.generativeai.GenerativeModel'):
                self.conversation_tool = ConversationTool(api_key="test_key")

    def test_validate_input_valid(self):
        """Test input validation with valid data"""
        valid_inputs = [
            {
                "user_message": "hello",
                "conversation_history": [],
                "language": "id"
            },
            {
                "user_message": "how are you?",
                "conversation_history": [{"role": "user", "content": "hi"}],
                "language": "en"
            }
        ]

        for params in valid_inputs:
            with self.subTest(params=params):
                input_data = ToolInput(parameters=params)
                self.assertTrue(self.conversation_tool.validate_input(input_data))

    def test_validate_input_invalid(self):
        """Test input validation with invalid data"""
        invalid_inputs = [
            {},  # Empty params
            {"user_message": "", "conversation_history": [], "language": "id"},  # Empty message
            {"user_message": "hello", "conversation_history": "not_list", "language": "id"},  # Invalid history
            {"user_message": "hello", "conversation_history": [], "language": "invalid"}  # Invalid language
        ]

        for params in invalid_inputs:
            with self.subTest(params=params):
                input_data = ToolInput(parameters=params)
                self.assertFalse(self.conversation_tool.validate_input(input_data))

    def test_get_schema(self):
        """Test tool schema generation"""
        schema = self.conversation_tool.get_schema()

        self.assertIn("type", schema)
        self.assertIn("properties", schema)
        self.assertIn("required", schema)
        self.assertIn("user_message", schema["properties"])
        self.assertIn("conversation_history", schema["properties"])
        self.assertIn("language", schema["properties"])

    @patch('tools.conversation_tool.genai.GenerativeModel')
    def test_execute_success(self, mock_model):
        """Test successful conversation execution"""
        # Mock Gemini response
        mock_response = Mock()
        mock_response.text = "Hello! How can I help you today?"
        mock_model_instance = Mock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_model_instance

        # Recreate tool with mocked model
        conversation_tool = ConversationTool(api_key="test_key")

        input_data = ToolInput(parameters={
            "user_message": "hello",
            "conversation_history": [],
            "language": "en"
        })

        result = conversation_tool.execute(input_data)

        self.assertTrue(result.success)
        self.assertIn("response", result.data)
        self.assertEqual(result.data["response"], "Hello! How can I help you today?")

    @patch('tools.conversation_tool.genai.GenerativeModel')
    def test_execute_with_history(self, mock_model):
        """Test conversation execution with history"""
        # Mock Gemini response
        mock_response = Mock()
        mock_response.text = "I'm doing well, thanks for asking!"
        mock_model_instance = Mock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_model_instance

        conversation_tool = ConversationTool(api_key="test_key")

        history = [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello!"}
        ]

        input_data = ToolInput(parameters={
            "user_message": "how are you?",
            "conversation_history": history,
            "language": "en"
        })

        result = conversation_tool.execute(input_data)

        self.assertTrue(result.success)
        self.assertIn("response", result.data)

    def test_execute_api_error(self):
        """Test conversation execution with API error"""
        # Mock model that raises exception
        with patch('google.generativeai.GenerativeModel') as mock_model:
            mock_model_instance = Mock()
            mock_model_instance.generate_content.side_effect = Exception("API Error")
            mock_model.return_value = mock_model_instance

            conversation_tool = ConversationTool(api_key="test_key")

            input_data = ToolInput(parameters={
                "user_message": "hello",
                "conversation_history": [],
                "language": "en"
            })

            result = conversation_tool.execute(input_data)

            self.assertFalse(result.success)
            self.assertIn("error", result.__dict__.keys())


if __name__ == '__main__':
    unittest.main()
