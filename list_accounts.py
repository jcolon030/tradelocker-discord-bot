import asyncio
from services.tradelocker import TradeLockerClient

async def main():
    client = await TradeLockerClient.create(set_account=False)

    if client is None:
        print("Failed to connect to TradeLocker.")
        return

    try:
        accounts = await client.get_accounts()

        if not accounts:
            print("No TradeLocker accounts found.")
            return

        print("\nAvailable TradeLocker Accounts:\n")

        for index, account in enumerate(accounts):
            print(f"[{index}] {account}")

    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())