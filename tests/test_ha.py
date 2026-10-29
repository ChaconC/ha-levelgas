from unittest.mock import AsyncMock, patch

from homeassistant import config_entries
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.levelgas.api import ApiError, AuthError

TANK = {
    "tankHash": "abc",
    "tankName": "Tepepan",
    "gasLevel": 69,
    "batteryLevel": 70,
    "lastUpdateInfo": "2026-10-28 18:01:24",
    "status": 1,
    "levelHistory": [
        {"reading": v, "date": f"2026-10-{d} 18:01:24"}
        for d, v in [(24, 72), (25, 71), (26, 30), (27, 70)]
    ],
}
DATA = {
    "email": "user@example.com",
    "password": "secret",
    "tank_hash": "abc",
    "tank_name": "Tepepan",
    "session": {"userHash": "u", "token": "t"},
}


async def test_user_flow_creates_entry_and_rejects_duplicate(hass):
    with (
        patch("custom_components.levelgas.config_flow.LevelgasClient.login", new=AsyncMock()),
        patch(
            "custom_components.levelgas.config_flow.LevelgasClient.tanks",
            new=AsyncMock(return_value=[{"tankHash": "abc", "name": "Tepepan"}]),
        ),
        patch("custom_components.levelgas.async_setup_entry", return_value=True),
    ):
        result = await hass.config_entries.flow.async_init(
            "levelgas", context={"source": config_entries.SOURCE_USER}
        )
        assert result["step_id"] == "user"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"email": "user@example.com", "password": "secret"}
        )
        assert result["type"] == "create_entry"
        assert result["data"]["tank_hash"] == "abc"
        assert result["result"].unique_id == "abc"
        other = await hass.config_entries.flow.async_init(
            "levelgas",
            context={"source": config_entries.SOURCE_USER},
            data={"email": "user@example.com", "password": "secret"},
        )
        assert other["reason"] == "already_configured"


async def test_setup_four_sensors_updates_unavailable_and_unloads(hass):
    entry = MockConfigEntry(domain="levelgas", data=DATA, unique_id="abc")
    entry.add_to_hass(hass)
    with patch(
        "custom_components.levelgas.coordinator.LevelgasClient.tank",
        new=AsyncMock(return_value=TANK),
    ) as read:
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        registry = er.async_get(hass)
        ids = {
            key: registry.async_get_entity_id("sensor", "levelgas", f"abc_{key}")
            for key in ("tank_level", "battery", "last_reading", "tank_level_smoothed")
        }
        assert all(ids.values())
        assert hass.states.get(ids["tank_level"]).state == "69"
        assert hass.states.get(ids["battery"]).state == "70"
        assert float(hass.states.get(ids["tank_level_smoothed"]).state) == 70
        assert hass.states.get(ids["last_reading"]).state == "2026-10-29T00:01:24+00:00"
        assert entry.runtime_data.update_interval.total_seconds() == 7200
        read.side_effect = ApiError("Unavailable")
        await entry.runtime_data.async_refresh()
        await hass.async_block_till_done()
        assert hass.states.get(ids["tank_level"]).state == "unavailable"
        read.side_effect = None
        await entry.runtime_data.async_refresh()
        await hass.async_block_till_done()
        assert hass.states.get(ids["tank_level"]).state == "69"
        assert await hass.config_entries.async_unload(entry.entry_id)


async def test_options_validate_odd_window(hass):
    entry = MockConfigEntry(domain="levelgas", data=DATA, unique_id="abc")
    entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == "form"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {"poll_hours": 2, "smoothing_samples": 4, "timezone": "America/Mexico_City"},
    )
    assert result["errors"]["base"] == "invalid_window"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {"poll_hours": 2, "smoothing_samples": 7, "timezone": "America/Mexico_City"},
    )
    assert result["type"] == "create_entry"


async def test_session_refresh_does_not_reload_the_integration(hass):
    entry = MockConfigEntry(domain="levelgas", data=DATA, unique_id="abc")
    entry.add_to_hass(hass)
    with patch(
        "custom_components.levelgas.coordinator.LevelgasClient.tank",
        new=AsyncMock(return_value=TANK),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        with patch.object(hass.config_entries, "async_reload", new=AsyncMock()) as reload:
            entry.runtime_data.client.session_token = {"userHash": "u", "token": "new"}
            await entry.runtime_data.async_refresh()
            await hass.async_block_till_done()
            assert entry.data["session"]["token"] == "new"
            reload.assert_not_called()


async def test_invalid_auth_flow_and_empty_account(hass):
    with patch(
        "custom_components.levelgas.config_flow.LevelgasClient.login",
        new=AsyncMock(side_effect=AuthError()),
    ):
        result = await hass.config_entries.flow.async_init(
            "levelgas",
            context={"source": config_entries.SOURCE_USER},
            data={"email": "e", "password": "p"},
        )
        assert result["errors"]["base"] == "invalid_auth"
    with (
        patch("custom_components.levelgas.config_flow.LevelgasClient.login", new=AsyncMock()),
        patch(
            "custom_components.levelgas.config_flow.LevelgasClient.tanks",
            new=AsyncMock(return_value=[]),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"email": "e", "password": "p"}
        )
        assert result["reason"] == "no_tanks"


async def test_reauth_requires_access_to_same_tank(hass):
    entry = MockConfigEntry(domain="levelgas", data=DATA, unique_id="abc")
    entry.add_to_hass(hass)
    with (
        patch("custom_components.levelgas.config_flow.LevelgasClient.login", new=AsyncMock()),
        patch(
            "custom_components.levelgas.config_flow.LevelgasClient.tanks",
            new=AsyncMock(return_value=[{"tankHash": "different"}]),
        ) as tanks,
        patch.object(hass.config_entries, "async_reload", new=AsyncMock(return_value=True)),
    ):
        result = await hass.config_entries.flow.async_init(
            "levelgas",
            context={"source": config_entries.SOURCE_REAUTH, "entry_id": entry.entry_id},
            data=DATA,
        )
        assert result["step_id"] == "reauth_confirm"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"email": "e", "password": "p"}
        )
        assert result["errors"]["base"] == "wrong_account"
        tanks.return_value = [{"tankHash": "abc"}]
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"email": "e", "password": "p"}
        )
        assert result["reason"] == "reauth_successful"
