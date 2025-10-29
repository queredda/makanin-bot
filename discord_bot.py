# Discord bot integration for Makanin.

import discord
from discord.ext import commands
from bot import MakaninBot
import config
import traceback


# Set up intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Create bot
bot_discord = commands.Bot(command_prefix="!", intents=intents)

# Initialize Makanin bot
makanin = MakaninBot()

# Color scheme for embeds
COLORS = {
    "success": discord.Color.green(),
    "info": discord.Color.blue(),
    "warning": discord.Color.orange(),
    "error": discord.Color.red(),
}


@bot_discord.event
async def on_ready():
    """Called when bot successfully connects to Discord"""
    print(f"Discord bot logged in as {bot_discord.user}")
    print(f"Bot is ready and connected!")
    await bot_discord.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.playing,
            name="Chat with me naturally!"
        )
    )


@bot_discord.event
async def on_message(message: discord.Message):
    """
    Listen to all messages and respond intelligently.
    Automatically detects food search intent using NLU.
    """
    # Don't respond to bot messages
    if message.author.bot:
        return

    # Don't respond to system messages
    if message.author == bot_discord.user:
        return

    # Ignore messages that are just emojis or very short
    if len(message.content.strip()) < 2:
        return

    # Show typing indicator while processing
    async with message.channel.typing():
        try:
            # Use NLU to parse the user input
            slots = makanin.nlu.parse_user_input(message.content)

            # Get bot response
            response = makanin.chat(message.content)

            # Check if this is a food finding response
            if slots.intent == "find_food" and response:
                # Send as formatted embeds
                await send_food_results(message, response)
            else:
                # General conversation response
                await send_chat_response(message, response)

        except Exception as e:
            print(f"Error processing message: {e}")
            traceback.print_exc()
            error_embed = discord.Embed(
                title="Oops! Something went wrong",
                description=f"Error: {str(e)}",
                color=COLORS["error"]
            )
            try:
                await message.reply(embed=error_embed, mention_author=False)
            except:
                pass


async def send_chat_response(message: discord.Message, response: str):
    """Send a general chat response"""
    try:
        # Split response if too long
        if len(response) > 2000:
            chunks = [response[i:i + 2000] for i in range(0, len(response), 2000)]
            for chunk in chunks:
                embed = discord.Embed(
                    description=chunk,
                    color=COLORS["info"]
                )
                embed.set_author(
                    name="Makanin"
                )
                await message.reply(embed=embed, mention_author=False)
        else:
            embed = discord.Embed(
                description=response,
                color=COLORS["info"]
            )
            embed.set_author(
                name="Makanin"
            )
            await message.reply(embed=embed, mention_author=False)
    except Exception as e:
        print(f"Error sending chat response: {e}")
        traceback.print_exc()


async def send_food_results(message: discord.Message, response: str):
    """Format and send food results as embeds"""
    try:
        # DEBUG: Print the raw response to see what we're working with
        print("\n" + "="*60)
        print("DEBUG: Raw response from bot.py:")
        print("="*60)
        print(response)
        print("="*60 + "\n")

        # Split the response into lines
        lines = response.strip().split("\n")

        print(f"DEBUG: Total lines: {len(lines)}")
        for i, line in enumerate(lines):
            print(f"Line {i}: [{line}]")

        # Main header embed
        header_embed = discord.Embed(
            title="Viral Food Spots Found!",
            description="Ini pilihan enak yang aku temukan buat kamu!",
            color=COLORS["success"]
        )
        header_embed.set_author(
            name="Makanin"
        )
        await message.reply(embed=header_embed, mention_author=False)

        # Parse and format each venue
        venues = []
        current_venue_name = None
        current_venue_data = {}

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Skip header lines
            if any(line.startswith(s) for s in ["Ini", "Here", "Yay", "Found", "━━", "✨"]):
                continue

            # Check if this is a venue number line (e.g., "#1 🍽️ Restaurant Name")
            if line.startswith("#") and "🍽️" in line:
                print(f"DEBUG: Found venue line: {line}")
                # Save previous venue if exists
                if current_venue_name:
                    venues.append({
                        "name": current_venue_name,
                        "data": current_venue_data.copy()
                    })

                # Extract new venue name
                parts = line.split("🍽️", 1)
                if len(parts) > 1:
                    current_venue_name = parts[1].strip()
                    current_venue_data = {}
                    print(f"DEBUG: Extracted venue name: {current_venue_name}")

            # Parse venue details
            elif current_venue_name:  # Only parse if we have a current venue
                if "🎥" in line and "TikTok" in line:
                    # Extract TikTok link
                    parts = line.split(":", 1)
                    if len(parts) > 1:
                        current_venue_data["tiktok"] = parts[1].strip()
                        print(f"DEBUG: Added TikTok: {parts[1].strip()[:50]}...")

                elif "🗺️" in line and "Maps" in line:
                    # Extract Maps link
                    parts = line.split(":", 1)
                    if len(parts) > 1:
                        current_venue_data["maps"] = parts[1].strip()
                        print(f"DEBUG: Added Maps: {parts[1].strip()[:50]}...")

                elif "🌤️" in line or "☁️" in line:
                    # Extract weather
                    if "Cuaca:" in line or "Weather:" in line:
                        parts = line.split(":", 1)
                        if len(parts) > 1:
                            current_venue_data["weather"] = parts[1].strip()
                            print(f"DEBUG: Added Weather: {parts[1].strip()}")

                elif "📍" in line and "Maps" not in line:
                    # Extract address
                    address = line.replace("📍", "").strip()
                    current_venue_data["address"] = address
                    print(f"DEBUG: Added Address: {address}")

        # Add the last venue
        if current_venue_name:
            venues.append({
                "name": current_venue_name,
                "data": current_venue_data.copy()
            })

        print(f"DEBUG: Total venues found: {len(venues)}")

        # Send embeds for each venue
        if venues:
            for venue in venues:
                await send_venue_embed(message, venue["name"], venue["data"])
        else:
            # If no venues were parsed, send raw response as fallback
            print(f"WARNING: Could not parse venues from response")
            print(f"Response length: {len(response)}")
            fallback_embed = discord.Embed(
                description=response,
                color=COLORS["info"]
            )
            await message.reply(embed=fallback_embed, mention_author=False)

    except Exception as e:
        print(f"Error parsing food results: {e}")
        traceback.print_exc()
        # Fallback: just send the raw response
        try:
            embed = discord.Embed(
                description=response,
                color=COLORS["info"]
            )
            await message.reply(embed=embed, mention_author=False)
        except:
            pass


async def send_venue_embed(message: discord.Message, venue_name: str, data: dict):
    """Send a formatted embed for a single venue"""
    try:
        embed = discord.Embed(
            title=venue_name,
            color=COLORS["success"]
        )

        if data.get("address"):
            embed.add_field(
                name="Location",
                value=data["address"],
                inline=False
            )

        if data.get("weather"):
            embed.add_field(
                name="Weather",
                value=data["weather"],
                inline=False
            )

        if data.get("maps"):
            embed.add_field(
                name="Google Maps",
                value=f"[View on Maps]({data['maps']})",
                inline=False
            )

        if data.get("tiktok"):
            embed.add_field(
                name="TikTok Video",
                value=f"[Watch Video]({data['tiktok']})",
                inline=False
            )

        embed.set_footer(text="Tap the links to explore!")
        await message.reply(embed=embed, mention_author=False)
    except Exception as e:
        print(f"Error sending venue embed: {e}")
        traceback.print_exc()


async def main():
    """Start the Discord bot"""
    if not config.DISCORD_TOKEN:
        print("Error: DISCORD_TOKEN not found in .env file")
        print("Please add DISCORD_TOKEN to your .env file")
        return

    print("\n" + "=" * 60)
    print("Starting Makanin Discord Bot...")
    print("=" * 60)
    print("Listening to all messages (no slash commands needed!)")
    print("=" * 60 + "\n")

    try:
        async with bot_discord:
            await bot_discord.start(config.DISCORD_TOKEN)
    except Exception as e:
        print(f"Failed to start bot: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
