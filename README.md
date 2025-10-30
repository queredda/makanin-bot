# Makanin - Bot Pencari Makanan Viral

Makanin adalah bot AI percakapan yang membantu kamu menemukan tempat makan viral menggunakan bahasa alami. Bicara secara
natural dalam Bahasa Indonesia atau English, dan bot akan menemukan restoran trending serta tempat makan dengan
informasi cuaca real-time.

**Makanin - Viral Food Finder Bot**
Makanin is a conversational AI bot that helps you discover viral food spots using natural language. Talk naturally in Indonesian or English, and the bot will find trending restaurants and food places with real-time weather information.

## Tim / Team

| Nama / Name                  | NIM                |
|------------------------------|--------------------|
| Flavia Hidayriamraata Pualam | 22/494376/TK54219  |
| Mahsa Quereda Bahjah         | 22/503299/TK/54984 |

## Fitur Utama / Main Features

### Pemahaman Bahasa Alami / Natural Language Understanding

- Deteksi intent otomatis (pencarian makanan vs chat umum)
- Ekstrak keyword makanan, lokasi, dan constraint
- Support Bahasa Indonesia dan English

### Integrasi TikTok / TikTok Integration

- Pencarian real-time di TikTok untuk konten makanan viral
- Powered by Ensemble Data API
- Mengambil metrik video (likes, views, shares)
- Ekstrak nama tempat dari deskripsi TikTok menggunakan Gemini AI

### Lokasi & Cuaca / Location & Weather

- **Google Maps API**: Resolusi lokasi dan link yang bisa dishare
- **OpenWeather API**: Cuaca real-time di lokasi tempat makan
- Menampilkan suhu, humidity, wind speed, dan kondisi cuaca

### Respons Cerdas / Smart Responses

- Return link video TikTok dengan metrik engagement
- Sediakan link Google Maps yang bisa diklik
- Tampilkan cuaca saat ini di setiap lokasi
- Rank hasil berdasarkan virality TikTok (engagement)

### Bot Discord / Discord Bot Integration

- Interface percakapan natural (tidak perlu slash commands)
- Deteksi intent otomatis
- Rich embeds dengan hasil terformat
- Typing indicators real-time
- Support percakapan multi-turn

### Memori Persisten / Persistent Memory

- **Redis Integration**: Simpan percakapan selama 7 hari
- **Session Management**: Ingat preferensi user selama 24 jam
- **Tool History**: Track semua penggunaan tools
- **Fallback**: Otomatis fallback ke in-memory jika Redis tidak available

## Struktur Proyek / Project Structure

```
makanin-bot/
├── config.py                    # Konfigurasi dan API keys
├── bot.py                       # Main bot implementation
├── discord_run.py               # Discord bot launcher dengan setup checks
├── api_clients.py               # External API integrations
├── clear_redis.py               # Redis cleanup utility
├── agent/                       # Agent system dengan tools
│   ├── agent.py                # Agent orchestrator utama
│   ├── memory.py               # Memory management interface
│   ├── redis_memory.py         # Redis backend untuk persistent storage
│   ├── tools.py                # Tool registry dan execution
│   └── prompts.py              # Prompt templates untuk AI
├── tools/                       # Agent tools (modular)
│   ├── __init__.py
│   ├── nlu_tool.py             # Natural Language Understanding
│   ├── tiktok_search_tool.py   # Pencarian TikTok
│   ├── location_resolution_tool.py # Resolusi lokasi Google Maps
│   ├── weather_tool.py         # Cuaca dari OpenWeather
│   ├── place_extraction_tool.py # Ekstrak nama tempat
│   └── conversation_tool.py    # Chat percakapan
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── unit/                   # Unit tests
│   │   ├── __init__.py
│   │   ├── test_agent.py
│   │   ├── test_memory.py
│   │   ├── test_nlu_tool.py
│   │   ├── test_conversation_tool.py
│   │   ├── test_place_extraction.py
│   │   └── test_tools.py
│   └── functional/             # Integration tests
│       ├── __init__.py
│       ├── test_agent_integration.py
│       └── test_tool_integration.py
├── logs/                        # Application logs
├── .env.example                 # Environment template
├── .env                         # Environment variables (gitignored)
└── requirements.txt             # Python dependencies
```

## Persyaratan Sistem / System Requirements

### Python & Dependencies

- Python 3.8+
- Libraries di `requirements.txt` termasuk:
    - `python-dotenv`: Environment variable management
    - `google-generativeai`: Gemini AI untuk NLU dan place extraction
    - `ensembledata`: TikTok search API
    - `discord.py`: Discord bot integration
    - `redis`: Persistent memory storage
    - `requests`: HTTP client untuk external APIs

### External Services / Layanan Eksternal

- **Redis Server** (untuk persistent memory)
- **Google Gemini API Key** (NLU & place extraction)
- **Google Maps API Key** (location resolution)
- **OpenWeather API Key** (weather data)
- **Ensemble Data Token** (TikTok search)
- **Discord Bot Token** (Discord integration)

### Redis Installation
```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server

# Verify Redis
redis-cli ping  # Should return: PONG
```

## Instalasi / Installation

### 1. Clone Repository
```bash
git clone https://github.com/queredda/makanin-bot.git
cd makanin-bot
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Copy `.env.example` ke `.env` dan isi dengan API keys:

```bash
# Google AI
GEMINI_API_KEY=your_gemini_api_key

# External APIs
GOOGLE_MAPS_API_KEY=your_maps_api_key
OPENWEATHER_API_KEY=your_weather_api_key
ENSEMBLE_DATA_TOKEN=your_ensemble_token

# Discord
DISCORD_TOKEN=your_discord_bot_token

# Redis Configuration (Optional)
MEMORY_BACKEND=redis          # atau "memory" untuk fallback
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
SESSION_TTL=86400            # 24 hours
CONVERSATION_TTL=604800      # 7 days
```

### 4. Start Redis Server
```bash
# Jika menggunakan Redis
redis-server
# atau
brew services start redis  # macOS
```

## Cara Penggunaan / Usage

### Discord Bot

```bash
python discord_run.py
```

### Contoh Percakapan / Example Conversations

**Bahasa Indonesia:**
```
User: cariin bakso enak di jogja
Makanin: Aku temukan beberapa bakso viral di Jogja! Cek ini:

#1 🍽️ Bakso Pak Min
🎥 Viral di TikTok: [video link]
📍 Alamat: Jl. Malioboro No. 123, Jogja
🗺️ Maps: [maps link]
🌤️ Cuaca: Cerah, 28°C

#2 🍽️ Bakso Mercon
🎥 Viral di TikTok: [video link]
📍 Alamat: Jl. Gejayan No. 45, Jogja
🗺️ Maps: [maps link]
🌤️ Cuaca: Berawan, 26°C
```

**English:**
```
User: find me good ramen near campus
Makanin: I found some viral ramen spots near campus! Check these out:

#1 🍽️ Ramen Ichiran
🎥 Viral on TikTok: [video link]
📍 Address: Near Campus Area
🗺️ Maps: [maps link]
🌤️ Weather: Partly Cloudy, 22°C
```

## Konfigurasi / Configuration

### Environment Variables
```python
# API Keys (Required)
GEMINI_API_KEY = "your_gemini_key"
GOOGLE_MAPS_API_KEY = "your_maps_key"
OPENWEATHER_API_KEY = "your_weather_key"
ENSEMBLE_DATA_TOKEN = "your_ensemble_token"
DISCORD_TOKEN = "your_discord_token"

# Redis Configuration (Optional)
MEMORY_BACKEND = "redis"  # "redis" atau "memory"
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = None  # Jika menggunakan password

# TTL Settings (Optional)
SESSION_TTL = 86400  # 24 jam
CONVERSATION_TTL = 604800  # 7 hari
TOOL_EXECUTION_TTL = 604800  # 7 hari

# Bot Settings (Optional)
DEFAULT_LANGUAGE = "id"  # "id" atau "en"
MAX_RESULTS = 10
GEMINI_MODEL = "gemini-2.5-flash"
```

## Arsitektur Sistem / System Architecture

### Agent-Based Architecture

```
User Message
       ↓
   [NLU Tool] - Pahami intent & ekstrak entities
       ↓
   [Agent] - Pilih tools yang dibutuhkan secara dinamis
       ↓
┌─────────────────────────────────┐
│  Tool Execution (Parallel)      │
│  • TikTok Search Tool           │
│  • Location Resolution Tool     │
│  • Weather Tool                 │
│  • Place Extraction Tool        │
└─────────────────────────────────┘
       ↓
   [Format Response] - Gabung semua hasil
       ↓
   User Response (Natural language)
```

### Memory Architecture

```
┌─────────────────────────────────┐
│         Redis (Persistent)       │
├─────────────────────────────────┤
│ • Sessions (24h TTL)            │
│ • Conversations (7d TTL)        │
│ • Tool Executions (7d TTL)      │
└─────────────────────────────────┘
              ↕
┌─────────────────────────────────┐
│      In-Memory (Cache)          │
├─────────────────────────────────┤
│ • Active sessions               │
│ • Recent conversations          │
│ • Tool results cache            │
└─────────────────────────────────┘
```

## Integrasi Redis / Redis Integration

### Fitur Persisten / Persistent Features

- **7-Day Conversation Memory**: Bot ingat percakapan selama seminggu
- **24-Hour Sessions**: Ingat preferensi user (bahasa, intent terakhir)
- **Tool Execution History**: Track semua tools yang digunakan
- **Automatic Cleanup**: Data otomatis dihapus setelah TTL expired

### Redis Management
```bash
# Check Redis status
redis-cli ping

# Check all keys
redis-cli keys "makanin:*"

# Monitor memory usage
redis-cli info memory

# Clear all Makanin data
python clear_redis.py

# Clear specific data types
python clear_redis.py --sessions-only     # Hapus session data saja
python clear_redis.py --conversations-only # Hapus percakapan saja
python clear_redis.py --tools-only        # Hapus tool execution history
```

### Redis Features Implementation

- **ContextManager**: Interface abstrak untuk memory management
- **RedisMemory**: Implementasi Redis dengan auto-reconnection
- **InMemoryMemory**: Fallback storage saat Redis tidak available
- **Automatic Cleanup**: TTL-based expiration untuk semua data
- **Error Handling**: Graceful fallback saat Redis connection failed

### Logging & Monitoring

```bash
# Check application logs
tail -f logs/makanin.log

# Monitor Redis activity
grep "Redis" logs/makanin.log

# Monitor tool executions
grep "Tool Execution" logs/makanin.log

# Monitor Discord bot activity
grep "Discord" logs/makanin.log
```

### Log Categories

- **Agent**: Agent orchestration dan decision making
- **Memory**: Redis operations dan fallback mechanisms
- **Tools**: Individual tool execution dan errors
- **Discord**: Bot interactions dan user messages
- **API**: External API calls dan responses

## Troubleshooting

### Masalah Umum / Common Issues

**Redis Connection Failed:**

```bash
# Start Redis server
redis-server

# Check if Redis is running
redis-cli ping
```

**API Key Issues:**

- Pastikan semua API keys valid dan active
- Check rate limits untuk setiap API service
- Verify environment variables di .env file

**Bot Not Responding:**

- Check Discord bot permissions di server
- Verify bot memiliki `Message Content Intent` enabled
- Check log output untuk error messages

### Error Messages / Pesan Error

```
[Agent] Error processing message: Connection failed
→ Redis tidak tersedia, bot akan fallback ke in-memory

[Redis Memory] Failed to connect to Redis: Connection refused
→ Start Redis server atau set MEMORY_BACKEND=memory

[Tool] Execution failed: API quota exceeded
→ Check API quota dan rate limits
```

## Development

### Project Architecture

- **Agent-Based System**: Modular tool execution dengan dynamic selection
- **Tool Registry**: Centralized tool management di `agent/tools.py`
- **Memory Abstraction**: Pluggable memory backends (Redis/In-Memory)
- **Error Resilience**: Auto-fallback dan graceful error handling
- **Logging**: Comprehensive logging dengan structured output

### Adding New Tools

1. Create new tool class di `tools/` directory
2. Extend `BaseTool` class dari `tools/base_tool.py`
3. Implement `execute()` method dengan proper error handling
4. Add tool metadata (name, description, parameters)
5. Import di `agent/agent.py` di `_register_tools()`
6. Add unit tests di `tests/unit/test_new_tool.py`

### Testing Framework

```bash
# Run all tests
python -m pytest tests/ -v

# Run unit tests only
python -m pytest tests/unit/ -v

# Run integration tests only
python -m pytest tests/functional/ -v

# Run specific test file
python -m pytest tests/unit/test_agent.py -v

# Run with coverage
python -m pytest tests/ --cov=agent --cov=tools --cov-report=html

# Test Redis connection
python -c "from agent.memory import ContextManager; cm = ContextManager()"

# Test bot components
python -c "from bot import MakaninBot; print('Bot import successful')"
```

### Test Structure

- **Unit Tests**: Test individual components dan tools
- **Integration Tests**: Test agent workflows dan tool interactions
- **Memory Tests**: Test Redis dan in-memory storage
- **NLU Tests**: Test natural language understanding
- **Tool Tests**: Test individual tool functionality

## License

Project ini dibuat untuk tujuan akademis dan pembelajaran Pemrosesan Bahasa Alami.
