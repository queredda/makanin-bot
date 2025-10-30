# Redis Memory Backend for Makanin bot agent system
# Provides persistent storage for conversations, sessions, and tool executions

import json
import redis
from typing import Dict, Any, List, Optional
from datetime import datetime
import config
import traceback

from .memory import ConversationMessage, ToolExecution, UserSession


class RedisMemoryBackend:
    """Redis-based persistent memory backend for the Makanin bot"""

    def __init__(self):
        self.redis_client = None
        self.connected = False
        self._connect()

    def _connect(self) -> bool:
        """Establish Redis connection with fallback to in-memory if fails"""
        try:
            self.redis_client = redis.Redis(
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                db=config.REDIS_DB,
                password=config.REDIS_PASSWORD,
                decode_responses=True,  # Return strings instead of bytes
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )

            # Test connection
            self.redis_client.ping()
            self.connected = True
            print("[Redis Memory] Connected to Redis successfully")
            return True

        except Exception as e:
            print(f"[Redis Memory] Failed to connect to Redis: {e}")
            if config.REDIS_USE_MEMORY_FALLBACK:
                print("[Redis Memory] Falling back to in-memory storage")
                self.connected = False
            else:
                print("[Redis Memory] Redis connection required but failed. Exiting.")
                raise
            return False

    def _serialize_datetime(self, obj: Any) -> str:
        """Convert datetime objects to ISO format for JSON serialization"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    def _deserialize_datetime(self, datetime_str: str) -> datetime:
        """Convert ISO format string back to datetime object"""
        try:
            return datetime.fromisoformat(datetime_str)
        except (ValueError, TypeError):
            return datetime.now()  # Fallback to current time

    def _serialize_user_session(self, session: UserSession) -> str:
        """Serialize UserSession to JSON string"""
        data = {
            "user_id": session.user_id,
            "language": session.language,
            "preferences": session.preferences,
            "last_intent": session.last_intent,
            "context_data": session.context_data,
            "created_at": session.created_at.isoformat()
        }
        return json.dumps(data)

    def _deserialize_user_session(self, json_str: str) -> UserSession:
        """Deserialize JSON string back to UserSession"""
        data = json.loads(json_str)
        return UserSession(
            user_id=data["user_id"],
            language=data.get("language", "id"),
            preferences=data.get("preferences", {}),
            last_intent=data.get("last_intent"),
            context_data=data.get("context_data", {}),
            created_at=self._deserialize_datetime(data.get("created_at"))
        )

    def _serialize_conversation_message(self, message: ConversationMessage) -> str:
        """Serialize ConversationMessage to JSON string"""
        data = {
            "role": message.role,
            "content": message.content,
            "timestamp": message.timestamp.isoformat(),
            "metadata": message.metadata
        }
        return json.dumps(data)

    def _deserialize_conversation_message(self, json_str: str) -> ConversationMessage:
        """Deserialize JSON string back to ConversationMessage"""
        data = json.loads(json_str)
        return ConversationMessage(
            role=data["role"],
            content=data["content"],
            timestamp=self._deserialize_datetime(data["timestamp"]),
            metadata=data.get("metadata", {})
        )

    def _serialize_tool_execution(self, execution: ToolExecution) -> str:
        """Serialize ToolExecution to JSON string"""
        data = {
            "tool_name": execution.tool_name,
            "input_data": execution.input_data,
            "result": execution.result,
            "success": execution.success,
            "timestamp": execution.timestamp.isoformat(),
            "execution_time": execution.execution_time
        }
        return json.dumps(data)

    def _deserialize_tool_execution(self, json_str: str) -> ToolExecution:
        """Deserialize JSON string back to ToolExecution"""
        data = json.loads(json_str)
        return ToolExecution(
            tool_name=data["tool_name"],
            input_data=data["input_data"],
            result=data["result"],
            success=data["success"],
            timestamp=self._deserialize_datetime(data["timestamp"]),
            execution_time=data["execution_time"]
        )

    def _get_session_key(self, user_id: str) -> str:
        """Get Redis key for user session"""
        return f"makanin:sessions:{user_id}"

    def _get_conversation_key(self, user_id: str) -> str:
        """Get Redis key for user conversation"""
        return f"makanin:conversations:{user_id}"

    def _get_tools_key(self, user_id: str) -> str:
        """Get Redis key for user tool executions"""
        return f"makanin:tools:{user_id}"

    def is_connected(self) -> bool:
        """Check if Redis is connected and available"""
        return self.connected and self.redis_client is not None

    def health_check(self) -> bool:
        """Perform Redis health check"""
        if not self.is_connected():
            return False

        try:
            self.redis_client.ping()
            return True
        except:
            self.connected = False
            return False

    # Session Operations
    def set_user_session(self, session: UserSession) -> bool:
        """Store user session in Redis with TTL"""
        if not self.is_connected():
            return False

        try:
            key = self._get_session_key(session.user_id)
            value = self._serialize_user_session(session)
            self.redis_client.setex(key, config.SESSION_TTL, value)
            return True
        except Exception as e:
            print(f"[Redis Memory] Failed to set user session: {e}")
            return False

    def get_user_session(self, user_id: str) -> Optional[UserSession]:
        """Retrieve user session from Redis"""
        if not self.is_connected():
            return None

        try:
            key = self._get_session_key(user_id)
            value = self.redis_client.get(key)
            if value:
                return self._deserialize_user_session(value)
            return None
        except Exception as e:
            print(f"[Redis Memory] Failed to get user session: {e}")
            return None

    def delete_user_session(self, user_id: str) -> bool:
        """Delete user session from Redis"""
        if not self.is_connected():
            return False

        try:
            key = self._get_session_key(user_id)
            self.redis_client.delete(key)
            return True
        except Exception as e:
            print(f"[Redis Memory] Failed to delete user session: {e}")
            return False

    # Conversation Operations
    def add_conversation_message(self, user_id: str, message: ConversationMessage, max_messages: int = 20) -> bool:
        """Add conversation message to Redis list with size limit"""
        if not self.is_connected():
            return False

        try:
            key = self._get_conversation_key(user_id)
            message_json = self._serialize_conversation_message(message)

            # Use pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            pipe.lpush(key, message_json)  # Add to beginning of list
            pipe.ltrim(key, 0, max_messages - 1)  # Keep only latest max_messages
            pipe.expire(key, config.CONVERSATION_TTL)  # Set TTL
            pipe.execute()

            return True
        except Exception as e:
            print(f"[Redis Memory] Failed to add conversation message: {e}")
            return False

    def get_conversation_history(self, user_id: str, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """Get conversation history from Redis"""
        if not self.is_connected():
            return []

        try:
            key = self._get_conversation_key(user_id)
            messages_json = self.redis_client.lrange(key, 0, -1)  # Get all messages

            # Convert JSON strings to ConversationMessage objects
            # Note: Redis returns in reverse order since we use lpush, so reverse to get chronological order
            messages = []
            for msg_json in reversed(messages_json):
                try:
                    message = self._deserialize_conversation_message(msg_json)
                    messages.append({
                        "role": message.role,
                        "content": message.content
                    })
                except Exception as e:
                    print(f"[Redis Memory] Failed to deserialize message: {e}")
                    continue

            # Apply limit if specified
            if limit:
                messages = messages[:limit]

            return messages
        except Exception as e:
            print(f"[Redis Memory] Failed to get conversation history: {e}")
            return []

    def clear_conversation(self, user_id: str) -> bool:
        """Clear conversation history for a user"""
        if not self.is_connected():
            return False

        try:
            key = self._get_conversation_key(user_id)
            self.redis_client.delete(key)
            return True
        except Exception as e:
            print(f"[Redis Memory] Failed to clear conversation: {e}")
            return False

    # Tool Execution Operations
    def add_tool_execution(self, user_id: str, execution: ToolExecution, max_executions: int = 50) -> bool:
        """Add tool execution record to Redis list with size limit"""
        if not self.is_connected():
            return False

        try:
            key = self._get_tools_key(user_id)
            execution_json = self._serialize_tool_execution(execution)

            # Use pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            pipe.lpush(key, execution_json)  # Add to beginning of list
            pipe.ltrim(key, 0, max_executions - 1)  # Keep only latest max_executions
            pipe.expire(key, config.TOOL_EXECUTION_TTL)  # Set TTL
            pipe.execute()

            return True
        except Exception as e:
            print(f"[Redis Memory] Failed to add tool execution: {e}")
            return False

    def get_tool_executions(self, user_id: str, limit: int = 10) -> List[ToolExecution]:
        """Get recent tool executions for a user from Redis"""
        if not self.is_connected():
            return []

        try:
            key = self._get_tools_key(user_id)
            executions_json = self.redis_client.lrange(key, 0, limit - 1)  # Get limited executions

            executions = []
            for exec_json in executions_json:
                try:
                    execution = self._deserialize_tool_execution(exec_json)
                    executions.append(execution)
                except Exception as e:
                    print(f"[Redis Memory] Failed to deserialize tool execution: {e}")
                    continue

            return executions
        except Exception as e:
            print(f"[Redis Memory] Failed to get tool executions: {e}")
            return []

    def clear_tool_executions(self, user_id: str) -> bool:
        """Clear tool executions for a user"""
        if not self.is_connected():
            return False

        try:
            key = self._get_tools_key(user_id)
            self.redis_client.delete(key)
            return True
        except Exception as e:
            print(f"[Redis Memory] Failed to clear tool executions: {e}")
            return False

    # User Management Operations
    def clear_all_user_data(self, user_id: str) -> bool:
        """Clear all data for a user (sessions, conversations, tool executions)"""
        if not self.is_connected():
            return False

        try:
            session_key = self._get_session_key(user_id)
            conversation_key = self._get_conversation_key(user_id)
            tools_key = self._get_tools_key(user_id)

            self.redis_client.delete(session_key, conversation_key, tools_key)
            return True
        except Exception as e:
            print(f"[Redis Memory] Failed to clear all user data: {e}")
            return False

    def get_all_user_ids(self) -> List[str]:
        """Get all user IDs that have data in Redis"""
        if not self.is_connected():
            return []

        try:
            # Get all keys matching our patterns
            session_keys = self.redis_client.keys("makanin:sessions:*")
            user_ids = []

            for key in session_keys:
                # Extract user_id from key like "makanin:sessions:12345"
                user_id = key.split(":")[-1]
                user_ids.append(user_id)

            return user_ids
        except Exception as e:
            print(f"[Redis Memory] Failed to get all user IDs: {e}")
            return []

    def cleanup_expired_data(self) -> int:
        """Manually trigger cleanup of expired keys (Redis handles this automatically)"""
        # Redis automatically handles expired keys with TTL
        # This is a placeholder for potential manual cleanup operations
        if not self.is_connected():
            return 0

        try:
            # Redis handles TTL cleanup automatically
            # This could be extended for custom cleanup logic if needed
            print("[Redis Memory] Redis handles expired data cleanup automatically")
            return 0
        except Exception as e:
            print(f"[Redis Memory] Cleanup failed: {e}")
            return 0
