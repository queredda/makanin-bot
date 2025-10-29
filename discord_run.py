"""
Simple starter script for running Makanin Discord bot.
Run this to start the bot: python discord_run.py
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

import config
from discord_bot import main
import asyncio


def check_setup():
    """Verify all required configurations before starting"""
    print("\n" + "=" * 60)
    print("Makanin Discord Bot - Pre-Launch Check")
    print("=" * 60)

    required = {
        "DISCORD_TOKEN": config.DISCORD_TOKEN,
        "GEMINI_API_KEY": config.GEMINI_API_KEY,
        "GOOGLE_MAPS_API_KEY": config.GOOGLE_MAPS_API_KEY,
        "OPENWEATHER_API_KEY": config.OPENWEATHER_API_KEY,
        "ENSEMBLE_DATA_TOKEN": config.ENSEMBLE_DATA_TOKEN,
    }

    missing = [k for k, v in required.items() if not v]

    if missing:
        print("Missing required environment variables:")
        for key in missing:
            print(f"   - {key}")
        print("\nPlease add these to your .env file:")
        print("   See DISCORD_SETUP.md for detailed instructions")
        return False

    print("All API keys configured!")
    print("Ready to start Discord bot\n")
    return True


if __name__ == "__main__":
    if check_setup():
        asyncio.run(main())
    else:
        sys.exit(1)
