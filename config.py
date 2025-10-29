import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
ENSEMBLE_DATA_TOKEN = os.getenv("ENSEMBLE_DATA_TOKEN")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Bot settings
DEFAULT_LANGUAGE = "id"  # Bahasa Indonesia
MAX_RESULTS = 10
TIMEOUT = 10  # seconds

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

REQUIRED_KEYS = {
    "GEMINI_API_KEY": GEMINI_API_KEY,
    "GOOGLE_MAPS_API_KEY": GOOGLE_MAPS_API_KEY,
    "OPENWEATHER_API_KEY": OPENWEATHER_API_KEY,
    "ENSEMBLE_DATA_TOKEN": ENSEMBLE_DATA_TOKEN,
}

missing_keys = [key for key, value in REQUIRED_KEYS.items() if not value]
if missing_keys:
    print(f"Missing API keys: {', '.join(missing_keys)}")
    print("Please set these in your .env file")
