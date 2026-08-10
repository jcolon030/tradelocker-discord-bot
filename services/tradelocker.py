from models.position import Position
import asyncio
import aiohttp
import ssl
import os
from dotenv import load_dotenv

# TradeLocker Account Constants (Change Later to allow discord embedded to choose account)
ACCOUNT_NUM = 0
ACCOUNT_TYPE = "live"

load_dotenv()

class TradeLockerClient:

    __base_url = f"https://{ACCOUNT_TYPE}.tradelocker.com/backend-api"
    __base_headers = {
                "accept": "application/json",
                "content-type": "application/json",
            }

    # Initializes class variables
    def __init__(self):
        self.__tokens = {}
        self.__http_session = self._make_session()
        self.__account_details = {}

    # Async class initialization
    @classmethod
    async def create(cls):
        client = cls()

        if not await client.login():
            await client._close()
            return None

        if not await client.set_account_details():
            await client._close()
            return None

        return client

    # PRIVATE FUNCTIONS
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

    # Helper function for making requests to TradeLocker API
    async def _request(self, method, endpoint, *, json=None, autheticated=True):
        url = f"{self.__base_url}{endpoint}"

        headers = self.__base_headers.copy()

        # If request requires TradeLocker Access Token
        if autheticated:
            headers["authorization"] = f"Bearer {self._get_access_token()}"

        try:
            async with self.__http_session.request(method, url, headers=headers, json=json) as r:
                r.raise_for_status()

                if r.status == 204:
                    return

                return await r.json()

        except aiohttp.ClientResponseError as e:
            print(f"HTTP Error: {e.status} - {e.message}")
            return None

        except aiohttp.ClientError as e:
            print(f"Request Error: {e}")
            return None

    # Returns access tokens
    def _get_access_token(self):
        return self.__tokens["accessToken"]

    # Closes aiohttp session
    async def _close(self):
        await self.__http_session.close()
        

    # PUBLIC FUNCTIONS
    # Attempts Login into TradeLocker API, Saves tokens Locally
    async def login(self):
        payload = {
            "email": os.getenv("TRADELOCKER_EMAIL"),
            "password": os.getenv("TRADELOCKER_PASSWORD"),
            "server": os.getenv("TRADELOCKER_SERVER")
        }

        data = await self._request(
            "POST",
            "/auth/jwt/token",
            headers=self.__base_headers,
            json=payload,
            autheticated=False
        )

        if data is None:
            return False

        self.__tokens["accessToken"] = data["accessToken"]
        self.__tokens["refreshToken"] = data["refreshToken"]
        self.__tokens["expireDate"] = data["expireDate"]

        return True

    # Attempts to refresh TradeLocker API tokens
    async def refresh_token(self):
        payload = {
            "refreshToken": self.__tokens["refreshToken"]
        }

        data = await self._request(
            "POST",
            "/auth/jwt/refresh",
            headers=self.__base_headers,
            json=payload,
            autheticated=False
        )

        if data is None:
            return False

        self.__tokens["accessToken"] = data["accessToken"]
        self.__tokens["refreshToken"] = data["refreshToken"]
        self.__tokens["expireDate"] = data["expireDate"]

        return True

    # Sets account details for class
    async def set_account_details(self):
        data = await self._request(
            "GET",
            "/auth/jwt/all-accounts"
        )

        if data is None:
            return False

        self.__account_details = data["accounts"][ACCOUNT_NUM]

        return True

    # Gets open positions for given account
    async def get_positions(self):
        account_id = self.__account_details["id"]

        data = await self._request(
            "GET",
            f"/trade/accounts/{account_id}/positions"
        )

        return [Position.convert_to_position(row) for row in data["d"]["positions"]]
