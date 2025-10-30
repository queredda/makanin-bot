# Memory and Context Management for Makanin bot agent system
# Handles conversation history, tool execution context, and user session data
# Supports both Redis (persistent) and in-memory backends

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import config

# Import Redis backend - will check availability at runtime
REDIS_AVAILABLE = True  # Assume available, will check at runtime


@dataclass
class ConversationMessage:
    """Represents a single conversation message"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolExecution:
    """Represents a tool execution in the conversation"""
    tool_name: str
    input_data: Dict[str, Any]
    result: Dict[str, Any]
    success: bool
    timestamp: datetime
    execution_time: float


@dataclass
class UserSession:
    """Represents a user's session data"""
    user_id: str
    language: str = "id"
    preferences: Dict[str, Any] = field(default_factory=dict)
    last_intent: Optional[str] = None
    context_data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


class ConversationMemory:
    """Manages conversation history and context with pluggable backends"""

    def __init__(self, max_messages: int = 20, max_sessions: int = 100):
        self.max_messages = max_messages
        self.max_sessions = max_sessions

        # Initialize backend based on configuration
        self.backend = self._initialize_backend()

        # Keep in-memory data for backward compatibility and fallback
        self.sessions: Dict[str, UserSession] = {}
        self.conversations: Dict[str, List[ConversationMessage]] = {}
        self.tool_executions: Dict[str, List[ToolExecution]] = {}

        print(f"[Memory] Using backend: {'Redis' if self._is_using_redis() else 'In-Memory'}")

    def _initialize_backend(self):
        """Initialize the appropriate memory backend"""
        # Check if Redis is configured and available
        if config.MEMORY_BACKEND == "redis":
            try:
                from .redis_memory import RedisMemoryBackend
                backend = RedisMemoryBackend()
                if backend.is_connected():
                    print("[Memory] Redis backend initialized successfully")
                    return backend
                else:
                    print(" [Memory] Redis backend failed to connect, using in-memory fallback")
                    return None
            except Exception as e:
                print(f"[Memory] Redis backend initialization failed: {e}")
                print("[Memory] Falling back to in-memory storage")
                return None
        else:
            print("[Memory] Using in-memory backend")
            return None

    def _is_using_redis(self) -> bool:
        """Check if Redis backend is being used"""
        return self.backend is not None and hasattr(self.backend, 'is_connected') and self.backend.is_connected()

    def get_or_create_session(self, user_id: str) -> UserSession:
        """Get or create a user session"""
        # Try Redis first if available
        if self._is_using_redis():
            session = self.backend.get_user_session(user_id)
            if session:
                # Also cache in memory for performance
                self.sessions[user_id] = session
                return session

        # Fallback to in-memory or create new session
        if user_id not in self.sessions:
            self.sessions[user_id] = UserSession(user_id=user_id)

            # Save to Redis if available
            if self._is_using_redis():
                self.backend.set_user_session(self.sessions[user_id])

            # Clean up old sessions if needed
            if len(self.sessions) > self.max_sessions:
                self._cleanup_old_sessions()

        return self.sessions[user_id]

    def add_message(self, user_id: str, role: str, content: str, metadata: Dict[str, Any] = None) -> None:
        """Add a message to the conversation history"""
        if user_id not in self.conversations:
            self.conversations[user_id] = []

        message = ConversationMessage(
            role=role,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )

        self.conversations[user_id].append(message)

        # Save to Redis if available
        if self._is_using_redis():
            self.backend.add_conversation_message(user_id, message, self.max_messages)

        # Limit conversation history in memory
        if len(self.conversations[user_id]) > self.max_messages:
            self.conversations[user_id] = self.conversations[user_id][-self.max_messages:]

    def get_conversation_history(self, user_id: str, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """Get conversation history in a format suitable for prompts"""
        # Try Redis first if available
        if self._is_using_redis():
            redis_messages = self.backend.get_conversation_history(user_id, limit)
            if redis_messages:
                # Update cache with Redis data
                return redis_messages

        # Fallback to in-memory
        if user_id not in self.conversations:
            return []

        messages = self.conversations[user_id]
        if limit:
            messages = messages[-limit:]

        return [
            {
                "role": msg.role,
                "content": msg.content
            }
            for msg in messages
        ]

    def add_tool_execution(self, user_id: str, tool_name: str, input_data: Dict[str, Any],
                           result: Dict[str, Any], success: bool, execution_time: float) -> None:
        """Add a tool execution record"""
        if user_id not in self.tool_executions:
            self.tool_executions[user_id] = []

        execution = ToolExecution(
            tool_name=tool_name,
            input_data=input_data,
            result=result,
            success=success,
            timestamp=datetime.now(),
            execution_time=execution_time
        )

        self.tool_executions[user_id].append(execution)

        # Save to Redis if available
        if self._is_using_redis():
            self.backend.add_tool_execution(user_id, execution, 50)  # Max 50 executions

        # Keep only recent executions in memory
        if len(self.tool_executions[user_id]) > 50:
            self.tool_executions[user_id] = self.tool_executions[user_id][-50:]

    def get_recent_tool_executions(self, user_id: str, limit: int = 10) -> List[ToolExecution]:
        """Get recent tool executions for a user"""
        # Try Redis first if available
        if self._is_using_redis():
            redis_executions = self.backend.get_tool_executions(user_id, limit)
            if redis_executions:
                return redis_executions

        # Fallback to in-memory
        if user_id not in self.tool_executions:
            return []
        return self.tool_executions[user_id][-limit:]

    def update_session_data(self, user_id: str, **kwargs) -> None:
        """Update user session data"""
        session = self.get_or_create_session(user_id)

        for key, value in kwargs.items():
            if hasattr(session, key):
                setattr(session, key, value)
            else:
                session.context_data[key] = value

        # Save to Redis if available
        if self._is_using_redis():
            self.backend.set_user_session(session)

    def get_session_data(self, user_id: str) -> UserSession:
        """Get user session data"""
        return self.get_or_create_session(user_id)

    def clear_conversation(self, user_id: str) -> None:
        """Clear conversation history for a user"""
        # Clear from Redis if available
        if self._is_using_redis():
            self.backend.clear_conversation(user_id)
            self.backend.clear_tool_executions(user_id)

        # Clear from in-memory
        if user_id in self.conversations:
            self.conversations[user_id].clear()
        if user_id in self.tool_executions:
            self.tool_executions[user_id].clear()

    def _cleanup_old_sessions(self) -> None:
        """Remove oldest sessions when limit is exceeded"""
        sorted_sessions = sorted(
            self.sessions.items(),
            key=lambda x: x[1].created_at
        )

        # Remove oldest 20% of sessions
        to_remove = int(self.max_sessions * 0.2)
        for user_id, _ in sorted_sessions[:to_remove]:
            del self.sessions[user_id]
            if user_id in self.conversations:
                del self.conversations[user_id]
            if user_id in self.tool_executions:
                del self.tool_executions[user_id]

    def get_context_summary(self, user_id: str) -> Dict[str, Any]:
        """Get a summary of the current conversation context"""
        session = self.get_or_create_session(user_id)
        conversation = self.conversations.get(user_id, [])
        recent_tools = self.get_recent_tool_executions(user_id, 5)

        return {
            "user_id": user_id,
            "language": session.language,
            "last_intent": session.last_intent,
            "conversation_length": len(conversation),
            "recent_tool_executions": [
                {
                    "tool_name": exec.tool_name,
                    "success": exec.success,
                    "execution_time": exec.execution_time
                }
                for exec in recent_tools
            ],
            "preferences": session.preferences,
            "context_data": session.context_data
        }


class ContextManager:
    """High-level context management for the agent"""

    def __init__(self):
        self.memory = ConversationMemory()

    def process_user_input(self, user_id: str, message: str) -> Dict[str, Any]:
        """Process user input and update context"""
        # Add user message to conversation
        self.memory.add_message(user_id, "user", message)

        # Get current context
        context = self.memory.get_context_summary(user_id)
        context["recent_conversation"] = self.memory.get_conversation_history(user_id, 5)

        return context

    def process_assistant_response(self, user_id: str, response: str, tools_used: List[str] = None) -> None:
        """Process assistant response and update context"""
        # Add assistant message to conversation
        metadata = {}
        if tools_used:
            metadata["tools_used"] = tools_used

        self.memory.add_message(user_id, "assistant", response, metadata)

    def record_tool_usage(self, user_id: str, tool_name: str, input_data: Dict[str, Any],
                          result: Dict[str, Any], success: bool, execution_time: float) -> None:
        """Record tool usage in context"""
        self.memory.add_tool_execution(user_id, tool_name, input_data, result, success, execution_time)

    def update_user_preferences(self, user_id: str, **preferences) -> None:
        """Update user preferences"""
        self.memory.update_session_data(user_id, preferences=preferences)

    def get_conversation_for_prompt(self, user_id: str, max_messages: int = 10) -> str:
        """Get conversation history formatted for prompt inclusion"""
        messages = self.memory.get_conversation_history(user_id, max_messages)

        if not messages:
            return ""

        conversation_text = ""
        for msg in messages:
            conversation_text += f"{msg['role'].capitalize()}: {msg['content']}\n"

        return conversation_text

    def clear_user_data(self, user_id: str) -> None:
        """Clear all data for a user"""
        # Clear from Redis if available
        if self.memory._is_using_redis():
            self.memory.backend.clear_all_user_data(user_id)

        # Clear from in-memory
        self.memory.clear_conversation(user_id)
        if user_id in self.memory.sessions:
            del self.memory.sessions[user_id]
