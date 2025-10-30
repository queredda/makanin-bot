# Updated MakaninBot using the new agent framework
# Replaces hardcoded flow with intelligent LLM-powered tool selection

import discord
from discord.ext import commands
import asyncio
import config
from agent.agent import MakaninAgent


class MakaninBot(commands.Bot):
    """Discord bot powered by the Makanin Agent system"""

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )

        # Initialize the agent system
        self.agent = MakaninAgent()
        self.is_ready = False

    async def on_ready(self):
        """Called when the bot is ready"""
        print(f"🤖 {self.user.name} has connected to Discord!")
        print(f"📊 Agent status: {self.agent.get_tool_status()}")
        self.is_ready = True

    async def on_message(self, message):
        """Handle incoming messages"""
        # Don't respond to own messages
        if message.author == self.user:
            return

        # Don't respond to bot messages
        if message.author.bot:
            return

        # Check if the bot is mentioned or if we're in a DM
        should_respond = (
                isinstance(message.channel, discord.DMChannel) or
                self.user.mentioned_in(message) or
                message.content.lower().startswith("makanin")
        )

        if not should_respond:
            return

        try:
            # Show typing indicator while processing
            async with message.channel.typing():
                # Process the message using the agent
                response = await self.agent.process_message(
                    user_id=str(message.author.id),
                    user_message=message.content
                )

                # Send the response
                if len(response) > 2000:  # Discord message limit
                    # Split long messages
                    parts = [response[i:i + 2000] for i in range(0, len(response), 2000)]
                    for part in parts:
                        await message.reply(part)
                else:
                    await message.reply(response)

        except Exception as e:
            print(f"❌ Error processing message: {e}")
            error_message = "Sorry, something went wrong! Please try again. 😅"
            await message.reply(error_message)

    async def setup_hook(self):
        """Called when the bot is starting up"""
        print("🚀 Makanin Bot is starting up...")
        print(f"🔧 Available tools: {self.agent.tool_registry.list_tools()}")


# Legacy MakaninBot class for backward compatibility
class LegacyMakaninBot:
    """Legacy MakaninBot for backward compatibility with existing code"""

    def __init__(self):
        # Initialize the new agent system
        self.agent = MakaninAgent()
        print("🔄 Using legacy MakaninBot with new agent framework")

    def chat(self, user_message: str) -> str:
        """
        Main chat method for backward compatibility.
        Now uses the agent system internally.
        """
        try:
            # Run the async method in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(
                    self.agent.process_message("legacy_user", user_message)
                )
                return response
            finally:
                loop.close()
        except Exception as e:
            print(f"❌ Error in legacy chat method: {e}")
            return "Sorry, something went wrong! Please try again. 😅"

    def find_food(self, slots):
        """Legacy method - now handled by agent system"""
        print("⚠️  Legacy find_food method called - use agent system instead")
        return []

    def format_response(self, venues, slots):
        """Legacy method - now handled by agent system"""
        print("⚠️  Legacy format_response method called - use agent system instead")
        return "Please use the new agent system for better results!"


def create_bot(use_discord: bool = True):
    """Create appropriate bot instance"""
    if use_discord:
        return DiscordMakaninBot()
    else:
        return LegacyMakaninBot()


def run_discord_bot():
    """Run the Discord bot"""
    bot = DiscordMakaninBot()
    bot.run(config.DISCORD_TOKEN)


# Keep the original class name for existing imports
MakaninBot = LegacyMakaninBot
DiscordMakaninBot = MakaninBot  # Discord bot class

if __name__ == "__main__":
    print("🍜 Makanin Bot with Agent Framework")
    print("Use 'python bot.py' to run the Discord bot")
    print("Or import MakaninBot class for programmatic use")
