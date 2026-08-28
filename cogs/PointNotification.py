import discord 
from discord.ext import commands, tasks
from database.trade_repository import TradeRepository
import datetime
from zoneinfo import ZoneInfo
import os
from dotenv import load_dotenv

load_dotenv()

# Grabs signal room channel id from .env.local
def get_notification_channel_id():
    points_notification_channel_id = os.getenv("POINTS_NOTIFICATION_CHANNEL_ID")
    if not points_notification_channel_id:
        raise RuntimeError("POINTS_NOTIFICATION_CHANNEL_ID is not set.")
    return int(points_notification_channel_id)

EASTERN = ZoneInfo("America/New_York")

class PointNotification(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.trade_repository: TradeRepository = bot.trade_repository
        self.send_point_summary.start()

    def cog_unload(self):
        self.send_point_summary.cancel()

    async def send_embed(self, points):

        image_path = "public/default.png"
        file = discord.File(image_path, "default.png")

        yesterday_date = (datetime.datetime.now(EASTERN).date() - datetime.timedelta(days=1))

        embed = discord.Embed(
            title=f"{yesterday_date}",
            color=discord.Color.blue()
        )

        embed.add_field(
            name=f"Yesterday was a {points}+ point day in profit on US30.",
            value="\u200b",
            inline=False
        )

        embed.add_field(
            name="Joining the Signal Room could see returns like this:",
            value=(
                f"0.01 x {points}pts = ${self.estimate_profit(points, 0.01):.2f}\n"
                f"0.05 x {points}pts = ${self.estimate_profit(points, 0.05):.2f}\n"
                f"0.10 x {points}pts = ${self.estimate_profit(points, 0.10):.2f}"
            ),
            inline=False
        )

        embed.set_thumbnail(url="attachment://default.png")

        channel_id = get_notification_channel_id()
        channel = self.bot.get_channel(channel_id)

        if channel is None:
            print(f"Could not find notification channel: {channel_id}")
            return

        await channel.send(embed=embed, file=file)

    @tasks.loop(time=datetime.time(hour=16, minute=0, tzinfo=EASTERN))
    async def send_point_summary(self):
        await self.generate_point_summary()

    async def generate_point_summary(self):
        now = datetime.datetime.now(EASTERN)

        end_time = now.replace(
            hour=16,
            minute=0,
            second=0,
            microsecond=0
        )

        start_time = end_time - datetime.timedelta(days=1)

        points = await self.trade_repository.get_total_points(
            start_time.isoformat(),
            end_time.isoformat()
        )

        await self.send_embed(points)

    def estimate_profit(self, points, lot_size):
        return points * (lot_size / 0.01)

    @send_point_summary.before_loop
    async def before_send_point_summary(self):
        await self.bot.wait_until_ready()

    @commands.command()
    async def test_trades(self, ctx):
        end_time = datetime.datetime.now(EASTERN).replace(
            hour=16,
            minute=0,
            second=0,
            microsecond=0
        )

        start_time = end_time - datetime.timedelta(days=1)

        fake_time = start_time + datetime.timedelta(hours=12)

        trades = [
            ("TEST001", "US30", 100, 0.01),
            ("TEST002", "US30", 200, 0.02),
            ("TEST003", "US30", -50, 0.01),
        ]

        for trade_id, symbol, price_change, lot_size in trades:

            await self.trade_repository.save_trade(
                trade_id,
                symbol,
                price_change,
                lot_size,
                fake_time
            )

        await ctx.send("Test trades added.")

    @commands.command()
    async def test_points(self, ctx):
        await self.generate_point_summary()

async def setup(bot):
    await bot.add_cog(PointNotification(bot))
