import aiosqlite

class TradeRepository:

    def __init__(self, database_path="database/trades.db"):
        self.database_path = database_path

    async def initialize(self):
        async with aiosqlite.connect(self.database_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    trade_id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    profit REAL NOT NULL,
                    lot_size REAL NOT NULL,
                    close_time TEXT NOT NULL
                )
            """)

            await db.commit()

    async def save_trade(self, trade_id, symbol, profit, lot_size, close_time):
        async with aiosqlite.connect(self.database_path) as db:
            await db.execute("""
                INSERT OR IGNORE INTO trades (
                    trade_id,
                    symbol,
                    profit,
                    lot_size,
                    close_time
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                trade_id,
                symbol,
                profit,
                lot_size,
                close_time
            ))

            await db.commit()

    async def get_trades(self, start_time, end_time):
        async with aiosqlite.connect(self.database_path) as db:
            cursor = await db.execute("""
                SELECT trade_id, symbol, profit, lot_size, close_time
                FROM trades
                WHERE close_time >= ?
                AND close_time < ?
                ORDER BY close_time
            """, (
                start_time,
                end_time
            ))

            rows = await cursor.fetchall()

            return rows

    async def get_total_points(self, start_time, end_time):
        async with aiosqlite.connect(self.database_path) as db:
            cursor = await db.execute("""
                SELECT SUM(profit * (0.01 / lot_size))
                FROM trades
                WHERE close_time >= ?
                AND close_time < ?
                AND lot_size > 0
            """, (start_time, end_time))

            row = await cursor.fetchone()

            return row[0] or 0