# Makanin Bot dengan sistem Agent dan Redis Memory
# Bot makanan dengan pencarian viral dan memori persisten

import discord
from discord.ext import commands
import asyncio
import config
from agent.agent import MakaninAgent


class MakaninBot(commands.Bot):
    """Bot Discord dengan sistem Agent Makanin"""

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )

        # Inisialisasi sistem agent
        self.agent = MakaninAgent()
        self.is_ready = False

    async def on_ready(self):
        """Dipanggil saat bot siap"""
        print(f"Bot {self.user.name} terhubung ke Discord!")
        print(f"Status Agent: {self.agent.get_tool_status()}")
        self.is_ready = True

    async def _send_chunked_response(self, message, response):
        """Kirim respons dalam beberapa pesan terpisah yang rapi dengan formatting"""
        lines = response.split('\n')
        current_item = []
        is_food_response = False

        # Header message pertama
        header_sent = False

        # Cek apakah ini food response (ada emoji atau kata kunci tertentu)
        food_indicators = ['🎉', 'Yay!', 'Aku nemuin', '🍽️', '📍', '🌤️', '🎥']
        is_food_response = any(indicator in response for indicator in food_indicators)

        # Jika bukan food response, kirim langsung
        if not is_food_response:
            # Untuk chat response, kirim langsung dengan normal formatting
            if len(response) > 2000:
                # Bagi pesan panjang untuk chat response
                parts = [response[i:i + 2000] for i in range(0, len(response), 2000)]
                for part in parts:
                    await message.reply(part)
            else:
                await message.reply(response)
            return

        # Untuk food response, gunakan formatting khusus
        for line in lines:
            # Jika ini adalah header/pembuka
            if not header_sent and ('🎉' in line or 'Yay!' in line or 'Aku nemuin' in line):
                await message.reply(line.strip())
                header_sent = True
                continue

            # Jika ini adalah separator (━━━) - skip
            if '━' * 10 in line:
                continue

            # Jika ini adalah nomor item (#1, #2, dll) - mulai item baru
            if line.strip().startswith('#') and any(line.strip().startswith(f'#{i}') for i in range(1, 10)):
                # Kirim item sebelumnya jika ada
                if current_item:
                    formatted_item = self._format_item(current_item)
                    await message.reply(formatted_item)

                # Mulai item baru
                current_item = [line.strip()]
                continue

            # Tambahkan line ke item saat ini
            if current_item:
                current_item.append(line.strip())

        # Kirim item terakhir
        if current_item:
            formatted_item = self._format_item(current_item)
            await message.reply(formatted_item)

    def _format_item(self, item_lines):
        """Format satu item dengan bullet points dan bold title"""
        if not item_lines:
            return ""

        # Ambil title dari baris pertama
        title = item_lines[0]
        formatted_lines = [f"**{title}**"]

        # Proses baris selanjutnya
        for line in item_lines[1:]:
            line = line.strip()
            if not line:
                continue

            # Identifikasi jenis informasi dan format dengan bullet points
            if any(keyword in line.lower() for keyword in ['cuaca', 'weather']):
                formatted_lines.append(f"- 🌤️ Cuaca: {line}")
            elif any(keyword in line.lower() for keyword in ['maps', 'google']):
                formatted_lines.append(f"- 📍 Maps: {line}")
            elif any(keyword in line.lower() for keyword in ['tiktok', 'viral']):
                formatted_lines.append(f"- 🎥 Viral di TikTok: {line}")
            elif 'http' in line:
                # Jika ada link tanpa prefix spesifik
                if 'tiktok' in line:
                    formatted_lines.append(f"- 🎥 Viral di TikTok: {line}")
                elif 'maps' in line:
                    formatted_lines.append(f"- 📍 Maps: {line}")
                else:
                    formatted_lines.append(f"- 🔗 Link: {line}")
            else:
                # Default untuk lokasi atau info lainnya
                if line and not line.startswith('#'):
                    formatted_lines.append(f"- 📍 Lokasi: {line}")

        return '\n'.join(formatted_lines)

    async def on_message(self, message):
        """Tangani pesan masuk"""
        # Jangan merespons pesan sendiri
        if message.author == self.user:
            return

        # Jangan merespons pesan bot lain
        if message.author.bot:
            return

        # Handle commands
        if message.content.startswith('!clear'):
            await self._handle_clear_command(message)
            return

        # Bot merespons semua pesan (kecuali dari bot lain)
        # Filter untuk DM tidak diperlukan lagi karena bot merespons semua channel

        try:
            # Cek intent terlebih dahulu untuk menentukan apakah perlu waiting message
            import json

            # Quick NLU check untuk intent
            try:
                nlu_result = await self.agent._execute_tool("nlu", {"text": message.content})
                show_waiting = nlu_result.success and nlu_result.data.get("intent") == "find_food"
            except:
                show_waiting = False  # Default tidak show waiting jika NLU gagal

            wait_message = None
            if show_waiting:
                # Kirim pesan penanda sedang proses hanya untuk food search
                wait_message = await message.reply("Tunggu dulu yaa, aku cariin dulu... 🔍")

            # Tampilkan indikator typing saat memproses
            async with message.channel.typing():
                # Proses pesan menggunakan agent
                response = await self.agent.process_message(
                    user_id=str(message.author.id),
                    user_message=message.content
                )

                # Hapus pesan tunggu jika ada
                if wait_message:
                    try:
                        await wait_message.delete()
                    except:
                        pass  # Jika tidak bisa delete, lanjut saja

                # Kirim respons dalam beberapa pesan terpisah
                await self._send_chunked_response(message, response)

        except Exception as e:
            print(f"Error memproses pesan: {e}")
            error_message = "Maaf, terjadi kesalahan! Silakan coba lagi."
            await message.reply(error_message)

    async def _handle_clear_command(self, message):
        """Handle !clear command"""
        user_id = str(message.author.id)

        # Check if user wants to clear only conversation or all data
        if "chat" in message.content.lower() or "conversation" in message.content.lower():
            # Clear only conversation
            success = self.agent.context_manager.memory.backend.clear_conversation(user_id)
            if success:
                await message.reply("✅ Chat history cleared! Let's start fresh 😊")
            else:
                await message.reply("❌ Failed to clear chat history. Please try again.")
        else:
            # Clear all user data
            success = self.agent.context_manager.clear_user_data(user_id)
            if success:
                await message.reply("✅ All your data has been cleared! Fresh start 🎉")
            else:
                await message.reply("❌ Failed to clear data. Please try again.")


# Legacy chat interface untuk kompatibilitas
class LegacyMakaninBot:
    """Legacy MakaninBot untuk kompatibilitas"""

    def __init__(self):
        self.agent = MakaninAgent()

    def chat(self, user_message: str) -> str:
        """Metode chat utama (legacy)"""
        try:
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
            print(f"Error di chat method: {e}")
            return "Maaf, terjadi kesalahan! Silakan coba lagi."


# Export class yang dibutuhkan
# Simpan kelas Discord asli yang inherits dari commands.Bot
DiscordBotClass = MakaninBot  # Discord bot asli

# Reassign untuk backward compatibility
MakaninBot = LegacyMakaninBot  # Default untuk penggunaan umum (legacy)
DiscordMakaninBot = DiscordBotClass  # Gunakan kelas Discord asli

if __name__ == "__main__":
    print("Makanin Bot dengan Agent Framework")
    print("Gunakan 'python discord_run.py' untuk menjalankan bot Discord")
    print("Atau import class MakaninBot untuk penggunaan programatik")
