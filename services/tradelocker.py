from models.position import Position
import asyncio
import aiohttp
import ssl
import os
from dotenv import load_dotenv

# TradeLocker Account Constants (Change Later to allow discord embedded to choose account)
ACCOUNT_NUM = 1
ACCOUNT_TYPE = "live"

load_dotenv(".env.local")

class TradeLockerClient:

    __base_url = f"https://{ACCOUNT_TYPE}.tradelocker.com/backend-api"
    __base_headers = {
                "accept": "application/json",
                "content-type": "application/json",
            }

    # Initializes class variables
    def __init__(self):

        self.__tokens = {} # TradeLocker API Tokens
        self.__http_session = self._make_session() # AIOHTTP Session
        self.__account_details = {} # TradeLocker Account Details
        self.__instruments = {} # Instrument Caching

    # Async class initialization
    @classmethod
    async def create(cls):
        client = cls()

        if not await client.login():
            await client.close()
            return None

        if not await client.set_account_details():
            await client.close()
            return None

        return client

    # PRIVATE FUNCTIONS
    # Creates AIOHTTP client session
    def _make_session(self):
        timeout = aiohttp.ClientTimeout(total=30, connect=10, sock_read=20)
        ssl_ctx = ssl.create_default_context()
        connector = aiohttp.TCPConnector(
            ssl=ssl_ctx,
            limit=20
        )
        return aiohttp.ClientSession(connector=connector, timeout=timeout)

    # Helper function for making requests to TradeLocker API
    async def _request(self, method, endpoint, *, json=None, authenticated=True, account_required=True, retry=True):
        url = f"{self.__base_url}{endpoint}"

        headers = self.__base_headers.copy()

        # If request requires TradeLocker Access Token
        if authenticated:
            headers["authorization"] = f"Bearer {self._get_access_token()}"

        if account_required:
            headers["accNum"] = str(self.__account_details["accNum"])

        try:
            async with self.__http_session.request(method, url, headers=headers, json=json) as r:

                # If access key expired, allows one retry after token refresh
                if r.status == 401 and authenticated and retry:
                    print("Access token expired. Refreshing...")

                    # Verifies token is refreshed
                    if not await self.refresh_token():
                        print("Failed to refresh access token.")
                        return None

                    # Recreates request
                    return await self._request(
                        method, 
                        endpoint, 
                        json=json, 
                        authenticated=authenticated, 
                        account_required=account_required, 
                        retry=False
                    )

                # Rate Limit Error
                if r.status == 429:
                    retry_after = r.headers.get("Retry-After")

                    print(
                        f"Rate limited: {endpoint} "
                        f"Retry-After: {retry_after}"
                    )

                    return None

                r.raise_for_status()

                if r.status == 204:
                    return

                return await r.json()

        # Connection Timeout
        except (aiohttp.ServerTimeoutError, aiohttp.ClientConnectionError) as e:
            print(f"Connection Error: {e}")

            if retry:
                await asyncio.sleep(1)

                # Recreates request
                return await self._request(
                    method, 
                    endpoint, 
                    json=json, 
                    authenticated=authenticated, 
                    account_required=account_required, 
                    retry=False
                )

            return None

        except aiohttp.ClientResponseError as e:
            print(f"HTTP Error: {e.status} - {e.message}")
            return None

        except aiohttp.ClientError as e:
            print(f"Request Error: {e}")
            return None

    def _apply_orders_to_positions(self, positions, orders):
        positions_by_id = {
            position.id: position
            for position in positions
        }

        for order in orders:
            position_id = str(order[16])

            position = positions_by_id.get(position_id)

            if position is None:
                continue

            order_type = order[5]

            if order_type == "limit":
                position.take_profit = (
                    float(order[9])
                    if order[9] is not None
                    else None
                )

            elif order_type == "stop":
                position.stop_loss = (
                    float(order[10])
                    if order[10] is not None
                    else None
                )

    # Returns access tokens
    def _get_access_token(self):
        return self.__tokens["accessToken"]

    def _get_account_id(self):
        return self.__account_details["id"]

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
            json=payload,
            authenticated=False,
            account_required=False
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
            json=payload,
            authenticated=False,
            account_required=False
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
            "/auth/jwt/all-accounts",
            account_required=False
        )

        if data is None:
            return False

        self.__account_details = data["accounts"][ACCOUNT_NUM]

        return True

    # Gets open positions for given account
    async def get_positions(self):
        position_data = await self._request(
            "GET",
            f"/trade/accounts/{self._get_account_id()}/positions"
        )

        if position_data is None:
            return None

        order_data = await self.get_orders()

        if order_data is None:
            return None

        positions = [Position.convert_to_position(row) for row in position_data["d"]["positions"]]

        self._apply_orders_to_positions(positions, order_data)

        return positions

    async def fetch_instrument_name(self, position: Position):
        key = (position.instrument_id, position.route_id)

        # Checks cache for instrument name
        if key in self.__instruments:
            return self.__instruments[key]

        data = await self._request(
            "GET",
            f"/trade/instruments/{position.instrument_id}?routeId={position.route_id}"
        )

        if data is None:
            return None

        name = data["d"]["name"]

        self.__instruments[key] = name # Caches instrument name

        return name

    async def get_orders(self):
        data = await self._request(
            "GET",
            f"/trade/accounts/{self._get_account_id()}/orders"
        )

        if data is None:
            return None

        return data["d"]["orders"]

    async def get_orders_history(self):
        data = await self._request(
            "GET",
            f"/trade/accounts/{self._get_account_id()}/ordersHistory"
        )

        if data is None:
            return None

        return data["d"]["ordersHistory"]

    def find_close_price(self, history, position_id: str):
        for order in history:
            if len(order) <= 16:
                continue

            if str(order[16]) != position_id:
                continue

            if order[9] is None:
                return None

            return float(order[9])
        
        return None

    # Closes aiohttp session
    async def close(self):
        await self.__http_session.close()