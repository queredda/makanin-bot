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

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
REDIS_USE_MEMORY_FALLBACK = os.getenv("REDIS_USE_MEMORY_FALLBACK", "true").lower() == "true"

# Memory Configuration
MEMORY_BACKEND = os.getenv("MEMORY_BACKEND", "redis")  # "redis" or "memory"
SESSION_TTL = int(os.getenv("SESSION_TTL", 86400))  # 24 hours in seconds
CONVERSATION_TTL = int(os.getenv("CONVERSATION_TTL", 604800))  # 7 days in seconds
TOOL_EXECUTION_TTL = int(os.getenv("TOOL_EXECUTION_TTL", 604800))  # 7 days in seconds

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
