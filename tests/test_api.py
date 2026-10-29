import aiohttp
import pytest
from aiohttp import web

from custom_components.levelgas.api import ApiError, AuthError, LevelgasClient


@pytest.fixture
async def api_server(socket_enabled, aiohttp_server, monkeypatch):
    async def start(handler):
        app = web.Application()
        app.router.add_route("*", "/{path:.*}", handler)
        server = await aiohttp_server(app)
        monkeypatch.setattr("custom_components.levelgas.api.API_BASE", str(server.make_url("/")))

    return start


async def test_session_renewal_and_correct_auth_header(api_server):
    calls = []

    async def handle(request):
        calls.append(request.path)
        if request.path == "/users/login":
            assert (await request.json())["password"] == "secret"
            return web.json_response(
                {"httpCode": 200, "message": {"userHash": "u", "token": "new"}}
            )
        if request.headers["Authorization"] == "Basic dTpvbGQ=":
            return web.Response(status=401)
        assert request.headers["Authorization"] == "Basic dTpuZXc="
        return web.json_response({"httpCode": 200, "message": {"tankHash": "abc"}})

    await api_server(handle)
    async with aiohttp.ClientSession() as session:
        client = LevelgasClient(
            session, "user@example.com", "secret", {"userHash": "u", "token": "old"}
        )
        assert (await client.tank("abc"))["tankHash"] == "abc"
        assert client.session_token["token"] == "new"
    assert calls == ["/tanks/tank//abc", "/users/login", "/tanks/tank//abc"]


async def test_rejected_auth_is_bounded(api_server):
    calls = []

    async def handle(request):
        calls.append(request.path)
        if request.path == "/users/login":
            return web.json_response(
                {"httpCode": 200, "message": {"userHash": "u", "token": "new"}}
            )
        return web.Response(status=401)

    await api_server(handle)
    async with aiohttp.ClientSession() as session:
        client = LevelgasClient(session, "u", "p", {"userHash": "u", "token": "t"})
        with pytest.raises(AuthError):
            await client.tank("abc")
    assert len(calls) == 3


async def test_other_tank_response_is_rejected(api_server):
    async def handle(request):
        return web.json_response({"httpCode": 200, "message": {"tankHash": "other"}})

    await api_server(handle)
    async with aiohttp.ClientSession() as session:
        client = LevelgasClient(session, "u", "p", {"userHash": "u", "token": "t"})
        with pytest.raises(ApiError):
            await client.tank("abc")


async def test_http_200_api_failure_is_not_success(api_server):
    async def handle(request):
        return web.json_response({"httpCode": 500, "apiError": 123, "message": "bad"})

    await api_server(handle)
    async with aiohttp.ClientSession() as session:
        client = LevelgasClient(session, "u", "p", {"userHash": "u", "token": "t"})
        with pytest.raises(ApiError):
            await client.tanks()
