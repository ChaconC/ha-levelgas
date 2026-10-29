"""Small asynchronous client for the API used by Levelgas Android 9.4.1."""

import asyncio
from base64 import b64encode
from urllib.parse import quote

import aiohttp

from .const import API_BASE, API_KEY


class ApiError(Exception):
    """The service could not return usable data."""


class AuthError(ApiError):
    """Account authentication needs attention."""


class LevelgasClient:
    def __init__(self, session, email, password, session_token=None):
        self.http = session
        self.email = email
        self.password = password
        self.session_token = session_token if self._valid_token(session_token) else None

    @staticmethod
    def _valid_token(token):
        return isinstance(token, dict) and all(
            isinstance(token.get(k), str) and token[k] for k in ("userHash", "token")
        )

    async def _request(self, path, body=None, auth=False):
        headers = {"x-api-key": API_KEY, "Accept": "application/json"}
        if auth:
            if self.session_token is None:
                raise AuthError("Missing account session")
            credentials = f"{self.session_token['userHash']}:{self.session_token['token']}"
            headers["Authorization"] = "Basic " + b64encode(credentials.encode()).decode()
            headers["needs_authentication"] = "true"
        try:
            async with asyncio.timeout(30):
                async with self.http.request(
                    "GET" if body is None else "POST",
                    API_BASE + path,
                    json=body,
                    headers=headers,
                    allow_redirects=False,
                ) as response:
                    if response.status in (401, 403):
                        raise AuthError("Account session rejected")
                    if response.status != 200:
                        raise ApiError(f"Levelgas HTTP status {response.status}")
                    data = await response.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError, ValueError) as error:
            raise ApiError("Could not read Levelgas response") from error
        if not isinstance(data, dict):
            raise ApiError("Unexpected response format")
        if data.get("httpCode") in (401, 403):
            raise AuthError("Account session rejected")
        if data.get("apiError") not in (None, 0) or data.get("httpCode", 200) != 200:
            if path == "users/login" and data.get("httpCode", 200) < 500:
                raise AuthError("Login rejected")
            raise ApiError("Levelgas reported an API error")
        return data.get("message")

    async def login(self):
        token = await self._request(
            "users/login",
            {
                "email": self.email,
                "password": self.password,
                "uID": "XXX-XXXXXXXX-XXX",
                "deviceOSVersion": "17",
                "deviceOSName": "Android",
                "appVersion": "9.4.1",
                "deviceName": "Home Assistant",
                "loginType": "Tradicional",
            },
        )
        if not self._valid_token(token):
            raise AuthError("Login did not return a session")
        self.session_token = {key: token[key] for key in ("userHash", "token")}

    async def _authenticated(self, path):
        if self.session_token is None:
            await self.login()
        try:
            return await self._request(path, auth=True)
        except AuthError:
            await self.login()
            return await self._request(path, auth=True)

    async def tanks(self):
        tanks = await self._authenticated("tanks/tank//")
        if not isinstance(tanks, list) or not all(
            isinstance(t, dict) and isinstance(t.get("tankHash"), str) and t["tankHash"]
            for t in tanks
        ):
            raise ApiError("Invalid tank list")
        return tanks

    async def tank(self, tank_hash):
        tank = await self._authenticated("tanks/tank//" + quote(tank_hash, safe=""))
        if not isinstance(tank, dict) or tank.get("tankHash") != tank_hash:
            raise ApiError("API returned a different tank")
        return tank
