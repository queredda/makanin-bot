# Natural Language Understanding module for Makanin bot.
# Uses Gemini AI to intelligently extract intent, keywords, location, and constraints.

from dataclasses import dataclass
from typing import Optional, List
import google.generativeai as genai
import json
import config


@dataclass
class IntentSlots:
    """Extracted intent and slots from user input"""
    intent: str  # "find_food", "chat", etc.
    keywords: List[str]  # cuisine/food keywords
    location: Optional[str]  # location hint (e.g., "Yogyakarta", "Jakarta")
    constraints: dict  # price, halal, nearby, open_now, etc.
    original_text: str
    language: str  # "id" for Indonesian, "en" for English


class NLUEngine:
    """
    Gemini-powered NLU engine.
    Uses Gemini API to understand natural language much better than regex patterns.
    """

    def __init__(self, api_key: str = None):
        """Initialize with Gemini API"""
        if api_key:
            genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(config.GEMINI_MODEL)

    def detect_language(self, text: str) -> str:
        """Detect if text is Indonesian or English"""
        indonesian_words = [
            "cariin", "carin", "dong", "donk", "deket", "dekat", "makanan", "makan",
            "tempat", "restoran", "murah", "halal", "viral", "area", "daerah", "di"
        ]

        text_lower = text.lower()
        if any(word in text_lower for word in indonesian_words):
            return "id"
        return "en"

    def parse_user_input(self, text: str) -> IntentSlots:
        """
        Use Gemini to parse user input and extract all slots intelligently.
        """
        print(f"\n[NLU Parse] Input: '{text}'")
        language = self.detect_language(text)

        # Build prompt for Gemini to extract intent, keywords, location, constraints
        prompt = f"""Analyze this user message and extract the following information in JSON format.

User message: "{text}"

Extract:
1. intent: "find_food" if user wants to find food/restaurants, otherwise "chat"
2. keywords: List of food/cuisine keywords (e.g., ["ramen", "bakso"]) - empty if chat intent
3. location: Location where they want to find food (e.g., "Yogyakarta", "Jakarta", "near campus") - null if not mentioned
4. constraints: Dictionary of constraints like {{"price": "cheap", "halal": true}} - empty if none
5. language: "id" for Indonesian, "en" for English

Rules:
- For keywords, extract ONLY food/cuisine types mentioned, NOT locations
- For location, extract city names, landmarks, or area names
- Be smart about understanding context and variations
- If they're looking for food (with intent="find_food"), extract keywords and location
- If they're just chatting, set intent="chat" and leave keywords/location empty

Example inputs and outputs:
- "cariin misoa di jogja" → {{"intent": "find_food", "keywords": ["misoa"], "location": "Jogja", "constraints": {{}}, "language": "id"}}
- "cari ramen enak jakarta" → {{"intent": "find_food", "keywords": ["ramen"], "location": "Jakarta", "constraints": {{}}, "language": "id"}}
- "halo, apa kabar?" → {{"intent": "chat", "keywords": [], "location": null, "constraints": {{}}, "language": "id"}}
- "find me cheap coffee near campus" → {{"intent": "find_food", "keywords": ["coffee"], "location": "near campus", "constraints": {{"price": "cheap"}}, "language": "en"}}

Return ONLY the JSON, no explanation:"""

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()

            # Parse JSON from response
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result_json = json.loads(json_match.group())
            else:
                result_json = json.loads(result_text)

            intent = result_json.get("intent", "chat")
            keywords = result_json.get("keywords", [])
            location = result_json.get("location")
            constraints = result_json.get("constraints", {})

            print(f"  [Gemini NLU] Intent: {intent}")
            print(f"  [Gemini NLU] Keywords: {keywords}")
            print(f"  [Gemini NLU] Location: {location}")
            print(f"  [Gemini NLU] Constraints: {constraints}")
            print(f"  [Gemini NLU] Language: {language}\n")

            return IntentSlots(
                intent=intent,
                keywords=keywords,
                location=location,
                constraints=constraints,
                original_text=text,
                language=language
            )

        except Exception as e:
            print(f"[Gemini NLU] Error: {e}")
            # Fallback: treat as chat if Gemini fails
            return IntentSlots(
                intent="chat",
                keywords=[],
                location=None,
                constraints={},
                original_text=text,
                language=language
            )
