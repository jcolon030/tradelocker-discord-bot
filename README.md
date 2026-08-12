<h1 align="center">TradeLocker Discord Signal Bot</h1>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/Discord.py-Bot-blue" alt="Discord.py">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/badge/TradeLocker-API-orange" alt="TradeLocker API">
</p>

<p align="center">
  <img width="30%" alt="Position Opened" src="https://github.com/user-attachments/assets/52c0871c-b704-4a76-82a8-617fcd8d4980" />
  <img width="30%" alt="Position Updated" src="https://github.com/user-attachments/assets/0f80be87-18c4-4bbb-b528-134b7de51681" />
  <img width="30%" alt="Position Closed" src="https://github.com/user-attachments/assets/3286f9ea-4ed7-49cb-8a79-d8ae93bb083e" />
</p>

<br/>

<p>
  TradeLocker Discord Signal Bot is a self-hosted bot that monitors a TradeLocker account and automatically posts trading activity to a designated Discord channel.
  It tracks when positions are opened, updated, and closed, removing the need to manually post trade updates.
</p>

## Why?

This project originally started as a small bot I built for a friend who wanted an easier way to share his TradeLocker activity with his Discord server. Instead of manually sending updates every time a trade changed, the bot could monitor his account and handle those updates automatically.

Over time, I continued improving the project, adding support for position updates, closed trades, API error handling, token refreshing, and other features. Eventually, I decided to clean up the original project and make it open source so anyone can self-host and configure it for their own TradeLocker account.

## What it does
The bot monitors a configured TradeLocker account and watches for changes to open positions. When a position is opened, updated, or closed, it automatically sends an embed to a selected Discord channel with the relevant trade information.
It also handles TradeLocker authentication in the background, including refreshing expired access tokens and caching instrument information to avoid unnecessary API requests.
The goal is simple: let the bot handle posting trade updates so they don't have to be shared manually.

## Features

| Feature | Description |
| --- | --- |
| Position Tracking | Detects when TradeLocker positions are opened or closed |
| Position Updates | Monitors changes to take-profit and stop-loss levels |
| Discord Signals | Automatically sends trade information as Discord embeds |
| Token Refresh | Automatically refreshes expired TradeLocker access tokens |
| Instrument Caching | Caches instrument information to reduce unnecessary API requests |
| Async Requests | Uses asynchronous API requests while monitoring account activity |

## Getting Started

**Requirements**

- Python 3.10+
- A Discord account/server
- A Discord bot application
- A TradeLocker account

**1. Clone the Repository and install dependencies**

You can copy the commands below in order to clone the repository

```bash
# Clone repository
git clone https://github.com/jcolon030/tradelocker-discord-bot
cd tradelocker-discord-bot

# Install dependencies
pip install -r requirements.txt
```

<br/>

**2. Create a Discord Bot**

Create a new application through the [Discord Developer Portal](https://discord.com/developers/home) and add a bot to the application.

Once created:

1. Copy the bot token. This will be used for `DISCORD_TOKEN`.
2. Invite the bot to the Discord server where you want trade signals to be posted.
3. Make sure the bot has permission to view and send messages in the signal channel.
4. Copy the ID of the channel you want to use for signals. This will be used for `SIGNAL_ROOM_CHANNEL_ID`.

>Make sure the bot has permission to View Channels, Send Messages, Embed Links, and Attach Files in the signal channel.

> Never share or commit your Discord bot token.

<br/>

**3. Configure Environment Variables**

Create a `.env` file in the root of the project using `.env.example` as a template:

```env
DISCORD_TOKEN=""

TRADELOCKER_EMAIL=""
TRADELOCKER_PASSWORD=""
TRADELOCKER_SERVER=""

TRADELOCKER_ACCOUNT_NUM=""
TRADELOCKER_ACCOUNT_TYPE="live"

SIGNAL_ROOM_CHANNEL_ID=""
```

<br/>

**4. Find Your TradeLocker Account**

After entering your TradeLocker login information, run:

```bash
python list_accounts.py
```

This will display the TradeLocker accounts available to you and their corresponding account numbers.

Set the account you want to the bot to monitor in your `.env` file:

```env
TRADELOCKER_ACCOUNT_NUM=0
```

<br/>

**5. Start the Bot**

Once everything is configured, start the bot with:

```bash
python main.py
```
If the connection is successful, the bot will begin monitoring the selected TradeLocker account
and posting position updates to your configured Discord channel.

## Environment Variable Configuration

| Variable | Description |
| --- | --- |
| `DISCORD_TOKEN` | Token for your Discord bot |
| `SIGNAL_ROOM_CHANNEL_ID` | Discord channel where signals will be sent |
| `TRADELOCKER_EMAIL` | TradeLocker account email |
| `TRADELOCKER_PASSWORD` | TradeLocker account password |
| `TRADELOCKER_SERVER` | TradeLocker server/broker |
| `TRADELOCKER_ACCOUNT_NUM` | Index of the TradeLocker account to monitor |
| `TRADELOCKER_ACCOUNT_TYPE` | `live` or `demo` |

## Project Structure 

```text
tradelocker-discord-bot/
├── cogs/
│   └── SignalRoom.py        # Monitors positions and sends Discord signals
│
├── models/
│   └── position.py          # Represents TradeLocker position data
│
├── services/
│   └── tradelocker.py       # Handles communication with the TradeLocker API
│
├── public/
│   └── logo.png             # Default logo used in Discord embeds
│
├── list_accounts.py         # Lists available TradeLocker accounts
├── main.py                  # Starts and configures the Discord bot
├── .env.example             # Template for required environment variables
├── requirements.txt         # Python dependencies
├── README.md
└── LICENSE
```

The project is separated into a few small components to keep the Discord logic, TradeLocker API communication, and data models independent from one another. `main.py` acts as the entry point, while the `SignalRoom` cog handles monitoring and sending trade updates. 

## Disclaimer

This project is an independent, open-source tool and is not affiliated with, endorsed by, or officially associated with TradeLocker.

This software is provided for educational and informational purposes only. It is not financial advice and does not provide or recommend trading strategies. Use of this software and any information it produces is at your own risk.

This project is provided under the MIT License and comes without warranty. The author is not responsible for financial losses, account issues, missed or incorrect signals, API-related issues, or other damages resulting from the use of this software.

## License

This project is licensed under the [MIT License](LICENSE).

