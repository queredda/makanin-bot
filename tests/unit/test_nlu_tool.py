import unittest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tools.nlu_tool import NLUTool
from agent.tools import ToolInput


class TestNLUTool(unittest.TestCase):
    """Unit tests for NLU Tool"""

    def setUp(self):
        """Set up test fixtures"""
        with patch('google.generativeai.config'):
            with patch('google.generativeai.GenerativeModel'):
                self.nlu_tool = NLUTool(api_key="test_key")

    def test_detect_language_indonesian(self):
        """Test language detection for Indonesian text"""
        indonesian_texts = [
            "cariin bakso dong",
            "makanan halal di dekat sini",
            "restoran murah di jogja"
        ]

        for text in indonesian_texts:
            with self.subTest(text=text):
                language = self.nlu_tool._detect_language(text)
                self.assertEqual(language, "id")

    def test_detect_language_english(self):
        """Test language detection for English text"""
        english_texts = [
            "find food near me",
            "cheap restaurant please",
            "looking for coffee"
        ]

        for text in english_texts:
            with self.subTest(text=text):
                language = self.nlu_tool._detect_language(text)
                self.assertEqual(language, "en")

    def test_validate_input_valid(self):
        """Test input validation with valid data"""
        valid_inputs = [
            {"text": "cari bakso"},
            {"text": "find restaurant"},
            {"text": "  test text  "}
        ]

        for params in valid_inputs:
            with self.subTest(params=params):
                input_data = ToolInput(parameters=params)
                self.assertTrue(self.nlu_tool.validate_input(input_data))

    def test_validate_input_invalid(self):
        """Test input validation with invalid data"""
        invalid_inputs = [
            {"text": ""},
            {"text": "   "},
            {"text": None},
            {},
            {"text": 123}
        ]

        for params in invalid_inputs:
            with self.subTest(params=params):
                input_data = ToolInput(parameters=params)
                self.assertFalse(self.nlu_tool.validate_input(input_data))

    @patch('tools.nlu_tool.genai.GenerativeModel')
    def test_parse_with_gemini_success(self, mock_model):
        """Test successful parsing with Gemini"""
        # Mock Gemini response
        mock_response = Mock()
        mock_response.text = '{"intent": "find_food", "keywords": ["bakso"], "location": "Jogja", "constraints": {}, "language": "id"}'
        mock_model_instance = Mock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_model_instance

        # Recreate tool with mocked model
        nlu_tool = NLUTool(api_key="test_key")

        result = nlu_tool._parse_with_gemini("cari bakso di jogja", "id")

        self.assertEqual(result["intent"], "find_food")
        self.assertEqual(result["keywords"], ["bakso"])
        self.assertEqual(result["location"], "Jogja")
        self.assertEqual(result["language"], "id")

    def test_parse_with_gemini_fallback(self):
        """Test fallback parsing when Gemini fails"""
        # Mock model that raises exception
        with patch('google.generativeai.GenerativeModel') as mock_model:
            mock_model_instance = Mock()
            mock_model_instance.generate_content.side_effect = Exception("API Error")
            mock_model.return_value = mock_model_instance

            nlu_tool = NLUTool(api_key="test_key")

            result = nlu_tool._parse_with_gemini("test text", "id")

            # Should return fallback values
            self.assertEqual(result["intent"], "chat")
            self.assertEqual(result["keywords"], [])
            self.assertEqual(result["location"], None)
            self.assertEqual(result["language"], "id")

    def test_get_schema(self):
        """Test tool schema generation"""
        schema = self.nlu_tool.get_schema()

        self.assertIn("type", schema)
        self.assertIn("properties", schema)
        self.assertIn("required", schema)
        self.assertEqual(schema["required"], ["text"])
        self.assertIn("text", schema["properties"])


if __name__ == '__main__':
    unittest.main()
