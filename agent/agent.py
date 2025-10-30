# Main Agent Orchestrator for Makanin bot
# Replaces hardcoded logic with intelligent LLM-powered tool selection and execution

from typing import Dict, Any, List, Optional, Tuple
import json
import google.generativeai as genai
import config

from agent.tools import ToolRegistry, ToolExecutor, ToolInput, tool_registry
from agent.memory import ContextManager
from agent.prompts import (
    TOOL_SELECTION_SYSTEM_PROMPT,
    get_tool_selection_prompt,
    get_response_generation_prompt,
    format_food_response
)


class MakaninAgent:
    """Intelligent agent that decides which tools to use based on user input"""

    def __init__(self):
        # Initialize components
        self.tool_registry = tool_registry  # Use the global registry
        self.tool_executor = ToolExecutor(self.tool_registry)
        self.context_manager = ContextManager()

        # Initialize Gemini for agent reasoning
        genai.configure(api_key=config.GEMINI_API_KEY)
        self.reasoning_model = genai.GenerativeModel(config.GEMINI_MODEL)

        # Register all tools
        self._register_tools()

        print("🤖 Makanin Agent initialized with tools:", self.tool_registry.list_tools())

    def _register_tools(self) -> None:
        """Register all available tools"""
        # Import tools to trigger registration
        import tools.tiktok_search_tool
        import tools.location_resolution_tool
        import tools.weather_tool
        import tools.conversation_tool
        import tools.place_extraction_tool
        import tools.nlu_tool

    async def process_message(self, user_id: str, user_message: str) -> str:
        """Process a user message and return the agent's response"""
        print(f"\n🚀 [Agent] Processing message from {user_id}: '{user_message}'")

        try:
            # Process user input and update context
            context = self.context_manager.process_user_input(user_id, user_message)

            # Step 1: Use NLU to understand user intent
            nlu_result = await self._execute_tool("nlu", {"text": user_message})
            if not nlu_result.success:
                return self._handle_error("NLU analysis failed", nlu_result.error)

            intent_data = nlu_result.data
            print(f"🎯 [Agent] Intent: {intent_data['intent']}, Keywords: {intent_data['keywords']}")

            # Update session data
            self.context_manager.update_user_preferences(
                user_id,
                language=intent_data.get("language", "id"),
                last_intent=intent_data["intent"]
            )

            # Step 2: Plan tool usage based on intent
            if intent_data["intent"] == "find_food":
                response = await self._handle_food_search_intent(user_id, intent_data, user_message)
            else:
                response = await self._handle_chat_intent(user_id, intent_data, user_message)

            # Step 3: Record assistant response
            self.context_manager.process_assistant_response(
                user_id, response, tools_used=self._get_used_tools()
            )

            return response

        except Exception as e:
            print(f"❌ [Agent] Error processing message: {e}")
            return self._handle_error("Processing failed", str(e))

    async def _handle_food_search_intent(self, user_id: str, intent_data: Dict[str, Any], user_message: str) -> str:
        """Handle food search intent with tool orchestration"""
        language = intent_data.get("language", "id")
        keywords = intent_data.get("keywords", [])
        location = intent_data.get("location")
        constraints = intent_data.get("constraints", {})

        print(f"🔍 [Agent] Starting food search workflow")

        # Step 1: Search TikTok for viral content
        tiktok_result = await self._execute_tool("tiktok_search", {
            "keywords": keywords,
            "location": location,
            "constraints": constraints,
            "max_results": config.MAX_RESULTS
        })

        if not tiktok_result.success or not tiktok_result.data:
            print("❌ [Agent] No TikTok results found")
            return format_food_response([], language)

        tiktok_results = tiktok_result.data
        print(f"📱 [Agent] Found {len(tiktok_results)} TikTok results")

        # Step 2: Process each TikTok result to extract venue info
        venues = []
        for idx, tiktok_item in enumerate(tiktok_results[:config.MAX_RESULTS]):
            print(f"\n--- Processing TikTok result {idx + 1} ---")

            # Extract restaurant name from TikTok description
            extraction_result = await self._execute_tool("place_extraction", {
                "tiktok_description": tiktok_item.get("tiktok_description", ""),
                "keywords": keywords,
                "hashtags": []  # Could be extracted from tiktok_item if needed
            })

            if not extraction_result.success:
                print(f"⏭️  Skipped: Could not extract restaurant name")
                continue

            place_name = extraction_result.data["place_name"]
            print(f"🏪 Extracted place name: {place_name}")

            # Resolve location using Google Maps
            location_result = await self._execute_tool("location_resolution", {
                "venue_name": place_name,
                "location_hint": location
            })

            if not location_result.success:
                print(f"⏭️  Skipped: Could not resolve location for '{place_name}'")
                continue

            location_data = location_result.data
            print(f"📍 Found location: {location_data.get('address', 'Unknown')}")

            # Get weather information
            weather_result = await self._execute_tool("weather", {
                "latitude": location_data["latitude"],
                "longitude": location_data["longitude"],
                "language": language
            })

            weather_summary = None
            if weather_result.success:
                weather_summary = weather_result.data.get("summary")
                print(f"🌤️  Weather: {weather_summary}")

            # Build venue object
            venue = {
                "id": tiktok_item.get("id", ""),
                "name": place_name,
                "description": tiktok_item.get("description", ""),
                "tiktok_link": tiktok_item.get("tiktok_link"),
                "address": location_data.get("address"),
                "maps_link": location_data.get("maps_link"),
                "weather_summary": weather_summary,
                "latitude": location_data.get("latitude"),
                "longitude": location_data.get("longitude")
            }

            venues.append(venue)

        print(f"\n✅ [Agent] Food search completed: {len(venues)} venues found")

        # Step 3: Generate response
        if venues:
            return format_food_response(venues, language)
        else:
            return format_food_response([], language)

    async def _handle_chat_intent(self, user_id: str, intent_data: Dict[str, Any], user_message: str) -> str:
        """Handle general conversation intent"""
        language = intent_data.get("language", "id")
        conversation_history = self.context_manager.memory.get_conversation_history(user_id, 5)

        print(f"💬 [Agent] Handling conversation intent")

        # Use conversation tool
        conversation_result = await self._execute_tool("conversation", {
            "user_message": user_message,
            "conversation_history": conversation_history,
            "language": language
        })

        if conversation_result.success:
            return conversation_result.data["response"]
        else:
            return self._handle_error("Conversation failed", conversation_result.error, language)

    async def _execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute a tool and record the result"""
        import time
        start_time = time.time()

        try:
            # Execute the tool
            result = self.tool_executor.execute_tool(tool_name, ToolInput(parameters=parameters))

            # Record execution in context
            current_user_id = getattr(self, '_current_user_id', 'default')
            execution_time = time.time() - start_time

            self.context_manager.record_tool_usage(
                current_user_id,
                tool_name,
                parameters,
                result.data if result.success else {"error": result.error},
                result.success,
                execution_time
            )

            return result

        except Exception as e:
            print(f"❌ [Agent] Tool execution failed: {e}")
            # Return error result
            error_result = type('Result', (), {
                'success': False,
                'error': str(e),
                'data': None
            })()
            return error_result

    def _handle_error(self, error_type: str, error_message: str, language: str = "id") -> str:
        """Handle errors and return appropriate responses"""
        print(f"❌ [Agent] {error_type}: {error_message}")

        if language == "id":
            return "Ah sorry! Terjadi kesalahan nih 😅 Bisa coba lagi? Terimakasih! 😊"
        else:
            return "Oops! Something went wrong there 😅 Can you try again? Thanks! 😊"

    def _get_used_tools(self) -> List[str]:
        """Get list of tools used in recent executions"""
        return [
            execution.tool_name
            for execution in self.tool_executor.get_execution_history()
        ]

    def get_tool_status(self) -> Dict[str, Any]:
        """Get status of all registered tools"""
        return {
            "available_tools": self.tool_registry.list_tools(),
            "recent_executions": len(self.tool_executor.get_execution_history()),
            "active_sessions": len(self.context_manager.memory.sessions)
        }

    async def create_tool_plan(self, user_message: str, user_id: str = "default") -> Dict[str, Any]:
        """Create a tool execution plan using LLM reasoning"""
        context = self.context_manager.process_user_input(user_id, user_message)

        # Get tool definitions
        tool_definitions = json.dumps(self.tool_registry.get_tool_definitions(), indent=2)

        # Generate plan using LLM
        prompt = get_tool_selection_prompt(user_message, tool_definitions, str(context))

        try:
            response = self.reasoning_model.generate_content(prompt)
            plan_json = json.loads(response.text.strip())
            return plan_json
        except Exception as e:
            print(f"❌ [Agent] Plan generation failed: {e}")
            # Return fallback plan
            return {
                "reasoning": "Failed to generate plan, using fallback",
                "tool_plan": [
                    {
                        "tool": "nlu",
                        "purpose": "Analyze user input",
                        "parameters": {"text": user_message},
                        "depends_on": []
                    }
                ],
                "expected_outcome": "Basic input analysis"
            }
