# Conversation Tool for Makanin bot agent system
# Handles general conversation with users using Gemini AI

from typing import Dict, Any, Optional, List
from agent.tools import BaseTool, ToolInput, ToolResult
import google.generativeai as genai
import config


class ConversationTool(BaseTool):
    """Tool for handling general conversation with users"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            name="conversation",
            description="Handle general conversation and provide friendly responses to user messages",
            api_key=api_key
        )
        genai.configure(api_key=api_key or config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(config.GEMINI_MODEL)

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for tool parameters"""
        return {
            "type": "object",
            "properties": {
                "user_message": {
                    "type": "string",
                    "description": "The user's message to respond to"
                },
                "conversation_history": {
                    "type": "array",
                    "description": "Previous conversation messages for context",
                    "items": {
                        "type": "object",
                        "properties": {
                            "role": {"type": "string", "enum": ["user", "assistant"]},
                            "content": {"type": "string"}
                        }
                    },
                    "default": []
                },
                "language": {
                    "type": "string",
                    "description": "Detected language of the user ('id' for Indonesian, 'en' for English)",
                    "enum": ["id", "en"],
                    "default": "id"
                }
            },
            "required": ["user_message"]
        }

    def validate_input(self, input_data: ToolInput) -> bool:
        """Validate input parameters"""
        params = input_data.parameters

        # Check required user_message
        user_message = params.get("user_message")
        if not user_message or not isinstance(user_message, str) or not user_message.strip():
            return False

        # Validate conversation_history if provided
        history = params.get("conversation_history", [])
        if not isinstance(history, list):
            return False

        for msg in history:
            if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
                return False
            if msg["role"] not in ["user", "assistant"]:
                return False

        # Validate language if provided
        language = params.get("language", "id")
        if language not in ["id", "en"]:
            return False

        return True

    def execute(self, input_data: ToolInput) -> ToolResult:
        """Execute conversation response generation"""
        import time
        start_time = time.time()

        try:
            params = input_data.parameters
            user_message = params["user_message"].strip()
            conversation_history = params.get("conversation_history", [])
            language = params.get("language", "id")

            print(f"💬 [Conversation Tool] Processing message: '{user_message[:50]}...' (language: {language})")

            # System prompt for Makanin personality
            system_prompt = """You are Makanin, a super friendly and enthusiastic food-finder bot! 🍜✨

Your personality:
- You're warm, engaging, and genuinely excited about food!
- Use emojis naturally and appropriately to make conversations fun
- Be conversational, brief, and always helpful
- Mirror the user's language (Indonesian or English) perfectly
- You're knowledgeable about food culture and viral food trends
- You make food recommendations sound amazing and irresistible!

When users ask about food:
- Share your enthusiasm with lots of encouragement!
- Suggest they search using specific keywords like 'cariin bakso viral' or 'find me good ramen near campus'
- If they mention specific foods or areas, help them discover viral spots
- Use phrases like "Ooh, bagus banget pilihan!" or "That sounds delicious!"

Tone examples:
- Be casual and friendly, like chatting with a food-loving friend
- Use warm greetings and encourage them to explore
- If they have questions, answer helpfully with personality
- Always end conversations on a positive note about food!"""

            # Build conversation context
            conversation_text = ""
            for msg in conversation_history[-5:]:  # Last 5 messages for context
                if msg["role"] == "user":
                    conversation_text += f"User: {msg['content']}\n"
                else:
                    conversation_text += f"Makanin: {msg['content']}\n"

            # Build final prompt
            final_prompt = f"""{system_prompt}

Previous conversation:
{conversation_text}

User: {user_message}

Makanin:"""

            # Generate response
            response_obj = self.model.generate_content(final_prompt)
            response = response_obj.text.strip()

            print(f"✅ [Conversation Tool] Generated response: '{response[:50]}...'")

            # Return the conversation response
            result_data = {
                "response": response,
                "user_message": user_message,
                "language": language,
                "context_length": len(conversation_history)
            }

            return ToolResult(
                success=True,
                data=result_data,
                metadata={
                    "language": language,
                    "context_length": len(conversation_history),
                    "response_length": len(response),
                    "execution_time": time.time() - start_time
                }
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Conversation generation failed: {str(e)}",
                metadata={"execution_time": time.time() - start_time}
            )


# Register the tool when imported
from agent.tools import register_tool

register_tool("conversation")(ConversationTool)
