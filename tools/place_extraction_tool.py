# Place Name Extraction Tool for Makanin bot agent system
# Extracts restaurant/venue names from TikTok descriptions using multiple methods

from typing import Dict, Any, Optional, List
from agent.tools import BaseTool, ToolInput, ToolResult
import google.generativeai as genai
import re
import config


class PlaceExtractionTool(BaseTool):
    """Tool for extracting restaurant names from TikTok descriptions"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            name="place_extraction",
            description="Extract restaurant/venue names from TikTok descriptions using pattern matching and AI",
            api_key=api_key
        )
        genai.configure(api_key=api_key or config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(config.GEMINI_MODEL)

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for tool parameters"""
        return {
            "type": "object",
            "properties": {
                "tiktok_description": {
                    "type": "string",
                    "description": "The TikTok description text to extract restaurant name from"
                },
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Search keywords to validate the extracted place name against",
                    "default": []
                },
                "hashtags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Hashtags from the TikTok post for context",
                    "default": []
                }
            },
            "required": ["tiktok_description"]
        }

    def validate_input(self, input_data: ToolInput) -> bool:
        """Validate input parameters"""
        params = input_data.parameters

        # Check required tiktok_description
        description = params.get("tiktok_description")
        if not description or not isinstance(description, str):
            return False

        # Validate keywords if provided
        keywords = params.get("keywords", [])
        if not isinstance(keywords, list):
            return False

        # Validate hashtags if provided
        hashtags = params.get("hashtags", [])
        if not isinstance(hashtags, list):
            return False

        return True

    def execute(self, input_data: ToolInput) -> ToolResult:
        """Execute place name extraction"""
        import time
        start_time = time.time()

        try:
            params = input_data.parameters
            description = params["tiktok_description"]
            keywords = params.get("keywords", [])
            hashtags = params.get("hashtags", [])

            print(f"🔍 [Place Extraction] Extracting from: '{description[:60]}...'")

            if not description.strip():
                return ToolResult(
                    success=False,
                    error="Empty TikTok description provided",
                    metadata={"execution_time": time.time() - start_time}
                )

            # Method 1: Pattern matching
            extracted_name = self._extract_by_patterns(description, keywords, hashtags)
            if extracted_name:
                print(f"✅ [Place Extraction] Pattern match found: '{extracted_name}'")
                return ToolResult(
                    success=True,
                    data={
                        "place_name": extracted_name,
                        "method": "pattern_matching",
                        "confidence": "high"
                    },
                    metadata={
                        "method": "pattern_matching",
                        "execution_time": time.time() - start_time
                    }
                )

            # Method 2: Gemini AI extraction
            extracted_name = self._extract_by_gemini(description, keywords)
            if extracted_name:
                print(f"✅ [Place Extraction] Gemini extraction found: '{extracted_name}'")
                return ToolResult(
                    success=True,
                    data={
                        "place_name": extracted_name,
                        "method": "gemini_ai",
                        "confidence": "medium"
                    },
                    metadata={
                        "method": "gemini_ai",
                        "execution_time": time.time() - start_time
                    }
                )

            # Method 3: Hashtag fallback
            extracted_name = self._extract_from_hashtags(hashtags, keywords)
            if extracted_name:
                print(f"✅ [Place Extraction] Hashtag fallback found: '{extracted_name}'")
                return ToolResult(
                    success=True,
                    data={
                        "place_name": extracted_name,
                        "method": "hashtag_fallback",
                        "confidence": "low"
                    },
                    metadata={
                        "method": "hashtag_fallback",
                        "execution_time": time.time() - start_time
                    }
                )

            print(f"❌ [Place Extraction] No restaurant name found")
            return ToolResult(
                success=False,
                error="Could not extract restaurant name from description",
                metadata={"execution_time": time.time() - start_time}
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Place extraction failed: {str(e)}",
                metadata={"execution_time": time.time() - start_time}
            )

    def _extract_by_patterns(self, description: str, keywords: List[str], hashtags: List[str]) -> Optional[str]:
        """Extract restaurant name using regex patterns"""
        # Look for @NAME pattern
        at_pattern = r'@([A-Za-z0-9\s\-\.]+?)(?:\s{2,}|📍|#|$)'
        at_matches = re.findall(at_pattern, description)

        # More aggressive @ pattern
        at_pattern_aggressive = r'@\s*([A-Za-z0-9\s\-\.]+?)(?:\s+#|$)'
        at_matches.extend(re.findall(at_pattern_aggressive, description))

        # Look for 📍NAME pattern
        pin_pattern = r'📍\s*@?\s*([A-Za-z0-9\s\-\.\(\)]+?)(?:\s{2,}|#|$)'
        pin_matches = re.findall(pin_pattern, description)

        candidates = []
        for match in at_matches:
            name = match.strip()
            if len(name) > 2:
                candidates.append(name)

        for match in pin_matches:
            name = match.strip() if isinstance(match, str) else match
            if name and len(name) > 2:
                candidates.append(name)

        # Validate candidates
        hashtags_lower = [h.lower() for h in hashtags]
        for candidate in candidates:
            if self._validate_venue_name(candidate, keywords, hashtags_lower, description):
                return candidate

        return None

    def _extract_by_gemini(self, description: str, keywords: List[str]) -> Optional[str]:
        """Extract restaurant name using Gemini AI"""
        keyword_hint = ""
        if keywords:
            keyword_list = ", ".join(keywords)
            keyword_hint = f"""
IMPORTANT: The venue MUST be related to these search keywords: {keyword_list}
If NOT about food matching these keywords, return "Not found"."""

        prompt = f"""Extract the ACTUAL RESTAURANT or FOOD VENUE NAME from this TikTok description.

PRIORITY - Look for names in this order:
1. Names directly after 📍 symbol (e.g., 📍@RESTAURANT NAME or 📍RESTAURANT NAME)
2. Names after @ symbol (e.g., @RESTAURANT NAME)
3. Restaurant names in descriptive text mentioning the venue
4. Restaurant names in hashtags (e.g., #restaurantname or #misoaqiuqiu99)
5. If description is very sparse/minimal, extract ANY restaurant-like name from hashtags

Important Rules:
- Look for ALL CAPS or Title Case names which are often restaurant names
- Include numbers in the name (e.g., "QIU QIU 99" not just "QIU QIU")
- Return EXACTLY as it appears (preserve capitalization and spacing)
- DO NOT simplify or shorten names
- DO NOT return creator names, generic hashtags (fyp, viral, etc), or generic words
- If description is minimal (just hashtags or few words), do your best to extract a plausible restaurant name from the text
- If truly impossible to extract any restaurant name, return "Not found"
- If found, return the exact name only - nothing else{keyword_hint}

Description: {description}

Return ONLY the restaurant name (or "Not found"):"""

        try:
            response = self.model.generate_content(prompt)
            place_name = response.text.strip()

            if not place_name or place_name.lower() == "not found":
                return None

            return place_name
        except Exception:
            return None

    def _extract_from_hashtags(self, hashtags: List[str], keywords: List[str]) -> Optional[str]:
        """Extract restaurant name from hashtags as last resort"""
        generic_hashtags = [
            "fyp", "fyppppppppppppppppppppppp", "viral", "jogjafood", "kulinerjogja",
            "baksojogja", "makananjogja", "kulinerviral", "infojogja", "makanananakkos",
            "jogjaistimewa"
        ]

        candidate_hashtags = [
            tag for tag in hashtags
            if len(tag) > 4 and tag not in generic_hashtags and not tag.startswith("fyp")
        ]

        for hashtag in candidate_hashtags:
            potential_name = hashtag.replace("jogja", "").replace("resto", "").replace("rm", "").strip()
            if potential_name and len(potential_name) > 2:
                formatted_name = " ".join([word.capitalize() for word in potential_name.split()])
                if self._validate_venue_name(formatted_name, keywords, hashtags, ""):
                    return formatted_name

        return None

    def _validate_venue_name(self, name: str, keywords: List[str], hashtags: List[str], description: str) -> bool:
        """Validate if a name looks like a real venue name"""
        if not name or len(name) < 2:
            return False

        # Skip obvious non-food terms
        non_food_keywords = ["disini", "pong", "fashion", "brand", "follow", "like", "share"]
        name_lower = name.lower()
        for keyword in non_food_keywords:
            if keyword in name_lower:
                return False

        # If keywords provided, validate against them
        if keywords:
            desc_lower = description.lower()
            hashtags_lower = [h.lower() for h in hashtags]

            has_keywords = any(
                kw.lower() in desc_lower or any(kw.lower() in tag for tag in hashtags_lower)
                for kw in keywords
            )

            if not has_keywords:
                return False

        return True


# Register the tool when imported
from agent.tools import register_tool

register_tool("processing")(PlaceExtractionTool)
