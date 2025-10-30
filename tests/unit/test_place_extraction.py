import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tools.place_extraction_tool import PlaceExtractionTool
from agent.tools import ToolInput


class TestPlaceExtractionTool(unittest.TestCase):
    """Unit tests for PlaceExtractionTool"""

    def setUp(self):
        """Set up test fixtures"""
        with patch('google.generativeai.config'):
            with patch('google.generativeai.GenerativeModel'):
                self.place_tool = PlaceExtractionTool(api_key="test_key")

    def test_validate_input_valid(self):
        """Test input validation with valid data"""
        valid_inputs = [
            {
                "tiktok_description": "Makan bakso enak di Bakso Pak Joko",
                "keywords": ["bakso"],
                "hashtags": ["baksoenak", "kulinerjogja"]
            },
            {
                "tiktok_description": "Found this amazing ramen place",
                "keywords": ["ramen"],
                "hashtags": []
            }
        ]

        for params in valid_inputs:
            with self.subTest(params=params):
                input_data = ToolInput(parameters=params)
                self.assertTrue(self.place_tool.validate_input(input_data))

    def test_validate_input_invalid(self):
        """Test input validation with invalid data"""
        invalid_inputs = [
            {},  # Empty params
            {"tiktok_description": "", "keywords": ["test"], "hashtags": []},  # Empty description
            {"tiktok_description": "test", "keywords": "not_list", "hashtags": []},  # Invalid keywords
            {"tiktok_description": "test", "keywords": [], "hashtags": "not_list"}  # Invalid hashtags
        ]

        for params in invalid_inputs:
            with self.subTest(params=params):
                input_data = ToolInput(parameters=params)
                self.assertFalse(self.place_tool.validate_input(input_data))

    def test_get_schema(self):
        """Test tool schema generation"""
        schema = self.place_tool.get_schema()

        self.assertIn("type", schema)
        self.assertIn("properties", schema)
        self.assertIn("required", schema)
        self.assertIn("tiktok_description", schema["properties"])
        self.assertIn("keywords", schema["properties"])
        self.assertIn("hashtags", schema["properties"])

    def test_extract_place_name_simple(self):
        """Test simple place name extraction"""
        test_cases = [
            ("Makan di Bakso Pak Joko", ["bakso"], "Bakso Pak Joko"),
            ("Found ramen at Ichiran", ["ramen"], "Ichiran"),
            ("Nasi goreng di warteg favorit", ["nasi goreng"], "warteg favorit")
        ]

        for description, keywords, expected in test_cases:
            with self.subTest(description=description):
                result = self.place_tool._extract_place_name(description, keywords)
                self.assertEqual(result, expected)

    def test_extract_place_name_with_hashtags(self):
        """Test place name extraction with hashtags"""
        description = "Mantap baksonya Bakso Pak Joko"
        keywords = ["bakso"]
        hashtags = ["baksopakjoko", "kulinerjogja"]

        result = self.place_tool._extract_place_name(description, keywords, hashtags)
        self.assertEqual(result, "Bakso Pak Joko")

    def test_extract_place_name_not_found(self):
        """Test place name extraction when not found"""
        description = "Enak sekali makanannya"
        keywords = ["makanan"]
        hashtags = ["enak", "makan"]

        result = self.place_tool._extract_place_name(description, keywords)
        self.assertIsNone(result)

    def test_extract_place_name_with_prefixes(self):
        """Test place name extraction with common prefixes"""
        test_cases = [
            ("Makan di RM Padang Sederhana", ["padang"], "RM Padang Sederhana"),
            ("Ngopi di Kedai Kopi Indonesia", ["kopi"], "Kedai Kopi Indonesia"),
            ("Mampir di Warung Nasi Ampera", ["nasi"], "Warung Nasi Ampera")
        ]

        for description, keywords, expected in test_cases:
            with self.subTest(description=description):
                result = self.place_tool._extract_place_name(description, keywords)
                self.assertEqual(result, expected)

    @patch('tools.place_extraction_tool.genai.GenerativeModel')
    def test_extract_with_gemini_success(self, mock_model):
        """Test place extraction with Gemini AI"""
        # Mock Gemini response
        mock_response = Mock()
        mock_response.text = '{"place_name": "Bakso Pak Joko", "confidence": 0.9}'
        mock_model_instance = Mock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_model_instance

        # Recreate tool with mocked model
        place_tool = PlaceExtractionTool(api_key="test_key")

        result = place_tool._extract_with_gemini("Bakso enak di Bakso Pak Joko", ["bakso"])

        self.assertEqual(result["place_name"], "Bakso Pak Joko")
        self.assertEqual(result["confidence"], 0.9)

    @patch('tools.place_extraction_tool.genai.GenerativeModel')
    def test_extract_with_gemini_fallback(self, mock_model):
        """Test place extraction with Gemini fallback on error"""
        # Mock model that raises exception
        mock_model_instance = Mock()
        mock_model_instance.generate_content.side_effect = Exception("API Error")
        mock_model.return_value = mock_model_instance

        place_tool = PlaceExtractionTool(api_key="test_key")

        result = place_tool._extract_with_gemini("test description", ["test"])

        # Should return fallback result
        self.assertIsNone(result["place_name"])
        self.assertEqual(result["confidence"], 0.0)

    @patch('tools.place_extraction_tool.genai.GenerativeModel')
    def test_execute_success(self, mock_model):
        """Test successful tool execution"""
        # Mock Gemini response
        mock_response = Mock()
        mock_response.text = '{"place_name": "Bakso Pak Joko", "confidence": 0.9}'
        mock_model_instance = Mock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_model_instance

        place_tool = PlaceExtractionTool(api_key="test_key")

        input_data = ToolInput(parameters={
            "tiktok_description": "Bakso enak di Bakso Pak Joko",
            "keywords": ["bakso"],
            "hashtags": ["baksoenak"]
        })

        result = place_tool.execute(input_data)

        self.assertTrue(result.success)
        self.assertIn("place_name", result.data)
        self.assertEqual(result.data["place_name"], "Bakso Pak Joko")

    def test_execute_no_place_found(self):
        """Test tool execution when no place is found"""
        input_data = ToolInput(parameters={
            "tiktok_description": "Makanan enak sekali",
            "keywords": ["makanan"],
            "hashtags": ["enak"]
        })

        result = self.place_tool.execute(input_data)

        self.assertFalse(result.success)
        self.assertIn("Could not extract", result.error)

    def test_clean_text(self):
        """Test text cleaning functionality"""
        test_cases = [
            ("Bakso Pak Joko!!!", "Bakso Pak Joko"),
            ("RM. Padang Sederhana", "RM Padang Sederhana"),
            ("Warung Nasi **Ampera**", "Warung Nasi Ampera"),
            ("  Kedai Kopi  Indonesia  ", "Kedai Kopi Indonesia")
        ]

        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                result = self.place_tool._clean_text(input_text)
                self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()
