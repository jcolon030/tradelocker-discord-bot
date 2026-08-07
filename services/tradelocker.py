from models.position import Position
import asyncio
import aiohttp
import ssl
import os
from dotenv import load_dotenv

load_dotenv()

class TradeLockerClient:

    __url = f"https://live.tradelocker.com/backend-api"
    __base_headers = {
                "accept": "application/json",
                "content-type": "application/json",
            }

    def __init__(self):
        self.__tokens = {}
        self.__http_session = self._make_session()

    # Attempts Login into TradeLocker API, Saves tokens Locally
    async def login(self):
        auth_url = f"{self.__url}/auth/jwt/token"

        # Pulls account information from .env file
        payload = {
            "email": os.getenv("TRADELOCKER_EMAIL"),
            "password": os.getenv("TRADELOCKER_PASSWORD"),
            "server": os.getenv("TRADELOCKER_SERVER")
        }

        try:
            async with self.__http_session.post(auth_url, headers=self.__base_headers, json=payload) as r:
                r.raise_for_status()

                data = await r.json()

                # Stores user TradeLocker API tokens in dictionary
                self.tokens["accessToken"] = data["accessToken"]
                self.tokens["refreshToken"] = data["refreshToken"]
                self.tokens["expireDate"] = data["expireDate"]

                return True

        except aiohttp.ClientResponseError as e:
            print(f"HTTP Error: {e.status} - {e.message}")
            return False

        except aiohttp.ClientError as e:
            print(f"Request Error: {e}")
            return False

    # Attempts to refresh TradeLocker API tokens
    async def refresh_token(self):
        auth_url = f"{self.__url}/auth/jwt/refresh"
        payload = {"refreshToken": self.__tokens["refreshToken"]} # Grabs current refreshToken from self

        try:
            async with self.__http_session.post(auth_url, headers=self.__base_headers, json=payload) as r:
                r.raise_for_status()

                data = await r.json()

                # Updates user tokens in dictionary
                self.tokens["accessToken"] = data["accessToken"]
                self.tokens["refreshToken"] = data["refreshToken"]
                self.tokens["expireDate"] = data["expireDate"]

                return True

        except aiohttp.ClientResponseError as e:
            print(f"HTTP Error: {e.status} - {e.message}")
            return False

        except aiohttp.ClientError as e:
            print(f"Request Error: {e}")
            return False

    # Creates AIOHTTP client session
    def _make_session(self):
        timeout = aiohttp.ClientTimeout(total=30, connect=10, sock_read=20)
        ssl_ctx = ssl.create_default_context()
        connector = aiohttp.TCPConnector(
            ssl=ssl_ctx,
            force_close=True,
            limit=20
        )
        return aiohttp.ClientSession(connector=connector, timeout=timeout)
        
