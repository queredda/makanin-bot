# Weather Tool for Makanin bot agent system
# Gets weather information for specific locations

from typing import Dict, Any, Optional
from agent.tools import BaseTool, ToolInput, ToolResult
from api_clients import OpenWeatherClient
import config


class WeatherTool(BaseTool):
    """Tool for getting weather information at specific locations"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            name="weather",
            description="Get current weather information for a specific location",
            api_key=api_key
        )
        self.client = OpenWeatherClient(api_key=api_key or config.OPENWEATHER_API_KEY)

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for tool parameters"""
        return {
            "type": "object",
            "properties": {
                "latitude": {
                    "type": "number",
                    "description": "Latitude coordinate of the location"
                },
                "longitude": {
                    "type": "number",
                    "description": "Longitude coordinate of the location"
                },
                "language": {
                    "type": "string",
                    "description": "Language for weather summary ('id' for Indonesian, 'en' for English)",
                    "enum": ["id", "en"],
                    "default": "id"
                }
            },
            "required": ["latitude", "longitude"]
        }

    def validate_input(self, input_data: ToolInput) -> bool:
        """Validate input parameters"""
        params = input_data.parameters

        # Check required coordinates
        lat = params.get("latitude")
        lng = params.get("longitude")

        if not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
            return False

        # Validate coordinate ranges
        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            return False

        # Validate language if provided
        language = params.get("language", "id")
        if language not in ["id", "en"]:
            return False

        return True

    def execute(self, input_data: ToolInput) -> ToolResult:
        """Execute weather lookup"""
        import time
        start_time = time.time()

        try:
            params = input_data.parameters
            lat = params["latitude"]
            lng = params["longitude"]
            language = params.get("language", "id")

            print(f"🌤️ [Weather Tool] Getting weather for coordinates: ({lat}, {lng})")

            # Get weather data
            weather_info = self.client.get_current_weather(lat, lng)
            if not weather_info:
                print(f"❌ [Weather Tool] Could not get weather data for coordinates ({lat}, {lng})")
                return ToolResult(
                    success=False,
                    error=f"Could not get weather data for coordinates: ({lat}, {lng})",
                    metadata={
                        "latitude": lat,
                        "longitude": lng,
                        "execution_time": time.time() - start_time
                    }
                )

            # Format weather summary
            weather_summary = self.client.format_weather_summary(weather_info, language=language)
            print(f"✅ [Weather Tool] Weather summary: {weather_summary}")

            # Build result data
            weather_data = {
                "coordinates": {"latitude": lat, "longitude": lng},
                "condition": weather_info.condition,
                "temperature": weather_info.temperature,
                "humidity": weather_info.humidity,
                "wind_speed": weather_info.wind_speed,
                "rain_chance": weather_info.rain_chance,
                "summary": weather_summary,
                "language": language
            }

            return ToolResult(
                success=True,
                data=weather_data,
                metadata={
                    "coordinates": (lat, lng),
                    "language": language,
                    "execution_time": time.time() - start_time
                }
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Weather lookup failed: {str(e)}",
                metadata={"execution_time": time.time() - start_time}
            )


# Register the tool when imported
from agent.tools import register_tool

register_tool("weather")(WeatherTool)
