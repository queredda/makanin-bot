# TikTok Search Tool for Makanin bot agent system
# Searches for viral food content on TikTok using Ensemble Data API

from typing import List, Dict, Any, Optional
from agent.tools import BaseTool, ToolInput, ToolResult
from api_clients import EnsembleDataClient
import config


class TikTokSearchTool(BaseTool):
    """Tool for searching viral food content on TikTok"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            name="tiktok_search",
            description="Search for viral food content on TikTok based on keywords and location",
            api_key=api_key
        )
        self.client = EnsembleDataClient(token=api_key or config.ENSEMBLE_DATA_TOKEN)

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for tool parameters"""
        return {
            "type": "object",
            "properties": {
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of food/cuisine keywords to search for (e.g., ['bakso', 'ramen'])"
                },
                "location": {
                    "type": "string",
                    "description": "Optional location hint for search (e.g., 'Yogyakarta', 'Jakarta')",
                    "nullable": True
                },
                "constraints": {
                    "type": "object",
                    "description": "Optional constraints for search (price, halal, etc.)",
                    "properties": {
                        "price": {"type": "string"},
                        "halal": {"type": "boolean"},
                        "nearby": {"type": "boolean"},
                        "open_now": {"type": "boolean"}
                    },
                    "nullable": True
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 10
                }
            },
            "required": ["keywords"]
        }

    def validate_input(self, input_data: ToolInput) -> bool:
        """Validate input parameters"""
        params = input_data.parameters

        # Check required keywords
        if not params.get("keywords") or not isinstance(params["keywords"], list):
            return False

        # Validate keywords are strings
        keywords = params["keywords"]
        if not all(isinstance(kw, str) and kw.strip() for kw in keywords):
            return False

        # Validate max_results if provided
        max_results = params.get("max_results", config.MAX_RESULTS)
        if not isinstance(max_results, int) or max_results <= 0:
            return False

        return True

    def execute(self, input_data: ToolInput) -> ToolResult:
        """Execute TikTok search"""
        import time
        start_time = time.time()

        try:
            params = input_data.parameters
            keywords = params["keywords"]
            location = params.get("location")
            constraints = params.get("constraints", {})
            max_results = params.get("max_results", config.MAX_RESULTS)

            print(f"🔍 [TikTok Search] Keywords: {keywords}, Location: {location}")
            print(f"🔍 [TikTok Search] Constraints: {constraints}")

            # Call Ensemble Data API
            results = self.client.search(
                keywords=keywords,
                location=location,
                constraints=constraints
            )

            if not results:
                print("📭 [TikTok Search] No results found")
                return ToolResult(
                    success=True,
                    data=[],
                    metadata={
                        "keywords": keywords,
                        "location": location,
                        "constraints": constraints,
                        "total_results": 0,
                        "api_units_charged": 0
                    }
                )

            # Limit results
            limited_results = results[:max_results]
            print(f"🎉 [TikTok Search] Found {len(limited_results)} results")

            # Convert to serializable format
            serializable_results = []
            for result in limited_results:
                serializable_results.append({
                    "id": result.get("id", ""),
                    "name": result.get("name", ""),
                    "description": result.get("description", ""),
                    "tiktok_link": result.get("tiktok_link"),
                    "tiktok_description": result.get("tiktok_description", ""),
                    "author": result.get("author", ""),
                    "likes": result.get("likes", 0),
                    "views": result.get("views", 0),
                    "shares": result.get("shares", 0),
                    "comments": result.get("comments", 0)
                })

            return ToolResult(
                success=True,
                data=serializable_results,
                metadata={
                    "keywords": keywords,
                    "location": location,
                    "constraints": constraints,
                    "total_results": len(limited_results),
                    "execution_time": time.time() - start_time
                }
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"TikTok search failed: {str(e)}",
                metadata={"execution_time": time.time() - start_time}
            )


# Register the tool when imported
from agent.tools import register_tool

register_tool("search")(TikTokSearchTool)
