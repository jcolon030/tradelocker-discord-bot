import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from services.tradelocker import TradeLockerClient
from database.trade_repository import TradeRepository

load_dotenv()

def get_discord_token():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN is not set.")
    return token

class TradeLockerBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(
            command_prefix="$",
            intents=intents
        )

    # Loads Cogs
    async def setup_hook(self):
        self.tradelocker = await TradeLockerClient.create()
        self.trade_repository = TradeRepository()

        await self.trade_repository.initialize()

        await self.load_extension(f"cogs.SignalRoom")
        await self.load_extension(f"cogs.PointNotification")
        print("All Cogs Loaded")

    # Runs once bot is ready to start
    async def on_ready(self):
        print(f"Logged in as {self.user}")

        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="Processing Signals"
            ),
            status=discord.Status.online
        )

    # Closes bot when code ends
    async def close(self):
        await self.tradelocker.close()
        await super().close()

if __name__ == "__main__":

    bot = TradeLockerBot()
    bot.run(get_discord_token())