# API client integrations for Makanin bot.
# Handles: Ensemble Data, Google Maps, OpenWeather APIs.


import requests
from typing import List, Dict, Optional
from dataclasses import dataclass
from ensembledata.api import EDClient
import config
import google.generativeai as genai


@dataclass
class FoodVenue:
    """Data class for a food venue"""
    id: str
    name: str
    description: str
    tiktok_link: Optional[str] = None
    tiktok_description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    maps_link: Optional[str] = None
    address: Optional[str] = None
    rating: Optional[float] = None
    weather_summary: Optional[str] = None


@dataclass
class WeatherInfo:
    """Data class for weather information"""
    condition: str
    temperature: float
    humidity: int
    wind_speed: float
    rain_chance: int  # percentage


class EnsembleDataClient:
    """Client for Ensemble Data API - TikTok viral food finder"""

    def __init__(self, token: str):
        """Initialize with Ensemble Data API token"""
        self.client = EDClient(token=token)

    def search(self, keywords: List[str], location: Optional[str] = None, constraints: Optional[Dict] = None) -> List[Dict]:
        """
        Search for viral food venues on TikTok using keywords and location.

        Args:
            keywords: List of food/cuisine keywords to search
            location: Optional location hint (city, area, landmark)
            constraints: Optional dict with price, halal, etc.

        Returns:
            List of TikTok videos with venue information
        """
        # Combine keywords with location for better search
        search_query = " ".join(keywords)
        if location:
            search_query += f" {location}"

        try:
            # Search TikTok for food-related videos with keywords
            result = self.client.tiktok.full_keyword_search(
                keyword=search_query,
                period="7",
                sorting="1",
                country="id"
            )

            if not result or not result.data:
                return []

            # Convert TikTok results to venue format
            venues = []
            for idx, video in enumerate(result.data[:config.MAX_RESULTS]):
                # Extract aweme_info (the actual TikTok video data)
                aweme_info = video.get("aweme_info", {})
                author = aweme_info.get("author", {})
                stats = aweme_info.get("statistics", {})
                aweme_id = aweme_info.get("aweme_id", f"tiktok_{idx}")
                author_username = author.get("unique_id", "unknown")

                venue = {
                    "id": aweme_id,
                    "name": author.get("nickname", "Unknown Author"),
                    "description": aweme_info.get("desc", ""),
                    "tiktok_link": f"https://www.tiktok.com/@{author_username}/video/{aweme_id}",
                    "tiktok_description": aweme_info.get("desc", ""),
                    "author": author_username,
                    "likes": stats.get("digg_count", 0),
                    "views": stats.get("play_count", 0),
                    "shares": stats.get("share_count", 0),
                    "comments": stats.get("comment_count", 0),
                }
                venues.append(venue)

            # Log API usage for transparency
            if hasattr(result, 'units_charged'):
                print(f"Ensemble Data API units charged: {result.units_charged}")

            return venues

        except Exception as e:
            print(f"Error querying Ensemble Data API: {e}")
            return []


class GoogleMapsClient:
    """Client for Google Maps API"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api"

    def text_search(self, query: str, location: Optional[str] = None) -> List[Dict]:
        """
        Search for places using Google Maps Text Search.
        Query can be extracted from TikTok description or venue name.
        """
        params = {
            "query": query,
            "key": self.api_key,
        }

        try:
            response = requests.get(
                f"{self.base_url}/place/textsearch/json",
                params=params,
                timeout=config.TIMEOUT
            )
            response.raise_for_status()
            return response.json().get("results", [])
        except requests.RequestException as e:
            print(f"Error in Google Maps Text Search: {e}")
            return []

    def get_place_details(self, place_id: str) -> Optional[Dict]:
        """
        Get detailed information about a place (lat/lng, address, etc.)
        """
        params = {
            "place_id": place_id,
            "fields": "geometry,formatted_address,formatted_phone_number,website,rating,opening_hours",
            "key": self.api_key,
        }

        try:
            response = requests.get(
                f"{self.base_url}/place/details/json",
                params=params,
                timeout=config.TIMEOUT
            )
            response.raise_for_status()
            return response.json().get("result")
        except requests.RequestException as e:
            print(f"Error in Google Maps Place Details: {e}")
            return None

    def get_share_link(self, lat: float, lng: float, place_name: Optional[str] = None) -> str:
        """Generate a shareable Google Maps link for a location"""
        if place_name:
            return f"https://www.google.com/maps/search/{place_name.replace(' ', '+')}/@{lat},{lng},15z"
        return f"https://www.google.com/maps/place/{lat},{lng}"


class OpenWeatherClient:
    """Client for OpenWeather API with Gemini-enhanced weather summaries"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5"
        # Initialize Gemini for weather summarization
        genai.configure(api_key=config.GEMINI_API_KEY)
        self.gemini_model = genai.GenerativeModel(config.GEMINI_MODEL)

    def get_current_weather(self, lat: float, lng: float) -> Optional[WeatherInfo]:
        """
        Get current weather at a location.
        Returns temperature, condition, humidity, wind speed, rain chance.
        """
        params = {
            "lat": lat,
            "lon": lng,
            "appid": self.api_key,
            "units": "metric"
        }

        try:
            response = requests.get(
                f"{self.base_url}/weather",
                params=params,
                timeout=config.TIMEOUT
            )
            response.raise_for_status()
            data = response.json()

            # Extract weather info
            main = data.get("main", {})
            weather = data.get("weather", [{}])[0]
            wind = data.get("wind", {})
            clouds = data.get("clouds", {})

            return WeatherInfo(
                condition=weather.get("main", "Unknown"),
                temperature=main.get("temp", 0),
                humidity=main.get("humidity", 0),
                wind_speed=wind.get("speed", 0),
                rain_chance=clouds.get("cloudiness", 0)  # Simplified: use cloud coverage as proxy
            )
        except requests.RequestException as e:
            print(f"Error fetching weather: {e}")
            return None

    def format_weather_summary(self, weather: WeatherInfo, language: str = "id") -> str:
        """
        Format weather info into a natural, friendly summary with warnings.
        Uses Gemini to intelligently paraphrase and detect weather warnings.
        """
        # Build raw weather data string
        raw_weather = f"Condition: {weather.condition}, Temperature: {weather.temperature}°C, Humidity: {weather.humidity}%, Wind: {weather.wind_speed:.1f} km/h, Cloud coverage: {weather.rain_chance}%"

        # Use Gemini to paraphrase and enhance
        if language == "id":
            prompt = f"""Paraphrase this weather data into a friendly, natural Indonesian summary for someone going to a restaurant.
Include any weather warnings if needed (e.g., " Watchout rain possible" if humidity is high and clouds/rain likely).

Weather data: {raw_weather}

Requirements:
- Keep it SHORT (1-2 sentences max)
- Use natural language, not technical terms
- If rain is likely (humidity >80% or clouds >70%), add a warning like:  Bersiaplah untuk hujan/Watchout hujan mungkin
- Be conversational and friendly
- Use emoji appropriately
- For Indonesian output, use Indonesian names for conditions

Example output format:
"Cerah dengan suhu hangat 26°C, anginnya lembut. Tetap nyaman untuk makan di luar!"
or
"Mendung dengan kelembaban tinggi 85%,  Bersiaplah untuk hujan. Mungkin lebih baik di dalam rumah."

Return ONLY the paraphrased weather summary, nothing else:"""
        else:
            prompt = f"""Paraphrase this weather data into a friendly, natural English summary for someone going to a restaurant.
Include any weather warnings if needed (e.g., " Watchout rain possible" if humidity is high and clouds/rain likely).

Weather data: {raw_weather}

Requirements:
- Keep it SHORT (1-2 sentences max)
- Use natural language, not technical terms
- If rain is likely (humidity >80% or clouds >70%), add a warning like:  Watchout rain possible or  Bring an umbrella!
- Be conversational and friendly
- Use emoji appropriately

Example output format:
"Sunny and warm at 26°C with a gentle breeze. Perfect weather to dine outside!"
or
"Cloudy with high humidity 85%,  Watchout rain possible! Better to eat indoors."

Return ONLY the paraphrased weather summary, nothing else:"""

        try:
            response = self.gemini_model.generate_content(prompt)
            summary = response.text.strip()
            return summary if summary else self._fallback_summary(weather, language)
        except Exception as e:
            print(f"   Weather paraphrasing error: {e}")
            # Fallback to simple format if Gemini fails
            return self._fallback_summary(weather, language)

    def _fallback_summary(self, weather: WeatherInfo, language: str = "id") -> str:
        """Fallback weather summary if Gemini fails"""
        # Detect if rain is likely
        rain_warning = ""
        if weather.humidity > 80 or weather.rain_chance > 70:
            rain_warning = "  Watchout hujan!" if language == "id" else "  Watchout rain!"

        if language == "id":
            return f"{weather.condition}, {weather.temperature}°C, Kelembaban {weather.humidity}%, Angin {weather.wind_speed:.1f} km/j{rain_warning}"
        else:
            return f"{weather.condition}, {weather.temperature}°C, Humidity {weather.humidity}%, Wind {weather.wind_speed:.1f} km/h{rain_warning}"
