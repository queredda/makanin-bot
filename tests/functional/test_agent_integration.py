import unittest
from unittest.mock import Mock, patch, AsyncMock
import asyncio
import sys
import os

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agent.agent import MakaninAgent


class TestAgentIntegration(unittest.TestCase):
    """Functional tests for MakaninAgent integration"""

    def setUp(self):
        """Set up test fixtures"""
        # Mock all external dependencies
        self.patches = [
            patch('google.generativeai.config'),
            patch('google.generativeai.GenerativeModel'),
            patch('agent.memory.redis.Redis')
        ]

        for p in self.patches:
            p.start()

        # Mock Redis client
        mock_redis = Mock()
        mock_redis.hgetall.return_value = {}
        mock_redis.hget.return_value = None
        mock_redis.lrange.return_value = []

        with patch('agent.memory.redis.Redis', return_value=mock_redis):
            self.agent = MakaninAgent()

    def tearDown(self):
        """Clean up test fixtures"""
        for p in self.patches:
            p.stop()

    def test_process_food_search_message_indonesian(self):
        """Test processing Indonesian food search message"""
        # Mock tool responses
        self.agent._execute_tool = AsyncMock(side_effect=[
            # NLU response
            Mock(success=True, data={
                "intent": "find_food",
                "keywords": ["bakso"],
                "location": "Jogja",
                "constraints": {},
                "language": "id"
            }),
            # TikTok search response
            Mock(success=True, data=[
                {
                    "id": "1",
                    "description": "Bakso enak di Bakso Pak Joko",
                    "tiktok_description": "Bakso enak di Bakso Pak Joko",
                    "tiktok_link": "https://tiktok.com/test1"
                }
            ]),
            # Place extraction response
            Mock(success=True, data={"place_name": "Bakso Pak Joko"}),
            # Location resolution response
            Mock(success=True, data={
                "address": "Jl. Malioboro No. 123, Jogja",
                "latitude": -7.7956,
                "longitude": 110.3695,
                "maps_link": "https://maps.google.com/test"
            }),
            # Weather response
            Mock(success=True, data={"summary": "Cerah, 28°C"})
        ])

        # Test message processing
        result = asyncio.run(self.agent.process_message("user123", "cariin bakso di jogja"))

        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)
        self.agent._execute_tool.assert_called()

    def test_process_food_search_message_english(self):
        """Test processing English food search message"""
        # Mock tool responses
        self.agent._execute_tool = AsyncMock(side_effect=[
            # NLU response
            Mock(success=True, data={
                "intent": "find_food",
                "keywords": ["ramen"],
                "location": "Tokyo",
                "constraints": {"price": "cheap"},
                "language": "en"
            }),
            # TikTok search response
            Mock(success=True, data=[
                {
                    "id": "2",
                    "description": "Amazing ramen at Ichiran",
                    "tiktok_description": "Amazing ramen at Ichiran Tokyo",
                    "tiktok_link": "https://tiktok.com/test2"
                }
            ]),
            # Place extraction response
            Mock(success=True, data={"place_name": "Ichiran"}),
            # Location resolution response
            Mock(success=True, data={
                "address": "Shibuya, Tokyo",
                "latitude": 35.6895,
                "longitude": 139.6917,
                "maps_link": "https://maps.google.com/test2"
            }),
            # Weather response
            Mock(success=True, data={"summary": "Clear, 22°C"})
        ])

        result = asyncio.run(self.agent.process_message("user456", "find cheap ramen in Tokyo"))

        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_process_conversation_message(self):
        """Test processing conversation message"""
        # Mock tool responses
        self.agent._execute_tool = AsyncMock(side_effect=[
            # NLU response
            Mock(success=True, data={
                "intent": "chat",
                "keywords": [],
                "location": None,
                "constraints": {},
                "language": "id"
            }),
            # Conversation response
            Mock(success=True, data={"response": "Halo! Ada yang bisa saya bantu?"})
        ])

        result = asyncio.run(self.agent.process_message("user789", "halo, apa kabar?"))

        self.assertIsInstance(result, str)
        self.assertIn("halo", result.lower())

    def test_process_message_no_tiktok_results(self):
        """Test processing message with no TikTok results"""
        # Mock tool responses
        self.agent._execute_tool = AsyncMock(side_effect=[
            # NLU response
            Mock(success=True, data={
                "intent": "find_food",
                "keywords": ["exotic_food"],
                "location": "Antarctica",
                "constraints": {},
                "language": "en"
            }),
            # Empty TikTok search response
            Mock(success=True, data=[])
        ])

        result = asyncio.run(self.agent.process_message("user999", "find exotic food in Antarctica"))

        self.assertIsInstance(result, str)
        # Should return appropriate message for no results
        self.assertTrue(len(result) > 0)

    def test_process_message_nlu_failure(self):
        """Test processing message with NLU failure"""
        # Mock NLU failure
        self.agent._execute_tool = AsyncMock(return_value=Mock(
            success=False,
            error="NLU API error"
        ))

        result = asyncio.run(self.agent.process_message("user_error", "test message"))

        self.assertIsInstance(result, str)
        # Should return error message
        self.assertIn("maaf", result.lower())

    def test_get_agent_status(self):
        """Test getting agent status"""
        # Mock components
        self.agent.tool_registry.list_tools = Mock(return_value=["nlu", "tiktok_search", "conversation"])
        self.agent.tool_executor.get_execution_history = Mock(return_value=[Mock(), Mock(), Mock()])
        self.agent.context_manager.memory.sessions = {"user1": {}, "user2": {}, "user3": {}}

        status = self.agent.get_tool_status()

        self.assertIn("available_tools", status)
        self.assertIn("recent_executions", status)
        self.assertIn("active_sessions", status)
        self.assertEqual(len(status["available_tools"]), 3)
        self.assertEqual(status["recent_executions"], 3)
        self.assertEqual(status["active_sessions"], 3)

    def test_multiple_food_keywords(self):
        """Test processing message with multiple food keywords"""
        # Mock tool responses
        self.agent._execute_tool = AsyncMock(side_effect=[
            # NLU response
            Mock(success=True, data={
                "intent": "find_food",
                "keywords": ["bakso", "soto"],
                "location": "Surabaya",
                "constraints": {},
                "language": "id"
            }),
            # TikTok search response
            Mock(success=True, data=[
                {
                    "id": "3",
                    "description": "Bakso dan Soto Pak Budi",
                    "tiktok_description": "Bakso dan Soto Pak Budi enak banget",
                    "tiktok_link": "https://tiktok.com/test3"
                }
            ]),
            # Place extraction response
            Mock(success=True, data={"place_name": "Bakso dan Soto Pak Budi"}),
            # Location resolution response
            Mock(success=True, data={
                "address": "Jl. Gubeng Pojok No. 45, Surabaya",
                "latitude": -7.2575,
                "longitude": 112.7521,
                "maps_link": "https://maps.google.com/test3"
            }),
            # Weather response
            Mock(success=True, data={"summary": "Berawan, 30°C"})
        ])

        result = asyncio.run(self.agent.process_message("user_multi", "cari bakso dan soto di surabaya"))

        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_process_message_with_constraints(self):
        """Test processing message with dietary constraints"""
        # Mock tool responses
        self.agent._execute_tool = AsyncMock(side_effect=[
            # NLU response
            Mock(success=True, data={
                "intent": "find_food",
                "keywords": ["steak"],
                "location": "Jakarta",
                "constraints": {"halal": True, "price": "medium"},
                "language": "id"
            }),
            # TikTok search response
            Mock(success=True, data=[
                {
                    "id": "4",
                    "description": "Halal Steak House Jakarta",
                    "tiktok_description": "Steak halal enak di Jakarta",
                    "tiktok_link": "https://tiktok.com/test4"
                }
            ]),
            # Place extraction response
            Mock(success=True, data={"place_name": "Halal Steak House"}),
            # Location resolution response
            Mock(success=True, data={
                "address": "Jl. Sudirman No. 78, Jakarta",
                "latitude": -6.2088,
                "longitude": 106.8456,
                "maps_link": "https://maps.google.com/test4"
            }),
            # Weather response
            Mock(success=True, data={"summary": "Hujan ringan, 26°C"})
        ])

        result = asyncio.run(self.agent.process_message("user_constraints", "cari steak halal harga sedang di jakarta"))

        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)


if __name__ == '__main__':
    unittest.main()
