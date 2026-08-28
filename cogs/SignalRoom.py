import discord
from discord.ext import commands, tasks
from services.tradelocker import TradeLockerClient
from models.position import Position
import os
from dotenv import load_dotenv

load_dotenv()

# Grabs signal room channel id from .env.local
def get_channel_id():
    signal_room_channel_id = os.getenv("SIGNAL_ROOM_CHANNEL_ID")
    if not signal_room_channel_id:
        raise RuntimeError("SIGNAL_ROOM_CHANNEL_ID is not set.")
    return int(signal_room_channel_id)

class SignalRoom(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot # Holds discord bot client
        self.tradelocker = None # Holds TradeLocker Client Class
        self.current_positions: dict[str, Position] = {} # Holds all open positions
        self.pending_closes: dict[str, Position] = {} # Holds any closed positions that have not been processed
        self.positions_initialized = False # Used for first position snapshot
        self.pending_empty_updates = set() # Used to track positions that have been updated but not closed

    # Runs when cogs are initialized
    async def cog_load(self):
        self.tradelocker = await TradeLockerClient.create()

        if self.tradelocker is None:
            print("Failed to initialize TradeLocker.")
            return

        self.handle_signals.start()

    # Runs before bot closes
    async def cog_unload(self):
        self.handle_signals.cancel()

        if self.tradelocker:
            await self.tradelocker.close()

    # Returns removed keys (closed positions)
    def _find_removed_keys(self, new_positions: dict[str, Position]):
        return self.current_positions.keys() - new_positions.keys()

    # Returns added keys (opened positions)
    def _find_added_keys(self, new_positions: dict[str, Position]):
        return new_positions.keys() - self.current_positions.keys()

    # Returns positions that exist in both snapshots
    def _find_common_keys(self, new_positions: dict[str, Position]):
        return new_positions.keys() & self.current_positions.keys()

    # Handles opened positions
    async def _handle_opened_positions(self, opened_ids, new_positions: dict[str, Position]):
        for position_id in opened_ids:
            position = new_positions[position_id]

            print(f"Position Opened: {position.id}")

            await self.create_signal("OPEN", position)

    # Handles any closed positions (wrapper function)
    async def _handle_closed_positions(self, closed_ids):
        for position_id in closed_ids:
            self.pending_empty_updates.discard(position_id)

            position = self.current_positions[position_id]

            print(f"Position Closed: {position.id}")

            self.pending_closes[position_id] = position

    # Handles any position is updated after position creation
    async def _handle_updated_positions(self, common_ids, new_positions: dict[str, Position]):
        # Loops through positions with new data
        for position_id in common_ids:

            old_position = self.current_positions[position_id]
            new_position = new_positions[position_id]

            # Checks if position has taken off TP/SL and the position is still open
            if position_id in self.pending_empty_updates:
                if (new_position.take_profit is None and new_position.stop_loss is None):
                    self.pending_empty_updates.discard(position_id)

                    print(f"Position Updated: {position_id}")

                    await self.create_signal(
                        "UPDATE",
                        new_position
                    )

                    continue

                self.pending_empty_updates.discard(position_id)

            # Checks for updated take profit or stop loss
            changed = (
                old_position.take_profit != new_position.take_profit
                or old_position.stop_loss != new_position.stop_loss
            )

            if not changed:
                continue

            # Puts position removing its TP/SL into buffer to verify
            if (new_position.take_profit is None and new_position.stop_loss is None):
                self.pending_empty_updates.add(position_id)
                continue

            print(f"Position Updated: {position_id}")
            
            await self.create_signal(
                "UPDATE",
                new_position
            )

    # Handles closed positions which may have not updated on Tradelocker during position close
    async def _handle_pending_closes(self):
        if not self.pending_closes:
            return

        history = await self.tradelocker.get_orders_history() # Fetches history for all past orders

        # Confirms history is not empty
        if history is None:
            return

        completed: list[str] = []

        # Loops through pending closes and checks it with order history
        for position_id, position in self.pending_closes.items():

            close_price = self.tradelocker.find_close_price(history, position_id)

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

    # Embedded Message Creator, requires order_tupe, position, and close_price (if applicable)
    async def create_signal(self, order_type: str, position: Position, close_price: float | None = None):

        # This can be replaced with any logo you desire
        image_path = "public/default.png"
        file = discord.File(image_path, "default.png")

        if order_type == "OPEN":
            embed = discord.Embed(title="🟢 Position Opened", color=discord.Color.green())
            symbol = await self.tradelocker.fetch_instrument_name(position)

            embed.add_field(name="Instrument", value=symbol, inline=True)
            embed.add_field(name="Market Order", value=position.side.capitalize(), inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)
            embed.add_field(name="Entry Price", value=str(position.entry_price), inline=True)
            embed.add_field(name="Take Profit", value=str(position.take_profit), inline=True)
            embed.add_field(name="Stop Loss", value=str(position.stop_loss), inline=True)
            embed.set_footer(text=f"Trade ID: {position.id[-4:]}")
            embed.set_thumbnail(url="attachment://default.png")
            embed.timestamp = discord.utils.utcnow()

        elif order_type == "UPDATE":
            embed = discord.Embed(title="🟡 Stop/Take Updated", color=discord.Color.gold())
            symbol = await self.tradelocker.fetch_instrument_name(position)

            embed.add_field(name="Instrument", value=symbol, inline=True)
            embed.add_field(name="Market Order", value=position.side.capitalize(), inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)
            embed.add_field(name="Entry Price", value=str(position.entry_price), inline=True)
            embed.add_field(name="Take Profit", value=str(position.take_profit), inline=True)
            embed.add_field(name="Stop Loss", value=str(position.stop_loss), inline=True)
            embed.set_footer(text=f"Trade ID: {position.id[-4:]}")
            embed.set_thumbnail(url="attachment://default.png")
            embed.timestamp = discord.utils.utcnow()

        elif order_type == "CLOSE":
            embed = discord.Embed(title="🔴 Position Closed", color=discord.Color.red())
            symbol = await self.tradelocker.fetch_instrument_name(position)

            embed.add_field(name="Instrument", value=symbol, inline=True)
            embed.add_field(name="Market Order", value=position.side.capitalize(), inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)
            embed.add_field(name="Closing Price", value=close_price, inline=True)
            embed.add_field(name="Take Profit", value=f"None", inline=True)
            embed.add_field(name="Stop Loss", value=f"None", inline=True)
            embed.set_footer(text=f"Trade ID: {position.id[-4:]}")
            embed.set_thumbnail(url="attachment://default.png")
            embed.timestamp = discord.utils.utcnow()

        channel = self.bot.get_channel(get_channel_id())

        if channel is None:
            print("Signal room channel not found.")
            return
        
        await channel.send(embed=embed, file=file)

    # Main Signal Loop, Handles all types of positions
    @tasks.loop(seconds=3)
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

    # Makes sure bot is ready before loop starts (safety precaution)
    @handle_signals.before_loop
    async def before_handle_signals(self):
        await self.bot.wait_until_ready()

    # Gives info for any hanging errors/crashes
    @handle_signals.error
    async def handle_signals_error(self, error):
        print(f"Signal loop error: {type(error).__name__}: {error}")

async def setup(bot):
    await bot.add_cog(SignalRoom(bot))
