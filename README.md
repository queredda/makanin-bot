#  Makanin - Viral Food Finder Bot

Makanin is a conversational AI bot that helps you discover viral food spots using natural language. Talk naturally in Indonesian or English, and the bot will find trending restaurants and food places with real-time weather information.


## Team
| Nama | NIM |
|--|--| 
| Flavia Hidayriamraata Pualam | 22/494376/TK54219 |
| Mahsa Quereda Bahjah | 22/503299/TK/54984 |

## Features

**Natural Language Understanding**
- Detects intent automatically (food finding vs. general chat)
- Extracts cuisine keywords, location hints, and constraints
- Supports both Bahasa Indonesia and English

**TikTok Integration**
- Real-time searches on TikTok for viral food content
- Powered by Ensemble Data API (official `ensembledata` library)
- Retrieves video metrics (likes, views, shares)
- Extracts place names from TikTok video descriptions using Gemini AI

 **Location & Weather**
- **Google Maps API**: Resolve locations and get shareable links
- **OpenWeather API**: Real-time weather at venues
- Shows temperature, humidity, wind speed, and weather conditions
 
**Smart Responses**
- Returns TikTok video links with engagement metrics
- Provides clickable Google Maps links to venues
- Shows current weather at each location
- Ranks results by TikTok virality (engagement)

**Discord Bot Integration**
- Natural conversation interface (no slash commands)
- Automatic intent detection
- Rich embeds with formatted results
- Real-time typing indicators
- Multi-turn conversation support

## Project Structure

```
makanin/
├── config.py           # Configuration and API keys
├── nlu.py              # Natural Language Understanding (Gemini-powered)
├── api_clients.py      # API client integrations (Ensemble Data, Google Maps, OpenWeather)
├── bot.py              # Main bot orchestrator
├── main.py             # CLI entry point (interactive terminal chat)
├── discord_bot.py      # Discord bot integration
├── discord_run.py      # Discord bot runner with pre-launch checks
├── requirements.txt    # Python dependencies
├── .env.example        # Template for environment variables
└── tests/              # Test suite
    ├── test_nlu.py
    ├── test_bot_integration.py
    ├── test_place_extraction.py
    ├── test_keyword_validation.py
    ├── test_tiktok_parsing.py
    └── test_complete_pipeline.py
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get API Credentials

You need to obtain credentials for the following services:

- **Google Gemini API**: https://ai.google.dev/ (free tier available)
- **Google Maps API**: https://developers.google.com/maps (enable Places API)
- **OpenWeather API**: https://openweathermap.org/api (free tier available)
- **Ensemble Data API**: https://ensembledata.com/ (TikTok data - sign up for token)

### 3. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
OPENWEATHER_API_KEY=your_openweather_api_key_here
ENSEMBLE_DATA_TOKEN=your_ensemble_data_token_here
DISCORD_TOKEN=your_discord_bot_token_here  # Optional: only for Discord bot
```

### 4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

The main dependency is the official **ensembledata** library for TikTok searches:
```bash
pip install ensembledata
```

## Usage

### Run the CLI Bot (Interactive Terminal)

```bash
python main.py
```

### Run the Discord Bot

1. **Get a Discord bot token:**
   - Visit [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application
   - Go to the "Bot" section and create a bot
   - Copy the bot token
   - Enable "Message Content Intent" in the Bot settings

2. **Add the token to your `.env` file:**
   ```
   DISCORD_TOKEN=your_discord_bot_token_here
   ```

3. **Invite the bot to your server:**
   - In the Developer Portal, go to OAuth2 > URL Generator
   - Select scopes: `bot`
   - Select bot permissions: `Send Messages`, `Read Message History`, `Embed Links`
   - Copy and visit the generated URL to invite the bot

4. **Run the Discord bot:**
   ```bash
   python discord_run.py
   ```

The Discord bot listens to all messages and automatically detects food search intent - no slash commands needed! Just chat naturally with the bot in any channel it has access to.

### Example Conversations

**Indonesian:**
```
You: Cariin bakso viral deket UGM dong
Makanin:
1. Bakso Pak X
🎥 TikTok: https://vm.tiktok.com/...
📍 Maps: https://www.google.com/maps/...
☁️ Cuaca: Cerah berawan, 31°C, Kelembaban 65%, Angin 5.2 km/j
📌 Jl. Kaliurang, Yogyakarta
```

**English:**
```
You: Find me good ramen near campus
Makanin:
1. Ramen Paradise
🎥 TikTok: https://vm.tiktok.com/...
📍 Maps: https://www.google.com/maps/...
☁️ Weather: Partly Cloudy, 28°C, Humidity 70%, Wind 4.8 km/h
📌 123 Main St, Campus Area
```

## How It Works

### Food-Finding Flow

1. **NLU Parsing**: Extract keywords, location, constraints (price, halal, etc.)
2. **Ensemble Search**: Query food venues matching criteria
3. **Place Resolution**: Extract place names from TikTok descriptions using Gemini
4. **Google Maps**: Get latitude/longitude and shareable links
5. **Weather**: Fetch current weather at each venue
6. **Response**: Format and return results with all information

### NLU Triggers

- **Food Finding**: "cariin", "carin", "find", "hunting", "recommend"
- **Price Constraints**: "murah" (cheap), "sedang" (medium), "mahal" (expensive)
- **Halal**: "halal", "no pork"
- **Location**: "deket" (near), "UGM", "Malioboro", etc.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│         User Input (Natural Language)               │
│    • Terminal (CLI)   • Discord Messages            │
└──────────────────────┬──────────────────────────────┘
                       ↓
        ┌──────────────────────────────┐
        │    NLU Module (Gemini AI)    │
        │ Extract: Intent, Keywords,   │
        │ Location, Constraints        │
        └──────────────┬───────────────┘
                       ↓
        ┌──────────────┴─────────────────┐
        │                                 │
   Intent = "find_food"           Intent = "chat"
        │                                 │
        ↓                                 ↓
┌───────────────────┐           ┌────────────────┐
│ Ensemble Data API │           │  Gemini Chat   │
│ (TikTok Search)   │           │  (Multi-turn)  │
└────────┬──────────┘           └───────┬────────┘
         ↓                               ↓
  Get TikTok Videos              Return Chat Reply
  (with engagement stats)               │
         │                               │
         ↓                               │
  ┌──────────────┐                      │
  │  Gemini AI   │                      │
  │  (Extract    │                      │
  │  restaurant  │                      │
  │  names from  │                      │
  │  TikTok)     │                      │
  └──────┬───────┘                      │
         ↓                               │
  ┌──────────────┐                      │
  │ Google Maps  │                      │
  │ (Resolve     │                      │
  │ locations +  │                      │
  │ share links) │                      │
  └──────┬───────┘                      │
         ↓                               │
  ┌──────────────┐                      │
  │ OpenWeather  │                      │
  │ (Get current │                      │
  │ weather at   │                      │
  │ venue)       │                      │
  └──────┬───────┘                      │
         ↓                               │
  Format Response                       │
  (with all info)                       │
         │                               │
         └───────────┬───────────────────┘
                     ↓
        ┌────────────────────────┐
        │   Return to User via:  │
        │   • CLI (terminal)     │
        │   • Discord (embeds)   │
        └────────────────────────┘
```

## Configuration

### Adjustable Settings

Edit `config.py`:

```python
DEFAULT_LANGUAGE = "id"      # Default language (id/en)
MAX_RESULTS = 5              # Max food venues to return
TIMEOUT = 10                 # API request timeout (seconds)
```

## TikTok Search Integration

Makanin uses the **Ensemble Data API** with the official `ensembledata` Python library to search TikTok for viral food content.

### How it Works

1. User enters a food query: "Cariin bakso viral deket UGM"
2. NLU extracts keywords ("bakso") and location ("UGM")
3. Ensemble Data API searches TikTok: `client.tiktok.full_keyword_search(keyword="bakso UGM", period="7")`
4. Returns trending TikTok videos about bakso near UGM from the last 7 days
5. For each video:
   - Extracts place name from video description using Gemini AI
   - Resolves address on Google Maps
   - Fetches current weather
   - Returns clickable links with engagement metrics

### Sample Ensemble Data API Usage

```python
from ensembledata.api import EDClient

client = EDClient(token="YOUR-TOKEN")

# Search for viral food content
result = client.tiktok.full_keyword_search(
    keyword="bakso viral",
    period="7",  # Last 7 days
)

print(result.data)  # List of TikTok videos
print(result.units_charged)  # API usage
```

## Error Handling

- If a venue location cannot be resolved, it's skipped with a note
- If weather data is unavailable, response shows location only
- If Ensemble Data API is down or returns no results, bot suggests trying different keywords
- If Gemini place extraction fails, uses the video author's name as fallback
- All API timeouts are handled gracefully with informative error messages

## Testing

### Run Tests

The project includes a comprehensive test suite in the `tests/` folder:

```bash
# Test NLU module
python tests/test_nlu.py

# Test place extraction from TikTok
python tests/test_place_extraction.py

# Test keyword validation
python tests/test_keyword_validation.py

# Test TikTok parsing
python tests/test_tiktok_parsing.py

# Test bot integration
python tests/test_bot_integration.py

# Test complete pipeline
python tests/test_complete_pipeline.py
```

### Example Test

```python
from nlu import NLUEngine
import config

nlu = NLUEngine(api_key=config.GEMINI_API_KEY)
slots = nlu.parse_user_input("Cariin bakso murah deket UGM dong")

print(slots.intent)        # "find_food"
print(slots.keywords)      # ["bakso"]
print(slots.location)      # "UGM"
print(slots.constraints)   # {"price": "cheap"}
```

## Future Enhancements

- [ ] Add user ratings and reviews
- [ ] Filter by operating hours
- [ ] Support for dietary restrictions
- [ ] Recommendation engine based on user preferences
- [ ] Multi-language support (more languages)
- [ ] Integration with delivery apps
- [ ] Caching for frequently searched locations
- [ ] Analytics dashboard

## Troubleshooting

**Missing API Keys**
- Check `.env` file is created and keys are set
- Ensure no extra spaces in `.env`

**Location Not Resolved**
- Try using full venue names in TikTok descriptions
- Check if place exists on Google Maps

**Rate Limiting**
- Add exponential backoff for API retries
- Check API quota in each service's dashboard

## License

MIT License - Feel free to use and modify!

