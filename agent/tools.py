# Tool framework for Makanin bot agent system
# Base interfaces and tool registry for dynamic tool selection

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
import json
import traceback


@dataclass
class ToolResult:
    """Standard result format for all tools"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    tool_name: str = ""
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolInput:
    """Standard input format for all tools"""
    parameters: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)


class BaseTool(ABC):
    """Abstract base class for all agent tools"""

    def __init__(self, name: str, description: str, api_key: Optional[str] = None):
        self.name = name
        self.description = description
        self.api_key = api_key

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for tool parameters"""
        pass

    @abstractmethod
    def validate_input(self, input_data: ToolInput) -> bool:
        """Validate input parameters before execution"""
        pass

    @abstractmethod
    def execute(self, input_data: ToolInput) -> ToolResult:
        """Execute the tool with given input"""
        pass

    @property
    def tool_definition(self) -> Dict[str, Any]:
        """Return tool definition for LLM consumption"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.get_schema()
        }


class ToolRegistry:
    """Registry for managing and discovering tools"""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._categories: Dict[str, List[str]] = {
            "search": [],
            "location": [],
            "weather": [],
            "conversation": [],
            "processing": []
        }

    def register(self, tool: BaseTool, category: str = "general") -> None:
        """Register a tool in the registry"""
        self._tools[tool.name] = tool

        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(tool.name)

        print(f"🔧 Registered tool: {tool.name} (category: {category})")

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name"""
        return self._tools.get(name)

    def get_all_tools(self) -> Dict[str, BaseTool]:
        """Get all registered tools"""
        return self._tools.copy()

    def get_tools_by_category(self, category: str) -> List[BaseTool]:
        """Get all tools in a specific category"""
        tool_names = self._categories.get(category, [])
        return [self._tools[name] for name in tool_names if name in self._tools]

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get all tool definitions for LLM consumption"""
        return [tool.tool_definition for tool in self._tools.values()]

    def list_tools(self) -> List[str]:
        """List all registered tool names"""
        return list(self._tools.keys())


# Global tool registry instance
tool_registry = ToolRegistry()


def register_tool(category: str = "general"):
    """Decorator for registering tools"""

    def decorator(cls):
        # Create instance and register
        instance = cls()
        tool_registry.register(instance, category)
        return cls

    return decorator


class ToolExecutor:
    """Handles tool execution with error handling and logging"""

    def __init__(self, registry: ToolRegistry = tool_registry):
        self.registry = registry
        self.execution_history: List[ToolResult] = []

    def execute_tool(self, tool_name: str, input_data: ToolInput) -> ToolResult:
        """Execute a tool with error handling"""
        import time
        start_time = time.time()

        tool = self.registry.get_tool(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool '{tool_name}' not found",
                tool_name=tool_name
            )

        try:
            # Validate input
            if not tool.validate_input(input_data):
                return ToolResult(
                    success=False,
                    error=f"Invalid input for tool '{tool_name}'",
                    tool_name=tool_name
                )

            # Execute tool
            result = tool.execute(input_data)
            result.tool_name = tool_name
            result.execution_time = time.time() - start_time

            # Store execution history
            self.execution_history.append(result)

            print(f"✅ Tool '{tool_name}' executed successfully ({result.execution_time:.2f}s)")
            return result

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Error executing tool '{tool_name}': {str(e)}"
            print(f"❌ {error_msg}")
            traceback.print_exc()

            result = ToolResult(
                success=False,
                error=error_msg,
                tool_name=tool_name,
                execution_time=execution_time
            )
            self.execution_history.append(result)
            return result

    def get_execution_history(self) -> List[ToolResult]:
        """Get history of tool executions"""
        return self.execution_history.copy()

    def clear_history(self) -> None:
        """Clear execution history"""
        self.execution_history.clear()
