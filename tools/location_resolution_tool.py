# Location Resolution Tool for Makanin bot agent system
# Resolves venue locations using Google Maps API

from typing import Dict, Any, Optional
from agent.tools import BaseTool, ToolInput, ToolResult
from api_clients import GoogleMapsClient
import config


class LocationResolutionTool(BaseTool):
    """Tool for resolving venue locations using Google Maps"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            name="location_resolution",
            description="Resolve venue locations using Google Maps to get coordinates and addresses",
            api_key=api_key
        )
        self.client = GoogleMapsClient(api_key=api_key or config.GOOGLE_MAPS_API_KEY)

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for tool parameters"""
        return {
            "type": "object",
            "properties": {
                "venue_name": {
                    "type": "string",
                    "description": "The name of the venue to search for (e.g., 'KEDAI QIU QIU 99')"
                },
                "location_hint": {
                    "type": "string",
                    "description": "Optional location hint to improve search accuracy (e.g., 'Yogyakarta')",
                    "nullable": True
                }
            },
            "required": ["venue_name"]
        }

    def validate_input(self, input_data: ToolInput) -> bool:
        """Validate input parameters"""
        params = input_data.parameters

        # Check required venue_name
        venue_name = params.get("venue_name")
        if not venue_name or not isinstance(venue_name, str) or not venue_name.strip():
            return False

        return True

    def execute(self, input_data: ToolInput) -> ToolResult:
        """Execute location resolution"""
        import time
        start_time = time.time()

        try:
            params = input_data.parameters
            venue_name = params["venue_name"].strip()
            location_hint = params.get("location_hint")

            print(f"📍 [Location Resolution] Searching for: '{venue_name}'")
            if location_hint:
                print(f"📍 [Location Resolution] Location hint: '{location_hint}'")

            # Build search query
            search_query = venue_name
            if location_hint:
                search_query += f" {location_hint}"

            # Search for the venue
            results = self.client.text_search(search_query)
            if not results:
                print(f"❌ [Location Resolution] No results found for '{venue_name}'")
                return ToolResult(
                    success=False,
                    error=f"Location not found for venue: {venue_name}",
                    metadata={
                        "venue_name": venue_name,
                        "search_query": search_query,
                        "execution_time": time.time() - start_time
                    }
                )

            # Get top result
            top_result = results[0]
            place_id = top_result.get("place_id")

            if not place_id:
                print(f"❌ [Location Resolution] No place_id found for '{venue_name}'")
                return ToolResult(
                    success=False,
                    error=f"No place ID found for venue: {venue_name}",
                    metadata={
                        "venue_name": venue_name,
                        "search_query": search_query,
                        "execution_time": time.time() - start_time
                    }
                )

            # Get detailed place information
            details = self.client.get_place_details(place_id)
            if not details or "geometry" not in details:
                print(f"❌ [Location Resolution] No details found for '{venue_name}'")
                return ToolResult(
                    success=False,
                    error=f"Could not get details for venue: {venue_name}",
                    metadata={
                        "venue_name": venue_name,
                        "place_id": place_id,
                        "execution_time": time.time() - start_time
                    }
                )

            # Extract location information
            geometry = details["geometry"]["location"]
            lat = geometry["lat"]
            lng = geometry["lng"]

            # Generate shareable link
            share_link = self.client.get_share_link(lat, lng, venue_name)

            # Build result data
            location_data = {
                "venue_name": venue_name,
                "latitude": lat,
                "longitude": lng,
                "address": details.get("formatted_address"),
                "maps_link": share_link,
                "place_id": place_id,
                "rating": details.get("rating"),
                "phone": details.get("formatted_phone_number"),
                "website": details.get("website"),
                "opening_hours": details.get("opening_hours")
            }

            print(f"✅ [Location Resolution] Found location for '{venue_name}'")
            print(f"📍 [Location Resolution] Address: {location_data['address']}")

            return ToolResult(
                success=True,
                data=location_data,
                metadata={
                    "venue_name": venue_name,
                    "search_query": search_query,
                    "execution_time": time.time() - start_time
                }
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Location resolution failed: {str(e)}",
                metadata={"execution_time": time.time() - start_time}
            )


# Register the tool when imported
from agent.tools import register_tool

register_tool("location")(LocationResolutionTool)
