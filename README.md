# TradeLocker Discord Signal Bot

Automatically sends TradeLocker position updates
to a Discord channel.

## Features

- Position opened notifications
- Position closed notifications
- Take-profit updates
- Stop-loss updates
- Automatic TradeLocker token refreshing
- Instrument caching
- Async API requests
- Discord embeds

## Requirements

- Python 3.10+
- Discord Bot
- TradeLocker account

## Installation

1. Clone repository
2. Create virtual environment
3. Install requirements
4. Copy .env.example to .env
5. Run python list_accounts.py
6. Configure credentials
7. Run python main.py

## Configuration

DISCORD_TOKEN=""

TRADELOCKER_EMAIL=""
TRADELOCKER_PASSWORD=""
TRADELOCKER_SERVER=""

TRADELOCKER_ACCOUNT_NUM=""
TRADELOCKER_ACCOUNT_TYPE="live"

SIGNAL_ROOM_CHANNEL_ID=""

## Disclaimer
This project is provided for educational and informational purposes only. It is not financial advice and is not intended to execute or recommend trades. Use this software at your own risk. The author is not responsible for financial losses, account issues, or other damages resulting from use of this software.
...