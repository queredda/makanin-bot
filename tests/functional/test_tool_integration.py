import unittest
from unittest.mock import Mock, patch, AsyncMock
import asyncio
import sys
import os

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agent.tools import ToolRegistry, ToolExecutor, ToolInput


class TestToolIntegration(unittest.TestCase):
    """Functional tests for tool integration"""

    def setUp(self):
        """Set up test fixtures"""
        self.patches = [
            patch('google.generativeai.config'),
            patch('google.generativeai.GenerativeModel')
        ]

        for p in self.patches:
            p.start()

        # Import tools to register them
        import tools.nlu_tool
        import tools.conversation_tool
        import tools.place_extraction_tool

        self.registry = ToolRegistry()
        self.executor = ToolExecutor(self.registry)

    def tearDown(self):
        """Clean up test fixtures"""
        for p in self.patches:
            p.stop()

    def test_nlu_tool_integration(self):
        """Test NLU tool integration"""
        from tools.nlu_tool import NLUTool

        # Mock Gemini response
        with patch('tools.nlu_tool.genai.GenerativeModel') as mock_model:
            mock_response = Mock()
            mock_response.text = '{"intent": "find_food", "keywords": ["bakso"], "location": "Jogja", "constraints": {}, "language": "id"}'
            mock_model_instance = Mock()
            mock_model_instance.generate_content.return_value = mock_response
            mock_model.return_value = mock_model_instance

            # Register and execute tool
            nlu_tool = NLUTool(api_key="test_key")
            self.registry.register(nlu_tool)

            input_data = ToolInput(parameters={"text": "cari bakso di jogja"})
            result = self.executor.execute_tool("nlu", input_data)

            self.assertTrue(result.success)
            self.assertEqual(result.data["intent"], "find_food")
            self.assertEqual(result.data["keywords"], ["bakso"])
            self.assertEqual(result.data["location"], "Jogja")

    def test_conversation_tool_integration(self):
        """Test conversation tool integration"""
        from tools.conversation_tool import ConversationTool

        # Mock Gemini response
        with patch('tools.conversation_tool.genai.GenerativeModel') as mock_model:
            mock_response = Mock()
            mock_response.text = "Halo! Ada yang bisa saya bantu hari ini?"
            mock_model_instance = Mock()
            mock_model_instance.generate_content.return_value = mock_response
            mock_model.return_value = mock_model_instance

            # Register and execute tool
            conversation_tool = ConversationTool(api_key="test_key")
            self.registry.register(conversation_tool)

            input_data = ToolInput(parameters={
                "user_message": "halo",
                "conversation_history": [],
                "language": "id"
            })
            result = self.executor.execute_tool("conversation", input_data)

            self.assertTrue(result.success)
            self.assertIn("response", result.data)
            self.assertEqual(result.data["response"], "Halo! Ada yang bisa saya bantu hari ini?")

    def test_place_extraction_tool_integration(self):
        """Test place extraction tool integration"""
        from tools.place_extraction_tool import PlaceExtractionTool

        # Mock Gemini response
        with patch('tools.place_extraction_tool.genai.GenerativeModel') as mock_model:
            mock_response = Mock()
            mock_response.text = '{"place_name": "Bakso Pak Joko", "confidence": 0.9}'
            mock_model_instance = Mock()
            mock_model_instance.generate_content.return_value = mock_response
            mock_model.return_value = mock_model_instance

            # Register and execute tool
            place_tool = PlaceExtractionTool(api_key="test_key")
            self.registry.register(place_tool)

            input_data = ToolInput(parameters={
                "tiktok_description": "Bakso enak di Bakso Pak Joko",
                "keywords": ["bakso"],
                "hashtags": ["baksoenak"]
            })
            result = self.executor.execute_tool("place_extraction", input_data)

            self.assertTrue(result.success)
            self.assertEqual(result.data["place_name"], "Bakso Pak Joko")
            self.assertEqual(result.data["confidence"], 0.9)

    def test_multiple_tool_execution_sequence(self):
        """Test executing multiple tools in sequence"""
        from tools.nlu_tool import NLUTool
        from tools.conversation_tool import ConversationTool

        # Mock Gemini responses
        with patch('tools.nlu_tool.genai.GenerativeModel') as mock_nlu_model, \
                patch('tools.conversation_tool.genai.GenerativeModel') as mock_conv_model:
            # Mock NLU response
            nlu_response = Mock()
            nlu_response.text = '{"intent": "chat", "keywords": [], "location": null, "constraints": {}, "language": "id"}'
            mock_nlu_instance = Mock()
            mock_nlu_instance.generate_content.return_value = nlu_response
            mock_nlu_model.return_value = mock_nlu_instance

            # Mock conversation response
            conv_response = Mock()
            conv_response.text = "Hai! Apa kabar?"
            mock_conv_instance = Mock()
            mock_conv_instance.generate_content.return_value = conv_response
            mock_conv_model.return_value = mock_conv_instance

            # Register tools
            nlu_tool = NLUTool(api_key="test_key")
            conversation_tool = ConversationTool(api_key="test_key")
            self.registry.register(nlu_tool)
            self.registry.register(conversation_tool)

            # Execute NLU first
            nlu_input = ToolInput(parameters={"text": "apa kabar?"})
            nlu_result = self.executor.execute_tool("nlu", nlu_input)

            self.assertTrue(nlu_result.success)

            # Execute conversation with NLU result
            conv_input = ToolInput(parameters={
                "user_message": "apa kabar?",
                "conversation_history": [],
                "language": nlu_result.data["language"]
            })
            conv_result = self.executor.execute_tool("conversation", conv_input)

            self.assertTrue(conv_result.success)
            self.assertEqual(conv_result.data["response"], "Hai! Apa kabar?")

    def test_tool_execution_history_tracking(self):
        """Test that tool execution history is properly tracked"""
        from tools.nlu_tool import NLUTool

        # Mock Gemini response
        with patch('tools.nlu_tool.genai.GenerativeModel') as mock_model:
            mock_response = Mock()
            mock_response.text = '{"intent": "chat", "keywords": [], "location": null, "constraints": {}, "language": "id"}'
            mock_model_instance = Mock()
            mock_model_instance.generate_content.return_value = mock_response
            mock_model.return_value = mock_model_instance

            # Register tool
            nlu_tool = NLUTool(api_key="test_key")
            self.registry.register(nlu_tool)

            # Execute tool multiple times
            for i in range(3):
                input_data = ToolInput(parameters={"text": f"test message {i}"})
                self.executor.execute_tool("nlu", input_data)

            # Check history
            history = self.executor.get_execution_history()
            self.assertEqual(len(history), 3)

            # Check all executions were successful
            for execution in history:
                self.assertTrue(execution.success)
                self.assertEqual(execution.tool_name, "nlu")

    def test_tool_registry_integration(self):
        """Test tool registry integration with multiple tools"""
        from tools.nlu_tool import NLUTool
        from tools.conversation_tool import ConversationTool

        # Create tools
        nlu_tool = NLUTool(api_key="test_key")
        conversation_tool = ConversationTool(api_key="test_key")

        # Register tools
        self.registry.register(nlu_tool)
        self.registry.register(conversation_tool)

        # Test tool definitions
        definitions = self.registry.get_tool_definitions()
        self.assertIn("nlu", definitions)
        self.assertIn("conversation", definitions)

        # Test tool listing
        tools = self.registry.list_tools()
        self.assertIn("nlu", tools)
        self.assertIn("conversation", tools)

    def test_tool_validation_integration(self):
        """Test tool validation integration"""
        from tools.nlu_tool import NLUTool

        # Mock Gemini (for tool creation)
        with patch('tools.nlu_tool.genai.GenerativeModel'):
            nlu_tool = NLUTool(api_key="test_key")
            self.registry.register(nlu_tool)

        # Test valid input
        valid_input = ToolInput(parameters={"text": "test message"})
        validation_result = nlu_tool.validate_input(valid_input)
        self.assertTrue(validation_result)

        # Test invalid input
        invalid_input = ToolInput(parameters={})  # Missing required "text"
        validation_result = nlu_tool.validate_input(invalid_input)
        self.assertFalse(validation_result)

        # Test execution with invalid input
        result = self.executor.execute_tool("nlu", invalid_input)
        self.assertFalse(result.success)
        self.assertIn("validation", result.error.lower())

    def test_error_handling_integration(self):
        """Test error handling across tools"""
        from tools.nlu_tool import NLUTool

        # Mock model that raises exception
        with patch('tools.nlu_tool.genai.GenerativeModel') as mock_model:
            mock_model_instance = Mock()
            mock_model_instance.generate_content.side_effect = Exception("API Error")
            mock_model.return_value = mock_model_instance

            # Register tool
            nlu_tool = NLUTool(api_key="test_key")
            self.registry.register(nlu_tool)

            # Execute with error
            input_data = ToolInput(parameters={"text": "test message"})
            result = self.executor.execute_tool("nlu", input_data)

            # Should handle error gracefully
            self.assertFalse(result.success)
            self.assertIn("error", result.__dict__.keys())


if __name__ == '__main__':
    unittest.main()
