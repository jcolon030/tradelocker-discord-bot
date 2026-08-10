import discord
from discord.ext import commands, tasks
from services.tradelocker import TradeLockerClient

class SignalRoom(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.tradelocker = None
        self.current_positions = {}

    async def cog_load(self):
        self.tradelocker = await TradeLockerClient.create()

        if self.tradelocker is None:
            print("Failed to initialize TradeLocker.")
            return

        self.handle_signals.start()

    async def create_signal(self):

        pass

    @tasks.loop(seconds=5)
    async def handle_signals(self):
        positions = await self.tradelocker.get_positions()

        if positions is None:
            return

        new_positions = {position.id: position for position in positions}

        # First Snapshot
        if not self.current_positions:
            self.current_positions = new_positions
            return

        # Compare snapshots

        self.current_positions = new_positions