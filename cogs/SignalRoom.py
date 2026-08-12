import discord
from discord.ext import commands, tasks
from services.tradelocker import TradeLockerClient
from models.position import Position

# Cog Constants (Change as needed)
SIGNAL_ROOM_CHANNEL_ID = 1382717358799323146

class SignalRoom(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.tradelocker = None
        self.current_positions: dict[str, Position] = {}
        self.pending_closes: dict[str, Position] = {}
        self.positions_initialized = False

    # Runs when cogs are initialized
    async def cog_load(self):
        self.tradelocker = await TradeLockerClient.create()

        if self.tradelocker is None:
            print("Failed to initialize TradeLocker.")
            return

        self.handle_signals.start()

    # Runs before bot closes
    def cog_unload(self):
        self.handle_signals.cancel()

        if self.tradelocker:
            self.tradelocker.close()

    # Returns removed keys (closed positions)
    def _find_removed_keys(self, new_positions: dict[str, Position]):
        return self.current_positions.keys() - new_positions.keys()

    # Returns added keys (opened positions)
    def _find_added_keys(self, new_positions: dict[str, Position]):
        return new_positions.keys() - self.current_positions.keys()

    # Returns positions that exist in both snapshots
    def _find_common_keys(self, new_positions: dict[str, Position]):
        return new_positions.keys() & self.current_positions.keys()

    async def _handle_opened_positions(self, opened_ids, new_positions: dict[str, Position]):
        for position_id in opened_ids:
            position = new_positions[position_id]

            print(f"Position Opened: {position.id}")

            await self.create_signal("OPEN", position)

    async def _handle_closed_positions(self, closed_ids):
        for position_id in closed_ids:
            position = self.current_positions[position_id]

            print(f"Position Closed: {position.id}")

            self.pending_closes[position_id] = position

    async def _handle_updated_positions(self, common_ids, new_positions: dict[str, Position]):
        for position_id in common_ids:

            old_position = self.current_positions[position_id]
            new_position = new_positions[position_id]

            if (old_position.take_profit != new_position.take_profit 
                or 
                old_position.stop_loss != new_position.stop_loss):

                print(f"Position Updated: {position_id}")

                await self.create_signal(
                    "UPDATE",
                    new_position
                )

    async def _handle_pending_closes(self):
        completed = []

        for position_id, position in self.pending_closes.items():

            close_price = await self.tradelocker.get_close_price(position_id)

            if close_price is None:
                continue

            await self.create_signal(
                "CLOSE",
                position,
                close_price=close_price
            )

            completed.append(position_id)

        for position_id in completed:
            del self.pending_closes[position_id]

    async def create_signal(self, order_type: str, position: Position, close_price: float | None = None):
        image_path = "public/logo.png"
        file = discord.File(image_path, "logo.png")

        if order_type == "OPEN":
            embed = discord.Embed(title="🟢 Position Opened", color=discord.Color.green())
            symbol = await self.tradelocker.fetch_instrument_name(position)

            embed.add_field(name="Instrument", value=symbol, inline=True)
            embed.add_field(name="Market Order", value=position.side, inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)
            embed.add_field(name="Entry Price", value=str(position.entry_price), inline=True)
            embed.add_field(name="Take Profit", value=str(position.take_profit), inline=True)
            embed.add_field(name="Stop Loss", value=str(position.stop_loss), inline=True)
            embed.set_footer(text=f"Trade ID: {position.id[-4:]}")
            embed.set_thumbnail(url="attachment://logo.png")
            embed.timestamp = discord.utils.utcnow()

        elif order_type == "UPDATE":
            embed = discord.Embed(title="🟡 Stop/Take Updated", color=discord.Color.gold())
            symbol = await self.tradelocker.fetch_instrument_name(position)

            embed.add_field(name="Instrument", value=symbol, inline=True)
            embed.add_field(name="Market Order", value=position.side, inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)
            embed.add_field(name="Entry Price", value=str(position.entry_price), inline=True)
            embed.add_field(name="Take Profit", value=str(position.take_profit), inline=True)
            embed.add_field(name="Stop Loss", value=str(position.stop_loss), inline=True)
            embed.set_footer(text=f"Trade ID: {position.id[-4:]}")
            embed.set_thumbnail(url="attachment://logo.png")
            embed.timestamp = discord.utils.utcnow()

        elif order_type == "CLOSE":
            embed = discord.Embed(title="🔴 Position Closed", color=discord.Color.red())
            symbol = await self.tradelocker.fetch_instrument_name(position)

            embed.add_field(name="Instrument", value=symbol, inline=True)
            embed.add_field(name="Market Order", value=position.side, inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)
            embed.add_field(name="Closing Price", value=close_price, inline=True)
            embed.add_field(name="Take Profit", value=f"None", inline=True)
            embed.add_field(name="Stop Loss", value=f"None", inline=True)
            embed.set_footer(text=f"Trade ID: {position.id[-4:]}")
            embed.set_thumbnail(url="attachment://logo.png")
            embed.timestamp = discord.utils.utcnow()

        channel = self.bot.get_channel(SIGNAL_ROOM_CHANNEL_ID)

        if channel is None:
            print("Signal room channel not found.")
            return
        
        await channel.send(embed=embed, file=file)
            

    @tasks.loop(seconds=5)
    async def handle_signals(self):
        positions = await self.tradelocker.get_positions()

        if positions is None:
            return

        new_positions = {position.id: position for position in positions}

        # First Snapshot
        if not self.positions_initialized:
            self.current_positions = new_positions
            self.positions_initialized = True
            return

        # Compare snapshots
        opened_ids = self._find_added_keys(new_positions)
        closed_ids = self._find_removed_keys(new_positions)
        common_ids = self._find_common_keys(new_positions)

        await self._handle_updated_positions(common_ids, new_positions)
        await self._handle_opened_positions(opened_ids, new_positions)
        await self._handle_closed_positions(closed_ids)
        await self._handle_pending_closes()

        self.current_positions = new_positions