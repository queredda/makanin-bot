import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agent.tools import BaseTool, ToolInput, ToolResult, ToolRegistry, ToolExecutor


class MockTool(BaseTool):
    """Mock tool for testing"""

    def __init__(self, name="mock_tool", should_fail=False):
        super().__init__(name=name, description="Mock tool for testing")
        self.should_fail = should_fail

    def get_schema(self):
        return {
            "type": "object",
            "properties": {
                "input": {"type": "string"}
            },
            "required": ["input"]
        }

    def validate_input(self, input_data):
        return "input" in input_data.parameters

    def execute(self, input_data):
        if self.should_fail:
            return ToolResult(success=False, error="Mock tool failed")
        return ToolResult(
            success=True,
            data={"result": f"processed: {input_data.parameters['input']}"}
        )


class TestBaseTool(unittest.TestCase):
    """Unit tests for BaseTool"""

    def test_base_tool_initialization(self):
        """Test BaseTool initialization"""
        tool = MockTool()
        self.assertEqual(tool.name, "mock_tool")
        self.assertEqual(tool.description, "Mock tool for testing")
        self.assertIsNotNone(tool.get_schema())

    def test_base_tool_validation(self):
        """Test BaseTool input validation"""
        tool = MockTool()

        # Valid input
        valid_input = ToolInput(parameters={"input": "test"})
        self.assertTrue(tool.validate_input(valid_input))

        # Invalid input
        invalid_input = ToolInput(parameters={})
        self.assertFalse(tool.validate_input(invalid_input))

    def test_base_tool_execution(self):
        """Test BaseTool execution"""
        tool = MockTool()
        input_data = ToolInput(parameters={"input": "test"})

        result = tool.execute(input_data)
        self.assertTrue(result.success)
        self.assertEqual(result.data["result"], "processed: test")

    def test_base_tool_execution_failure(self):
        """Test BaseTool execution failure"""
        tool = MockTool(should_fail=True)
        input_data = ToolInput(parameters={"input": "test"})

        result = tool.execute(input_data)
        self.assertFalse(result.success)
        self.assertEqual(result.error, "Mock tool failed")


class TestToolRegistry(unittest.TestCase):
    """Unit tests for ToolRegistry"""

    def setUp(self):
        """Set up test fixtures"""
        self.registry = ToolRegistry()

    def test_register_tool(self):
        """Test tool registration"""
        tool = MockTool()
        self.registry.register(tool)

        self.assertIn("mock_tool", self.registry._tools)
        self.assertEqual(self.registry.get_tool("mock_tool"), tool)

    def test_register_duplicate_tool(self):
        """Test registering duplicate tool raises error"""
        tool1 = MockTool()
        tool2 = MockTool(name="mock_tool")

        self.registry.register(tool1)
        with self.assertRaises(ValueError):
            self.registry.register(tool2)

    def test_get_tool_not_found(self):
        """Test getting non-existent tool returns None"""
        tool = self.registry.get_tool("non_existent")
        self.assertIsNone(tool)

    def test_list_tools(self):
        """Test listing registered tools"""
        tool1 = MockTool(name="tool1")
        tool2 = MockTool(name="tool2")

        self.registry.register(tool1)
        self.registry.register(tool2)

        tools = self.registry.list_tools()
        self.assertEqual(len(tools), 2)
        self.assertIn("tool1", tools)
        self.assertIn("tool2", tools)

    def test_get_tool_definitions(self):
        """Test getting tool definitions"""
        tool = MockTool()
        self.registry.register(tool)

        definitions = self.registry.get_tool_definitions()
        self.assertIn("mock_tool", definitions)
        self.assertEqual(definitions["mock_tool"]["name"], "mock_tool")
        self.assertEqual(definitions["mock_tool"]["description"], "Mock tool for testing")


class TestToolExecutor(unittest.TestCase):
    """Unit tests for ToolExecutor"""

    def setUp(self):
        """Set up test fixtures"""
        self.registry = ToolRegistry()
        self.executor = ToolExecutor(self.registry)
        self.tool = MockTool()
        self.registry.register(self.tool)

    def test_execute_tool_success(self):
        """Test successful tool execution"""
        input_data = ToolInput(parameters={"input": "test"})
        result = self.executor.execute_tool("mock_tool", input_data)

        self.assertTrue(result.success)
        self.assertEqual(result.data["result"], "processed: test")

    def test_execute_tool_not_found(self):
        """Test executing non-existent tool"""
        input_data = ToolInput(parameters={"input": "test"})
        result = self.executor.execute_tool("non_existent", input_data)

        self.assertFalse(result.success)
        self.assertIn("not found", result.error)

    def test_execute_tool_validation_failure(self):
        """Test tool execution with invalid input"""
        invalid_input = ToolInput(parameters={})  # Missing required "input"
        result = self.executor.execute_tool("mock_tool", invalid_input)

        self.assertFalse(result.success)
        self.assertIn("validation", result.error.lower())

    def test_get_execution_history(self):
        """Test getting execution history"""
        input_data = ToolInput(parameters={"input": "test"})

        # Execute tool
        self.executor.execute_tool("mock_tool", input_data)

        # Get history
        history = self.executor.get_execution_history()

        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].tool_name, "mock_tool")
        self.assertTrue(history[0].success)

    def test_clear_execution_history(self):
        """Test clearing execution history"""
        input_data = ToolInput(parameters={"input": "test"})

        # Execute tool
        self.executor.execute_tool("mock_tool", input_data)

        # Verify history exists
        self.assertEqual(len(self.executor.get_execution_history()), 1)

        # Clear history
        self.executor.clear_execution_history()

        # Verify history is cleared
        self.assertEqual(len(self.executor.get_execution_history()), 0)


if __name__ == '__main__':
    unittest.main()
