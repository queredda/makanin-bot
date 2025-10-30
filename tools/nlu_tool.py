# NLU Tool for Makanin bot agent system
# Natural Language Understanding for intent classification and slot extraction

from typing import Dict, Any, Optional, List
from agent.tools import BaseTool, ToolInput, ToolResult
import google.generativeai as genai
import json
import re
import config


class NLUTool(BaseTool):
    """Tool for natural language understanding and intent classification"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            name="nlu",
            description="Analyze user input to extract intent, keywords, location, and constraints",
            api_key=api_key
        )
        genai.configure(api_key=api_key or config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(config.GEMINI_MODEL)

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for tool parameters"""
        return {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The user input text to analyze"
                }
            },
            "required": ["text"]
        }

    def validate_input(self, input_data: ToolInput) -> bool:
        """Validate input parameters"""
        params = input_data.parameters

        # Check required text
        text = params.get("text")
        if not text or not isinstance(text, str) or not text.strip():
            return False

        return True

    def execute(self, input_data: ToolInput) -> ToolResult:
        """Execute NLU analysis"""
        import time
        start_time = time.time()

        try:
            params = input_data.parameters
            text = params["text"].strip()

            print(f"🧠 [NLU Tool] Analyzing: '{text}'")

            # Detect language first
            language = self._detect_language(text)

            # Use Gemini for NLU
            intent_data = self._parse_with_gemini(text, language)

            print(
                f"✅ [NLU Tool] Intent: {intent_data['intent']}, Keywords: {intent_data['keywords']}, Location: {intent_data.get('location')}")

            return ToolResult(
                success=True,
                data=intent_data,
                metadata={
                    "language": language,
                    "text_length": len(text),
                    "execution_time": time.time() - start_time
                }
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"NLU analysis failed: {str(e)}",
                metadata={"execution_time": time.time() - start_time}
            )

    def _detect_language(self, text: str) -> str:
        """Detect if text is Indonesian or English"""
        indonesian_words = [
            "cariin", "carin", "dong", "donk", "deket", "dekat", "makanan", "makan",
            "tempat", "restoran", "murah", "halal", "viral", "area", "daerah", "di"
        ]

        text_lower = text.lower()
        if any(word in text_lower for word in indonesian_words):
            return "id"
        return "en"

    def _parse_with_gemini(self, text: str, language: str) -> Dict[str, Any]:
        """Parse user input using Gemini AI"""
        prompt = f"""Analyze this user message and extract the following information in JSON format.

User message: "{text}"

Extract:
1. intent: "find_food" if user wants to find food/restaurants, otherwise "chat"
2. keywords: List of ALL food/cuisine keywords mentioned (e.g., ["ramen", "bakso", "sushi"]) - extract multiple if present
3. location: Location where they want to find food (e.g., "Yogyakarta", "Jakarta", "near campus") - null if not mentioned
4. constraints: Dictionary of constraints like {{"price": "cheap", "halal": true}} - empty if none
5. language: "id" for Indonesian, "en" for English

CRITICAL RULES:
- For keywords, extract ALL food/cuisine types mentioned, NOT locations
- Multiple keywords should be extracted when user mentions multiple foods
- For location, extract city names, landmarks, or area names
- Be smart about understanding context and variations
- If they're looking for food (with intent="find_food"), extract ALL keywords and location
- If they're just chatting, set intent="chat" and leave keywords/location empty

Example inputs and outputs:
- "cariin misoa di jogja" → {{"intent": "find_food", "keywords": ["misoa"], "location": "Jogja", "constraints": {{}}, "language": "id"}}
- "cari ramen enak jakarta" → {{"intent": "find_food", "keywords": ["ramen"], "location": "Jakarta", "constraints": {{}}, "language": "id"}}
- "ramen jogja" → {{"intent": "find_food", "keywords": ["ramen"], "location": "Jogja", "constraints": {{}}, "language": "id"}}
- "bakso dan soto di surabaya" → {{"intent": "find_food", "keywords": ["bakso", "soto"], "location": "Surabaya", "constraints": {{}}, "language": "id"}}
- "find coffee and cake near campus" → {{"intent": "find_food", "keywords": ["coffee", "cake"], "location": "near campus", "constraints": {{}}, "language": "en"}}
- "halo, apa kabar?" → {{"intent": "chat", "keywords": [], "location": null, "constraints": {{}}, "language": "id"}}
- "find me cheap coffee near campus" → {{"intent": "find_food", "keywords": ["coffee"], "location": "near campus", "constraints": {{"price": "cheap"}}, "language": "en"}}

Return ONLY the JSON, no explanation:"""

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()

            # Parse JSON from response
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result_json = json.loads(json_match.group())
            else:
                result_json = json.loads(result_text)

            return {
                "intent": result_json.get("intent", "chat"),
                "keywords": result_json.get("keywords", []),
                "location": result_json.get("location"),
                "constraints": result_json.get("constraints", {}),
                "language": language,
                "original_text": text
            }

        except Exception as e:
            print(f"❌ [NLU Tool] Gemini parsing failed: {e}")
            # Fallback to basic parsing
            return {
                "intent": "chat",
                "keywords": [],
                "location": None,
                "constraints": {},
                "language": language,
                "original_text": text
            }


# Register the tool when imported
from agent.tools import register_tool

register_tool("processing")(NLUTool)
